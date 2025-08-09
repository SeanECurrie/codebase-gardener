"""
Structured logging configuration using structlog.

This module provides centralized logging configuration with structured output,
contextual data binding, and environment-specific formatting.
"""

import logging
import logging.handlers
import sys
from pathlib import Path
from typing import Any

import structlog
from structlog.types import Processor

from .settings import settings


def configure_logging(
    log_level: str | None = None,
    debug: bool | None = None,
    log_file: Path | None = None
) -> None:
    """
    Configure structured logging for the application.

    Args:
        log_level: Override the log level from settings
        debug: Override debug mode from settings
        log_file: Optional log file path for file output
    """
    # Use settings defaults if not provided
    if log_level is None:
        log_level = settings.log_level
    if debug is None:
        debug = settings.debug

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Configure structlog processors
    processors = _get_processors(debug=debug)

    # Configure structlog
    structlog.configure(
        processors=processors,
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.upper())
        ),
        logger_factory=structlog.WriteLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure file logging if requested
    if log_file:
        _configure_file_logging(log_file, log_level)

    # Log configuration completion
    logger = structlog.get_logger(__name__)
    logger.info(
        "Logging configured",
        log_level=log_level,
        debug=debug,
        log_file=str(log_file) if log_file else None,
    )


def _get_processors(debug: bool = False) -> list[Processor]:
    """
    Get the list of structlog processors based on environment.

    Args:
        debug: Whether to use debug-friendly formatting

    Returns:
        List of structlog processors
    """
    # Base processors for all environments
    processors = [
        # Add context variables from contextvars
        structlog.contextvars.merge_contextvars,

        # Add log level to each log entry
        structlog.processors.add_log_level,

        # Add timestamp
        structlog.processors.TimeStamper(fmt="ISO"),

        # Note: add_logger_name removed due to WriteLogger compatibility

        # Add stack info for exceptions
        structlog.processors.StackInfoRenderer(),

        # Format exceptions
        structlog.processors.format_exc_info,
    ]

    if debug:
        # Development-friendly console output
        processors.extend([
            # Add colors and pretty formatting for development
            structlog.dev.ConsoleRenderer(colors=True),
        ])
    else:
        # Production JSON output
        processors.extend([
            # Convert to JSON for structured logging
            structlog.processors.JSONRenderer(),
        ])

    return processors


def _configure_file_logging(log_file: Path, log_level: str) -> None:
    """
    Configure file-based logging with rotation.

    Args:
        log_file: Path to the log file
        log_level: Logging level
    """
    # Ensure log directory exists
    log_file.parent.mkdir(parents=True, exist_ok=True)

    # Create rotating file handler
    file_handler = logging.handlers.RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10MB
        backupCount=5,
        encoding="utf-8",
    )

    # Set formatter for file output (always JSON)
    file_handler.setFormatter(
        logging.Formatter("%(message)s")
    )

    # Set log level
    file_handler.setLevel(getattr(logging, log_level.upper()))

    # Add to root logger
    logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog BoundLogger
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables that will be included in all log messages.

    Args:
        **kwargs: Key-value pairs to bind to the logging context
    """
    structlog.contextvars.clear_contextvars()
    for key, value in kwargs.items():
        structlog.contextvars.bind_contextvars(**{key: value})


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


class LoggerMixin:
    """
    Mixin class to add structured logging to any class.

    Usage:
        class MyClass(LoggerMixin):
            def my_method(self):
                self.logger.info("Method called", method="my_method")
    """

    @property
    def logger(self) -> structlog.BoundLogger:
        """Get a logger bound to this class."""
        if not hasattr(self, "_logger"):
            self._logger = get_logger(self.__class__.__module__)
        return self._logger


def log_function_call(func_name: str, **kwargs: Any) -> None:
    """
    Log a function call with parameters.

    Args:
        func_name: Name of the function being called
        **kwargs: Function parameters to log
    """
    logger = get_logger("function_calls")
    logger.debug(
        "Function called",
        function=func_name,
        parameters=kwargs,
    )


def log_performance(operation: str, duration: float, **kwargs: Any) -> None:
    """
    Log performance metrics for an operation.

    Args:
        operation: Name of the operation
        duration: Duration in seconds
        **kwargs: Additional metrics to log
    """
    logger = get_logger("performance")
    logger.info(
        "Performance metric",
        operation=operation,
        duration_seconds=duration,
        **kwargs,
    )


def log_error(
    error: Exception,
    operation: str,
    **kwargs: Any
) -> None:
    """
    Log an error with structured context.

    Args:
        error: The exception that occurred
        operation: The operation that failed
        **kwargs: Additional context
    """
    logger = get_logger("errors")
    logger.error(
        "Operation failed",
        operation=operation,
        error_type=type(error).__name__,
        error_message=str(error),
        **kwargs,
        exc_info=True,
    )


# Note: Logging configuration is not automatically initialized
# Call configure_logging() explicitly when needed
