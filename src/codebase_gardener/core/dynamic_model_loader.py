"""
Dynamic Model Loader System

This module provides dynamic loading and unloading of LoRA adapters for efficient
project switching with memory management optimized for Mac Mini M4 constraints.
"""

import threading
import time
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from ..utils.error_handling import (
    ModelError,
    graceful_fallback,
)

logger = structlog.get_logger(__name__)


class LoaderStatus(str, Enum):
    """Status of the dynamic model loader."""

    IDLE = "idle"
    LOADING = "loading"
    UNLOADING = "unloading"
    ERROR = "error"


@dataclass
class AdapterInfo:
    """Information about a loaded adapter."""

    project_id: str
    adapter_name: str
    model: Any | None  # PeftModel or fallback
    loaded_at: datetime
    last_accessed: datetime
    memory_usage_mb: float
    base_model_name: str

    def update_access_time(self) -> None:
        """Update the last accessed timestamp."""
        self.last_accessed = datetime.now()


@dataclass
class LoaderMetrics:
    """Metrics for the dynamic model loader."""

    total_adapters_loaded: int
    active_adapters: int
    memory_usage_mb: float
    cache_hits: int
    cache_misses: int
    load_time_avg_seconds: float
    unload_time_avg_seconds: float


class DynamicModelLoaderError(ModelError):
    """Raised when dynamic model loader operations fail."""

    pass


class DynamicModelLoader:
    """
    Dynamic model loader for efficient LoRA adapter management.

    This class provides:
    - Dynamic loading/unloading of LoRA adapters
    - Memory-efficient caching with LRU eviction
    - Graceful fallback when PEFT is not available
    - Resource monitoring for Mac Mini M4 constraints
    """

    def __init__(self, max_adapters: int = 2, memory_limit_mb: int = 4000):
        """
        Initialize the dynamic model loader.

        Args:
            max_adapters: Maximum number of adapters to keep loaded
            memory_limit_mb: Memory limit for adapter cache
        """
        self.max_adapters = max_adapters
        self.memory_limit_mb = memory_limit_mb
        self.status = LoaderStatus.IDLE

        # Adapter cache (LRU)
        self._adapters: OrderedDict[str, AdapterInfo] = OrderedDict()
        self._lock = threading.RLock()

        # Metrics
        self._metrics = LoaderMetrics(
            total_adapters_loaded=0,
            active_adapters=0,
            memory_usage_mb=0.0,
            cache_hits=0,
            cache_misses=0,
            load_time_avg_seconds=0.0,
            unload_time_avg_seconds=0.0,
        )

        # Check if PEFT is available
        self._peft_available = self._check_peft_availability()

        logger.info(
            "DynamicModelLoader initialized",
            max_adapters=max_adapters,
            memory_limit_mb=memory_limit_mb,
            peft_available=self._peft_available,
        )

    def _check_peft_availability(self) -> bool:
        """Check if PEFT dependencies are available."""
        try:
            import importlib.util

            # Check if modules are available without importing them
            peft_spec = importlib.util.find_spec("peft")
            transformers_spec = importlib.util.find_spec("transformers")
            return peft_spec is not None and transformers_spec is not None
        except ImportError:
            logger.warning("PEFT dependencies not available, using fallback mode")
            return False

    @graceful_fallback(fallback_value=None)
    def load_adapter(self, project_id: str, adapter_path: Path) -> Any:
        """
        Load a LoRA adapter for a project.

        Args:
            project_id: The project identifier
            adapter_path: Path to the adapter files

        Returns:
            Loaded adapter model or None if unavailable
        """
        with self._lock:
            # Check if already loaded
            if project_id in self._adapters:
                adapter_info = self._adapters[project_id]
                adapter_info.update_access_time()
                # Move to end (most recently used)
                self._adapters.move_to_end(project_id)
                self._metrics.cache_hits += 1

                logger.debug("Adapter cache hit", project_id=project_id)
                return adapter_info.model

            self._metrics.cache_misses += 1

            if not self._peft_available:
                logger.warning(
                    "PEFT not available, creating fallback adapter",
                    project_id=project_id,
                )
                return self._create_fallback_adapter(project_id, adapter_path)

            # Try to load real adapter
            return self._load_real_adapter(project_id, adapter_path)

    def _create_fallback_adapter(self, project_id: str, adapter_path: Path) -> Any:
        """Create a fallback adapter when PEFT is not available."""
        fallback_adapter = {
            "project_id": project_id,
            "adapter_path": str(adapter_path),
            "type": "fallback",
            "loaded_at": datetime.now(),
            "capabilities": ["basic_analysis"],
        }

        # Store in cache
        adapter_info = AdapterInfo(
            project_id=project_id,
            adapter_name=f"fallback_{project_id}",
            model=fallback_adapter,
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=10.0,  # Minimal memory usage for fallback
            base_model_name="fallback",
        )

        self._adapters[project_id] = adapter_info
        self._metrics.active_adapters += 1
        self._metrics.total_adapters_loaded += 1

        return fallback_adapter

    @graceful_fallback(fallback_value=None)
    def _load_real_adapter(self, project_id: str, adapter_path: Path) -> Any:
        """Load a real PEFT adapter."""
        if not adapter_path.exists():
            logger.warning(
                "Adapter path does not exist",
                project_id=project_id,
                path=str(adapter_path),
            )
            return None

        try:
            from peft import PeftConfig, PeftModel
            from transformers import AutoModelForCausalLM

            self.status = LoaderStatus.LOADING
            start_time = time.time()

            # Load configuration
            config = PeftConfig.from_pretrained(adapter_path)

            # Load base model (simplified - would normally be more complex)
            base_model = AutoModelForCausalLM.from_pretrained(
                config.base_model_name_or_path, torch_dtype="auto", device_map="auto"
            )

            # Load adapter
            model = PeftModel.from_pretrained(base_model, adapter_path)

            load_time = time.time() - start_time

            # Estimate memory usage (simplified)
            memory_usage = self._estimate_memory_usage(model)

            # Create adapter info
            adapter_info = AdapterInfo(
                project_id=project_id,
                adapter_name=adapter_path.name,
                model=model,
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=memory_usage,
                base_model_name=config.base_model_name_or_path,
            )

            # Manage memory before adding
            self._manage_memory(memory_usage)

            # Add to cache
            self._adapters[project_id] = adapter_info
            self._metrics.active_adapters += 1
            self._metrics.total_adapters_loaded += 1
            self._update_load_time_metric(load_time)

            self.status = LoaderStatus.IDLE

            logger.info(
                "Adapter loaded successfully",
                project_id=project_id,
                load_time=load_time,
                memory_mb=memory_usage,
            )

            return model

        except Exception as e:
            self.status = LoaderStatus.ERROR
            logger.error("Failed to load adapter", project_id=project_id, error=str(e))
            raise DynamicModelLoaderError(f"Failed to load adapter: {e}") from e

    def unload_adapter(self, project_id: str) -> None:
        """
        Unload an adapter to free memory.

        Args:
            project_id: The project identifier
        """
        with self._lock:
            if project_id not in self._adapters:
                return

            adapter_info = self._adapters[project_id]

            try:
                self.status = LoaderStatus.UNLOADING
                start_time = time.time()

                # Clean up model (if it has cleanup methods)
                if hasattr(adapter_info.model, "unload"):
                    adapter_info.model.unload()

                # Remove from cache
                del self._adapters[project_id]
                self._metrics.active_adapters -= 1

                unload_time = time.time() - start_time
                self._update_unload_time_metric(unload_time)

                self.status = LoaderStatus.IDLE

                logger.info(
                    "Adapter unloaded", project_id=project_id, unload_time=unload_time
                )

            except Exception as e:
                self.status = LoaderStatus.ERROR
                logger.error(
                    "Failed to unload adapter", project_id=project_id, error=str(e)
                )

    def get_loaded_adapters(self) -> list[str]:
        """Get list of currently loaded adapter project IDs."""
        with self._lock:
            return list(self._adapters.keys())

    def get_metrics(self) -> LoaderMetrics:
        """Get current loader metrics."""
        with self._lock:
            # Update current memory usage
            total_memory = sum(info.memory_usage_mb for info in self._adapters.values())
            self._metrics.memory_usage_mb = total_memory
            self._metrics.active_adapters = len(self._adapters)

            return self._metrics

    def cleanup(self) -> None:
        """Clean up all loaded adapters."""
        with self._lock:
            project_ids = list(self._adapters.keys())
            for project_id in project_ids:
                try:
                    self.unload_adapter(project_id)
                except Exception as e:
                    logger.error(
                        "Error during cleanup", project_id=project_id, error=str(e)
                    )

    def _manage_memory(self, required_memory_mb: float) -> None:
        """Manage memory by unloading least recently used adapters."""
        while (
            self._get_total_memory_usage() + required_memory_mb > self.memory_limit_mb
            or len(self._adapters) >= self.max_adapters
        ):
            if not self._adapters:
                break

            # Remove least recently used adapter (first item)
            lru_project_id = next(iter(self._adapters))
            logger.info(
                "Evicting LRU adapter for memory management", project_id=lru_project_id
            )
            self.unload_adapter(lru_project_id)

    def _get_total_memory_usage(self) -> float:
        """Get total memory usage of loaded adapters."""
        return sum(info.memory_usage_mb for info in self._adapters.values())

    def _estimate_memory_usage(self, model: Any) -> float:
        """Estimate memory usage of a model (simplified)."""
        if hasattr(model, "get_memory_footprint"):
            return model.get_memory_footprint() / (1024 * 1024)  # Convert to MB

        # Fallback estimation
        return 500.0  # Default estimate for LoRA adapter

    def _update_load_time_metric(self, load_time: float) -> None:
        """Update average load time metric."""
        current_avg = self._metrics.load_time_avg_seconds
        count = self._metrics.total_adapters_loaded

        # Calculate new average
        new_avg = ((current_avg * (count - 1)) + load_time) / count
        self._metrics.load_time_avg_seconds = new_avg

    def _update_unload_time_metric(self, unload_time: float) -> None:
        """Update average unload time metric."""
        # Simple implementation - could be more sophisticated
        self._metrics.unload_time_avg_seconds = unload_time


# Global loader instance
_loader_instance: DynamicModelLoader | None = None
_loader_lock = threading.Lock()


def get_dynamic_model_loader() -> DynamicModelLoader:
    """
    Get the global dynamic model loader instance.

    Returns:
        DynamicModelLoader: The global instance
    """
    global _loader_instance

    if _loader_instance is None:
        with _loader_lock:
            if _loader_instance is None:
                _loader_instance = DynamicModelLoader()

    return _loader_instance
