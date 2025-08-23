"""
Data processing and parsing module for semantic code analysis.

This module provides Tree-sitter based parsing and semantic chunking capabilities
for converting source code into structured, embedded representations.
"""

# Tree-sitter parsing
# Embedding management orchestration
from .embedding_manager import (
    EmbeddingJobResult,
    EmbeddingManager,
    EmbeddingManagerConfig,
    create_embedding_manager,
)

# Embedding generation and management
from .embeddings import (
    EmbeddingConfig,
    EmbeddingResult,
    NomicEmbeddings,
    create_embeddings_generator,
)
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

# Vector storage system
from .vector_store import (
    SearchResult,
    VectorStore,
    VectorStoreStats,
    create_vector_store,
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
    # Embedding system exports
    "NomicEmbeddings",
    "EmbeddingConfig",
    "EmbeddingResult",
    "create_embeddings_generator",
    # Vector store exports
    "VectorStore",
    "VectorStoreStats",
    "SearchResult",
    "create_vector_store",
    # Embedding manager exports
    "EmbeddingManager",
    "EmbeddingManagerConfig",
    "EmbeddingJobResult",
    "create_embedding_manager",
]
