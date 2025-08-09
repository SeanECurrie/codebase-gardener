"""
Utility functions and helpers for Codebase Gardener.

This module provides common utilities including:

- File system operations and path handling
- Error handling framework and custom exceptions
- Directory setup and initialization utilities
- Logging configuration and structured logging
"""

from .error_handling import (  # Base exceptions; Retry decorators; Error handling decorators; Utility functions
    CodebaseGardenerError,
    ConfigurationError,
    DirectorySetupError,
    FileUtilityError,
    ModelError,
    ModelInferenceError,
    ModelLoadingError,
    NetworkError,
    ParsingError,
    ProjectError,
    StorageError,
    TrainingError,
    TreeSitterError,
    VectorStoreError,
    format_error_for_user,
    get_error_context,
    graceful_fallback,
    handle_errors,
    is_retryable_error,
    log_errors,
    model_retry,
    network_retry,
    retry_with_backoff,
    storage_retry,
)
from .file_utils import (  # Classes and enums; Convenience functions
    FileChange,
    FileInfo,
    FileSnapshot,
    FileType,
    FileUtilities,
    atomic_write_file,
    detect_file_type,
    find_source_files,
    get_file_info,
    is_source_code_file,
    normalize_path,
    safe_read_file,
)

__all__ = [
    # Base exceptions
    "CodebaseGardenerError",
    "ConfigurationError",
    "ModelError",
    "ModelLoadingError",
    "ModelInferenceError",
    "ParsingError",
    "TreeSitterError",
    "StorageError",
    "VectorStoreError",
    "DirectorySetupError",
    "NetworkError",
    "ProjectError",
    "TrainingError",
    "FileUtilityError",

    # Retry decorators
    "retry_with_backoff",
    "model_retry",
    "network_retry",
    "storage_retry",

    # Error handling decorators
    "handle_errors",
    "graceful_fallback",
    "log_errors",

    # Utility functions
    "format_error_for_user",
    "is_retryable_error",
    "get_error_context",

    # File utilities classes and enums
    "FileUtilities",
    "FileType",
    "FileInfo",
    "FileChange",
    "FileSnapshot",

    # File utilities convenience functions
    "detect_file_type",
    "is_source_code_file",
    "get_file_info",
    "find_source_files",
    "safe_read_file",
    "atomic_write_file",
    "normalize_path",
]
