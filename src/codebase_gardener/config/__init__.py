"""
Configuration and logging package for Codebase Gardener.

This package provides centralized configuration management and structured logging
for the entire application.
"""

from .logging_config import (
    LoggerMixin,
    bind_context,
    clear_context,
    configure_logging,
    get_logger,
    log_error,
    log_function_call,
    log_performance,
)
from .settings import get_settings, reload_settings, settings

__all__ = [
    # Settings
    "settings",
    "get_settings",
    "reload_settings",
    # Logging
    "configure_logging",
    "get_logger",
    "bind_context",
    "clear_context",
    "LoggerMixin",
    "log_function_call",
    "log_performance",
    "log_error",
]
