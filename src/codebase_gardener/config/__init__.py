"""
Configuration management for Codebase Gardener.

This module provides centralized configuration management using Pydantic
for validation and environment variable support. All application settings
are defined here and can be overridden via environment variables with
the CODEBASE_GARDENER_ prefix.
"""

from codebase_gardener.config.settings import Settings, get_settings

# Create global settings instance
settings = get_settings()

__all__ = [
    "Settings",
    "get_settings", 
    "settings",
]