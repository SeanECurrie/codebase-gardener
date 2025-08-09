"""
Dynamic Model Loader System

This module provides dynamic loading and unloading of LoRA adapters for efficient
project switching with memory management optimized for Mac Mini M4 constraints.
"""

import threading
import time
from collections import OrderedDict
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog
import torch
from peft import PeftConfig, PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

from ..config.settings import Settings
from ..core.project_registry import ProjectRegistry, get_project_registry

# DISABLED: Complex components not needed for simple auditor
# from ..models.ollama_client import OllamaClient
# from ..models.peft_manager import PeftManager
from ..utils.error_handling import (
    ModelError,
    retry_with_backoff,
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
    model: PeftModel | None
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

    Provides dynamic loading/unloading of LoRA adapters with memory management,
    LRU caching, compatibility verification, and fallback mechanisms.
    """

    def __init__(
        self,
        settings: Settings,
        ollama_client: Any | None = None,  # DISABLED: Complex component
        peft_manager: Any | None = None,  # DISABLED: Complex component
        project_registry: ProjectRegistry | None = None
    ):
        """
        Initialize the dynamic model loader.

        Args:
            settings: Application settings
            ollama_client: DISABLED - Complex component not needed for simple auditor
            peft_manager: DISABLED - Complex component not needed for simple auditor
            project_registry: Optional project registry instance
        """
        self.settings = settings
        # DISABLED: Complex components not needed for simple auditor
        self.ollama_client = None  # ollama_client or OllamaClient(settings)
        self.peft_manager = None   # peft_manager or PeftManager(settings)
        self.project_registry = project_registry or get_project_registry()

        # Adapter cache with LRU ordering
        self._adapter_cache: OrderedDict[str, AdapterInfo] = OrderedDict()
        self._max_cache_size = 3  # Maximum adapters to keep in memory
        self._memory_limit_mb = 4096  # 4GB memory limit for Mac Mini M4

        # Current state
        self._current_adapter: str | None = None
        self._base_model: AutoModelForCausalLM | None = None
        self._base_tokenizer: AutoTokenizer | None = None
        self._current_base_model_name: str | None = None

        # Thread safety
        self._lock = threading.RLock()
        self._status = LoaderStatus.IDLE

        # Metrics
        self._metrics = LoaderMetrics(
            total_adapters_loaded=0,
            active_adapters=0,
            memory_usage_mb=0.0,
            cache_hits=0,
            cache_misses=0,
            load_time_avg_seconds=0.0,
            unload_time_avg_seconds=0.0
        )
        self._load_times: list[float] = []
        self._unload_times: list[float] = []

        logger.info(
            "Dynamic model loader initialized",
            max_cache_size=self._max_cache_size,
            memory_limit_mb=self._memory_limit_mb
        )

    def get_status(self) -> LoaderStatus:
        """Get current loader status."""
        return self._status

    def get_current_adapter(self) -> str | None:
        """Get currently active adapter ID."""
        return self._current_adapter

    def get_metrics(self) -> LoaderMetrics:
        """Get loader metrics."""
        with self._lock:
            self._metrics.active_adapters = len(self._adapter_cache)
            self._metrics.memory_usage_mb = self._calculate_memory_usage()

            if self._load_times:
                self._metrics.load_time_avg_seconds = sum(self._load_times) / len(self._load_times)
            if self._unload_times:
                self._metrics.unload_time_avg_seconds = sum(self._unload_times) / len(self._unload_times)

            return self._metrics

    def _calculate_memory_usage(self) -> float:
        """Calculate current memory usage in MB."""
        total_memory = 0.0

        # Base model memory (if loaded)
        if self._base_model is not None:
            total_memory += 4000.0  # Approximate base model size

        # Adapter memory
        for adapter_info in self._adapter_cache.values():
            total_memory += adapter_info.memory_usage_mb

        return total_memory

    def _check_memory_availability(self, required_mb: float) -> bool:
        """Check if enough memory is available for loading."""
        current_usage = self._calculate_memory_usage()
        available = self._memory_limit_mb - current_usage

        logger.debug(
            "Memory availability check",
            current_usage_mb=current_usage,
            required_mb=required_mb,
            available_mb=available
        )

        return available >= required_mb

    def _get_adapter_id(self, project_id: str, adapter_name: str = "default") -> str:
        """Generate adapter ID from project and adapter name."""
        return f"{project_id}_{adapter_name}"

    def _manage_cache(self) -> None:
        """Manage adapter cache using LRU eviction."""
        while len(self._adapter_cache) > self._max_cache_size:
            # Remove least recently used adapter
            oldest_id, oldest_info = self._adapter_cache.popitem(last=False)

            logger.info(
                "Evicting adapter from cache",
                adapter_id=oldest_id,
                last_accessed=oldest_info.last_accessed.isoformat()
            )

            # Clean up model from memory
            if oldest_info.model is not None:
                del oldest_info.model
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

    def _verify_adapter_compatibility(
        self,
        adapter_path: Path,
        base_model_name: str
    ) -> bool:
        """
        Verify that an adapter is compatible with the base model.

        Args:
            adapter_path: Path to the adapter
            base_model_name: Name of the base model

        Returns:
            True if compatible, False otherwise
        """
        try:
            # Load adapter config
            config = PeftConfig.from_pretrained(str(adapter_path))

            # Check if base model names match
            if hasattr(config, 'base_model_name_or_path'):
                adapter_base = config.base_model_name_or_path
                if adapter_base != base_model_name:
                    logger.warning(
                        "Base model mismatch",
                        adapter_base=adapter_base,
                        expected_base=base_model_name,
                        adapter_path=str(adapter_path)
                    )
                    return False

            logger.debug(
                "Adapter compatibility verified",
                adapter_path=str(adapter_path),
                base_model=base_model_name
            )
            return True

        except Exception as e:
            logger.error(
                "Failed to verify adapter compatibility",
                adapter_path=str(adapter_path),
                base_model=base_model_name,
                error=str(e)
            )
            return False

    def _load_base_model(self, model_name: str) -> None:
        """Load base model if not already loaded or if different model needed."""
        if (self._base_model is not None and
            self._current_base_model_name == model_name):
            return

        logger.info("Loading base model", model_name=model_name)

        try:
            # Unload current base model if different
            if self._base_model is not None:
                del self._base_model
                del self._base_tokenizer
                if torch.cuda.is_available():
                    torch.cuda.empty_cache()

            # Load new base model
            self._base_model = AutoModelForCausalLM.from_pretrained(
                model_name,
                device_map="auto",
                torch_dtype=torch.float16,
                low_cpu_mem_usage=True
            )

            self._base_tokenizer = AutoTokenizer.from_pretrained(model_name)
            if self._base_tokenizer.pad_token is None:
                self._base_tokenizer.pad_token = self._base_tokenizer.eos_token

            self._current_base_model_name = model_name

            logger.info("Base model loaded successfully", model_name=model_name)

        except Exception as e:
            logger.error("Failed to load base model", model_name=model_name, error=str(e))
            raise DynamicModelLoaderError(f"Failed to load base model {model_name}: {str(e)}")

    @retry_with_backoff(max_attempts=3)
    def load_adapter(
        self,
        project_id: str,
        adapter_name: str = "default",
        force_reload: bool = False
    ) -> bool:
        """
        Load a LoRA adapter for the specified project.

        Args:
            project_id: Project identifier
            adapter_name: Name of the adapter
            force_reload: Force reload even if already cached

        Returns:
            True if successfully loaded, False otherwise

        Raises:
            DynamicModelLoaderError: If loading fails
        """
        adapter_id = self._get_adapter_id(project_id, adapter_name)

        with self._lock:
            self._status = LoaderStatus.LOADING
            start_time = time.time()

            try:
                # Check if already cached and not forcing reload
                if adapter_id in self._adapter_cache and not force_reload:
                    adapter_info = self._adapter_cache[adapter_id]
                    adapter_info.update_access_time()

                    # Move to end (most recently used)
                    self._adapter_cache.move_to_end(adapter_id)
                    self._current_adapter = adapter_id
                    self._metrics.cache_hits += 1

                    logger.debug("Adapter loaded from cache", adapter_id=adapter_id)
                    return True

                self._metrics.cache_misses += 1

                # Get project metadata
                project = self.project_registry.get_project(project_id)
                if not project:
                    raise DynamicModelLoaderError(f"Project not found: {project_id}")

                # Check if adapter exists and is ready
                if not project.lora_adapter_path or not project.lora_adapter_path.exists():
                    raise DynamicModelLoaderError(
                        f"LoRA adapter not found for project {project_id}"
                    )

                # Determine base model name
                base_model_name = "microsoft/DialoGPT-medium"  # Default base model

                # Verify adapter compatibility
                if not self._verify_adapter_compatibility(project.lora_adapter_path, base_model_name):
                    logger.warning(
                        "Adapter compatibility check failed, proceeding with fallback",
                        adapter_id=adapter_id
                    )

                # Check memory availability
                estimated_adapter_size = 50.0  # MB
                if not self._check_memory_availability(estimated_adapter_size):
                    logger.info("Insufficient memory, managing cache")
                    self._manage_cache()

                    if not self._check_memory_availability(estimated_adapter_size):
                        raise DynamicModelLoaderError(
                            f"Insufficient memory to load adapter {adapter_id}"
                        )

                # Load base model
                self._load_base_model(base_model_name)

                # Load adapter
                logger.info("Loading LoRA adapter", adapter_id=adapter_id)

                peft_model = PeftModel.from_pretrained(
                    self._base_model,
                    str(project.lora_adapter_path),
                    device_map="auto"
                )

                # Create adapter info
                adapter_info = AdapterInfo(
                    project_id=project_id,
                    adapter_name=adapter_name,
                    model=peft_model,
                    loaded_at=datetime.now(),
                    last_accessed=datetime.now(),
                    memory_usage_mb=estimated_adapter_size,
                    base_model_name=base_model_name
                )

                # Add to cache
                self._adapter_cache[adapter_id] = adapter_info
                self._current_adapter = adapter_id

                # Manage cache size
                self._manage_cache()

                # Update metrics
                load_time = time.time() - start_time
                self._load_times.append(load_time)
                if len(self._load_times) > 100:  # Keep only recent times
                    self._load_times = self._load_times[-50:]

                self._metrics.total_adapters_loaded += 1

                logger.info(
                    "Adapter loaded successfully",
                    adapter_id=adapter_id,
                    load_time_seconds=load_time
                )

                return True

            except Exception as e:
                logger.error("Failed to load adapter", adapter_id=adapter_id, error=str(e))
                self._status = LoaderStatus.ERROR
                raise DynamicModelLoaderError(f"Failed to load adapter {adapter_id}: {str(e)}")

            finally:
                if self._status != LoaderStatus.ERROR:
                    self._status = LoaderStatus.IDLE

    def unload_adapter(self, project_id: str, adapter_name: str = "default") -> bool:
        """
        Unload a LoRA adapter from memory.

        Args:
            project_id: Project identifier
            adapter_name: Name of the adapter

        Returns:
            True if successfully unloaded, False if not found
        """
        adapter_id = self._get_adapter_id(project_id, adapter_name)

        with self._lock:
            self._status = LoaderStatus.UNLOADING
            start_time = time.time()

            try:
                if adapter_id not in self._adapter_cache:
                    logger.debug("Adapter not in cache", adapter_id=adapter_id)
                    return False

                # Remove from cache
                adapter_info = self._adapter_cache.pop(adapter_id)

                # Clean up model
                if adapter_info.model is not None:
                    del adapter_info.model
                    if torch.cuda.is_available():
                        torch.cuda.empty_cache()

                # Update current adapter if this was active
                if self._current_adapter == adapter_id:
                    self._current_adapter = None

                # Update metrics
                unload_time = time.time() - start_time
                self._unload_times.append(unload_time)
                if len(self._unload_times) > 100:
                    self._unload_times = self._unload_times[-50:]

                logger.info(
                    "Adapter unloaded successfully",
                    adapter_id=adapter_id,
                    unload_time_seconds=unload_time
                )

                return True

            except Exception as e:
                logger.error("Failed to unload adapter", adapter_id=adapter_id, error=str(e))
                return False

            finally:
                self._status = LoaderStatus.IDLE

    def switch_project(self, project_id: str, adapter_name: str = "default") -> bool:
        """
        High-level project switching with automatic adapter management.

        Args:
            project_id: Project identifier to switch to
            adapter_name: Name of the adapter

        Returns:
            True if successfully switched, False otherwise
        """
        adapter_id = self._get_adapter_id(project_id, adapter_name)

        logger.info("Switching to project", project_id=project_id, adapter_name=adapter_name)

        try:
            # Load the target adapter
            success = self.load_adapter(project_id, adapter_name)

            if success:
                logger.info("Project switch completed", project_id=project_id)
            else:
                logger.error("Project switch failed", project_id=project_id)

            return success

        except Exception as e:
            logger.error("Project switch error", project_id=project_id, error=str(e))
            return False

    def get_loaded_adapters(self) -> list[dict[str, Any]]:
        """
        Get information about currently loaded adapters.

        Returns:
            List of adapter information dictionaries
        """
        with self._lock:
            adapters = []
            for adapter_id, adapter_info in self._adapter_cache.items():
                adapters.append({
                    "adapter_id": adapter_id,
                    "project_id": adapter_info.project_id,
                    "adapter_name": adapter_info.adapter_name,
                    "loaded_at": adapter_info.loaded_at.isoformat(),
                    "last_accessed": adapter_info.last_accessed.isoformat(),
                    "memory_usage_mb": adapter_info.memory_usage_mb,
                    "base_model_name": adapter_info.base_model_name,
                    "is_current": adapter_id == self._current_adapter
                })

            return sorted(adapters, key=lambda x: x["last_accessed"], reverse=True)

    def clear_cache(self) -> None:
        """Clear all cached adapters."""
        with self._lock:
            logger.info("Clearing adapter cache", cached_adapters=len(self._adapter_cache))

            for adapter_info in self._adapter_cache.values():
                if adapter_info.model is not None:
                    del adapter_info.model

            self._adapter_cache.clear()
            self._current_adapter = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Adapter cache cleared")

    @contextmanager
    def adapter_context(self, project_id: str, adapter_name: str = "default"):
        """
        Context manager for temporary adapter usage.

        Args:
            project_id: Project identifier
            adapter_name: Name of the adapter

        Yields:
            Loaded adapter model or None if loading fails
        """
        adapter_id = self._get_adapter_id(project_id, adapter_name)
        was_loaded = adapter_id in self._adapter_cache

        try:
            # Load adapter
            success = self.load_adapter(project_id, adapter_name)
            if success and adapter_id in self._adapter_cache:
                yield self._adapter_cache[adapter_id].model
            else:
                yield None
        finally:
            # Unload if it wasn't previously loaded
            if not was_loaded:
                self.unload_adapter(project_id, adapter_name)

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the dynamic model loader.

        Returns:
            Health check results
        """
        with self._lock:
            try:
                memory_usage = self._calculate_memory_usage()
                memory_available = self._memory_limit_mb - memory_usage

                health_status = {
                    "status": "healthy" if self._status != LoaderStatus.ERROR else "error",
                    "loader_status": self._status.value,
                    "current_adapter": self._current_adapter,
                    "cached_adapters": len(self._adapter_cache),
                    "memory_usage_mb": memory_usage,
                    "memory_available_mb": memory_available,
                    "memory_utilization_percent": (memory_usage / self._memory_limit_mb) * 100,
                    "base_model_loaded": self._base_model is not None,
                    "base_model_name": self._current_base_model_name,
                    "metrics": self.get_metrics().__dict__
                }

                # Check for potential issues
                warnings = []
                if memory_usage > self._memory_limit_mb * 0.9:
                    warnings.append("High memory usage detected")
                if len(self._adapter_cache) >= self._max_cache_size:
                    warnings.append("Adapter cache is full")

                health_status["warnings"] = warnings

                return health_status

            except Exception as e:
                logger.error("Health check failed", error=str(e))
                return {
                    "status": "error",
                    "error": str(e),
                    "loader_status": self._status.value
                }

    def cleanup(self) -> None:
        """Clean up resources and prepare for shutdown."""
        logger.info("Cleaning up dynamic model loader")

        with self._lock:
            # Clear adapter cache
            self.clear_cache()

            # Unload base model
            if self._base_model is not None:
                del self._base_model
                del self._base_tokenizer
                self._current_base_model_name = None

            if torch.cuda.is_available():
                torch.cuda.empty_cache()

            logger.info("Dynamic model loader cleanup completed")


# Global instance management
_loader_instance: DynamicModelLoader | None = None
_loader_lock = threading.Lock()


def get_dynamic_model_loader(
    settings: Settings | None = None,
    **kwargs
) -> DynamicModelLoader:
    """
    Get the global dynamic model loader instance.

    Args:
        settings: Optional settings override
        **kwargs: Additional arguments for loader initialization

    Returns:
        DynamicModelLoader: The global loader instance
    """
    global _loader_instance

    if _loader_instance is None:
        with _loader_lock:
            if _loader_instance is None:
                from ..config.settings import get_settings
                _loader_instance = DynamicModelLoader(
                    settings or get_settings(),
                    **kwargs
                )

    return _loader_instance


def cleanup_global_loader() -> None:
    """Clean up the global loader instance."""
    global _loader_instance

    if _loader_instance is not None:
        with _loader_lock:
            if _loader_instance is not None:
                _loader_instance.cleanup()
                _loader_instance = None
