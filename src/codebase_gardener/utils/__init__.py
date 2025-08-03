"""
Utility functions and helpers for Codebase Gardener.

This module provides common utilities including:

- File system operations and path handling
- Error handling framework and custom exceptions
- Directory setup and initialization utilities
- Logging configuration and structured logging
"""

from .error_handling import (
    # Base exceptions
    CodebaseGardenerError,
    ConfigurationError,
    ModelError,
    ModelLoadingError,
    ModelInferenceError,
    ParsingError,
    TreeSitterError,
    StorageError,
    VectorStoreError,
    DirectorySetupError,
    NetworkError,
    ProjectError,
    TrainingError,
    
    # Retry decorators
    retry_with_backoff,
    model_retry,
    network_retry,
    storage_retry,
    
    # Error handling decorators
    handle_errors,
    graceful_fallback,
    log_errors,
    
    # Utility functions
    format_error_for_user,
    is_retryable_error,
    get_error_context,
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
]