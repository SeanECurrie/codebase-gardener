"""
Tests for the PEFT Manager module.

Comprehensive test suite covering LoRA adapter creation, training, loading,
and resource management functionality.
"""

import json
import pytest
import tempfile
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, call

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

from src.codebase_gardener.models.peft_manager import (
    PeftManager,
    AdapterMetadata,
    TrainingProgress,
    TrainingError,
    AdapterError
)
from src.codebase_gardener.config.settings import Settings
from src.codebase_gardener.utils.error_handling import ModelError


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.data_dir = Path(tempfile.mkdtemp())
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_timeout = 30
    return settings


@pytest.fixture
def peft_manager(mock_settings):
    """Create PeftManager instance for testing."""
    with patch('src.codebase_gardener.models.peft_manager.logger'):
        return PeftManager(mock_settings)


@pytest.fixture
def sample_training_data():
    """Sample training data for testing."""
    return [
        {"input": "def hello():", "output": "    return 'Hello, World!'"},
        {"input": "class MyClass:", "output": "    def __init__(self):\n        pass"},
        {"input": "import numpy as np", "output": "# NumPy for numerical operations"},
    ]


@pytest.fixture
def sample_adapter_metadata():
    """Sample adapter metadata for testing."""
    return AdapterMetadata(
        name="test_adapter",
        project_name="test_project",
        created_at=datetime.now(),
        model_name="microsoft/DialoGPT-medium",
        config={"r": 16, "lora_alpha": 32},
        training_metrics={"final_loss": 0.5},
        file_path=Path("/tmp/test_adapter.bin"),
        size_mb=10.5,
        status="ready"
    )


class TestPeftManagerInitialization:
    """Test PeftManager initialization and setup."""
    
    def test_initialization_success(self, mock_settings):
        """Test successful PeftManager initialization."""
        with patch('src.codebase_gardener.models.peft_manager.logger'):
            manager = PeftManager(mock_settings)
            
            assert manager.settings == mock_settings
            assert manager.adapters_dir == mock_settings.data_dir / "adapters"
            assert manager.adapters_dir.exists()
            assert len(manager._adapters_cache) == 0
            assert len(manager._adapter_metadata) == 0
    
    def test_adapters_directory_creation(self, mock_settings):
        """Test that adapters directory is created."""
        adapters_dir = mock_settings.data_dir / "adapters"
        assert not adapters_dir.exists()
        
        with patch('src.codebase_gardener.models.peft_manager.logger'):
            PeftManager(mock_settings)
            
        assert adapters_dir.exists()
    
    def test_load_existing_metadata(self, mock_settings, sample_adapter_metadata):
        """Test loading existing adapter metadata."""
        # Create metadata file
        adapters_dir = mock_settings.data_dir / "adapters"
        adapters_dir.mkdir(parents=True, exist_ok=True)
        
        metadata_file = adapters_dir / "metadata.json"
        metadata_dict = {
            "test_project_test_adapter": {
                "name": sample_adapter_metadata.name,
                "project_name": sample_adapter_metadata.project_name,
                "created_at": sample_adapter_metadata.created_at.isoformat(),
                "model_name": sample_adapter_metadata.model_name,
                "config": sample_adapter_metadata.config,
                "training_metrics": sample_adapter_metadata.training_metrics,
                "file_path": str(sample_adapter_metadata.file_path),
                "size_mb": sample_adapter_metadata.size_mb,
                "status": sample_adapter_metadata.status
            }
        }
        
        with open(metadata_file, 'w') as f:
            json.dump(metadata_dict, f)
        
        with patch('src.codebase_gardener.models.peft_manager.logger'):
            manager = PeftManager(mock_settings)
            
        assert len(manager._adapter_metadata) == 1
        assert "test_project_test_adapter" in manager._adapter_metadata


class TestAdapterCreation:
    """Test LoRA adapter creation and training."""
    
    @patch('src.codebase_gardener.models.peft_manager.threading.Thread')
    def test_create_adapter_success(self, mock_thread, peft_manager, sample_training_data):
        """Test successful adapter creation."""
        mock_thread_instance = Mock()
        mock_thread.return_value = mock_thread_instance
        
        with patch.object(peft_manager, '_check_memory_usage', return_value={"available_gb": 4.0}):
            adapter_id = peft_manager.create_adapter(
                project_name="test_project",
                training_data=sample_training_data,
                adapter_name="test_adapter"
            )
        
        assert adapter_id == "test_project_test_adapter"
        assert adapter_id in peft_manager._adapter_metadata
        
        metadata = peft_manager._adapter_metadata[adapter_id]
        assert metadata.name == "test_adapter"
        assert metadata.project_name == "test_project"
        assert metadata.status == "training"
        
        # Verify training thread was started
        mock_thread.assert_called_once()
        mock_thread_instance.start.assert_called_once()
    
    def test_create_adapter_insufficient_memory(self, peft_manager, sample_training_data):
        """Test adapter creation with insufficient memory."""
        with patch.object(peft_manager, '_check_memory_usage', return_value={"available_gb": 1.0}):
            with pytest.raises(AdapterError, match="Insufficient memory"):
                peft_manager.create_adapter(
                    project_name="test_project",
                    training_data=sample_training_data
                )
    
    def test_create_adapter_custom_config(self, peft_manager, sample_training_data):
        """Test adapter creation with custom configuration."""
        custom_config = {"r": 8, "lora_alpha": 16}
        
        with patch.object(peft_manager, '_check_memory_usage', return_value={"available_gb": 4.0}):
            with patch('src.codebase_gardener.models.peft_manager.threading.Thread'):
                adapter_id = peft_manager.create_adapter(
                    project_name="test_project",
                    training_data=sample_training_data,
                    config_override=custom_config
                )
        
        metadata = peft_manager._adapter_metadata[adapter_id]
        assert metadata.config["r"] == 8
        assert metadata.config["lora_alpha"] == 16
    
    @patch('src.codebase_gardener.models.peft_manager.AutoModelForCausalLM')
    @patch('src.codebase_gardener.models.peft_manager.AutoTokenizer')
    @patch('src.codebase_gardener.models.peft_manager.get_peft_model')
    @patch('src.codebase_gardener.models.peft_manager.Dataset')
    @patch('src.codebase_gardener.models.peft_manager.Trainer')
    @patch('src.codebase_gardener.models.peft_manager.BitsAndBytesConfig')
    @patch('src.codebase_gardener.models.peft_manager.LoraConfig')
    @patch('src.codebase_gardener.models.peft_manager.TrainingArguments')
    @patch('src.codebase_gardener.models.peft_manager.DataCollatorForLanguageModeling')
    def test_train_adapter_success(self, mock_data_collator, mock_training_args, mock_lora_config, 
                                 mock_bits_config, mock_trainer_class, mock_dataset, mock_get_peft_model, 
                                 mock_tokenizer, mock_model, peft_manager, sample_training_data):
        """Test successful adapter training."""
        # Setup mocks
        mock_model_instance = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        mock_peft_model = Mock()
        mock_get_peft_model.return_value = mock_peft_model
        
        mock_dataset_instance = Mock()
        mock_dataset.from_dict.return_value = mock_dataset_instance
        mock_dataset_instance.map.return_value = mock_dataset_instance
        
        # Mock trainer
        mock_trainer = Mock()
        mock_trainer.state.log_history = [{"train_loss": 0.5}]
        mock_trainer.state.global_step = 100
        mock_trainer_class.return_value = mock_trainer
        
        # Create adapter metadata
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = AdapterMetadata(
            name="test_adapter",
            project_name="test_project",
            created_at=datetime.now(),
            model_name="microsoft/DialoGPT-medium",
            config={"r": 16, "lora_alpha": 32},
            training_metrics={},
            file_path=Path("/tmp/test_adapter.bin"),
            size_mb=0.0,
            status="training"
        )
        
        # Mock the save_pretrained method to avoid file operations
        with patch.object(mock_peft_model, 'save_pretrained'):
            # Run training
            peft_manager._train_adapter(
                adapter_id=adapter_id,
                base_model="microsoft/DialoGPT-medium",
                training_data=sample_training_data,
                config={"r": 16, "lora_alpha": 32}
            )
        
        # Verify metadata was updated
        metadata = peft_manager._adapter_metadata[adapter_id]
        assert metadata.status == "ready"
        assert "final_loss" in metadata.training_metrics


class TestAdapterLoading:
    """Test LoRA adapter loading and unloading."""
    
    def test_load_adapter_from_cache(self, peft_manager):
        """Test loading adapter from cache."""
        adapter_id = "test_project_test_adapter"
        mock_model = Mock()
        peft_manager._adapters_cache[adapter_id] = mock_model
        
        result = peft_manager.load_adapter("test_project", "test_adapter")
        assert result == mock_model
    
    def test_load_adapter_not_found(self, peft_manager):
        """Test loading non-existent adapter."""
        with pytest.raises(AdapterError, match="not found"):
            peft_manager.load_adapter("nonexistent_project", "nonexistent_adapter")
    
    def test_load_adapter_not_ready(self, peft_manager, sample_adapter_metadata):
        """Test loading adapter that's not ready."""
        sample_adapter_metadata.status = "training"
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        with pytest.raises(AdapterError, match="not ready"):
            peft_manager.load_adapter("test_project", "test_adapter")
    
    @patch('src.codebase_gardener.models.peft_manager.AutoModelForCausalLM')
    @patch('src.codebase_gardener.models.peft_manager.PeftModel')
    def test_load_adapter_success(self, mock_peft_model, mock_auto_model, 
                                peft_manager, sample_adapter_metadata):
        """Test successful adapter loading."""
        # Setup metadata
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        # Setup mocks
        mock_base_model = Mock()
        mock_auto_model.from_pretrained.return_value = mock_base_model
        
        mock_loaded_model = Mock()
        mock_peft_model.from_pretrained.return_value = mock_loaded_model
        
        with patch.object(peft_manager, '_check_memory_usage', return_value={"available_gb": 4.0}):
            result = peft_manager.load_adapter("test_project", "test_adapter")
        
        assert result == mock_loaded_model
        assert adapter_id in peft_manager._adapters_cache
        
        # Verify model loading calls
        mock_auto_model.from_pretrained.assert_called_once()
        mock_peft_model.from_pretrained.assert_called_once()
    
    def test_unload_adapter_success(self, peft_manager):
        """Test successful adapter unloading."""
        adapter_id = "test_project_test_adapter"
        mock_model = Mock()
        peft_manager._adapters_cache[adapter_id] = mock_model
        
        result = peft_manager.unload_adapter("test_project", "test_adapter")
        
        assert result is True
        assert adapter_id not in peft_manager._adapters_cache
    
    def test_unload_adapter_not_cached(self, peft_manager):
        """Test unloading adapter not in cache."""
        result = peft_manager.unload_adapter("test_project", "test_adapter")
        assert result is False


class TestAdapterManagement:
    """Test adapter management operations."""
    
    def test_list_adapters_empty(self, peft_manager):
        """Test listing adapters when none exist."""
        result = peft_manager.list_adapters()
        assert result == []
    
    def test_list_adapters_with_data(self, peft_manager, sample_adapter_metadata):
        """Test listing adapters with existing data."""
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        result = peft_manager.list_adapters()
        
        assert len(result) == 1
        adapter_info = result[0]
        assert adapter_info["id"] == adapter_id
        assert adapter_info["name"] == sample_adapter_metadata.name
        assert adapter_info["project_name"] == sample_adapter_metadata.project_name
        assert adapter_info["status"] == sample_adapter_metadata.status
    
    def test_list_adapters_filtered_by_project(self, peft_manager):
        """Test listing adapters filtered by project."""
        # Add adapters for different projects
        metadata1 = AdapterMetadata(
            name="adapter1", project_name="project1", created_at=datetime.now(),
            model_name="model", config={}, training_metrics={},
            file_path=Path("/tmp/1"), size_mb=1.0, status="ready"
        )
        metadata2 = AdapterMetadata(
            name="adapter2", project_name="project2", created_at=datetime.now(),
            model_name="model", config={}, training_metrics={},
            file_path=Path("/tmp/2"), size_mb=1.0, status="ready"
        )
        
        peft_manager._adapter_metadata["project1_adapter1"] = metadata1
        peft_manager._adapter_metadata["project2_adapter2"] = metadata2
        
        result = peft_manager.list_adapters(project_name="project1")
        
        assert len(result) == 1
        assert result[0]["project_name"] == "project1"
    
    def test_delete_adapter_success(self, peft_manager, sample_adapter_metadata):
        """Test successful adapter deletion."""
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        # Mock file operations
        with patch('shutil.rmtree') as mock_rmtree:
            with patch.object(Path, 'exists', return_value=True):
                result = peft_manager.delete_adapter("test_project", "test_adapter")
        
        assert result is True
        assert adapter_id not in peft_manager._adapter_metadata
        mock_rmtree.assert_called_once()
    
    def test_delete_adapter_not_found(self, peft_manager):
        """Test deleting non-existent adapter."""
        result = peft_manager.delete_adapter("nonexistent_project", "nonexistent_adapter")
        assert result is False


class TestTrainingProgress:
    """Test training progress tracking."""
    
    def test_get_training_progress_not_training(self, peft_manager):
        """Test getting progress when not training."""
        result = peft_manager.get_training_progress("test_project", "test_adapter")
        assert result is None
    
    def test_is_training_false(self, peft_manager):
        """Test is_training when not training."""
        result = peft_manager.is_training("test_project", "test_adapter")
        assert result is False
    
    def test_is_training_true(self, peft_manager):
        """Test is_training when training is active."""
        adapter_id = "test_project_test_adapter"
        mock_thread = Mock()
        mock_thread.is_alive.return_value = True
        peft_manager._training_threads[adapter_id] = mock_thread
        
        result = peft_manager.is_training("test_project", "test_adapter")
        assert result is True


class TestMemoryManagement:
    """Test memory management functionality."""
    
    @patch('torch.cuda.is_available', return_value=False)
    @patch('psutil.Process')
    def test_check_memory_usage_cpu(self, mock_process, mock_cuda, peft_manager):
        """Test memory usage checking on CPU."""
        mock_process_instance = Mock()
        mock_process_instance.memory_info.return_value.rss = 2048 * 1024 * 1024  # 2GB
        mock_process.return_value = mock_process_instance
        
        result = peft_manager._check_memory_usage()
        
        assert "allocated_gb" in result
        assert "reserved_gb" in result
        assert "available_gb" in result
        assert result["allocated_gb"] == 2.0
    
    @patch('torch.cuda.is_available', return_value=True)
    @patch('torch.cuda.memory_allocated', return_value=1024**3)  # 1GB
    @patch('torch.cuda.memory_reserved', return_value=2*1024**3)  # 2GB
    @patch('torch.cuda.get_device_properties')
    def test_check_memory_usage_cuda(self, mock_props, mock_reserved, 
                                   mock_allocated, mock_cuda, peft_manager):
        """Test memory usage checking on CUDA."""
        mock_props.return_value.total_memory = 8 * 1024**3  # 8GB
        
        result = peft_manager._check_memory_usage()
        
        assert result["allocated_gb"] == 1.0
        assert result["reserved_gb"] == 2.0
        assert result["available_gb"] == 6.0
    
    def test_manage_cache_within_limit(self, peft_manager):
        """Test cache management when within limits."""
        # Add adapters within limit
        for i in range(2):
            peft_manager._adapters_cache[f"adapter_{i}"] = Mock()
        
        initial_count = len(peft_manager._adapters_cache)
        peft_manager._manage_cache()
        
        assert len(peft_manager._adapters_cache) == initial_count
    
    def test_manage_cache_exceeds_limit(self, peft_manager):
        """Test cache management when exceeding limits."""
        # Add more adapters than the limit
        for i in range(5):
            peft_manager._adapters_cache[f"adapter_{i}"] = Mock()
        
        peft_manager._manage_cache()
        
        assert len(peft_manager._adapters_cache) <= peft_manager._max_cache_size
    
    def test_get_memory_usage(self, peft_manager):
        """Test getting memory usage information."""
        # Add some test data
        peft_manager._adapters_cache["test1"] = Mock()
        peft_manager._adapter_metadata["test1"] = Mock()
        
        with patch.object(peft_manager, '_check_memory_usage', 
                         return_value={"allocated_gb": 2.0, "reserved_gb": 2.0, "available_gb": 4.0}):
            result = peft_manager.get_memory_usage()
        
        assert "allocated_gb" in result
        assert "cached_adapters" in result
        assert "total_adapters" in result
        assert result["cached_adapters"] == 1
        assert result["total_adapters"] == 1


class TestContextManager:
    """Test adapter context manager."""
    
    def test_adapter_context_not_cached(self, peft_manager):
        """Test context manager with adapter not in cache."""
        mock_model = Mock()
        
        with patch.object(peft_manager, 'load_adapter', return_value=mock_model) as mock_load:
            with patch.object(peft_manager, 'unload_adapter') as mock_unload:
                with peft_manager.adapter_context("test_project", "test_adapter") as model:
                    assert model == mock_model
                
                mock_load.assert_called_once_with("test_project", "test_adapter")
                mock_unload.assert_called_once_with("test_project", "test_adapter")
    
    def test_adapter_context_already_cached(self, peft_manager):
        """Test context manager with adapter already cached."""
        adapter_id = "test_project_test_adapter"
        mock_model = Mock()
        peft_manager._adapters_cache[adapter_id] = mock_model
        
        with patch.object(peft_manager, 'load_adapter', return_value=mock_model) as mock_load:
            with patch.object(peft_manager, 'unload_adapter') as mock_unload:
                with peft_manager.adapter_context("test_project", "test_adapter") as model:
                    assert model == mock_model
                
                mock_load.assert_called_once_with("test_project", "test_adapter")
                mock_unload.assert_not_called()  # Should not unload if was cached


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_training_error_propagation(self, peft_manager, sample_training_data):
        """Test that training errors are properly propagated."""
        with patch.object(peft_manager, '_check_memory_usage', return_value={"available_gb": 4.0}):
            with patch('src.codebase_gardener.models.peft_manager.AutoModelForCausalLM') as mock_model:
                mock_model.from_pretrained.side_effect = Exception("Model loading failed")
                
                # Create adapter metadata
                adapter_id = "test_project_test_adapter"
                peft_manager._adapter_metadata[adapter_id] = AdapterMetadata(
                    name="test_adapter", project_name="test_project", created_at=datetime.now(),
                    model_name="microsoft/DialoGPT-medium", config={}, training_metrics={},
                    file_path=Path("/tmp/test"), size_mb=0.0, status="training"
                )
                
                with pytest.raises(TrainingError):
                    peft_manager._train_adapter(
                        adapter_id=adapter_id,
                        base_model="microsoft/DialoGPT-medium",
                        training_data=sample_training_data,
                        config={}
                    )
                
                # Verify metadata was updated to error status
                assert peft_manager._adapter_metadata[adapter_id].status == "error"
    
    def test_adapter_loading_error(self, peft_manager, sample_adapter_metadata):
        """Test adapter loading error handling."""
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        with patch('src.codebase_gardener.models.peft_manager.AutoModelForCausalLM') as mock_model:
            mock_model.from_pretrained.side_effect = Exception("Model loading failed")
            
            with pytest.raises(AdapterError, match="Failed to load adapter"):
                peft_manager.load_adapter("test_project", "test_adapter")


class TestUtilityMethods:
    """Test utility methods."""
    
    def test_get_adapter_id(self, peft_manager):
        """Test adapter ID generation."""
        result = peft_manager._get_adapter_id("test_project", "test_adapter")
        assert result == "test_project_test_adapter"
        
        result = peft_manager._get_adapter_id("test_project")
        assert result == "test_project_default"
    
    def test_get_adapter_path(self, peft_manager):
        """Test adapter path generation."""
        result = peft_manager._get_adapter_path("test_adapter")
        expected = peft_manager.adapters_dir / "test_adapter.bin"
        assert result == expected
    
    def test_save_and_load_metadata(self, peft_manager, sample_adapter_metadata):
        """Test metadata persistence."""
        adapter_id = "test_project_test_adapter"
        peft_manager._adapter_metadata[adapter_id] = sample_adapter_metadata
        
        # Save metadata
        peft_manager._save_adapter_metadata()
        
        # Clear and reload
        peft_manager._adapter_metadata.clear()
        peft_manager._load_adapter_metadata()
        
        # Verify data was restored
        assert adapter_id in peft_manager._adapter_metadata
        restored_metadata = peft_manager._adapter_metadata[adapter_id]
        assert restored_metadata.name == sample_adapter_metadata.name
        assert restored_metadata.project_name == sample_adapter_metadata.project_name