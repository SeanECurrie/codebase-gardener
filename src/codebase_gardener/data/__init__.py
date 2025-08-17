"""
Data processing and parsing module for semantic code analysis.

This module provides Tree-sitter based parsing and semantic chunking capabilities
for converting source code into structured, embedded representations.
"""

# Tree-sitter parsing
from .parser import (
    CodeElement,
    CodeStructure,
    ParseError,
    ParseResult,
    SupportedLanguage,
    TreeSitterParser,
    create_parser_for_file,
    get_supported_extensions,
    is_supported_file,
)

# Semantic preprocessing and chunking
from .preprocessor import (
    ChunkType,
    CodeChunk,
    CodePreprocessor,
    PreprocessingConfig,
    preprocess_code_string,
    preprocess_file,
)

# Semantic file processing integration
from .semantic_file_processor import (
    SemanticFileProcessor,
    analyze_codebase_with_semantics,
    get_file_semantic_chunks,
)

__all__ = [
    # Parser exports
    "TreeSitterParser",
    "SupportedLanguage",
    "CodeElement",
    "ParseResult",
    "CodeStructure",
    "ParseError",
    "create_parser_for_file",
    "get_supported_extensions",
    "is_supported_file",
    # Preprocessor exports
    "CodePreprocessor",
    "CodeChunk",
    "ChunkType",
    "PreprocessingConfig",
    "preprocess_file",
    "preprocess_code_string",
    # Semantic file processor exports
    "SemanticFileProcessor",
    "analyze_codebase_with_semantics",
    "get_file_semantic_chunks",
]
