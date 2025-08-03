"""
Configuration and logging package for Codebase Gardener.

This package provides centralized configuration management and structured logging
for the entire application.
"""

from .settings import settings, get_settings, reload_settings
from .logging_config import (
    configure_logging,
    get_logger,
    bind_context,
    clear_context,
    LoggerMixin,
    log_function_call,
    log_performance,
    log_error,
)

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