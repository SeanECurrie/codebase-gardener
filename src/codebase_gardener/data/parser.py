"""
Tree-sitter code parser integration for multi-language AST parsing and structure extraction.

This module provides Layer 1 (Structural Analysis) of the multi-modal understanding stack,
offering AST parsing, code structure extraction, and error recovery for multiple programming languages.
"""

import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

import structlog
from tree_sitter import Language, Node, Parser, Tree

from codebase_gardener.utils.error_handling import ParsingError, retry_with_backoff

logger = structlog.get_logger(__name__)


class SupportedLanguage(Enum):
    """Supported programming languages for parsing."""

    PYTHON = "python"
    JAVASCRIPT = "javascript"
    TYPESCRIPT = "typescript"
    # Extensible for future languages: JAVA, GO, RUST, etc.


@dataclass
class CodeElement:
    """Represents a parsed code element (function, class, etc.)."""

    name: str
    element_type: str  # function, class, method, variable, etc.
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    content: str
    language: str
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate code element data."""
        if not self.name.strip():
            raise ValueError("Code element name cannot be empty")
        if self.start_line < 0 or self.end_line < 0:
            raise ValueError("Line numbers must be non-negative")
        if self.start_line > self.end_line:
            raise ValueError("Start line cannot be greater than end line")


@dataclass
class ParseError:
    """Represents a parsing error with context."""

    message: str
    line: int
    column: int
    byte_offset: int
    error_type: str = "syntax_error"
    context: Optional[str] = None


@dataclass
class CodeStructure:
    """Represents the extracted structure of a code file."""

    functions: List[CodeElement] = field(default_factory=list)
    classes: List[CodeElement] = field(default_factory=list)
    imports: List[CodeElement] = field(default_factory=list)
    variables: List[CodeElement] = field(default_factory=list)
    comments: List[CodeElement] = field(default_factory=list)

    def add_element(self, element: CodeElement) -> None:
        """Add a code element to the appropriate category."""
        if element.element_type == "function":
            self.functions.append(element)
        elif element.element_type == "class":
            self.classes.append(element)
        elif element.element_type == "import":
            self.imports.append(element)
        elif element.element_type == "variable":
            self.variables.append(element)
        elif element.element_type == "comment":
            self.comments.append(element)

    def get_all_elements(self) -> List[CodeElement]:
        """Get all code elements as a flat list."""
        return (
            self.functions +
            self.classes +
            self.imports +
            self.variables +
            self.comments
        )

    def get_element_count(self) -> Dict[str, int]:
        """Get count of each element type."""
        return {
            "functions": len(self.functions),
            "classes": len(self.classes),
            "imports": len(self.imports),
            "variables": len(self.variables),
            "comments": len(self.comments),
            "total": len(self.get_all_elements())
        }


@dataclass
class ParseResult:
    """Result of parsing a code file."""

    tree: Optional[Tree]
    structure: CodeStructure
    errors: List[ParseError] = field(default_factory=list)
    language: Optional[str] = None
    file_path: Optional[Path] = None

    @property
    def has_errors(self) -> bool:
        """Check if parsing resulted in errors."""
        return len(self.errors) > 0

    @property
    def is_valid(self) -> bool:
        """Check if parsing was successful."""
        return self.tree is not None and not self.has_errors


class TreeSitterParser:
    """
    Multi-language code parser using Tree-sitter for AST generation and structure extraction.

    Provides robust parsing with error recovery, incremental parsing support,
    and structured code element extraction for multiple programming languages.
    """

    # Language to file extension mapping
    LANGUAGE_EXTENSIONS = {
        SupportedLanguage.PYTHON: {".py", ".pyi"},
        SupportedLanguage.JAVASCRIPT: {".js", ".jsx", ".mjs"},
        SupportedLanguage.TYPESCRIPT: {".ts", ".tsx", ".d.ts"},
    }

    # Node types that represent code elements we want to extract
    ELEMENT_NODE_TYPES = {
        SupportedLanguage.PYTHON: {
            "function_definition": "function",
            "class_definition": "class",
            "import_statement": "import",
            "import_from_statement": "import",
            "assignment": "variable",
            "comment": "comment",
        },
        SupportedLanguage.JAVASCRIPT: {
            "function_declaration": "function",
            "function_expression": "function",
            "arrow_function": "function",
            "class_declaration": "class",
            "import_statement": "import",
            "variable_declaration": "variable",
            "comment": "comment",
        },
        SupportedLanguage.TYPESCRIPT: {
            "function_declaration": "function",
            "function_expression": "function",
            "arrow_function": "function",
            "class_declaration": "class",
            "interface_declaration": "interface",
            "type_alias_declaration": "type",
            "import_statement": "import",
            "variable_declaration": "variable",
            "comment": "comment",
        },
    }

    def __init__(self, language: Union[str, SupportedLanguage]):
        """
        Initialize parser for a specific language.

        Args:
            language: Programming language to parse

        Raises:
            ParsingError: If language is not supported
        """
        if isinstance(language, str):
            try:
                self.language = SupportedLanguage(language.lower())
            except ValueError:
                raise ParsingError(
                    f"Unsupported language: {language}",
                    details={"supported_languages": [lang.value for lang in SupportedLanguage]}
                )
        else:
            self.language = language

        self._language_obj = None
        self._setup_language()

        logger.info(
            "TreeSitter parser initialized",
            language=self.language.value
        )

    def _setup_language(self) -> None:
        """Set up the Tree-sitter language parser."""
        try:
            if self.language == SupportedLanguage.PYTHON:
                import tree_sitter_python as tspython
                self._language_obj = Language(tspython.language())
            elif self.language == SupportedLanguage.JAVASCRIPT:
                import tree_sitter_javascript as tsjavascript
                self._language_obj = Language(tsjavascript.language())
            elif self.language == SupportedLanguage.TYPESCRIPT:
                import tree_sitter_typescript as tstypescript
                self._language_obj = Language(tstypescript.language_typescript())
            else:
                raise ParsingError(f"Language setup not implemented: {self.language.value}")

            # Initialize parser with language (new API)
            self.parser = Parser(self._language_obj)

        except ImportError as e:
            raise ParsingError(
                f"Failed to import Tree-sitter language module for {self.language.value}",
                details={"import_error": str(e)}
            )
        except Exception as e:
            raise ParsingError(
                f"Failed to setup Tree-sitter language: {self.language.value}",
                details={"error": str(e)}
            )

    @classmethod
    def detect_language(cls, file_path: Union[str, Path]) -> Optional[SupportedLanguage]:
        """
        Detect programming language from file extension.

        Args:
            file_path: Path to the code file

        Returns:
            Detected language or None if not supported
        """
        path = Path(file_path)
        extension = path.suffix.lower()

        # Handle special cases like .d.ts
        if path.name.endswith('.d.ts'):
            extension = '.d.ts'

        for language, extensions in cls.LANGUAGE_EXTENSIONS.items():
            if extension in extensions:
                return language

        return None

    @classmethod
    def create_for_file(cls, file_path: Union[str, Path]) -> Optional['TreeSitterParser']:
        """
        Create a parser instance for a specific file based on its extension.

        Args:
            file_path: Path to the code file

        Returns:
            Parser instance or None if language not supported
        """
        language = cls.detect_language(file_path)
        if language is None:
            return None

        return cls(language)

    @retry_with_backoff(max_attempts=2)
    def parse(self, code: str, file_path: Optional[Path] = None, old_tree: Optional[Tree] = None) -> ParseResult:
        """
        Parse source code and extract structure.

        Args:
            code: Source code to parse
            file_path: Optional file path for context
            old_tree: Optional previous tree for incremental parsing

        Returns:
            ParseResult with AST, structure, and any errors

        Raises:
            ParsingError: If parsing fails completely
        """
        try:
            # Convert code to bytes for Tree-sitter
            code_bytes = code.encode('utf-8')

            # Parse with optional incremental parsing
            if old_tree is not None:
                tree = self.parser.parse(code_bytes, old_tree)
            else:
                tree = self.parser.parse(code_bytes)

            if tree is None:
                raise ParsingError(
                    "Tree-sitter returned None - parsing failed completely",
                    details={"language": self.language.value, "code_length": len(code)}
                )

            # Extract errors from the tree
            errors = self._extract_errors(tree, code)

            # Extract code structure
            structure = self._extract_structure(tree, code)

            result = ParseResult(
                tree=tree,
                structure=structure,
                errors=errors,
                language=self.language.value,
                file_path=file_path
            )

            logger.info(
                "Code parsing completed",
                language=self.language.value,
                file_path=str(file_path) if file_path else None,
                element_count=structure.get_element_count(),
                error_count=len(errors),
                has_errors=result.has_errors
            )

            return result

        except Exception as e:
            error_msg = f"Failed to parse {self.language.value} code"
            logger.error(
                error_msg,
                error=str(e),
                language=self.language.value,
                file_path=str(file_path) if file_path else None,
                code_length=len(code)
            )
            raise ParsingError(
                error_msg,
                details={
                    "language": self.language.value,
                    "error": str(e),
                    "file_path": str(file_path) if file_path else None
                }
            )

    def _extract_errors(self, tree: Tree, code: str) -> List[ParseError]:
        """Extract parsing errors from the AST."""
        errors = []
        code_lines = code.split('\n')

        def find_errors(node: Node):
            if node.type == "ERROR":
                # Calculate line and column from byte offset
                line_num = code[:node.start_byte].count('\n')
                line_start = code.rfind('\n', 0, node.start_byte) + 1
                column = node.start_byte - line_start

                # Get context around the error
                context = None
                if 0 <= line_num < len(code_lines):
                    context = code_lines[line_num]

                error = ParseError(
                    message=f"Syntax error at line {line_num + 1}",
                    line=line_num + 1,
                    column=column,
                    byte_offset=node.start_byte,
                    error_type="syntax_error",
                    context=context
                )
                errors.append(error)

            # Recursively check children
            for child in node.children:
                find_errors(child)

        find_errors(tree.root_node)
        return errors

    def _extract_structure(self, tree: Tree, code: str) -> CodeStructure:
        """Extract code structure from the AST."""
        structure = CodeStructure()
        element_types = self.ELEMENT_NODE_TYPES.get(self.language, {})

        def traverse_node(node: Node):
            # Check if this node represents a code element we want to extract
            if node.type in element_types:
                element = self._create_code_element(node, code, element_types[node.type])
                if element:
                    structure.add_element(element)

            # Recursively traverse children
            for child in node.children:
                traverse_node(child)

        traverse_node(tree.root_node)
        return structure

    def _create_code_element(self, node: Node, code: str, element_type: str) -> Optional[CodeElement]:
        """Create a CodeElement from an AST node."""
        try:
            # Extract basic information
            start_line = node.start_point[0] + 1  # Convert to 1-based line numbers
            end_line = node.end_point[0] + 1
            start_byte = node.start_byte
            end_byte = node.end_byte
            content = code[start_byte:end_byte]

            # Extract name based on node type and language
            name = self._extract_element_name(node, code)
            if not name:
                return None

            # Extract additional metadata
            metadata = self._extract_element_metadata(node, code)

            return CodeElement(
                name=name,
                element_type=element_type,
                start_line=start_line,
                end_line=end_line,
                start_byte=start_byte,
                end_byte=end_byte,
                content=content,
                language=self.language.value,
                metadata=metadata
            )

        except Exception as e:
            logger.warning(
                "Failed to create code element",
                node_type=node.type,
                error=str(e),
                language=self.language.value
            )
            return None

    def _extract_element_name(self, node: Node, code: str) -> Optional[str]:
        """Extract the name of a code element from its AST node."""
        try:
            if self.language == SupportedLanguage.PYTHON:
                return self._extract_python_name(node, code)
            elif self.language in [SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT]:
                return self._extract_js_ts_name(node, code)
            else:
                return None
        except Exception:
            return None

    def _extract_python_name(self, node: Node, code: str) -> Optional[str]:
        """Extract name from Python AST node."""
        if node.type in ["function_definition", "class_definition"]:
            # Look for identifier child
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]
        elif node.type in ["import_statement", "import_from_statement"]:
            # Extract import names
            names = []
            for child in node.children:
                if child.type == "dotted_name" or child.type == "identifier":
                    names.append(code[child.start_byte:child.end_byte])
            return ", ".join(names) if names else None
        elif node.type == "assignment":
            # Extract variable name from assignment
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]

        return None

    def _extract_js_ts_name(self, node: Node, code: str) -> Optional[str]:
        """Extract name from JavaScript/TypeScript AST node."""
        if node.type in ["function_declaration", "class_declaration"]:
            # Look for identifier child
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]
        elif node.type == "function_expression":
            # May be anonymous
            for child in node.children:
                if child.type == "identifier":
                    return code[child.start_byte:child.end_byte]
            return "<anonymous>"
        elif node.type == "arrow_function":
            return "<arrow_function>"
        elif node.type == "import_statement":
            # Extract import specifiers
            names = []
            for child in node.children:
                if child.type == "import_specifier":
                    for grandchild in child.children:
                        if grandchild.type == "identifier":
                            names.append(code[grandchild.start_byte:grandchild.end_byte])
            return ", ".join(names) if names else None
        elif node.type == "variable_declaration":
            # Extract variable names
            names = []
            for child in node.children:
                if child.type == "variable_declarator":
                    for grandchild in child.children:
                        if grandchild.type == "identifier":
                            names.append(code[grandchild.start_byte:grandchild.end_byte])
            return ", ".join(names) if names else None

        return None

    def _extract_element_metadata(self, node: Node, code: str) -> Dict[str, Any]:
        """Extract additional metadata for a code element."""
        metadata = {
            "node_type": node.type,
            "child_count": len(node.children),
            "byte_size": node.end_byte - node.start_byte,
        }

        # Add language-specific metadata
        if self.language == SupportedLanguage.PYTHON:
            metadata.update(self._extract_python_metadata(node, code))
        elif self.language in [SupportedLanguage.JAVASCRIPT, SupportedLanguage.TYPESCRIPT]:
            metadata.update(self._extract_js_ts_metadata(node, code))

        return metadata

    def _extract_python_metadata(self, node: Node, code: str) -> Dict[str, Any]:
        """Extract Python-specific metadata."""
        metadata = {}

        if node.type == "function_definition":
            # Check for decorators
            decorators = []
            for child in node.children:
                if child.type == "decorator":
                    decorators.append(code[child.start_byte:child.end_byte])
            if decorators:
                metadata["decorators"] = decorators

            # Check for async
            if "async" in code[node.start_byte:node.start_byte + 20]:
                metadata["is_async"] = True

        elif node.type == "class_definition":
            # Check for base classes
            for child in node.children:
                if child.type == "argument_list":
                    metadata["has_base_classes"] = True
                    break

        return metadata

    def _extract_js_ts_metadata(self, node: Node, code: str) -> Dict[str, Any]:
        """Extract JavaScript/TypeScript-specific metadata."""
        metadata = {}

        if node.type in ["function_declaration", "function_expression"]:
            # Check for async
            if "async" in code[max(0, node.start_byte - 10):node.start_byte + 20]:
                metadata["is_async"] = True

        elif node.type == "arrow_function":
            metadata["is_arrow_function"] = True

        return metadata


def create_parser_for_file(file_path: Union[str, Path]) -> Optional[TreeSitterParser]:
    """
    Convenience function to create a parser for a specific file.

    Args:
        file_path: Path to the code file

    Returns:
        Parser instance or None if language not supported
    """
    return TreeSitterParser.create_for_file(file_path)


def get_supported_extensions() -> Set[str]:
    """
    Get all supported file extensions.

    Returns:
        Set of supported file extensions
    """
    extensions = set()
    for lang_extensions in TreeSitterParser.LANGUAGE_EXTENSIONS.values():
        extensions.update(lang_extensions)
    return extensions


def is_supported_file(file_path: Union[str, Path]) -> bool:
    """
    Check if a file is supported for parsing.

    Args:
        file_path: Path to check

    Returns:
        True if file is supported
    """
    return TreeSitterParser.detect_language(file_path) is not None
