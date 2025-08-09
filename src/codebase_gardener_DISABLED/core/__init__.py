"""
Core business logic for Codebase Gardener.

This module contains the core components that implement the project-specific
AI analysis functionality:

- Project registry for managing multiple codebases
- Project context manager for maintaining separate conversation states
- Dynamic model loader for efficient LoRA adapter switching
- LoRA training pipeline for creating project-specific adapters
"""

from .dynamic_model_loader import (
    AdapterInfo,
    DynamicModelLoader,
    DynamicModelLoaderError,
    LoaderMetrics,
    LoaderStatus,
    cleanup_global_loader,
    get_dynamic_model_loader,
)
from .project_context_manager import (
    ContextManagerError,
    ConversationMessage,
    ProjectContext,
    ProjectContextManager,
    get_project_context_manager,
    setup_context_manager_integration,
)
from .project_registry import (
    ProjectMetadata,
    ProjectRegistry,
    ProjectRegistryError,
    TrainingStatus,
    get_project_registry,
)
from .training_pipeline import (
    TrainingConfig,
    TrainingDataPreparator,
    TrainingPhase,
    TrainingPipeline,
    TrainingProgress,
    TrainingProgressTracker,
    cancel_project_training,
    get_project_training_progress,
    get_training_pipeline,
    is_project_training_active,
    start_project_training,
)

__all__ = [
    'ProjectRegistry',
    'ProjectMetadata',
    'TrainingStatus',
    'ProjectRegistryError',
    'get_project_registry',
    'TrainingPipeline',
    'TrainingProgress',
    'TrainingPhase',
    'TrainingConfig',
    'TrainingDataPreparator',
    'TrainingProgressTracker',
    'get_training_pipeline',
    'start_project_training',
    'get_project_training_progress',
    'is_project_training_active',
    'cancel_project_training',
    'DynamicModelLoader',
    'LoaderStatus',
    'AdapterInfo',
    'LoaderMetrics',
    'DynamicModelLoaderError',
    'get_dynamic_model_loader',
    'cleanup_global_loader',
    'ProjectContextManager',
    'ProjectContext',
    'ConversationMessage',
    'ContextManagerError',
    'get_project_context_manager',
    'setup_context_manager_integration'
]
