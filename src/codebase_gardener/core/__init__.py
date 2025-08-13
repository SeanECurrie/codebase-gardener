"""
Core system components for Codebase Gardener.
"""

from .advanced_features_controller import (
    AdvancedFeaturesController,
    advanced_features_controller,
    check_advanced_features,
    enhance_analysis,
    get_enhancement_level,
)
from .component_registry import ComponentRegistry, get_component_registry
from .dynamic_model_loader import DynamicModelLoader, get_dynamic_model_loader
from .project_context_manager import ProjectContextManager, get_context_manager
from .project_registry import (
    ProjectMetadata,
    ProjectRegistry,
    ProjectRegistryError,
    TrainingStatus,
    get_project_registry,
)

__all__ = [
    # Component Registry
    "ComponentRegistry",
    "get_component_registry",
    # Advanced Features Controller
    "AdvancedFeaturesController",
    "advanced_features_controller",
    "check_advanced_features",
    "enhance_analysis",
    "get_enhancement_level",
    # Project Registry
    "ProjectRegistry",
    "ProjectMetadata",
    "ProjectRegistryError",
    "TrainingStatus",
    "get_project_registry",
    # Project Context Manager
    "ProjectContextManager",
    "get_context_manager",
    # Dynamic Model Loader
    "DynamicModelLoader",
    "get_dynamic_model_loader",
]
