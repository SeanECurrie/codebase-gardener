"""
Semantic file processor that integrates Tree-sitter parsing with existing file discovery.

This module bridges the existing SimpleFileUtilities with the new Tree-sitter parsing
capabilities, providing semantic analysis integration for the CLI.
"""

import time
from pathlib import Path
from typing import Any, Optional

import structlog

from simple_file_utils import SimpleFileUtilities

from .parser import TreeSitterParser, get_supported_extensions, is_supported_file
from .preprocessor import CodeChunk, CodePreprocessor, PreprocessingConfig

logger = structlog.get_logger(__name__)


class SemanticFileProcessor:
    """
    Processes files with semantic analysis capabilities.

    Integrates existing file discovery with Tree-sitter parsing and semantic chunking.
    """

    def __init__(
        self, preprocessing_config: Optional[PreprocessingConfig] = None, settings=None
    ):
        """
        Initialize the semantic file processor.

        Args:
            preprocessing_config: Configuration for semantic preprocessing
            settings: Optional settings (for component registry compatibility)
        """
        self.file_utils = SimpleFileUtilities()
        self.preprocessor = CodePreprocessor(preprocessing_config)
        self.supported_extensions = get_supported_extensions()

        logger.info(
            "Semantic file processor initialized",
            supported_extensions=len(self.supported_extensions),
            max_chunk_size=self.preprocessor.config.max_chunk_size,
        )

    def discover_semantic_files(self, directory_path: str) -> list[Path]:
        """
        Discover files that can be processed with semantic analysis.

        Args:
            directory_path: Directory to scan for files

        Returns:
            List of file paths that support semantic analysis
        """
        try:
            # Use existing file discovery
            all_files = self.file_utils.find_source_files(Path(directory_path))

            # Filter for semantic analysis support
            semantic_files = []
            for file_path in all_files:
                # file_path is already a Path object from find_source_files
                if is_supported_file(file_path):
                    semantic_files.append(file_path)

            logger.info(
                "Semantic file discovery completed",
                directory=directory_path,
                total_files=len(all_files),
                semantic_files=len(semantic_files),
            )

            return semantic_files

        except Exception as e:
            logger.error(
                "Semantic file discovery failed", directory=directory_path, error=str(e)
            )
            return []

    def analyze_file(self, file_path: Path) -> Optional[dict[str, Any]]:
        """
        Analyze a single file with semantic parsing.

        Args:
            file_path: Path to the file to analyze

        Returns:
            Analysis results or None if analysis fails
        """
        try:
            start_time = time.time()

            # Check if file supports semantic analysis
            if not is_supported_file(file_path):
                return None

            # Read file content
            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse with Tree-sitter
            parser = TreeSitterParser.create_for_file(file_path)
            if parser is None:
                return None

            parse_result = parser.parse(content, file_path)

            # Generate semantic chunks
            chunks = self.preprocessor.preprocess_file(file_path, content)

            # Calculate analysis metrics
            analysis_time = time.time() - start_time

            result = {
                "file_path": str(file_path),
                "language": parse_result.language,
                "parse_successful": parse_result.is_valid,
                "has_errors": parse_result.has_errors,
                "error_count": len(parse_result.errors),
                "structure": {
                    "functions": len(parse_result.structure.functions),
                    "classes": len(parse_result.structure.classes),
                    "imports": len(parse_result.structure.imports),
                    "variables": len(parse_result.structure.variables),
                    "total_elements": len(parse_result.structure.get_all_elements()),
                },
                "chunks": {
                    "count": len(chunks),
                    "total_size": sum(chunk.size for chunk in chunks),
                    "types": self._get_chunk_type_distribution(chunks),
                    "average_complexity": self._calculate_average_complexity(chunks),
                },
                "file_stats": {
                    "size_bytes": len(content),
                    "line_count": len(content.split("\n")),
                    "non_empty_lines": len(
                        [line for line in content.split("\n") if line.strip()]
                    ),
                },
                "analysis_time": round(analysis_time, 3),
            }

            logger.debug(
                "File analysis completed",
                file_path=str(file_path),
                language=parse_result.language,
                chunks=len(chunks),
                analysis_time=analysis_time,
            )

            return result

        except Exception as e:
            logger.warning(
                "File analysis failed", file_path=str(file_path), error=str(e)
            )
            return None

    def analyze_codebase(self, directory_path: str) -> dict[str, Any]:
        """
        Analyze entire codebase with semantic parsing.

        Args:
            directory_path: Directory to analyze

        Returns:
            Comprehensive codebase analysis results
        """
        start_time = time.time()

        try:
            # Discover semantic files
            semantic_files = self.discover_semantic_files(directory_path)

            # Analyze each file
            file_analyses = []
            successful_analyses = 0
            failed_analyses = 0

            for file_path in semantic_files:
                analysis = self.analyze_file(file_path)
                if analysis:
                    file_analyses.append(analysis)
                    successful_analyses += 1
                else:
                    failed_analyses += 1

            # Aggregate results
            total_analysis_time = time.time() - start_time

            result = {
                "directory": directory_path,
                "analysis_timestamp": time.time(),
                "total_analysis_time": round(total_analysis_time, 3),
                "file_summary": {
                    "total_files": len(semantic_files),
                    "analyzed_successfully": successful_analyses,
                    "analysis_failed": failed_analyses,
                    "success_rate": round(
                        successful_analyses / len(semantic_files) * 100, 1
                    )
                    if semantic_files
                    else 0,
                },
                "language_distribution": self._get_language_distribution(file_analyses),
                "structure_summary": self._get_structure_summary(file_analyses),
                "chunk_summary": self._get_chunk_summary(file_analyses),
                "complexity_analysis": self._get_complexity_analysis(file_analyses),
                "file_analyses": file_analyses,
            }

            logger.info(
                "Codebase analysis completed",
                directory=directory_path,
                files_analyzed=successful_analyses,
                total_time=total_analysis_time,
            )

            return result

        except Exception as e:
            logger.error(
                "Codebase analysis failed", directory=directory_path, error=str(e)
            )
            return {
                "directory": directory_path,
                "error": str(e),
                "analysis_timestamp": time.time(),
            }

    def get_file_chunks(self, file_path: Path) -> list[CodeChunk]:
        """
        Get semantic chunks for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of semantic code chunks
        """
        try:
            if not is_supported_file(file_path):
                return []

            with open(file_path, encoding="utf-8", errors="ignore") as f:
                content = f.read()

            return self.preprocessor.preprocess_file(file_path, content)

        except Exception as e:
            logger.warning(
                "Failed to get chunks for file", file_path=str(file_path), error=str(e)
            )
            return []

    def _get_chunk_type_distribution(self, chunks: list[CodeChunk]) -> dict[str, int]:
        """Get distribution of chunk types."""
        distribution = {}
        for chunk in chunks:
            chunk_type = chunk.chunk_type.value
            distribution[chunk_type] = distribution.get(chunk_type, 0) + 1
        return distribution

    def _calculate_average_complexity(self, chunks: list[CodeChunk]) -> float:
        """Calculate average complexity score of chunks."""
        if not chunks:
            return 0.0
        return round(sum(chunk.complexity_score for chunk in chunks) / len(chunks), 2)

    def _get_language_distribution(
        self, file_analyses: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Get distribution of programming languages."""
        distribution = {}
        for analysis in file_analyses:
            language = analysis.get("language", "unknown")
            distribution[language] = distribution.get(language, 0) + 1
        return distribution

    def _get_structure_summary(
        self, file_analyses: list[dict[str, Any]]
    ) -> dict[str, int]:
        """Get summary of code structure elements."""
        summary = {
            "total_functions": 0,
            "total_classes": 0,
            "total_imports": 0,
            "total_variables": 0,
            "total_elements": 0,
        }

        for analysis in file_analyses:
            structure = analysis.get("structure", {})
            summary["total_functions"] += structure.get("functions", 0)
            summary["total_classes"] += structure.get("classes", 0)
            summary["total_imports"] += structure.get("imports", 0)
            summary["total_variables"] += structure.get("variables", 0)
            summary["total_elements"] += structure.get("total_elements", 0)

        return summary

    def _get_chunk_summary(self, file_analyses: list[dict[str, Any]]) -> dict[str, Any]:
        """Get summary of semantic chunks."""
        total_chunks = 0
        total_size = 0
        type_distribution = {}

        for analysis in file_analyses:
            chunks_info = analysis.get("chunks", {})
            total_chunks += chunks_info.get("count", 0)
            total_size += chunks_info.get("total_size", 0)

            chunk_types = chunks_info.get("types", {})
            for chunk_type, count in chunk_types.items():
                type_distribution[chunk_type] = (
                    type_distribution.get(chunk_type, 0) + count
                )

        return {
            "total_chunks": total_chunks,
            "total_size": total_size,
            "average_chunk_size": round(total_size / total_chunks, 1)
            if total_chunks > 0
            else 0,
            "type_distribution": type_distribution,
        }

    def _get_complexity_analysis(
        self, file_analyses: list[dict[str, Any]]
    ) -> dict[str, float]:
        """Get complexity analysis summary."""
        complexities = []

        for analysis in file_analyses:
            chunks_info = analysis.get("chunks", {})
            avg_complexity = chunks_info.get("average_complexity", 0)
            if avg_complexity > 0:
                complexities.append(avg_complexity)

        if not complexities:
            return {"average": 0.0, "min": 0.0, "max": 0.0}

        return {
            "average": round(sum(complexities) / len(complexities), 2),
            "min": round(min(complexities), 2),
            "max": round(max(complexities), 2),
        }


def analyze_codebase_with_semantics(
    directory_path: str, config: Optional[PreprocessingConfig] = None
) -> dict[str, Any]:
    """
    Convenience function to analyze a codebase with semantic parsing.

    Args:
        directory_path: Directory to analyze
        config: Optional preprocessing configuration

    Returns:
        Comprehensive analysis results
    """
    processor = SemanticFileProcessor(config)
    return processor.analyze_codebase(directory_path)


def get_file_semantic_chunks(
    file_path: Path, config: Optional[PreprocessingConfig] = None
) -> list[CodeChunk]:
    """
    Convenience function to get semantic chunks for a file.

    Args:
        file_path: Path to the file
        config: Optional preprocessing configuration

    Returns:
        List of semantic code chunks
    """
    processor = SemanticFileProcessor(config)
    return processor.get_file_chunks(file_path)
