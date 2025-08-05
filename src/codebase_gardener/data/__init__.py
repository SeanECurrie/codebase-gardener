"""
Data processing and storage for Codebase Gardener.

This module handles:

- Code parsing using Tree-sitter for multiple programming languages
- Code preprocessing and intelligent chunking
- Vector storage using LanceDB for similarity search
- Project-specific vector store management
"""

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

from .preprocessor import (
    ChunkType,
    CodeChunk,
    CodePreprocessor,
    PreprocessingConfig,
    preprocess_file,
    preprocess_code_string,
)

from .vector_store import (
    CodeChunkSchema,
    SearchResult,
    VectorStore,
)

from .project_vector_store import (
    ProjectVectorStoreInfo,
    ProjectVectorStoreManager,
    get_project_vector_store_manager,
    reset_project_vector_store_manager,
)

__all__ = [
    # Parser exports
    "CodeElement",
    "CodeStructure", 
    "ParseError",
    "ParseResult",
    "SupportedLanguage",
    "TreeSitterParser",
    "create_parser_for_file",
    "get_supported_extensions",
    "is_supported_file",
    # Preprocessor exports
    "ChunkType",
    "CodeChunk",
    "CodePreprocessor",
    "PreprocessingConfig",
    "preprocess_file",
    "preprocess_code_string",
    # Vector store exports
    "CodeChunkSchema",
    "SearchResult",
    "VectorStore",
    # Project vector store exports
    "ProjectVectorStoreInfo",
    "ProjectVectorStoreManager",
    "get_project_vector_store_manager",
    "reset_project_vector_store_manager",
]