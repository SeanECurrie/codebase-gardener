"""
Error handling framework for Codebase Gardener.

This module provides a comprehensive error handling system with:
- Custom exception hierarchy for structured error handling
- Retry decorators with exponential backoff
- Integration with structured logging
- User-friendly error messages
"""

import functools
import time
from collections.abc import Callable
from datetime import datetime
from typing import Any, TypeVar

import structlog
from tenacity import (
    RetryError,
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

logger = structlog.get_logger(__name__)

# Type variable for decorated functions
F = TypeVar('F', bound=Callable[..., Any])


class CodebaseGardenerError(Exception):
    """Base exception for all Codebase Gardener errors.

    Provides structured error handling with context and user-friendly messages.
    """

    def __init__(
        self,
        message: str,
        details: dict[str, Any] | None = None,
        user_message: str | None = None,
        suggestions: list[str] | None = None
    ):
        super().__init__(message)
        self.message = message
        self.details = details or {}
        self.user_message = user_message or message
        self.suggestions = suggestions or []
        self.timestamp = datetime.now()

        # Log the error with structured context
        logger.error(
            "Codebase Gardener error occurred",
            error_type=self.__class__.__name__,
            message=message,
            details=self.details,
            user_message=self.user_message,
            suggestions=self.suggestions,
            timestamp=self.timestamp.isoformat()
        )

    def to_dict(self) -> dict[str, Any]:
        """Convert error to dictionary for serialization."""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "details": self.details,
            "user_message": self.user_message,
            "suggestions": self.suggestions,
            "timestamp": self.timestamp.isoformat()
        }


class ConfigurationError(CodebaseGardenerError):
    """Errors related to configuration and setup."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check your configuration file for syntax errors",
                "Verify all required environment variables are set",
                "Ensure configuration values are within valid ranges"
            ]
        super().__init__(message, **kwargs)


class ModelError(CodebaseGardenerError):
    """Errors related to AI model operations."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if Ollama is running and accessible",
                "Verify the model is downloaded and available",
                "Check system resources (memory, disk space)",
                "Try restarting the model service"
            ]
        super().__init__(message, **kwargs)


class ModelLoadingError(ModelError):
    """Specific error for model loading failures."""

    def __init__(self, model_name: str, **kwargs):
        message = f"Failed to load model: {model_name}"
        details = kwargs.get('details', {})
        details.update({"model_name": model_name})
        kwargs['details'] = details

        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                f"Verify model '{model_name}' is downloaded",
                "Check available system memory",
                "Try loading a smaller model",
                "Restart Ollama service"
            ]

        super().__init__(message, **kwargs)


class ModelInferenceError(ModelError):
    """Specific error for model inference failures."""

    def __init__(self, operation: str, **kwargs):
        message = f"Model inference failed during: {operation}"
        details = kwargs.get('details', {})
        details.update({"operation": operation})
        kwargs['details'] = details

        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if the model is still loaded",
                "Verify input data format is correct",
                "Try reducing input size",
                "Check system resources"
            ]

        super().__init__(message, **kwargs)


class ParsingError(CodebaseGardenerError):
    """Errors during code parsing and analysis."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if the file contains valid code",
                "Verify the programming language is supported",
                "Try parsing individual files to isolate the issue",
                "Check file encoding (should be UTF-8)"
            ]
        super().__init__(message, **kwargs)


class TreeSitterError(ParsingError):
    """Specific error for Tree-sitter parsing failures."""

    def __init__(self, file_path: str, language: str, **kwargs):
        message = f"Tree-sitter parsing failed for {file_path} (language: {language})"
        details = kwargs.get('details', {})
        details.update({"file_path": file_path, "language": language})
        kwargs['details'] = details

        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                f"Verify {file_path} contains valid {language} code",
                f"Check if Tree-sitter grammar for {language} is installed",
                "Try parsing a simpler file first",
                "Check file encoding and syntax"
            ]

        super().__init__(message, **kwargs)


class StorageError(CodebaseGardenerError):
    """Errors related to data storage and retrieval."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check available disk space",
                "Verify file/directory permissions",
                "Ensure the storage path is accessible",
                "Try restarting the application"
            ]
        super().__init__(message, **kwargs)


class VectorStoreError(StorageError):
    """Specific error for vector store operations."""

    def __init__(self, operation: str, **kwargs):
        message = f"Vector store operation failed: {operation}"
        details = kwargs.get('details', {})
        details.update({"operation": operation})
        kwargs['details'] = details

        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if vector store database is accessible",
                "Verify embedding dimensions match",
                "Check available disk space",
                "Try rebuilding the vector store"
            ]

        super().__init__(message, **kwargs)


class DirectorySetupError(StorageError):
    """Specific error for directory setup operations."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check directory permissions",
                "Verify parent directories exist",
                "Ensure sufficient disk space",
                "Try running with appropriate permissions"
            ]
        super().__init__(message, **kwargs)


class NetworkError(CodebaseGardenerError):
    """Errors related to network operations."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check internet connectivity",
                "Verify service URLs are correct",
                "Check if firewall is blocking connections",
                "Try again after a few moments"
            ]
        super().__init__(message, **kwargs)


class PreprocessingError(CodebaseGardenerError):
    """Errors during code preprocessing and chunking."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if the code contains valid syntax",
                "Verify the programming language is supported",
                "Try preprocessing smaller code segments",
                "Check file encoding (should be UTF-8)"
            ]
        super().__init__(message, **kwargs)


class EmbeddingError(CodebaseGardenerError):
    """Errors during embedding generation."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check if the embedding model is loaded correctly",
                "Verify system has sufficient memory",
                "Try reducing batch size for embedding generation",
                "Check if input text is valid and not empty"
            ]
        super().__init__(message, **kwargs)


class ProjectError(CodebaseGardenerError):
    """Errors related to project management."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Verify project directory exists and is accessible",
                "Check project configuration file",
                "Ensure project is properly initialized",
                "Try re-adding the project"
            ]
        super().__init__(message, **kwargs)


class TrainingError(CodebaseGardenerError):
    """Errors related to model training operations."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check available system memory",
                "Verify training data is valid",
                "Ensure sufficient disk space for model storage",
                "Try reducing training parameters"
            ]
        super().__init__(message, **kwargs)


class FileUtilityError(CodebaseGardenerError):
    """Errors related to file utility operations."""

    def __init__(self, message: str, **kwargs):
        if 'suggestions' not in kwargs:
            kwargs['suggestions'] = [
                "Check file permissions and access rights",
                "Verify file path exists and is accessible",
                "Ensure sufficient disk space for file operations",
                "Check for file locks or concurrent access issues"
            ]
        super().__init__(message, **kwargs)


# Retry decorator configurations
DEFAULT_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=4, max=10),
}

MODEL_RETRY_CONFIG = {
    "stop": stop_after_attempt(2),
    "wait": wait_exponential(multiplier=2, min=5, max=30),
    "retry": retry_if_exception_type((ModelError, NetworkError, ConnectionError)),
}

NETWORK_RETRY_CONFIG = {
    "stop": stop_after_attempt(5),
    "wait": wait_exponential(multiplier=1, min=2, max=60),
    "retry": retry_if_exception_type((NetworkError, ConnectionError, TimeoutError)),
}

STORAGE_RETRY_CONFIG = {
    "stop": stop_after_attempt(3),
    "wait": wait_exponential(multiplier=1, min=1, max=5),
    "retry": retry_if_exception_type((StorageError, OSError, IOError)),
}


def retry_with_backoff(
    max_attempts: int = 3,
    min_wait: float = 1.0,
    max_wait: float = 10.0,
    multiplier: float = 2.0,
    retry_exceptions: tuple | None = None
) -> Callable[[F], F]:
    """
    Decorator for retrying functions with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        min_wait: Minimum wait time between retries (seconds)
        max_wait: Maximum wait time between retries (seconds)
        multiplier: Exponential backoff multiplier
        retry_exceptions: Tuple of exception types to retry on

    Returns:
        Decorated function with retry logic
    """
    if retry_exceptions is None:
        retry_exceptions = (Exception,)

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                @retry(
                    stop=stop_after_attempt(max_attempts),
                    wait=wait_exponential(multiplier=multiplier, min=min_wait, max=max_wait),
                    retry=retry_if_exception_type(retry_exceptions),
                )
                def _inner():
                    return func(*args, **kwargs)

                return _inner()
            except RetryError as e:
                # Extract the original exception from RetryError
                original_exception = e.last_attempt.exception()
                logger.error(
                    "Function failed after all retry attempts",
                    function=func.__name__,
                    attempts=max_attempts,
                    original_error=str(original_exception),
                    error_type=type(original_exception).__name__
                )
                raise original_exception from e

        return wrapper
    return decorator


def model_retry(func: F) -> F:
    """Decorator for retrying model operations with appropriate backoff."""
    return retry(**MODEL_RETRY_CONFIG)(func)


def network_retry(func: F) -> F:
    """Decorator for retrying network operations with appropriate backoff."""
    return retry(**NETWORK_RETRY_CONFIG)(func)


def storage_retry(func: F) -> F:
    """Decorator for retrying storage operations with appropriate backoff."""
    return retry(**STORAGE_RETRY_CONFIG)(func)


def retry_with_exponential_backoff(max_retries: int = 3) -> Callable[[F], F]:
    """
    Simple retry decorator with exponential backoff.

    Args:
        max_retries: Maximum number of retry attempts

    Returns:
        Decorated function with retry logic
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(max_retries + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    if attempt == max_retries:
                        # Last attempt failed, reraise the exception
                        raise

                    # Calculate wait time with exponential backoff
                    wait_time = 2 ** attempt
                    logger.warning(
                        f"Attempt {attempt + 1} failed, retrying in {wait_time}s",
                        function=func.__name__,
                        error=str(e),
                        attempt=attempt + 1,
                        max_retries=max_retries
                    )
                    time.sleep(wait_time)

        return wrapper
    return decorator


def handle_errors(
    error_type: type[CodebaseGardenerError] = CodebaseGardenerError,
    user_message: str | None = None,
    suggestions: list[str] | None = None,
    reraise: bool = True
) -> Callable[[F], F]:
    """
    Decorator for handling and converting exceptions to structured errors.

    Args:
        error_type: Type of CodebaseGardenerError to raise
        user_message: User-friendly error message
        suggestions: List of suggestions for resolving the error
        reraise: Whether to reraise the structured error

    Returns:
        Decorated function with error handling
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except CodebaseGardenerError:
                # Already a structured error, just reraise
                raise
            except Exception as e:
                # Convert to structured error
                details = {
                    "function": func.__name__,
                    "original_error": str(e),
                    "original_error_type": type(e).__name__
                }

                structured_error = error_type(
                    message=f"Error in {func.__name__}: {str(e)}",
                    details=details,
                    user_message=user_message,
                    suggestions=suggestions
                )

                if reraise:
                    raise structured_error from e
                else:
                    logger.error(
                        "Error handled without reraising",
                        function=func.__name__,
                        error=str(e)
                    )
                    return None

        return wrapper
    return decorator


def graceful_fallback(
    fallback_value: Any = None,
    log_level: str = "warning"
) -> Callable[[F], F]:
    """
    Decorator for graceful error handling with fallback values.

    Args:
        fallback_value: Value to return on error
        log_level: Logging level for the error

    Returns:
        Decorated function with graceful error handling
    """
    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                log_func = getattr(logger, log_level.lower(), logger.warning)
                log_func(
                    "Function failed, using fallback value",
                    function=func.__name__,
                    error=str(e),
                    fallback_value=fallback_value
                )
                return fallback_value

        return wrapper
    return decorator


def log_errors(func: F) -> F:
    """Decorator for logging errors without handling them."""
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            logger.error(
                "Error occurred in function",
                function=func.__name__,
                error=str(e),
                error_type=type(e).__name__
            )
            raise

    return wrapper


# Utility functions for error handling

def format_error_for_user(error: CodebaseGardenerError) -> str:
    """Format error for user display with suggestions."""
    message = f"Error: {error.user_message}\n"

    if error.suggestions:
        message += "\nSuggestions:\n"
        for i, suggestion in enumerate(error.suggestions, 1):
            message += f"  {i}. {suggestion}\n"

    return message


def is_retryable_error(error: Exception) -> bool:
    """Check if an error is retryable."""
    retryable_types = (
        NetworkError,
        ConnectionError,
        TimeoutError,
        ModelLoadingError,
        VectorStoreError,
        OSError,
        IOError
    )
    return isinstance(error, retryable_types)


def get_error_context(error: Exception) -> dict[str, Any]:
    """Extract context information from an error."""
    context = {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": datetime.now().isoformat()
    }

    if isinstance(error, CodebaseGardenerError):
        context.update({
            "details": error.details,
            "user_message": error.user_message,
            "suggestions": error.suggestions
        })

    return context
