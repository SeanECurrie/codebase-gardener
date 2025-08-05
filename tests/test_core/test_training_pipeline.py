"""
Tests for the LoRA training pipeline.

This module tests the training pipeline orchestration, progress tracking,
and integration with existing components.
"""

import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
from typing import Dict, List, Any

import pytest

from codebase_gardener.core.training_pipeline import (
    TrainingPipeline,
    TrainingProgress,
    TrainingPhase,
    TrainingConfig,
    TrainingDataPreparator,
    TrainingProgressTracker,
    get_training_pipeline,
    start_project_training,
    get_project_training_progress,
    is_project_training_active,
    cancel_project_training
)
from codebase_gardener.core.project_registry import TrainingStatus, ProjectMetadata
from codebase_gardener.data.preprocessor import CodeChunk, ChunkType
from codebase_gardener.utils.error_handling import TrainingError


class TestTrainingConfig:
    """Test training configuration."""
    
    def test_default_config(self):
        """Test default configuration values."""
        config = TrainingConfig()
        
        assert config.min_training_chunks == 50
        assert config.max_training_chunks == 5000
        assert config.training_data_quality_threshold == 0.5
        assert config.memory_limit_gb == 4.0
        assert config.training_timeout_minutes == 30
        assert config.progress_update_interval == 5.0
    
    def test_custom_config(self):
        """Test custom configuration values."""
        config = TrainingConfig(
            min_training_chunks=100,
            max_training_chunks=1000,
            training_data_quality_threshold=0.7,
            memory_limit_gb=8.0,
            training_timeout_minutes=60,
            progress_update_interval=10.0
        )
        
        assert config.min_training_chunks == 100
        assert config.max_training_chunks == 1000
        assert config.training_data_quality_threshold == 0.7
        assert config.memory_limit_gb == 8.0
        assert config.training_timeout_minutes == 60
        assert config.progress_update_interval == 10.0
    
    @patch('codebase_gardener.core.training_pipeline.settings')
    def test_from_settings(self, mock_settings):
        """Test creating config from settings."""
        mock_settings.min_training_chunks = 75
        mock_settings.max_training_chunks = 2000
        mock_settings.training_data_quality_threshold = 0.6
        mock_settings.training_memory_limit_gb = 6.0
        mock_settings.training_timeout_minutes = 45
        mock_settings.training_progress_update_interval = 3.0
        
        config = TrainingConfig.from_settings()
        
        assert config.min_training_chunks == 75
        assert config.max_training_chunks == 2000
        assert config.training_data_quality_threshold == 0.6
        assert config.memory_limit_gb == 6.0
        assert config.training_timeout_minutes == 45
        assert config.progress_update_interval == 3.0


class TestTrainingProgress:
    """Test training progress tracking."""
    
    def test_progress_creation(self):
        """Test creating training progress."""
        progress = TrainingProgress(
            phase=TrainingPhase.TRAINING,
            progress_percent=50.0,
            message="Training in progress",
            details={"step": 100}
        )
        
        assert progress.phase == TrainingPhase.TRAINING
        assert progress.progress_percent == 50.0
        assert progress.message == "Training in progress"
        assert progress.details == {"step": 100}
        assert isinstance(progress.timestamp, datetime)
    
    def test_progress_auto_timestamp(self):
        """Test automatic timestamp generation."""
        progress = TrainingProgress(
            phase=TrainingPhase.INITIALIZING,
            progress_percent=0.0,
            message="Starting"
        )
        
        assert progress.timestamp is not None
        assert isinstance(progress.timestamp, datetime)


class TestTrainingDataPreparator:
    """Test training data preparation."""
    
    @pytest.fixture
    def config(self):
        """Training configuration fixture."""
        return TrainingConfig(
            min_training_chunks=5,
            max_training_chunks=100,
            training_data_quality_threshold=0.3
        )
    
    @pytest.fixture
    def preparator(self, config):
        """Training data preparator fixture."""
        return TrainingDataPreparator(config)
    
    @pytest.fixture
    def sample_chunks(self):
        """Sample code chunks for testing."""
        return [
            CodeChunk(
                id="chunk_1",
                content="def hello_world():\n    return 'Hello, World!'",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=Path("test.py"),
                start_line=1,
                end_line=2,
                start_byte=0,
                end_byte=50,
                metadata={"has_docstring": False},
                dependencies=[],
                complexity_score=0.8
            ),
            CodeChunk(
                id="chunk_2",
                content="class TestClass:\n    def __init__(self):\n        self.value = 42",
                language="python",
                chunk_type=ChunkType.CLASS,
                file_path=Path("test.py"),
                start_line=4,
                end_line=6,
                start_byte=51,
                end_byte=100,
                metadata={"has_docstring": False},
                dependencies=[],
                complexity_score=0.6
            ),
            CodeChunk(
                id="chunk_3",
                content="import os\nimport sys",
                language="python",
                chunk_type=ChunkType.IMPORT,
                file_path=Path("test.py"),
                start_line=1,
                end_line=2,
                start_byte=0,
                end_byte=20,
                metadata={},
                dependencies=["os", "sys"],
                complexity_score=0.1
            )
        ]
    
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    @patch('codebase_gardener.core.training_pipeline.VectorStore')
    @patch('codebase_gardener.core.training_pipeline.CodePreprocessor')
    def test_prepare_training_data_success(self, mock_preprocessor_class, mock_vector_store_class, 
                                         mock_registry_class, preparator, sample_chunks):
        """Test successful training data preparation."""
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_project = Mock()
        mock_project.source_path = "/test/project"
        mock_registry.get_project.return_value = mock_project
        
        # Mock vector store (empty)
        mock_vector_store = Mock()
        mock_vector_store_class.return_value = mock_vector_store
        mock_vector_store.get_stats.return_value = {"total_chunks": 0}
        
        # Mock preprocessor
        mock_preprocessor = Mock()
        mock_preprocessor_class.return_value = mock_preprocessor
        mock_preprocessor.preprocess_file.return_value = sample_chunks
        
        # Mock file system
        with patch('pathlib.Path.rglob') as mock_rglob:
            mock_rglob.return_value = [Path("/test/project/test.py")]
            
            training_data = preparator.prepare_training_data("test_project")
        
        assert len(training_data) > 0
        assert all(isinstance(example, dict) for example in training_data)
        assert all("input_ids" in example and "labels" in example for example in training_data)
    
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    def test_prepare_training_data_project_not_found(self, mock_registry_class, preparator):
        """Test training data preparation when project not found."""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_project.return_value = None
        
        with pytest.raises(TrainingError, match="Project 'nonexistent' not found"):
            preparator.prepare_training_data("nonexistent")
    
    def test_filter_quality_chunks(self, preparator, sample_chunks):
        """Test filtering chunks by quality."""
        quality_chunks = preparator._filter_quality_chunks(sample_chunks)
        
        # Should filter out the import chunk (low complexity)
        assert len(quality_chunks) == 2
        assert all(chunk.complexity_score >= 0.3 for chunk in quality_chunks)
    
    def test_is_meaningful_chunk(self, preparator, sample_chunks):
        """Test meaningful chunk detection."""
        function_chunk = sample_chunks[0]  # Function
        class_chunk = sample_chunks[1]     # Class
        import_chunk = sample_chunks[2]    # Import only
        
        assert preparator._is_meaningful_chunk(function_chunk) is True
        assert preparator._is_meaningful_chunk(class_chunk) is True
        assert preparator._is_meaningful_chunk(import_chunk) is False
    
    def test_select_best_chunks(self, preparator, sample_chunks):
        """Test selecting best chunks when limit exceeded."""
        # Set a low limit
        preparator.config.max_training_chunks = 2
        
        selected = preparator._select_best_chunks(sample_chunks)
        
        assert len(selected) == 2
        # Should select chunks with highest complexity scores
        assert selected[0].complexity_score >= selected[1].complexity_score
    
    def test_create_training_examples(self, preparator, sample_chunks):
        """Test creating training examples from chunks."""
        function_chunk = sample_chunks[0]
        examples = preparator._create_training_examples(function_chunk)
        
        assert len(examples) >= 1  # At least explanation example
        assert all("input_ids" in ex and "labels" in ex for ex in examples)
        assert all("metadata" in ex for ex in examples)


class TestTrainingProgressTracker:
    """Test training progress tracking."""
    
    @pytest.fixture
    def config(self):
        """Training configuration fixture."""
        return TrainingConfig()
    
    @pytest.fixture
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    def tracker(self, mock_registry_class, config):
        """Training progress tracker fixture."""
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        return TrainingProgressTracker("test_project", config)
    
    def test_tracker_initialization(self, tracker):
        """Test tracker initialization."""
        assert tracker.project_name == "test_project"
        assert tracker.current_progress.phase == TrainingPhase.INITIALIZING
        assert tracker.current_progress.progress_percent == 0.0
    
    def test_add_progress_callback(self, tracker):
        """Test adding progress callbacks."""
        callback = Mock()
        tracker.add_progress_callback(callback)
        
        # Update progress and verify callback is called
        tracker.update_progress(
            TrainingPhase.TRAINING,
            50.0,
            "Training in progress"
        )
        
        callback.assert_called_once()
        args = callback.call_args[0]
        assert args[0].phase == TrainingPhase.TRAINING
        assert args[0].progress_percent == 50.0
    
    def test_update_progress(self, tracker):
        """Test progress updates."""
        tracker.update_progress(
            TrainingPhase.PREPARING_DATA,
            25.0,
            "Preparing data",
            details={"chunks": 100}
        )
        
        progress = tracker.current_progress
        assert progress.phase == TrainingPhase.PREPARING_DATA
        assert progress.progress_percent == 25.0
        assert progress.message == "Preparing data"
        assert progress.details == {"chunks": 100}
    
    def test_callback_error_handling(self, tracker):
        """Test error handling in callbacks."""
        # Add a callback that raises an exception
        def failing_callback(progress):
            raise ValueError("Callback error")
        
        tracker.add_progress_callback(failing_callback)
        
        # Should not raise exception
        tracker.update_progress(
            TrainingPhase.TRAINING,
            50.0,
            "Training"
        )
        
        # Progress should still be updated
        assert tracker.current_progress.progress_percent == 50.0


class TestTrainingPipeline:
    """Test the main training pipeline."""
    
    @pytest.fixture
    def config(self):
        """Training configuration fixture."""
        return TrainingConfig(
            min_training_chunks=5,
            max_training_chunks=100,
            memory_limit_gb=2.0,
            training_timeout_minutes=5
        )
    
    @pytest.fixture
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    @patch('codebase_gardener.core.training_pipeline.PeftManager')
    def pipeline(self, mock_peft_manager_class, mock_registry_class, config):
        """Training pipeline fixture."""
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        
        # Mock PEFT manager
        mock_peft_manager = Mock()
        mock_peft_manager_class.return_value = mock_peft_manager
        
        return TrainingPipeline(config)
    
    @pytest.fixture
    def mock_project(self):
        """Mock project metadata."""
        return ProjectMetadata(
            project_id="test-id",
            name="test_project",
            source_path=Path("/test/project"),
            created_at=datetime.now(),
            training_status=TrainingStatus.NOT_STARTED
        )
    
    def test_pipeline_initialization(self, pipeline):
        """Test pipeline initialization."""
        assert isinstance(pipeline.config, TrainingConfig)
        assert pipeline.registry is not None
        assert pipeline.peft_manager is not None
        assert pipeline.data_preparator is not None
    
    @patch('codebase_gardener.core.training_pipeline.TrainingDataPreparator')
    def test_start_training_success(self, mock_preparator_class, pipeline, mock_project):
        """Test successful training start."""
        # Mock project registry
        pipeline.registry.get_project.return_value = mock_project
        
        # Mock data preparator
        mock_preparator = Mock()
        mock_preparator_class.return_value = mock_preparator
        mock_preparator.prepare_training_data.return_value = [
            {"input_ids": "test", "labels": "test"}
        ]
        
        # Mock PEFT manager
        pipeline.peft_manager.create_adapter.return_value = "adapter_123"
        
        training_id = pipeline.start_training("test_project")
        
        assert training_id is not None
        assert "test_project" in training_id
        assert pipeline.is_training_active("test_project")
    
    def test_start_training_project_not_found(self, pipeline):
        """Test training start when project not found."""
        pipeline.registry.get_project.return_value = None
        
        with pytest.raises(TrainingError, match="Project 'nonexistent' not found"):
            pipeline.start_training("nonexistent")
    
    def test_start_training_already_in_progress(self, pipeline, mock_project):
        """Test training start when already in progress."""
        pipeline.registry.get_project.return_value = mock_project
        
        # Start first training
        with patch.object(pipeline, '_run_training'):
            pipeline.start_training("test_project")
        
        # Try to start second training
        with pytest.raises(TrainingError, match="Training already in progress"):
            pipeline.start_training("test_project")
    
    def test_get_training_progress(self, pipeline, mock_project):
        """Test getting training progress."""
        pipeline.registry.get_project.return_value = mock_project
        
        # No training started
        progress = pipeline.get_training_progress("test_project")
        assert progress is None
        
        # Start training
        with patch.object(pipeline, '_run_training'):
            pipeline.start_training("test_project")
        
        # Should have progress now
        progress = pipeline.get_training_progress("test_project")
        assert progress is not None
        assert progress.phase == TrainingPhase.INITIALIZING
    
    def test_cancel_training(self, pipeline, mock_project):
        """Test cancelling training."""
        pipeline.registry.get_project.return_value = mock_project
        
        # Start training
        with patch.object(pipeline, '_run_training'):
            pipeline.start_training("test_project")
        
        # Cancel training
        result = pipeline.cancel_training("test_project")
        assert result is True
        
        # Check progress is marked as failed
        progress = pipeline.get_training_progress("test_project")
        assert progress.phase == TrainingPhase.FAILED
        assert "cancelled" in progress.message.lower()
    
    def test_cancel_training_not_active(self, pipeline):
        """Test cancelling training when not active."""
        result = pipeline.cancel_training("nonexistent")
        assert result is False
    
    @patch('codebase_gardener.core.training_pipeline.psutil')
    def test_check_memory_availability_sufficient(self, mock_psutil, pipeline):
        """Test memory check with sufficient memory."""
        mock_psutil.virtual_memory.return_value.available = 8 * 1024**3  # 8GB
        
        # Should not raise exception
        pipeline._check_memory_availability()
    
    @patch('codebase_gardener.core.training_pipeline.psutil')
    def test_check_memory_availability_insufficient(self, mock_psutil, pipeline):
        """Test memory check with insufficient memory."""
        mock_psutil.virtual_memory.return_value.available = 1 * 1024**3  # 1GB
        
        with pytest.raises(TrainingError, match="Insufficient memory"):
            pipeline._check_memory_availability()
    
    def test_get_active_trainings(self, pipeline, mock_project):
        """Test getting all active trainings."""
        pipeline.registry.get_project.return_value = mock_project
        
        # No active trainings
        active = pipeline.get_active_trainings()
        assert len(active) == 0
        
        # Start training
        with patch.object(pipeline, '_run_training'):
            pipeline.start_training("test_project")
        
        # Should have one active training
        active = pipeline.get_active_trainings()
        assert len(active) == 1
        assert "test_project" in active
    
    def test_training_context(self, pipeline):
        """Test training context manager."""
        with pipeline.training_context("test_project"):
            # Should not raise exception
            pass
    
    def test_training_context_with_error(self, pipeline):
        """Test training context manager with error."""
        with pytest.raises(ValueError):
            with pipeline.training_context("test_project"):
                raise ValueError("Test error")


class TestGlobalFunctions:
    """Test global convenience functions."""
    
    @patch('codebase_gardener.core.training_pipeline.TrainingPipeline')
    def test_get_training_pipeline(self, mock_pipeline_class):
        """Test getting global training pipeline."""
        mock_pipeline = Mock()
        mock_pipeline_class.return_value = mock_pipeline
        
        # Clear global instance
        import codebase_gardener.core.training_pipeline as tp_module
        tp_module._training_pipeline = None
        
        pipeline = get_training_pipeline()
        assert pipeline is not None
        
        # Should return same instance on second call
        pipeline2 = get_training_pipeline()
        assert pipeline is pipeline2
    
    @patch('codebase_gardener.core.training_pipeline.get_training_pipeline')
    def test_start_project_training(self, mock_get_pipeline):
        """Test starting project training."""
        mock_pipeline = Mock()
        mock_pipeline.start_training.return_value = "training_123"
        mock_get_pipeline.return_value = mock_pipeline
        
        callback = Mock()
        training_id = start_project_training("test_project", callback)
        
        assert training_id == "training_123"
        mock_pipeline.start_training.assert_called_once_with("test_project", callback)
    
    @patch('codebase_gardener.core.training_pipeline.get_training_pipeline')
    def test_get_project_training_progress(self, mock_get_pipeline):
        """Test getting project training progress."""
        mock_pipeline = Mock()
        mock_progress = Mock()
        mock_pipeline.get_training_progress.return_value = mock_progress
        mock_get_pipeline.return_value = mock_pipeline
        
        progress = get_project_training_progress("test_project")
        
        assert progress is mock_progress
        mock_pipeline.get_training_progress.assert_called_once_with("test_project")
    
    @patch('codebase_gardener.core.training_pipeline.get_training_pipeline')
    def test_is_project_training_active(self, mock_get_pipeline):
        """Test checking if project training is active."""
        mock_pipeline = Mock()
        mock_pipeline.is_training_active.return_value = True
        mock_get_pipeline.return_value = mock_pipeline
        
        is_active = is_project_training_active("test_project")
        
        assert is_active is True
        mock_pipeline.is_training_active.assert_called_once_with("test_project")
    
    @patch('codebase_gardener.core.training_pipeline.get_training_pipeline')
    def test_cancel_project_training(self, mock_get_pipeline):
        """Test cancelling project training."""
        mock_pipeline = Mock()
        mock_pipeline.cancel_training.return_value = True
        mock_get_pipeline.return_value = mock_pipeline
        
        result = cancel_project_training("test_project")
        
        assert result is True
        mock_pipeline.cancel_training.assert_called_once_with("test_project")


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @pytest.fixture
    def config(self):
        """Training configuration fixture."""
        return TrainingConfig(
            min_training_chunks=2,
            max_training_chunks=10,
            memory_limit_gb=1.0,
            training_timeout_minutes=1
        )
    
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    @patch('codebase_gardener.core.training_pipeline.PeftManager')
    @patch('codebase_gardener.core.training_pipeline.TrainingDataPreparator')
    def test_full_training_workflow(self, mock_preparator_class, mock_peft_manager_class, 
                                  mock_registry_class, config):
        """Test complete training workflow."""
        # Mock project
        mock_project = ProjectMetadata(
            project_id="test-id",
            name="test_project",
            source_path=Path("/test/project"),
            created_at=datetime.now(),
            training_status=TrainingStatus.NOT_STARTED
        )
        
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_project.return_value = mock_project
        
        # Mock data preparator
        mock_preparator = Mock()
        mock_preparator_class.return_value = mock_preparator
        mock_preparator.prepare_training_data.return_value = [
            {"input_ids": "test input", "labels": "test output"}
        ]
        
        # Mock PEFT manager
        mock_peft_manager = Mock()
        mock_peft_manager_class.return_value = mock_peft_manager
        mock_peft_manager.create_adapter.return_value = "adapter_123"
        
        # Create pipeline
        pipeline = TrainingPipeline(config)
        
        # Track progress updates
        progress_updates = []
        def progress_callback(progress):
            progress_updates.append(progress)
        
        # Start training
        training_id = pipeline.start_training("test_project", progress_callback)
        
        # Wait a bit for background thread
        time.sleep(0.1)
        
        # Verify training was started
        assert training_id is not None
        assert pipeline.is_training_active("test_project")
        
        # Wait for completion (with timeout)
        start_time = time.time()
        while pipeline.is_training_active("test_project") and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Verify final state
        final_progress = pipeline.get_training_progress("test_project")
        assert final_progress is not None
        
        # Verify PEFT manager was called
        mock_peft_manager.create_adapter.assert_called_once()
    
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    @patch('codebase_gardener.core.training_pipeline.PeftManager')
    @patch('codebase_gardener.core.training_pipeline.TrainingDataPreparator')
    def test_training_failure_handling(self, mock_preparator_class, mock_peft_manager_class, 
                                     mock_registry_class, config):
        """Test training failure handling."""
        # Mock project
        mock_project = ProjectMetadata(
            project_id="test-id",
            name="test_project",
            source_path=Path("/test/project"),
            created_at=datetime.now(),
            training_status=TrainingStatus.NOT_STARTED
        )
        
        # Mock registry
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_registry.get_project.return_value = mock_project
        
        # Mock data preparator to fail
        mock_preparator = Mock()
        mock_preparator_class.return_value = mock_preparator
        mock_preparator.prepare_training_data.side_effect = Exception("Data preparation failed")
        
        # Mock PEFT manager
        mock_peft_manager = Mock()
        mock_peft_manager_class.return_value = mock_peft_manager
        
        # Create pipeline
        pipeline = TrainingPipeline(config)
        
        # Start training
        training_id = pipeline.start_training("test_project")
        
        # Wait for failure
        start_time = time.time()
        while pipeline.is_training_active("test_project") and time.time() - start_time < 5:
            time.sleep(0.1)
        
        # Verify failure state
        final_progress = pipeline.get_training_progress("test_project")
        assert final_progress is not None
        assert final_progress.phase == TrainingPhase.FAILED
        assert "failed" in final_progress.message.lower()
        
        # Verify registry was updated
        mock_registry.update_training_status.assert_called_with("test_project", TrainingStatus.FAILED)


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def config(self):
        """Training configuration fixture."""
        return TrainingConfig(min_training_chunks=100)  # High threshold
    
    @pytest.fixture
    def preparator(self, config):
        """Training data preparator fixture."""
        return TrainingDataPreparator(config)
    
    @patch('codebase_gardener.core.training_pipeline.ProjectRegistry')
    def test_insufficient_training_data(self, mock_registry_class, preparator):
        """Test error when insufficient training data."""
        # Mock registry with valid project
        mock_registry = Mock()
        mock_registry_class.return_value = mock_registry
        mock_project = Mock()
        mock_project.source_path = "/test/project"
        mock_registry.get_project.return_value = mock_project
        
        # Mock empty vector store and no files
        with patch('codebase_gardener.core.training_pipeline.VectorStore') as mock_vs_class:
            mock_vs = Mock()
            mock_vs_class.return_value = mock_vs
            mock_vs.get_stats.return_value = {"total_chunks": 0}
            
            with patch('pathlib.Path.rglob') as mock_rglob:
                mock_rglob.return_value = []  # No files
                
                with pytest.raises(TrainingError, match="Insufficient training data"):
                    preparator.prepare_training_data("test_project")
    
    def test_training_error_details(self):
        """Test training error includes helpful details."""
        try:
            raise TrainingError(
                "Test training error",
                details={"step": "data_preparation", "chunks_found": 10}
            )
        except TrainingError as e:
            assert e.message == "Test training error"
            assert e.details["step"] == "data_preparation"
            assert e.details["chunks_found"] == 10
            assert len(e.suggestions) > 0


if __name__ == "__main__":
    pytest.main([__file__])