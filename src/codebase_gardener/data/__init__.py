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

__all__ = [
    "CodeElement",
    "CodeStructure", 
    "ParseError",
    "ParseResult",
    "SupportedLanguage",
    "TreeSitterParser",
    "create_parser_for_file",
    "get_supported_extensions",
    "is_supported_file",
]