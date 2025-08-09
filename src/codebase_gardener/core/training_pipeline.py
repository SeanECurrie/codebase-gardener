"""
LoRA Training Pipeline for Codebase Gardener.

This module provides a comprehensive training pipeline that orchestrates the training
of project-specific LoRA adapters. It coordinates between existing components to
provide a seamless training experience with progress tracking and error handling.
"""

import threading
import time
from collections.abc import Callable
from contextlib import contextmanager
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

from codebase_gardener.config import settings
from codebase_gardener.core.project_registry import ProjectRegistry, TrainingStatus
from codebase_gardener.data.preprocessor import CodeChunk, CodePreprocessor
from codebase_gardener.data.vector_store import VectorStore
from codebase_gardener.models.peft_manager import PeftManager
from codebase_gardener.utils.error_handling import (
    TrainingError,
    retry_with_exponential_backoff,
)

logger = structlog.get_logger(__name__)


class TrainingPhase(str, Enum):
    """Training pipeline phases for progress tracking."""
    INITIALIZING = "initializing"
    PREPARING_DATA = "preparing_data"
    STARTING_TRAINING = "starting_training"
    TRAINING = "training"
    COMPLETING = "completing"
    COMPLETED = "completed"
    FAILED = "failed"


@dataclass
class TrainingProgress:
    """Training progress information."""
    phase: TrainingPhase
    progress_percent: float
    message: str
    details: dict[str, Any] | None = None
    timestamp: datetime | None = None

    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now()


@dataclass
class TrainingConfig:
    """Configuration for training pipeline."""
    min_training_chunks: int = 50
    max_training_chunks: int = 5000
    training_data_quality_threshold: float = 0.5
    memory_limit_gb: float = 4.0
    training_timeout_minutes: int = 30
    progress_update_interval: float = 5.0  # seconds

    @classmethod
    def from_settings(cls) -> 'TrainingConfig':
        """Create training config from application settings."""
        return cls(
            min_training_chunks=getattr(settings, 'min_training_chunks', 50),
            max_training_chunks=getattr(settings, 'max_training_chunks', 5000),
            training_data_quality_threshold=getattr(settings, 'training_data_quality_threshold', 0.5),
            memory_limit_gb=getattr(settings, 'training_memory_limit_gb', 4.0),
            training_timeout_minutes=getattr(settings, 'training_timeout_minutes', 30),
            progress_update_interval=getattr(settings, 'training_progress_update_interval', 5.0),
        )


class TrainingDataPreparator:
    """Prepares code chunks for LoRA training."""

    def __init__(self, config: TrainingConfig):
        self.config = config
        self.logger = structlog.get_logger(__name__).bind(component="training_data_preparator")

    def prepare_training_data(self, project_name: str) -> list[dict[str, Any]]:
        """
        Prepare training data from project code chunks.

        Args:
            project_name: Name of the project to prepare data for

        Returns:
            List of training examples in HuggingFace format

        Raises:
            TrainingError: If data preparation fails
        """
        self.logger.info("Starting training data preparation", project_name=project_name)

        try:
            # Get project metadata
            registry = ProjectRegistry()
            project = registry.get_project(project_name)
            if not project:
                raise TrainingError(f"Project '{project_name}' not found in registry")

            # Load code chunks from vector store or preprocessing
            chunks = self._load_code_chunks(project_name)

            # Filter and validate chunks
            quality_chunks = self._filter_quality_chunks(chunks)

            # Check minimum data requirements
            if len(quality_chunks) < self.config.min_training_chunks:
                raise TrainingError(
                    f"Insufficient training data: {len(quality_chunks)} chunks "
                    f"(minimum required: {self.config.min_training_chunks})",
                    details={
                        "chunks_found": len(chunks),
                        "quality_chunks": len(quality_chunks),
                        "minimum_required": self.config.min_training_chunks
                    }
                )

            # Limit chunks to prevent memory issues
            if len(quality_chunks) > self.config.max_training_chunks:
                quality_chunks = self._select_best_chunks(quality_chunks)
                self.logger.info(
                    "Limited training chunks for memory efficiency",
                    original_count=len(quality_chunks),
                    selected_count=len(quality_chunks)
                )

            # Convert to training format
            training_data = self._convert_to_training_format(quality_chunks)

            self.logger.info(
                "Training data preparation completed",
                project_name=project_name,
                training_examples=len(training_data),
                chunk_count=len(quality_chunks)
            )

            return training_data

        except Exception as e:
            self.logger.error(
                "Training data preparation failed",
                project_name=project_name,
                error=str(e)
            )
            if isinstance(e, TrainingError):
                raise
            raise TrainingError(f"Failed to prepare training data: {e}") from e

    def _load_code_chunks(self, project_name: str) -> list[CodeChunk]:
        """Load code chunks for the project."""
        try:
            # Try to load from vector store first
            vector_store = VectorStore(project_name)
            if vector_store.get_stats()["total_chunks"] > 0:
                # Get all chunks from vector store
                # This is a simplified approach - in practice, we'd need a method to get all chunks
                self.logger.info("Loading chunks from vector store", project_name=project_name)
                return []  # Placeholder - would implement actual chunk loading

            # Fall back to preprocessing project files
            self.logger.info("Preprocessing project files for training data", project_name=project_name)
            registry = ProjectRegistry()
            project = registry.get_project(project_name)

            preprocessor = CodePreprocessor()
            chunks = []

            # Process all Python files in the project
            source_path = Path(project.source_path)
            for py_file in source_path.rglob("*.py"):
                try:
                    file_chunks = preprocessor.preprocess_file(py_file)
                    chunks.extend(file_chunks)
                except Exception as e:
                    self.logger.warning(
                        "Failed to preprocess file",
                        file_path=str(py_file),
                        error=str(e)
                    )
                    continue

            return chunks

        except Exception as e:
            raise TrainingError(f"Failed to load code chunks: {e}") from e

    def _filter_quality_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Filter chunks based on quality criteria."""
        quality_chunks = []

        for chunk in chunks:
            # Check complexity score
            if chunk.complexity_score < self.config.training_data_quality_threshold:
                continue

            # Check content length
            if len(chunk.content.strip()) < 20:
                continue

            # Check for meaningful content (not just imports or comments)
            if self._is_meaningful_chunk(chunk):
                quality_chunks.append(chunk)

        self.logger.info(
            "Filtered chunks by quality",
            original_count=len(chunks),
            quality_count=len(quality_chunks),
            threshold=self.config.training_data_quality_threshold
        )

        return quality_chunks

    def _is_meaningful_chunk(self, chunk: CodeChunk) -> bool:
        """Check if chunk contains meaningful code for training."""
        content = chunk.content.strip()

        # Skip chunks that are mostly imports
        lines = content.split('\n')
        import_lines = sum(1 for line in lines if line.strip().startswith(('import ', 'from ')))
        if import_lines / len(lines) > 0.8:
            return False

        # Skip chunks that are mostly comments
        comment_lines = sum(1 for line in lines if line.strip().startswith('#'))
        if comment_lines / len(lines) > 0.6:
            return False

        # Require minimum function/class content
        has_function = 'def ' in content
        has_class = 'class ' in content

        return has_function or has_class

    def _select_best_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Select the best chunks when we have too many."""
        # Sort by complexity score (descending) and take the top chunks
        sorted_chunks = sorted(chunks, key=lambda c: c.complexity_score, reverse=True)
        return sorted_chunks[:self.config.max_training_chunks]

    def _convert_to_training_format(self, chunks: list[CodeChunk]) -> list[dict[str, Any]]:
        """Convert code chunks to HuggingFace training format."""
        training_data = []

        for chunk in chunks:
            # Create training examples for code completion and explanation
            examples = self._create_training_examples(chunk)
            training_data.extend(examples)

        return training_data

    def _create_training_examples(self, chunk: CodeChunk) -> list[dict[str, Any]]:
        """Create training examples from a code chunk."""
        examples = []

        # Example 1: Code completion
        if len(chunk.content) > 100:
            # Take first 60% as input, rest as completion
            split_point = int(len(chunk.content) * 0.6)
            input_text = chunk.content[:split_point]
            completion = chunk.content[split_point:]

            examples.append({
                "input_ids": f"Complete this {chunk.language} code:\n{input_text}",
                "labels": completion,
                "metadata": {
                    "chunk_id": chunk.id,
                    "chunk_type": chunk.chunk_type.value,
                    "language": chunk.language,
                    "complexity": chunk.complexity_score
                }
            })

        # Example 2: Code explanation
        examples.append({
            "input_ids": f"Explain this {chunk.language} code:\n{chunk.content}",
            "labels": f"This code defines a {chunk.chunk_type.value} that implements functionality "
                     f"with complexity score {chunk.complexity_score:.2f}. "
                     f"Dependencies: {', '.join(chunk.dependencies[:3]) if chunk.dependencies else 'none'}.",
            "metadata": {
                "chunk_id": chunk.id,
                "chunk_type": chunk.chunk_type.value,
                "language": chunk.language,
                "complexity": chunk.complexity_score
            }
        })

        return examples


class TrainingProgressTracker:
    """Tracks and manages training progress."""

    def __init__(self, project_name: str, config: TrainingConfig):
        self.project_name = project_name
        self.config = config
        self.registry = ProjectRegistry()
        self.logger = structlog.get_logger(__name__).bind(
            component="training_progress_tracker",
            project_name=project_name
        )

        self._current_progress = TrainingProgress(
            phase=TrainingPhase.INITIALIZING,
            progress_percent=0.0,
            message="Initializing training pipeline"
        )
        self._callbacks: list[Callable[[TrainingProgress], None]] = []
        self._lock = threading.Lock()

    def add_progress_callback(self, callback: Callable[[TrainingProgress], None]):
        """Add a callback for progress updates."""
        with self._lock:
            self._callbacks.append(callback)

    def update_progress(
        self,
        phase: TrainingPhase,
        progress_percent: float,
        message: str,
        details: dict[str, Any] | None = None
    ):
        """Update training progress."""
        with self._lock:
            self._current_progress = TrainingProgress(
                phase=phase,
                progress_percent=progress_percent,
                message=message,
                details=details
            )

            # Update registry status
            if phase == TrainingPhase.TRAINING:
                status = TrainingStatus.TRAINING
            elif phase == TrainingPhase.COMPLETED:
                status = TrainingStatus.COMPLETED
            elif phase == TrainingPhase.FAILED:
                status = TrainingStatus.FAILED
            else:
                status = TrainingStatus.TRAINING

            try:
                self.registry.update_training_status(self.project_name, status)
            except Exception as e:
                self.logger.warning("Failed to update registry status", error=str(e))

            # Log progress
            self.logger.info(
                "Training progress updated",
                phase=phase.value,
                progress_percent=progress_percent,
                message=message,
                details=details
            )

            # Notify callbacks
            for callback in self._callbacks:
                try:
                    callback(self._current_progress)
                except Exception as e:
                    self.logger.warning("Progress callback failed", error=str(e))

    @property
    def current_progress(self) -> TrainingProgress:
        """Get current training progress."""
        with self._lock:
            return self._current_progress


class TrainingPipeline:
    """
    Main training pipeline orchestrator.

    Coordinates between PeftManager, ProjectRegistry, and other components
    to provide a seamless training experience with progress tracking.
    """

    def __init__(self, config: TrainingConfig | None = None):
        self.config = config or TrainingConfig.from_settings()
        self.registry = ProjectRegistry()
        self.peft_manager = PeftManager(settings)
        self.data_preparator = TrainingDataPreparator(self.config)
        self.logger = structlog.get_logger(__name__).bind(component="training_pipeline")

        self._active_trainings: dict[str, TrainingProgressTracker] = {}
        self._training_threads: dict[str, threading.Thread] = {}
        self._lock = threading.Lock()

    @retry_with_exponential_backoff(max_retries=2)
    def start_training(
        self,
        project_name: str,
        progress_callback: Callable[[TrainingProgress], None] | None = None
    ) -> str:
        """
        Start training a LoRA adapter for the specified project.

        Args:
            project_name: Name of the project to train
            progress_callback: Optional callback for progress updates

        Returns:
            Training ID for tracking progress

        Raises:
            TrainingError: If training cannot be started
        """
        self.logger.info("Starting training pipeline", project_name=project_name)

        # Validate project exists
        project = self.registry.get_project(project_name)
        if not project:
            raise TrainingError(f"Project '{project_name}' not found in registry")

        # Check if training is already in progress
        with self._lock:
            if project_name in self._active_trainings:
                current_progress = self._active_trainings[project_name].current_progress
                if current_progress.phase not in [TrainingPhase.COMPLETED, TrainingPhase.FAILED]:
                    raise TrainingError(
                        f"Training already in progress for project '{project_name}'",
                        details={"current_phase": current_progress.phase.value}
                    )

        # Create progress tracker
        progress_tracker = TrainingProgressTracker(project_name, self.config)
        if progress_callback:
            progress_tracker.add_progress_callback(progress_callback)

        with self._lock:
            self._active_trainings[project_name] = progress_tracker

        # Start training in background thread
        training_thread = threading.Thread(
            target=self._run_training,
            args=(project_name, progress_tracker),
            name=f"training-{project_name}",
            daemon=True
        )

        with self._lock:
            self._training_threads[project_name] = training_thread

        training_thread.start()

        training_id = f"{project_name}-{int(time.time())}"
        self.logger.info(
            "Training started in background",
            project_name=project_name,
            training_id=training_id
        )

        return training_id

    def get_training_progress(self, project_name: str) -> TrainingProgress | None:
        """Get current training progress for a project."""
        with self._lock:
            tracker = self._active_trainings.get(project_name)
            return tracker.current_progress if tracker else None

    def is_training_active(self, project_name: str) -> bool:
        """Check if training is currently active for a project."""
        progress = self.get_training_progress(project_name)
        if not progress:
            return False

        return progress.phase not in [TrainingPhase.COMPLETED, TrainingPhase.FAILED]

    def cancel_training(self, project_name: str) -> bool:
        """
        Cancel active training for a project.

        Args:
            project_name: Name of the project

        Returns:
            True if training was cancelled, False if no active training
        """
        with self._lock:
            if project_name not in self._active_trainings:
                return False

            # Update progress to indicate cancellation
            tracker = self._active_trainings[project_name]
            tracker.update_progress(
                TrainingPhase.FAILED,
                0.0,
                "Training cancelled by user"
            )

            # Clean up
            self._cleanup_training(project_name)

        self.logger.info("Training cancelled", project_name=project_name)
        return True

    def _run_training(self, project_name: str, progress_tracker: TrainingProgressTracker):
        """Run the complete training pipeline."""
        try:
            # Phase 1: Initialize (0-10%)
            progress_tracker.update_progress(
                TrainingPhase.INITIALIZING,
                5.0,
                "Initializing training pipeline"
            )

            # Check memory availability
            self._check_memory_availability()

            progress_tracker.update_progress(
                TrainingPhase.INITIALIZING,
                10.0,
                "Memory check completed"
            )

            # Phase 2: Prepare training data (10-30%)
            progress_tracker.update_progress(
                TrainingPhase.PREPARING_DATA,
                15.0,
                "Loading and processing code chunks"
            )

            training_data = self.data_preparator.prepare_training_data(project_name)

            progress_tracker.update_progress(
                TrainingPhase.PREPARING_DATA,
                30.0,
                f"Training data prepared: {len(training_data)} examples"
            )

            # Phase 3: Start training (30-40%)
            progress_tracker.update_progress(
                TrainingPhase.STARTING_TRAINING,
                35.0,
                "Initializing LoRA adapter training"
            )

            # Create training progress callback for PeftManager
            def peft_progress_callback(peft_progress: float, message: str):
                # Map PEFT progress (0-100%) to our training phase (40-90%)
                pipeline_progress = 40.0 + (peft_progress * 0.5)
                progress_tracker.update_progress(
                    TrainingPhase.TRAINING,
                    pipeline_progress,
                    message
                )

            # Start actual training
            adapter_id = self.peft_manager.create_adapter(
                project_name,
                training_data,
                progress_callback=peft_progress_callback
            )

            progress_tracker.update_progress(
                TrainingPhase.TRAINING,
                90.0,
                "Training completed, finalizing adapter"
            )

            # Phase 4: Complete (90-100%)
            progress_tracker.update_progress(
                TrainingPhase.COMPLETING,
                95.0,
                "Saving adapter and updating metadata"
            )

            # Update registry with completion
            self.registry.update_training_status(project_name, TrainingStatus.COMPLETED)

            progress_tracker.update_progress(
                TrainingPhase.COMPLETED,
                100.0,
                f"Training completed successfully. Adapter ID: {adapter_id}",
                details={"adapter_id": adapter_id}
            )

            self.logger.info(
                "Training pipeline completed successfully",
                project_name=project_name,
                adapter_id=adapter_id
            )

        except Exception as e:
            self.logger.error(
                "Training pipeline failed",
                project_name=project_name,
                error=str(e),
                error_type=type(e).__name__
            )

            # Update progress to failed state
            progress_tracker.update_progress(
                TrainingPhase.FAILED,
                0.0,
                f"Training failed: {str(e)}",
                details={"error": str(e), "error_type": type(e).__name__}
            )

            # Update registry
            try:
                self.registry.update_training_status(project_name, TrainingStatus.FAILED)
            except Exception as registry_error:
                self.logger.error(
                    "Failed to update registry status",
                    project_name=project_name,
                    error=str(registry_error)
                )

        finally:
            # Clean up training resources
            self._cleanup_training(project_name)

    def _check_memory_availability(self):
        """Check if sufficient memory is available for training."""
        try:
            import psutil
            available_memory_gb = psutil.virtual_memory().available / (1024**3)

            if available_memory_gb < self.config.memory_limit_gb:
                raise TrainingError(
                    f"Insufficient memory for training: {available_memory_gb:.1f}GB available, "
                    f"{self.config.memory_limit_gb}GB required",
                    details={
                        "available_memory_gb": available_memory_gb,
                        "required_memory_gb": self.config.memory_limit_gb
                    }
                )

            self.logger.info(
                "Memory check passed",
                available_memory_gb=available_memory_gb,
                required_memory_gb=self.config.memory_limit_gb
            )

        except ImportError:
            self.logger.warning("psutil not available, skipping memory check")
        except Exception as e:
            self.logger.warning("Memory check failed", error=str(e))

    def _cleanup_training(self, project_name: str):
        """Clean up training resources."""
        with self._lock:
            # Remove from active trainings
            if project_name in self._active_trainings:
                del self._active_trainings[project_name]

            # Clean up thread reference
            if project_name in self._training_threads:
                del self._training_threads[project_name]

        self.logger.debug("Training resources cleaned up", project_name=project_name)

    @contextmanager
    def training_context(self, project_name: str):
        """Context manager for training operations."""
        self.logger.info("Entering training context", project_name=project_name)
        try:
            yield
        except Exception as e:
            self.logger.error(
                "Error in training context",
                project_name=project_name,
                error=str(e)
            )
            raise
        finally:
            self.logger.info("Exiting training context", project_name=project_name)

    def get_active_trainings(self) -> dict[str, TrainingProgress]:
        """Get all currently active trainings."""
        with self._lock:
            return {
                project_name: tracker.current_progress
                for project_name, tracker in self._active_trainings.items()
            }

    def wait_for_training_completion(
        self,
        project_name: str,
        timeout_seconds: float | None = None
    ) -> TrainingProgress:
        """
        Wait for training to complete.

        Args:
            project_name: Name of the project
            timeout_seconds: Maximum time to wait (None for no timeout)

        Returns:
            Final training progress

        Raises:
            TrainingError: If training fails or times out
        """
        start_time = time.time()
        timeout_seconds = timeout_seconds or (self.config.training_timeout_minutes * 60)

        while True:
            progress = self.get_training_progress(project_name)
            if not progress:
                raise TrainingError(f"No training found for project '{project_name}'")

            if progress.phase in [TrainingPhase.COMPLETED, TrainingPhase.FAILED]:
                return progress

            if time.time() - start_time > timeout_seconds:
                raise TrainingError(
                    f"Training timeout after {timeout_seconds}s",
                    details={"timeout_seconds": timeout_seconds}
                )

            time.sleep(self.config.progress_update_interval)


# Global training pipeline instance
_training_pipeline: TrainingPipeline | None = None


def get_training_pipeline() -> TrainingPipeline:
    """Get the global training pipeline instance."""
    global _training_pipeline
    if _training_pipeline is None:
        _training_pipeline = TrainingPipeline()
    return _training_pipeline


# Convenience functions for external use

def start_project_training(
    project_name: str,
    progress_callback: Callable[[TrainingProgress], None] | None = None
) -> str:
    """Start training for a project."""
    pipeline = get_training_pipeline()
    return pipeline.start_training(project_name, progress_callback)


def get_project_training_progress(project_name: str) -> TrainingProgress | None:
    """Get training progress for a project."""
    pipeline = get_training_pipeline()
    return pipeline.get_training_progress(project_name)


def is_project_training_active(project_name: str) -> bool:
    """Check if training is active for a project."""
    pipeline = get_training_pipeline()
    return pipeline.is_training_active(project_name)


def cancel_project_training(project_name: str) -> bool:
    """Cancel training for a project."""
    pipeline = get_training_pipeline()
    return pipeline.cancel_training(project_name)
