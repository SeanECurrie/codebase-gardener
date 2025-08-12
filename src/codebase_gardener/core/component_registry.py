"""
Component Registry for Dynamic Loading and Graceful Fallbacks

This module provides a registry system for dynamically loading components
with graceful fallback behavior. Components can be registered, loaded on-demand,
and provide fallback implementations when advanced features are unavailable.

Key Features:
- Dynamic component loading with graceful fallbacks
- Component availability detection
- Resource management and cleanup
- Integration with configuration system
- Comprehensive error handling

Architecture:
Follows Layer 2 (Enhancement Controller) design pattern where advanced
features are dynamically loaded and gracefully degrade to simple mode
when unavailable.
"""

import importlib
import logging
import threading
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum
from typing import Any, TypeVar

from codebase_gardener.config.settings import get_settings
from codebase_gardener.utils.error_handling import (
    CodebaseGardenerError,
    handle_errors,
)

logger = logging.getLogger(__name__)

T = TypeVar("T")


class ComponentStatus(Enum):
    """Status of a component in the registry."""

    AVAILABLE = "available"
    LOADING = "loading"
    LOADED = "loaded"
    FAILED = "failed"
    DISABLED = "disabled"


@dataclass
class ComponentInfo:
    """Information about a registered component."""

    name: str
    module_path: str
    class_name: str
    dependencies: list[str]
    fallback_class: type | None = None
    status: ComponentStatus = ComponentStatus.AVAILABLE
    instance: Any | None = None
    error_message: str | None = None


class ComponentRegistry:
    """Registry for dynamic component loading with graceful fallbacks."""

    def __init__(self):
        self._components: dict[str, ComponentInfo] = {}
        self._lock = threading.Lock()
        self._settings = get_settings()
        self._register_core_components()

    def _register_core_components(self):
        """Register core components with their fallback implementations."""
        # Project management components
        self.register(
            name="project_registry",
            module_path="codebase_gardener.core.project_registry",
            class_name="ProjectRegistry",
            dependencies=["config"],
        )

        self.register(
            name="project_context_manager",
            module_path="codebase_gardener.core.project_context_manager",
            class_name="ProjectContextManager",
            dependencies=["config"],
        )

        # Data components
        self.register(
            name="vector_store",
            module_path="codebase_gardener.data.vector_store",
            class_name="VectorStore",
            dependencies=["lancedb"],
        )

        self.register(
            name="project_vector_store_manager",
            module_path="codebase_gardener.data.project_vector_store",
            class_name="ProjectVectorStoreManager",
            dependencies=["lancedb", "vector_store"],
        )

        # Model components
        self.register(
            name="dynamic_model_loader",
            module_path="codebase_gardener.core.dynamic_model_loader",
            class_name="DynamicModelLoader",
            dependencies=["transformers", "peft"],
        )

        # Training components
        self.register(
            name="training_pipeline",
            module_path="codebase_gardener.core.training_pipeline",
            class_name="TrainingPipeline",
            dependencies=["transformers", "peft", "vector_store"],
        )

    def register(
        self,
        name: str,
        module_path: str,
        class_name: str,
        dependencies: list[str],
        fallback_class: type | None = None,
    ):
        """Register a component with the registry."""
        with self._lock:
            self._components[name] = ComponentInfo(
                name=name,
                module_path=module_path,
                class_name=class_name,
                dependencies=dependencies,
                fallback_class=fallback_class,
            )
        logger.debug(f"Registered component: {name}")

    def is_available(self, name: str) -> bool:
        """Check if a component is available for loading."""
        if name not in self._components:
            return False

        component = self._components[name]
        if component.status == ComponentStatus.LOADED:
            return True

        # Check dependencies
        return self._check_dependencies(component.dependencies)

    def _check_dependencies(self, dependencies: list[str]) -> bool:
        """Check if all dependencies are available."""
        for dep in dependencies:
            try:
                if dep in ["lancedb", "transformers", "peft", "tree_sitter"]:
                    # Check external dependencies
                    importlib.import_module(dep)
                elif dep in self._components:
                    # Check internal component dependencies
                    if not self.is_available(dep):
                        return False
            except ImportError:
                return False
        return True

    @handle_errors(logger)
    def get_component(self, name: str, **kwargs) -> Any:
        """Get a component instance, loading it if necessary."""
        if name not in self._components:
            raise CodebaseGardenerError(f"Component '{name}' not registered")

        component = self._components[name]

        with self._lock:
            # Return existing instance if available
            if component.instance is not None:
                return component.instance

            # Check if component failed previously
            if component.status == ComponentStatus.FAILED:
                return self._get_fallback(component)

            # Try to load component
            try:
                component.status = ComponentStatus.LOADING
                instance = self._load_component(component, **kwargs)
                component.instance = instance
                component.status = ComponentStatus.LOADED
                logger.info(f"Successfully loaded component: {name}")
                return instance

            except Exception as e:
                component.status = ComponentStatus.FAILED
                component.error_message = str(e)
                logger.warning(f"Failed to load component {name}: {e}")
                return self._get_fallback(component)

    def _load_component(self, component: ComponentInfo, **kwargs) -> Any:
        """Load a component from its module path."""
        # Check dependencies first
        if not self._check_dependencies(component.dependencies):
            missing = [
                dep
                for dep in component.dependencies
                if not self._check_dependencies([dep])
            ]
            raise ImportError(f"Missing dependencies: {missing}")

        # Import module and get class
        module = importlib.import_module(component.module_path)
        component_class = getattr(module, component.class_name)

        # Create instance with settings
        if "settings" not in kwargs and hasattr(component_class, "__init__"):
            kwargs["settings"] = self._settings

        return component_class(**kwargs)

    def _get_fallback(self, component: ComponentInfo) -> Any:
        """Get fallback implementation for a component."""
        if component.fallback_class:
            logger.info(f"Using fallback for component: {component.name}")
            return component.fallback_class()
        else:
            # Return a simple mock that logs usage
            logger.warning(f"No fallback available for component: {component.name}")
            return ComponentMock(component.name)

    def get_status(self) -> dict[str, ComponentStatus]:
        """Get status of all registered components."""
        return {name: comp.status for name, comp in self._components.items()}

    def get_health_report(self) -> dict[str, Any]:
        """Get comprehensive health report of all components."""
        report = {
            "total_components": len(self._components),
            "loaded_components": 0,
            "failed_components": 0,
            "available_components": 0,
            "component_status": {},
        }

        for name, component in self._components.items():
            report["component_status"][name] = {
                "status": component.status.value,
                "dependencies_met": self._check_dependencies(component.dependencies),
                "error_message": component.error_message,
            }

            if component.status == ComponentStatus.LOADED:
                report["loaded_components"] += 1
            elif component.status == ComponentStatus.FAILED:
                report["failed_components"] += 1
            elif self.is_available(name):
                report["available_components"] += 1

        return report

    def cleanup(self):
        """Clean up all loaded components."""
        with self._lock:
            for component in self._components.values():
                if component.instance and hasattr(component.instance, "cleanup"):
                    try:
                        component.instance.cleanup()
                    except Exception as e:
                        logger.warning(f"Error cleaning up {component.name}: {e}")
                component.instance = None
                if component.status == ComponentStatus.LOADED:
                    component.status = ComponentStatus.AVAILABLE


class ComponentMock:
    """Mock component for graceful fallback behavior."""

    def __init__(self, component_name: str):
        self.component_name = component_name

    def __getattr__(self, name: str) -> Callable:
        """Return a mock method that logs the call."""

        def mock_method(*args, **kwargs):
            logger.info(f"Mock call: {self.component_name}.{name}(*{args}, **{kwargs})")
            return None

        return mock_method


# Global registry instance
_registry: ComponentRegistry | None = None
_registry_lock = threading.Lock()


def get_component_registry() -> ComponentRegistry:
    """Get the global component registry instance."""
    global _registry
    if _registry is None:
        with _registry_lock:
            if _registry is None:
                _registry = ComponentRegistry()
    return _registry


def get_component(name: str, **kwargs) -> Any:
    """Convenience function to get a component from the global registry."""
    return get_component_registry().get_component(name, **kwargs)


def is_component_available(name: str) -> bool:
    """Check if a component is available in the global registry."""
    return get_component_registry().is_available(name)
