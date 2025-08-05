"""
Core business logic for Codebase Gardener.

This module contains the core components that implement the project-specific
AI analysis functionality:

- Project registry for managing multiple codebases
- Project context manager for maintaining separate conversation states
- Dynamic model loader for efficient LoRA adapter switching
- LoRA training pipeline for creating project-specific adapters
"""

from .project_registry import (
    ProjectRegistry,
    ProjectMetadata,
    TrainingStatus,
    ProjectRegistryError,
    get_project_registry
)

__all__ = [
    'ProjectRegistry',
    'ProjectMetadata', 
    'TrainingStatus',
    'ProjectRegistryError',
    'get_project_registry'
]