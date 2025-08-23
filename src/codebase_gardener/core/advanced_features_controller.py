"""
Advanced Features Controller - Layer 2 Enhancement System

This module provides the AdvancedFeaturesController class that coordinates
advanced components through the ComponentRegistry while providing graceful
fallbacks and resource monitoring.
"""

import threading
import time
from datetime import datetime
from pathlib import Path
from typing import Any

import structlog

from ..utils import (
    graceful_fallback,
)
from .component_registry import ComponentRegistry

logger = structlog.get_logger(__name__)


class AdvancedFeaturesController:
    """
    Layer 2 Enhancement Controller that coordinates advanced features.

    This controller provides:
    - Component availability detection and dynamic loading
    - Resource monitoring and constraint management
    - Integration hooks for CLI functionality
    - Graceful degradation when advanced features unavailable
    - Performance optimization for Mac Mini M4 constraints
    """

    def __init__(self, enable_monitoring: bool = True):
        """Initialize the advanced features controller.

        Args:
            enable_monitoring: Whether to enable resource monitoring
        """
        self.registry = ComponentRegistry()
        self.enable_monitoring = enable_monitoring
        self._resource_monitor = None
        self._lock = threading.Lock()

        # Feature availability cache
        self._feature_cache = {}
        self._cache_timestamp = None
        self._cache_ttl = 300  # 5 minutes

        logger.info(
            "AdvancedFeaturesController initialized",
            enable_monitoring=enable_monitoring,
        )

    def check_feature_availability(self, feature_name: str) -> bool:
        """
        Check if an advanced feature is available.

        Args:
            feature_name: Name of the feature to check

        Returns:
            True if feature is available, False otherwise
        """
        try:
            # Check cache first
            if self._is_cache_valid():
                cached_result = self._feature_cache.get(feature_name)
                if cached_result is not None:
                    return cached_result

            # Check component availability
            available = self._check_component_availability(feature_name)

            # Update cache
            self._update_cache(feature_name, available)

            logger.debug(
                "Feature availability checked",
                feature=feature_name,
                available=available,
            )
            return available

        except Exception as e:
            logger.warning(
                "Feature availability check failed", feature=feature_name, error=str(e)
            )
            return False

    def get_available_features(self) -> list[str]:
        """Get list of currently available advanced features."""
        features = [
            "rag_retrieval",
            "semantic_search",
            "training_pipeline",
            "project_management",
            "vector_storage",
            "embedding_generation",
            "semantic_analysis",
            "code_parsing",
            "semantic_chunking",
        ]

        available = []
        for feature in features:
            if self.check_feature_availability(feature):
                available.append(feature)

        logger.info(
            "Available features determined",
            total=len(features),
            available=len(available),
        )
        return available

    def is_feature_available(self, feature_name: str) -> bool:
        """Alias for check_feature_availability for convenience."""
        return self.check_feature_availability(feature_name)

    def get_enhancement_level(self, directory_path: Path) -> str:
        """
        Determine appropriate enhancement level for a codebase.

        Args:
            directory_path: Path to the codebase directory

        Returns:
            Enhancement level: 'simple', 'standard', or 'advanced'
        """
        try:
            # Analyze codebase size and complexity
            file_count = self._count_source_files(directory_path)
            available_features = self.get_available_features()

            if file_count <= 5:
                return "simple"
            elif file_count <= 100 and len(available_features) >= 3:
                return "standard"
            elif len(available_features) >= 5:
                return "advanced"
            else:
                return "simple"

        except Exception as e:
            logger.warning(
                "Enhancement level detection failed",
                directory=str(directory_path),
                error=str(e),
            )
            return "simple"

    def enhance_analysis(self, analysis_context: dict[str, Any]) -> dict[str, Any]:
        """
        Enhance analysis with available advanced features.

        Args:
            analysis_context: Basic analysis context from MVP CLI

        Returns:
            Enhanced analysis context with additional data
        """
        try:
            enhanced = analysis_context.copy()
            enhancement_level = self.get_enhancement_level(
                Path(analysis_context.get("directory_path", "."))
            )

            enhanced["enhancement_level"] = enhancement_level
            enhanced["available_features"] = self.get_available_features()
            enhanced["enhanced_timestamp"] = datetime.now().isoformat()

            # Apply enhancements based on available features
            if self.check_feature_availability("rag_retrieval"):
                enhanced = self._apply_rag_enhancement(enhanced)

            if self.check_feature_availability("semantic_search"):
                enhanced = self._apply_semantic_enhancement(enhanced)

            if self.check_feature_availability("project_management"):
                enhanced = self._apply_project_enhancement(enhanced)

            logger.info(
                "Analysis enhanced",
                level=enhancement_level,
                features_applied=len(
                    [k for k in enhanced.keys() if k.startswith("enhanced_")]
                ),
            )
            return enhanced

        except Exception as e:
            logger.error("Analysis enhancement failed", error=str(e))
            # Return original context on failure
            return analysis_context

    @graceful_fallback(fallback_value={})
    def get_resource_status(self) -> dict[str, Any]:
        """Get current resource usage and constraints."""
        if not self.enable_monitoring:
            return {"monitoring": "disabled"}

        try:
            import psutil

            # Get system resources
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            status = {
                "memory_used_gb": round(memory.used / (1024**3), 2),
                "memory_available_gb": round(memory.available / (1024**3), 2),
                "memory_percent": memory.percent,
                "disk_free_gb": round(disk.free / (1024**3), 2),
                "disk_percent": (disk.used / disk.total) * 100,
                "timestamp": datetime.now().isoformat(),
            }

            # Check constraints for Mac Mini M4 (6GB memory)
            status["within_constraints"] = (
                status["memory_used_gb"] < 4.5  # Leave 1.5GB buffer
                and status["disk_free_gb"] > 1.0  # Ensure 1GB free space
            )

            return status

        except ImportError:
            return {"error": "psutil not available", "monitoring": "unavailable"}
        except Exception as e:
            logger.warning("Resource status check failed", error=str(e))
            return {"error": str(e), "monitoring": "failed"}

    def cleanup_resources(self) -> None:
        """Clean up resources and cached components."""
        try:
            with self._lock:
                # Clear feature cache
                self._feature_cache.clear()
                self._cache_timestamp = None

                # Cleanup component registry
                if hasattr(self.registry, "cleanup"):
                    self.registry.cleanup()

                logger.info("Resources cleaned up successfully")

        except Exception as e:
            logger.error("Resource cleanup failed", error=str(e))

    def _check_component_availability(self, feature_name: str) -> bool:
        """Check if components for a feature are available."""
        feature_components = {
            "rag_retrieval": ["vector_store", "project_vector_store_manager"],
            "semantic_search": ["vector_store"],
            "training_pipeline": [
                "peft_manager",
                "training_pipeline",
                "dynamic_model_loader",
            ],
            "project_management": ["project_registry", "project_context_manager"],
            "vector_storage": ["vector_store"],
            "embedding_generation": ["nomic_embeddings", "embedding_manager"],
            "semantic_analysis": [
                "tree_sitter_parser",
                "code_preprocessor",
                "semantic_file_processor",
            ],
            "code_parsing": ["tree_sitter_parser"],
            "semantic_chunking": ["code_preprocessor", "semantic_file_processor"],
        }

        required_components = feature_components.get(feature_name, [])
        if not required_components:
            return False

        # Check if all required components are available
        for component_name in required_components:
            try:
                component = self.registry.get_component(component_name)
                # Check if it's a mock (fallback)
                if hasattr(component, "_is_mock") and component._is_mock:
                    return False
            except Exception:
                return False

        return True

    def _is_cache_valid(self) -> bool:
        """Check if feature cache is still valid."""
        if self._cache_timestamp is None:
            return False
        return (time.time() - self._cache_timestamp) < self._cache_ttl

    def _update_cache(self, feature_name: str, available: bool) -> None:
        """Update feature availability cache."""
        with self._lock:
            self._feature_cache[feature_name] = available
            self._cache_timestamp = time.time()

    def _count_source_files(self, directory_path: Path) -> int:
        """Count source files in directory for complexity assessment."""
        try:
            from ..utils import FileUtilities

            file_utils = FileUtilities()
            source_files = file_utils.find_source_files(directory_path)
            return len(source_files)
        except Exception as e:
            logger.warning("Source file counting failed", error=str(e))
            return 0

    @graceful_fallback(fallback_value={})
    def _apply_rag_enhancement(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply RAG-based enhancements to analysis context."""
        try:
            # Get vector store component (unused for now, placeholder for future implementation)
            self.registry.get_component("vector_store")

            # This would retrieve relevant context from vector store
            # For now, just add placeholder enhancement
            context["enhanced_rag"] = {
                "status": "available",
                "context_retrieved": True,
                "enhancement_applied": datetime.now().isoformat(),
            }

            return context
        except Exception as e:
            logger.warning("RAG enhancement failed", error=str(e))
            return context

    @graceful_fallback(fallback_value={})
    def _apply_semantic_enhancement(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply semantic search enhancements to analysis context."""
        try:
            # This would add semantic analysis capabilities
            context["enhanced_semantic"] = {
                "status": "available",
                "semantic_analysis": True,
                "enhancement_applied": datetime.now().isoformat(),
            }

            return context
        except Exception as e:
            logger.warning("Semantic enhancement failed", error=str(e))
            return context

    @graceful_fallback(fallback_value={})
    def analyze_with_semantics(self, directory_path: str) -> dict[str, Any]:
        """
        Perform semantic analysis of a codebase using Tree-sitter parsing.

        Args:
            directory_path: Path to the codebase directory

        Returns:
            Comprehensive semantic analysis results
        """
        try:
            if not self.is_feature_available("semantic_analysis"):
                logger.info("Semantic analysis not available, using basic analysis")
                return {"error": "semantic_analysis_unavailable"}

            # Load semantic file processor
            processor = self.registry.get_component("semantic_file_processor")

            # Perform semantic analysis
            analysis_result = processor.analyze_codebase(directory_path)

            logger.info(
                "Semantic analysis completed",
                directory=directory_path,
                files_analyzed=analysis_result.get("file_summary", {}).get(
                    "analyzed_successfully", 0
                ),
                languages=list(analysis_result.get("language_distribution", {}).keys()),
            )

            return analysis_result

        except Exception as e:
            logger.error(
                "Semantic analysis failed", error=str(e), directory=directory_path
            )
            return {"error": str(e)}

    @graceful_fallback(fallback_value=[])
    def get_file_semantic_chunks(self, file_path: str) -> list:
        """
        Get semantic chunks for a specific file.

        Args:
            file_path: Path to the file

        Returns:
            List of semantic code chunks
        """
        try:
            if not self.is_feature_available("semantic_chunking"):
                return []

            from pathlib import Path

            processor = self.registry.get_component("semantic_file_processor")
            chunks = processor.get_file_chunks(Path(file_path))

            # Convert chunks to serializable format
            chunk_data = []
            for chunk in chunks:
                chunk_data.append(
                    {
                        "id": chunk.id,
                        "type": chunk.chunk_type.value,
                        "content": chunk.content,
                        "language": chunk.language,
                        "start_line": chunk.start_line,
                        "end_line": chunk.end_line,
                        "size": chunk.size,
                        "complexity": chunk.complexity_score,
                        "metadata": chunk.metadata,
                    }
                )

            return chunk_data

        except Exception as e:
            logger.warning(
                "Failed to get semantic chunks", file_path=file_path, error=str(e)
            )
            return []

    @graceful_fallback(fallback_value={})
    def _apply_project_enhancement(self, context: dict[str, Any]) -> dict[str, Any]:
        """Apply project management enhancements to analysis context."""
        try:
            # Get project registry component (unused for now, placeholder for future implementation)
            self.registry.get_component("project_registry")

            # This would add project-specific context
            context["enhanced_project"] = {
                "status": "available",
                "project_context": True,
                "enhancement_applied": datetime.now().isoformat(),
            }

            return context
        except Exception as e:
            logger.warning("Project enhancement failed", error=str(e))
            return context


# Global controller instance
advanced_features_controller = AdvancedFeaturesController()


# Convenience functions
def check_advanced_features() -> bool:
    """Check if any advanced features are available."""
    return len(advanced_features_controller.get_available_features()) > 0


def get_enhancement_level(directory_path: Path) -> str:
    """Get appropriate enhancement level for a directory."""
    return advanced_features_controller.get_enhancement_level(directory_path)


def enhance_analysis(analysis_context: dict[str, Any]) -> dict[str, Any]:
    """Enhance analysis context with available advanced features."""
    return advanced_features_controller.enhance_analysis(analysis_context)
