"""
Code preprocessing and intelligent chunking system using AST structure.

This module provides Layer 2 of the multi-modal understanding stack, transforming
parsed AST structures into semantically meaningful code chunks with metadata
for embedding generation and LoRA training.
"""

import hashlib
import re
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from codebase_gardener.data.parser import (
    CodeElement,
    ParseResult,
    TreeSitterParser,
)
from codebase_gardener.utils.error_handling import (
    PreprocessingError,
    retry_with_backoff,
)

logger = structlog.get_logger(__name__)


class ChunkType(Enum):
    """Types of code chunks based on semantic meaning."""

    FUNCTION = "function"
    CLASS = "class"
    METHOD = "method"
    MODULE = "module"
    IMPORT = "import"
    VARIABLE = "variable"
    COMMENT = "comment"
    INTERFACE = "interface"
    TYPE = "type"
    BLOCK = "block"


@dataclass
class CodeChunk:
    """
    Represents a semantically meaningful chunk of code with metadata.

    This is the primary output of the preprocessing system, designed for
    embedding generation and LoRA training.
    """

    id: str
    content: str
    language: str
    chunk_type: ChunkType
    file_path: Path | None
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    metadata: dict[str, Any] = field(default_factory=dict)
    dependencies: list[str] = field(default_factory=list)
    complexity_score: float = 0.0

    def __post_init__(self):
        """Validate chunk data."""
        if not self.content.strip():
            raise ValueError("Code chunk content cannot be empty")
        if self.start_line < 0 or self.end_line < 0:
            raise ValueError("Line numbers must be non-negative")
        if self.start_line > self.end_line:
            raise ValueError("Start line cannot be greater than end line")
        if self.complexity_score < 0:
            raise ValueError("Complexity score must be non-negative")

    @property
    def size(self) -> int:
        """Get the size of the chunk in characters."""
        return len(self.content)

    @property
    def non_whitespace_size(self) -> int:
        """Get the size of the chunk excluding whitespace."""
        return len(re.sub(r"\s+", "", self.content))

    @property
    def line_count(self) -> int:
        """Get the number of lines in the chunk."""
        return self.end_line - self.start_line + 1


@dataclass
class PreprocessingConfig:
    """Configuration for code preprocessing and chunking."""

    max_chunk_size: int = 2048  # Maximum characters per chunk
    min_chunk_size: int = 50  # Minimum characters per chunk
    overlap_size: int = 100  # Overlap between chunks in characters
    preserve_comments: bool = True
    preserve_docstrings: bool = True
    normalize_whitespace: bool = True
    extract_imports: bool = True
    calculate_complexity: bool = True
    include_context: bool = True  # Include surrounding context in metadata


class CodePreprocessor:
    """
    Intelligent code preprocessing and chunking system.

    Transforms parsed AST structures into semantically meaningful chunks
    with rich metadata for embedding generation and LoRA training.
    """

    def __init__(self, config: PreprocessingConfig | None = None, settings=None):
        """
        Initialize the preprocessor with configuration.

        Args:
            config: Preprocessing configuration, uses defaults if None
            settings: Optional settings (for component registry compatibility)
        """
        self.config = config or PreprocessingConfig()

        logger.info(
            "Code preprocessor initialized",
            max_chunk_size=self.config.max_chunk_size,
            min_chunk_size=self.config.min_chunk_size,
            preserve_comments=self.config.preserve_comments,
        )

    @retry_with_backoff(max_attempts=2)
    def preprocess_file(self, file_path: Path, code: str) -> list[CodeChunk]:
        """
        Preprocess a code file into semantic chunks.

        Args:
            file_path: Path to the code file
            code: Source code content

        Returns:
            List of CodeChunk objects

        Raises:
            PreprocessingError: If preprocessing fails
        """
        try:
            # Parse the code using Tree-sitter
            parser = TreeSitterParser.create_for_file(file_path)
            if parser is None:
                raise PreprocessingError(
                    f"Unsupported file type: {file_path.suffix}",
                    details={"file_path": str(file_path)},
                )

            parse_result = parser.parse(code, file_path)

            # Generate chunks from the parsed structure
            chunks = self._generate_chunks(parse_result, code, file_path)

            # Post-process chunks
            chunks = self._post_process_chunks(chunks)

            logger.info(
                "File preprocessing completed",
                file_path=str(file_path),
                chunk_count=len(chunks),
                total_size=sum(chunk.size for chunk in chunks),
                language=parse_result.language,
            )

            return chunks

        except Exception as e:
            error_msg = f"Failed to preprocess file: {file_path}"
            logger.error(error_msg, error=str(e), file_path=str(file_path))
            raise PreprocessingError(
                error_msg, details={"file_path": str(file_path), "error": str(e)}
            )

    def preprocess_code(
        self, code: str, language: str, file_path: Path | None = None
    ) -> list[CodeChunk]:
        """
        Preprocess code string into semantic chunks.

        Args:
            code: Source code content
            language: Programming language
            file_path: Optional file path for context

        Returns:
            List of CodeChunk objects

        Raises:
            PreprocessingError: If preprocessing fails
        """
        try:
            # Create parser for the specified language
            parser = TreeSitterParser(language)
            parse_result = parser.parse(code, file_path)

            # Generate chunks from the parsed structure
            chunks = self._generate_chunks(parse_result, code, file_path)

            # Post-process chunks
            chunks = self._post_process_chunks(chunks)

            logger.info(
                "Code preprocessing completed",
                chunk_count=len(chunks),
                total_size=sum(chunk.size for chunk in chunks),
                language=language,
            )

            return chunks

        except Exception as e:
            error_msg = f"Failed to preprocess {language} code"
            logger.error(error_msg, error=str(e), language=language)
            raise PreprocessingError(
                error_msg, details={"language": language, "error": str(e)}
            )

    def _generate_chunks(
        self, parse_result: ParseResult, code: str, file_path: Path | None
    ) -> list[CodeChunk]:
        """Generate chunks from parsed code structure."""
        chunks = []

        # Extract module-level information
        module_info = self._extract_module_info(parse_result, code)

        # Process each code element
        for element in parse_result.structure.get_all_elements():
            chunk = self._create_chunk_from_element(
                element, code, file_path, module_info
            )
            if chunk and self._is_valid_chunk(chunk):
                chunks.append(chunk)

        # Handle large elements that need splitting
        chunks = self._split_oversized_chunks(chunks, code)

        # Add module-level chunk if significant content exists
        module_chunk = self._create_module_chunk(
            parse_result, code, file_path, module_info
        )
        if module_chunk and self._is_valid_chunk(module_chunk):
            chunks.insert(0, module_chunk)

        return chunks

    def _extract_module_info(
        self, parse_result: ParseResult, code: str
    ) -> dict[str, Any]:
        """Extract module-level information for context."""
        info = {
            "imports": [],
            "docstring": None,
            "language": parse_result.language,
            "has_errors": parse_result.has_errors,
            "element_count": parse_result.structure.get_element_count(),
        }

        # Extract imports
        for import_element in parse_result.structure.imports:
            info["imports"].append(
                {
                    "name": import_element.name,
                    "content": import_element.content.strip(),
                    "line": import_element.start_line,
                }
            )

        # Extract module docstring (first string literal or comment)
        lines = code.split("\n")
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Found docstring
                docstring_lines = [stripped]
                quote_type = stripped[:3]
                if not stripped.endswith(quote_type) or len(stripped) == 3:
                    # Multi-line docstring
                    for j in range(i + 1, min(i + 20, len(lines))):
                        docstring_lines.append(lines[j])
                        if lines[j].strip().endswith(quote_type):
                            break
                info["docstring"] = "\n".join(docstring_lines)
                break
            elif stripped.startswith("#") and len(stripped) > 10:
                # Module-level comment
                info["docstring"] = stripped
                break

        return info

    def _create_chunk_from_element(
        self,
        element: CodeElement,
        code: str,
        file_path: Path | None,
        module_info: dict[str, Any],
    ) -> CodeChunk | None:
        """Create a code chunk from a parsed code element."""
        try:
            # Determine chunk type
            chunk_type = self._map_element_to_chunk_type(element)

            # Normalize content
            content = self._normalize_content(element.content)

            # Generate unique ID
            chunk_id = self._generate_chunk_id(content, element.start_line, file_path)

            # Extract dependencies
            dependencies = self._extract_dependencies(element, module_info)

            # Calculate complexity
            complexity = (
                self._calculate_complexity(element, code)
                if self.config.calculate_complexity
                else 0.0
            )

            # Build metadata
            metadata = self._build_chunk_metadata(element, module_info, complexity)

            return CodeChunk(
                id=chunk_id,
                content=content,
                language=element.language,
                chunk_type=chunk_type,
                file_path=file_path,
                start_line=element.start_line,
                end_line=element.end_line,
                start_byte=element.start_byte,
                end_byte=element.end_byte,
                metadata=metadata,
                dependencies=dependencies,
                complexity_score=complexity,
            )

        except Exception as e:
            logger.warning(
                "Failed to create chunk from element",
                element_name=element.name,
                element_type=element.element_type,
                error=str(e),
            )
            return None

    def _map_element_to_chunk_type(self, element: CodeElement) -> ChunkType:
        """Map a code element type to a chunk type."""
        mapping = {
            "function": ChunkType.FUNCTION,
            "class": ChunkType.CLASS,
            "method": ChunkType.METHOD,
            "import": ChunkType.IMPORT,
            "variable": ChunkType.VARIABLE,
            "comment": ChunkType.COMMENT,
            "interface": ChunkType.INTERFACE,
            "type": ChunkType.TYPE,
        }

        return mapping.get(element.element_type, ChunkType.BLOCK)

    def _normalize_content(self, content: str) -> str:
        """Normalize code content for consistent processing."""
        if not self.config.normalize_whitespace:
            return content

        # Remove excessive blank lines
        content = re.sub(r"\n\s*\n\s*\n", "\n\n", content)

        # Normalize indentation (convert tabs to spaces)
        content = content.expandtabs(4)

        # Remove trailing whitespace from lines
        lines = content.split("\n")
        lines = [line.rstrip() for line in lines]
        content = "\n".join(lines)

        # Ensure content ends with newline
        if content and not content.endswith("\n"):
            content += "\n"

        return content

    def _generate_chunk_id(
        self, content: str, start_line: int, file_path: Path | None
    ) -> str:
        """Generate a unique ID for a code chunk."""
        # Create a hash based on content, location, and file path
        hash_input = f"{content}{start_line}{file_path or ''}"
        return hashlib.md5(
            hash_input.encode("utf-8"), usedforsecurity=False
        ).hexdigest()[:12]

    def _extract_dependencies(
        self, element: CodeElement, module_info: dict[str, Any]
    ) -> list[str]:
        """Extract dependencies for a code element."""
        dependencies = []

        # Add imports as dependencies
        for import_info in module_info.get("imports", []):
            dependencies.append(import_info["name"])

        # Extract function/method calls from content
        content = element.content

        # Simple regex patterns for common dependency patterns
        patterns = [
            r"(\w+)\(",  # Function calls
            r"from\s+(\w+(?:\.\w+)*)",  # From imports
            r"import\s+(\w+(?:\.\w+)*)",  # Import statements
            r"(\w+)\.(\w+)",  # Method calls
        ]

        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if isinstance(match, tuple):
                    dependencies.extend(match)
                else:
                    dependencies.append(match)

        # Remove duplicates and filter out common keywords
        keywords = {
            "if",
            "else",
            "for",
            "while",
            "def",
            "class",
            "return",
            "len",
            "str",
            "int",
            "float",
            "self",
            "True",
            "False",
            "None",
            "and",
            "or",
            "not",
            "in",
            "is",
            "with",
            "as",
            "try",
            "except",
            "finally",
            "raise",
            "from",
            "import",
            "pass",
            "break",
            "continue",
        }
        dependencies = list(
            set(dep for dep in dependencies if dep not in keywords and len(dep) > 1)
        )

        return dependencies[:10]  # Limit to top 10 dependencies

    def _calculate_complexity(self, element: CodeElement, code: str) -> float:
        """Calculate complexity score for a code element."""
        content = element.content

        # Basic complexity metrics
        complexity = 1.0  # Base complexity

        # Cyclomatic complexity indicators
        complexity_keywords = [
            "if",
            "elif",
            "else",
            "for",
            "while",
            "try",
            "except",
            "finally",
            "with",
        ]
        for keyword in complexity_keywords:
            complexity += content.count(f" {keyword} ") + content.count(f"\n{keyword} ")

        # Nesting depth (approximate)
        lines = content.split("\n")
        max_indent = 0
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                max_indent = max(
                    max_indent, indent // 4
                )  # Assuming 4-space indentation

        complexity += max_indent * 0.5

        # Function/method calls
        complexity += len(re.findall(r"\w+\(", content)) * 0.1

        # Length factor
        complexity += len(content) / 1000.0

        return round(complexity, 2)

    def _build_chunk_metadata(
        self, element: CodeElement, module_info: dict[str, Any], complexity: float
    ) -> dict[str, Any]:
        """Build comprehensive metadata for a code chunk."""
        metadata = {
            "element_type": element.element_type,
            "element_name": element.name,
            "line_count": element.end_line - element.start_line + 1,
            "byte_size": element.end_byte - element.start_byte,
            "complexity": complexity,
            "language": element.language,
        }

        # Add element-specific metadata
        metadata.update(element.metadata)

        # Add module context if enabled
        if self.config.include_context:
            metadata["module_info"] = {
                "import_count": len(module_info.get("imports", [])),
                "has_docstring": module_info.get("docstring") is not None,
                "total_elements": module_info.get("element_count", {}).get("total", 0),
            }

        # Add quality indicators
        metadata["quality_indicators"] = {
            "has_docstring": self._has_docstring(element.content),
            "has_comments": self._has_comments(element.content),
            "is_well_formatted": self._is_well_formatted(element.content),
        }

        return metadata

    def _has_docstring(self, content: str) -> bool:
        """Check if content has a docstring."""
        lines = content.strip().split("\n")
        for line in lines[1:4]:  # Check first few lines after definition
            stripped = line.strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                return True
        return False

    def _has_comments(self, content: str) -> bool:
        """Check if content has comments."""
        return "#" in content or "//" in content or "/*" in content

    def _is_well_formatted(self, content: str) -> bool:
        """Basic check for code formatting quality."""
        lines = content.split("\n")
        if not lines:
            return False

        # Check for consistent indentation
        indents = []
        for line in lines:
            if line.strip():
                indent = len(line) - len(line.lstrip())
                indents.append(indent)

        if not indents:
            return True

        # Check if indentation is consistent (multiples of 2 or 4)
        consistent = all(indent % 2 == 0 or indent % 4 == 0 for indent in indents)

        # Check for reasonable line length (not too long)
        reasonable_length = all(len(line) < 120 for line in lines)

        return consistent and reasonable_length

    def _create_module_chunk(
        self,
        parse_result: ParseResult,
        code: str,
        file_path: Path | None,
        module_info: dict[str, Any],
    ) -> CodeChunk | None:
        """Create a chunk representing module-level content."""
        # Extract module-level content (imports, docstring, module variables)
        module_content_parts = []

        # Add docstring if present
        if module_info.get("docstring"):
            module_content_parts.append(module_info["docstring"])

        # Add imports
        if self.config.extract_imports and module_info.get("imports"):
            import_lines = [imp["content"] for imp in module_info["imports"]]
            module_content_parts.extend(import_lines)

        # Add module-level variables and constants
        for var_element in parse_result.structure.variables:
            if var_element.start_line <= 20:  # Only top-level variables
                module_content_parts.append(var_element.content.strip())

        if not module_content_parts:
            return None

        content = "\n".join(module_content_parts)
        content = self._normalize_content(content)

        if len(content.strip()) < self.config.min_chunk_size:
            return None

        # Generate chunk
        chunk_id = self._generate_chunk_id(content, 1, file_path)

        metadata = {
            "element_type": "module",
            "element_name": file_path.stem if file_path else "module",
            "line_count": len(content.split("\n")),
            "byte_size": len(content),
            "complexity": 1.0,
            "language": parse_result.language,
            "is_module_chunk": True,
            "import_count": len(module_info.get("imports", [])),
            "has_docstring": module_info.get("docstring") is not None,
        }

        return CodeChunk(
            id=chunk_id,
            content=content,
            language=parse_result.language or "unknown",
            chunk_type=ChunkType.MODULE,
            file_path=file_path,
            start_line=1,
            end_line=len(content.split("\n")),
            start_byte=0,
            end_byte=len(content),
            metadata=metadata,
            dependencies=module_info.get("imports", [])[:5],  # Top 5 imports
            complexity_score=1.0,
        )

    def _is_valid_chunk(self, chunk: CodeChunk) -> bool:
        """Check if a chunk meets quality criteria."""
        # Content quality
        content = chunk.content.strip()
        if not content:
            return False

        # Size constraints - be more lenient for meaningful code structures
        if chunk.chunk_type in [ChunkType.FUNCTION, ChunkType.CLASS, ChunkType.METHOD]:
            # For code structures, use a lower minimum size
            if chunk.non_whitespace_size < max(20, self.config.min_chunk_size // 3):
                return False
        else:
            # For other chunks, use the configured minimum
            if chunk.non_whitespace_size < self.config.min_chunk_size:
                return False

        # Skip chunks that are just comments unless configured to preserve them
        if chunk.chunk_type == ChunkType.COMMENT and not self.config.preserve_comments:
            return False

        # Skip trivial chunks (e.g., single variable assignments without context)
        if chunk.chunk_type == ChunkType.VARIABLE and len(content.split("\n")) == 1:
            return False

        return True

    def _split_oversized_chunks(
        self, chunks: list[CodeChunk], code: str
    ) -> list[CodeChunk]:
        """Split chunks that exceed maximum size."""
        result = []

        for chunk in chunks:
            if chunk.size <= self.config.max_chunk_size:
                result.append(chunk)
            else:
                # Split large chunk
                split_chunks = self._split_chunk(chunk, code)
                result.extend(split_chunks)

        return result

    def _split_chunk(self, chunk: CodeChunk, code: str) -> list[CodeChunk]:
        """Split a large chunk into smaller semantic pieces."""
        # For now, implement simple line-based splitting
        # TODO: Implement more sophisticated AST-based splitting

        lines = chunk.content.split("\n")
        if len(lines) <= 2:
            return [chunk]  # Can't split further

        # Split roughly in half, but try to find good break points
        mid_point = len(lines) // 2

        # Look for natural break points around the mid point
        break_point = mid_point
        for i in range(max(1, mid_point - 5), min(len(lines) - 1, mid_point + 5)):
            line = lines[i].strip()
            if (
                not line
                or line.startswith("#")
                or line.startswith("def ")
                or line.startswith("class ")
            ):
                break_point = i
                break

        # Create two chunks
        first_lines = lines[:break_point]
        second_lines = lines[break_point:]

        chunks = []

        # First chunk
        if first_lines:
            first_content = "\n".join(first_lines)
            first_chunk = CodeChunk(
                id=chunk.id + "_1",
                content=first_content,
                language=chunk.language,
                chunk_type=chunk.chunk_type,
                file_path=chunk.file_path,
                start_line=chunk.start_line,
                end_line=chunk.start_line + len(first_lines) - 1,
                start_byte=chunk.start_byte,
                end_byte=chunk.start_byte + len(first_content),
                metadata={**chunk.metadata, "is_split_chunk": True, "split_part": 1},
                dependencies=chunk.dependencies,
                complexity_score=chunk.complexity_score * 0.6,
            )
            chunks.append(first_chunk)

        # Second chunk
        if second_lines:
            second_content = "\n".join(second_lines)
            second_chunk = CodeChunk(
                id=chunk.id + "_2",
                content=second_content,
                language=chunk.language,
                chunk_type=chunk.chunk_type,
                file_path=chunk.file_path,
                start_line=chunk.start_line + break_point,
                end_line=chunk.end_line,
                start_byte=chunk.start_byte + len("\n".join(first_lines)) + 1,
                end_byte=chunk.end_byte,
                metadata={**chunk.metadata, "is_split_chunk": True, "split_part": 2},
                dependencies=chunk.dependencies,
                complexity_score=chunk.complexity_score * 0.4,
            )
            chunks.append(second_chunk)

        return chunks

    def _post_process_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Post-process chunks for quality and consistency."""
        # Sort chunks by line number
        chunks.sort(key=lambda c: c.start_line)

        # Remove duplicates based on content similarity
        chunks = self._remove_duplicate_chunks(chunks)

        # Add overlap if configured
        if self.config.overlap_size > 0:
            chunks = self._add_chunk_overlap(chunks)

        return chunks

    def _remove_duplicate_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Remove duplicate chunks based on content similarity."""
        seen_hashes = set()
        unique_chunks = []

        for chunk in chunks:
            # Create a hash of normalized content
            normalized = re.sub(r"\s+", " ", chunk.content.strip())
            content_hash = hashlib.md5(
                normalized.encode("utf-8"), usedforsecurity=False
            ).hexdigest()

            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_chunks.append(chunk)

        return unique_chunks

    def _add_chunk_overlap(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Add overlap between adjacent chunks."""
        if len(chunks) <= 1:
            return chunks

        overlapped_chunks = []

        for i, chunk in enumerate(chunks):
            if i == 0:
                overlapped_chunks.append(chunk)
                continue

            prev_chunk = chunks[i - 1]

            # Add overlap from previous chunk
            overlap_lines = min(
                self.config.overlap_size
                // 50,  # Approximate lines from character count
                3,  # Maximum 3 lines of overlap
            )

            if overlap_lines > 0:
                prev_lines = prev_chunk.content.split("\n")
                overlap_content = "\n".join(prev_lines[-overlap_lines:])

                # Create new chunk with overlap
                new_content = overlap_content + "\n" + chunk.content
                new_chunk = CodeChunk(
                    id=chunk.id,
                    content=new_content,
                    language=chunk.language,
                    chunk_type=chunk.chunk_type,
                    file_path=chunk.file_path,
                    start_line=chunk.start_line - overlap_lines,
                    end_line=chunk.end_line,
                    start_byte=chunk.start_byte,
                    end_byte=chunk.end_byte,
                    metadata={**chunk.metadata, "has_overlap": True},
                    dependencies=chunk.dependencies,
                    complexity_score=chunk.complexity_score,
                )
                overlapped_chunks.append(new_chunk)
            else:
                overlapped_chunks.append(chunk)

        return overlapped_chunks


def preprocess_file(
    file_path: Path, config: PreprocessingConfig | None = None
) -> list[CodeChunk]:
    """
    Convenience function to preprocess a single file.

    Args:
        file_path: Path to the code file
        config: Optional preprocessing configuration

    Returns:
        List of CodeChunk objects
    """
    preprocessor = CodePreprocessor(config)

    with open(file_path, encoding="utf-8") as f:
        code = f.read()

    return preprocessor.preprocess_file(file_path, code)


def preprocess_code_string(
    code: str, language: str, config: PreprocessingConfig | None = None
) -> list[CodeChunk]:
    """
    Convenience function to preprocess a code string.

    Args:
        code: Source code content
        language: Programming language
        config: Optional preprocessing configuration

    Returns:
        List of CodeChunk objects
    """
    preprocessor = CodePreprocessor(config)
    return preprocessor.preprocess_code(code, language)
