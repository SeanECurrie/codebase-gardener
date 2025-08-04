"""
Tests for the PEFT Manager module.

This module tests the HuggingFace PEFT manager functionality including
LoRA adapter creation, training, management, and error handling.
"""

import json
import pytest
import tempfile
import shutil
from pathlib import Path
from datetime import datetime
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List

from codebase_gardener.models.peft_manager import (
    PEFTManager,
    AdapterInfo,
    TrainingResult,
    TrainingConfig,
    PEFTError,
    PEFTTrainingError,
    AdapterNotFoundError,
    ResourceError,
)
from codebase_gardener.config.settings import Settings


@pytest.fixture
def temp_settings():
    """Create temporary settings for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        settings = Settings()
        settings.data_dir = Path(temp_dir)
        settings.default_base_model = "microsoft/DialoGPT-small"
        yield settings


@pytest.fixture
def peft_manager(temp_settings):
    """Create PEFT manager instance for testing."""
    return PEFTManager(temp_settings)


@pytest.fixture
def sample_training_data():
    """Sample training data for testing."""
    return [
        {
            "input": "def hello_world():",
            "output": "This function prints 'Hello, World!' to the console."
        },
        {
            "input": "class Calculator:",
            "output": "This is a calculator class for basic arithmetic operations."
        },
        {
            "input": "import numpy as np",
            "output": "This imports the NumPy library for numerical computations."
        },
    ]


@pytest.fixture
def sample_adapter_metadata():
    """Sample adapter metadata for testing."""
    return {
        "adapter_id": "test_project_20250203_120000",
        "project_id": "test_project",
        "created_at": "2025-02-03T12:00:00",
        "model_name": "microsoft/DialoGPT-small",
        "config": {
            "rank": 8,
            "alpha": 16,
            "target_modules": ["q_proj", "v_proj"],
            "dropout": 0.1,
        },
        "status": "completed",
        "last_trained": "2025-02-03T12:30:00",
        "training_steps": 100,
        "final_loss": 0.5,
    }


class TestPEFTManager:
    """Test cases for PEFTManager class."""
    
    def test_init(self, temp_settings):
        """Test PEFT manager initialization."""
        manager = PEFTManager(temp_settings)
        
        assert manager.settings == temp_settings
        assert manager.adapters_dir == temp_settings.data_dir / "adapters"
        assert manager.adapters_dir.exists()
        assert manager._current_training is None
        assert manager._training_cancelled is False
    
    def test_training_config_defaults(self):
        """Test TrainingConfig default values."""
        config = TrainingConfig()
        
        assert config.rank == 8
        assert config.alpha == 16
        assert config.target_modules == ["q_proj", "v_proj"]
        assert config.dropout == 0.1
        assert config.batch_size == 1
        assert config.learning_rate == 2e-4
        assert config.num_epochs == 3
        assert config.max_steps == 500
        assert config.gradient_checkpointing is True
        assert config.warmup_steps == 50
    
    def test_training_config_custom(self):
        """Test TrainingConfig with custom values."""
        config = TrainingConfig(
            rank=16,
            alpha=32,
            target_modules=["q_proj", "k_proj", "v_proj"],
            dropout=0.05,
            batch_size=2,
        )
        
        assert config.rank == 16
        assert config.alpha == 32
        assert config.target_modules == ["q_proj", "k_proj", "v_proj"]
        assert config.dropout == 0.05
        assert config.batch_size == 2
    
    def test_list_adapters_empty(self, peft_manager):
        """Test listing adapters when none exist."""
        adapters = peft_manager.list_adapters()
        assert adapters == []
    
    def test_list_adapters_with_data(self, peft_manager, sample_adapter_metadata):
        """Test listing adapters with existing data."""
        # Create a mock adapter directory with metadata
        adapter_id = sample_adapter_metadata["adapter_id"]
        adapter_dir = peft_manager.adapters_dir / adapter_id
        adapter_dir.mkdir(parents=True)
        
        # Write metadata file
        with open(adapter_dir / "metadata.json", "w") as f:
            json.dump(sample_adapter_metadata, f)
        
        # Create some dummy files to test size calculation
        (adapter_dir / "adapter_model.bin").write_text("dummy model data")
        (adapter_dir / "adapter_config.json").write_text('{"test": "config"}')
        
        adapters = peft_manager.list_adapters()
        
        assert len(adapters) == 1
        adapter = adapters[0]
        assert adapter.adapter_id == adapter_id
        assert adapter.project_id == "test_project"
        assert adapter.model_name == "microsoft/DialoGPT-small"
        assert adapter.rank == 8
        assert adapter.alpha == 16
        assert adapter.target_modules == ["q_proj", "v_proj"]
        assert adapter.training_steps == 100
        assert adapter.status == "completed"
        assert adapter.file_size_mb > 0
    
    def test_get_adapter_info_success(self, peft_manager, sample_adapter_metadata):
        """Test getting adapter info for existing adapter."""
        # Create mock adapter
        adapter_id = sample_adapter_metadata["adapter_id"]
        adapter_dir = peft_manager.adapters_dir / adapter_id
        adapter_dir.mkdir(parents=True)
        
        with open(adapter_dir / "metadata.json", "w") as f:
            json.dump(sample_adapter_metadata, f)
        
        (adapter_dir / "adapter_model.bin").write_text("dummy model data")
        
        adapter_info = peft_manager.get_adapter_info(adapter_id)
        
        assert adapter_info.adapter_id == adapter_id
        assert adapter_info.project_id == "test_project"
        assert adapter_info.status == "completed"
    
    def test_get_adapter_info_not_found(self, peft_manager):
        """Test getting adapter info for non-existent adapter."""
        with pytest.raises(AdapterNotFoundError):
            peft_manager.get_adapter_info("non_existent_adapter")
    
    def test_delete_adapter_success(self, peft_manager, sample_adapter_metadata):
        """Test successful adapter deletion."""
        # Create mock adapter
        adapter_id = sample_adapter_metadata["adapter_id"]
        adapter_dir = peft_manager.adapters_dir / adapter_id
        adapter_dir.mkdir(parents=True)
        
        with open(adapter_dir / "metadata.json", "w") as f:
            json.dump(sample_adapter_metadata, f)
        
        assert adapter_dir.exists()
        
        result = peft_manager.delete_adapter(adapter_id)
        
        assert result is True
        assert not adapter_dir.exists()
    
    def test_delete_adapter_not_found(self, peft_manager):
        """Test deleting non-existent adapter."""
        result = peft_manager.delete_adapter("non_existent_adapter")
        assert result is False
    
    def test_cancel_training_no_training(self, peft_manager):
        """Test canceling training when none is running."""
        result = peft_manager.cancel_training()
        assert result is False
    
    def test_cancel_training_with_training(self, peft_manager):
        """Test canceling training when training is running."""
        peft_manager._current_training = "test_adapter"
        
        result = peft_manager.cancel_training()
        
        assert result is True
        assert peft_manager._training_cancelled is True
    
    def test_get_training_status_none(self, peft_manager):
        """Test getting training status when none is running."""
        status = peft_manager.get_training_status()
        assert status is None
    
    def test_get_training_status_active(self, peft_manager):
        """Test getting training status when training is active."""
        peft_manager._current_training = "test_adapter"
        
        status = peft_manager.get_training_status()
        assert status == "test_adapter"
    
    def test_default_base_model_property(self, peft_manager):
        """Test default base model property."""
        model = peft_manager.default_base_model
        assert model == "microsoft/DialoGPT-small"
    
    @patch('codebase_gardener.models.peft_manager.AutoTokenizer')
    @patch('codebase_gardener.models.peft_manager.AutoModelForCausalLM')
    @patch('codebase_gardener.models.peft_manager.get_peft_model')
    @patch('codebase_gardener.models.peft_manager.torch')
    def test_prepare_training_dataset(
        self, mock_torch, mock_get_peft_model, mock_model, mock_tokenizer, 
        peft_manager, sample_training_data
    ):
        """Test training dataset preparation."""
        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.return_value = {
            'input_ids': [1, 2, 3],
            'attention_mask': [1, 1, 1]
        }
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Test dataset preparation
        dataset = peft_manager._prepare_training_dataset(
            sample_training_data, mock_tokenizer_instance
        )
        
        assert dataset is not None
        # The actual dataset testing would require more complex mocking
        # of the HuggingFace datasets library
    
    def test_get_peak_memory_usage_cuda_available(self, peft_manager):
        """Test peak memory usage calculation when CUDA is available."""
        with patch('torch.cuda.is_available', return_value=True):
            with patch('torch.cuda.max_memory_allocated', return_value=1024 * 1024 * 100):  # 100MB
                memory = peft_manager._get_peak_memory_usage()
                assert memory == 100.0
    
    def test_get_peak_memory_usage_cuda_not_available(self, peft_manager):
        """Test peak memory usage calculation when CUDA is not available."""
        with patch('torch.cuda.is_available', return_value=False):
            memory = peft_manager._get_peak_memory_usage()
            assert memory == 0.0


class TestPEFTManagerIntegration:
    """Integration tests for PEFT manager with mocked dependencies."""
    
    @patch('codebase_gardener.models.peft_manager.AutoTokenizer')
    @patch('codebase_gardener.models.peft_manager.AutoModelForCausalLM')
    @patch('codebase_gardener.models.peft_manager.get_peft_model')
    @patch('codebase_gardener.models.peft_manager.torch')
    def test_create_adapter_success(
        self, mock_torch, mock_get_peft_model, mock_model, mock_tokenizer,
        peft_manager, sample_training_data
    ):
        """Test successful adapter creation with mocked training."""
        # Mock CUDA availability
        mock_torch.cuda.is_available.return_value = False
        mock_torch.cuda.empty_cache = Mock()
        
        # Mock tokenizer
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer_instance.return_value = {
            'input_ids': [1, 2, 3],
            'attention_mask': [1, 1, 1]
        }
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        # Mock model
        mock_model_instance = Mock()
        mock_model_instance.print_trainable_parameters = Mock()
        mock_model_instance.save_pretrained = Mock()
        mock_model.from_pretrained.return_value = mock_model_instance
        
        # Mock PEFT model
        mock_peft_model = Mock()
        mock_peft_model.print_trainable_parameters = Mock()
        mock_peft_model.save_pretrained = Mock()
        mock_get_peft_model.return_value = mock_peft_model
        
        # Mock trainer and training result
        with patch.object(peft_manager, '_create_trainer') as mock_create_trainer:
            mock_trainer = Mock()
            mock_train_result = Mock()
            mock_train_result.global_step = 100
            mock_train_result.training_loss = 0.5
            mock_trainer.train.return_value = mock_train_result
            mock_create_trainer.return_value = mock_trainer
            
            # Mock dataset preparation
            with patch.object(peft_manager, '_prepare_training_dataset') as mock_prepare:
                mock_dataset = Mock()
                mock_prepare.return_value = mock_dataset
                
                # Create adapter
                adapter_id = peft_manager.create_adapter(
                    project_id="test_project",
                    training_data=sample_training_data,
                )
                
                # Verify adapter was created
                assert adapter_id.startswith("test_project_")
                
                # Check metadata file was created
                adapter_dir = peft_manager.adapters_dir / adapter_id
                metadata_file = adapter_dir / "metadata.json"
                assert metadata_file.exists()
                
                with open(metadata_file) as f:
                    metadata = json.load(f)
                
                assert metadata["adapter_id"] == adapter_id
                assert metadata["project_id"] == "test_project"
                assert metadata["status"] == "completed"
                assert metadata["training_steps"] == 100
                assert metadata["final_loss"] == 0.5
    
    @patch('codebase_gardener.models.peft_manager.AutoTokenizer')
    @patch('codebase_gardener.models.peft_manager.AutoModelForCausalLM')
    def test_create_adapter_training_failure(
        self, mock_model, mock_tokenizer, peft_manager, sample_training_data
    ):
        """Test adapter creation with training failure."""
        # Mock tokenizer to raise an exception
        mock_tokenizer.from_pretrained.side_effect = Exception("Model loading failed")
        
        with pytest.raises(PEFTTrainingError):
            peft_manager.create_adapter(
                project_id="test_project",
                training_data=sample_training_data,
            )
        
        # Verify no adapter directory was left behind
        adapter_dirs = list(peft_manager.adapters_dir.glob("test_project_*"))
        assert len(adapter_dirs) == 0
    
    @pytest.mark.asyncio
    async def test_create_adapter_async(self, peft_manager, sample_training_data):
        """Test asynchronous adapter creation."""
        with patch.object(peft_manager, 'create_adapter') as mock_create:
            mock_create.return_value = "test_adapter_id"
            
            adapter_id = await peft_manager.create_adapter_async(
                project_id="test_project",
                training_data=sample_training_data,
            )
            
            assert adapter_id == "test_adapter_id"
            mock_create.assert_called_once()


class TestPEFTManagerErrorHandling:
    """Test error handling in PEFT manager."""
    
    def test_adapter_info_corrupted_metadata(self, peft_manager):
        """Test handling of corrupted metadata file."""
        adapter_id = "corrupted_adapter"
        adapter_dir = peft_manager.adapters_dir / adapter_id
        adapter_dir.mkdir(parents=True)
        
        # Write invalid JSON
        with open(adapter_dir / "metadata.json", "w") as f:
            f.write("invalid json content")
        
        with pytest.raises(PEFTError):
            peft_manager.get_adapter_info(adapter_id)
    
    def test_list_adapters_with_corrupted_metadata(self, peft_manager, sample_adapter_metadata):
        """Test listing adapters with some corrupted metadata."""
        # Create valid adapter
        valid_adapter_id = "valid_adapter"
        valid_adapter_dir = peft_manager.adapters_dir / valid_adapter_id
        valid_adapter_dir.mkdir(parents=True)
        
        valid_metadata = sample_adapter_metadata.copy()
        valid_metadata["adapter_id"] = valid_adapter_id
        
        with open(valid_adapter_dir / "metadata.json", "w") as f:
            json.dump(valid_metadata, f)
        
        # Create corrupted adapter
        corrupted_adapter_id = "corrupted_adapter"
        corrupted_adapter_dir = peft_manager.adapters_dir / corrupted_adapter_id
        corrupted_adapter_dir.mkdir(parents=True)
        
        with open(corrupted_adapter_dir / "metadata.json", "w") as f:
            f.write("invalid json")
        
        # List adapters should return only valid ones
        adapters = peft_manager.list_adapters()
        
        assert len(adapters) == 1
        assert adapters[0].adapter_id == valid_adapter_id
    
    def test_delete_adapter_permission_error(self, peft_manager, sample_adapter_metadata):
        """Test adapter deletion with permission error."""
        adapter_id = sample_adapter_metadata["adapter_id"]
        adapter_dir = peft_manager.adapters_dir / adapter_id
        adapter_dir.mkdir(parents=True)
        
        with open(adapter_dir / "metadata.json", "w") as f:
            json.dump(sample_adapter_metadata, f)
        
        # Mock shutil.rmtree to raise PermissionError
        with patch('shutil.rmtree', side_effect=PermissionError("Access denied")):
            result = peft_manager.delete_adapter(adapter_id)
            assert result is False


class TestTrainingResult:
    """Test TrainingResult dataclass."""
    
    def test_training_result_success(self):
        """Test successful training result."""
        result = TrainingResult(
            adapter_id="test_adapter",
            success=True,
            training_steps=100,
            final_loss=0.5,
            training_time_seconds=300.0,
            memory_peak_mb=1024.0,
        )
        
        assert result.adapter_id == "test_adapter"
        assert result.success is True
        assert result.training_steps == 100
        assert result.final_loss == 0.5
        assert result.training_time_seconds == 300.0
        assert result.memory_peak_mb == 1024.0
        assert result.error_message is None
    
    def test_training_result_failure(self):
        """Test failed training result."""
        result = TrainingResult(
            adapter_id="test_adapter",
            success=False,
            training_steps=0,
            final_loss=None,
            training_time_seconds=60.0,
            memory_peak_mb=512.0,
            error_message="Training failed due to insufficient memory",
        )
        
        assert result.adapter_id == "test_adapter"
        assert result.success is False
        assert result.training_steps == 0
        assert result.final_loss is None
        assert result.error_message == "Training failed due to insufficient memory"


class TestAdapterInfo:
    """Test AdapterInfo dataclass."""
    
    def test_adapter_info_creation(self):
        """Test AdapterInfo creation."""
        created_at = datetime.now()
        last_trained = datetime.now()
        
        info = AdapterInfo(
            adapter_id="test_adapter",
            project_id="test_project",
            created_at=created_at,
            last_trained=last_trained,
            model_name="microsoft/DialoGPT-small",
            rank=8,
            alpha=16,
            target_modules=["q_proj", "v_proj"],
            training_steps=100,
            file_size_mb=10.5,
            status="completed",
        )
        
        assert info.adapter_id == "test_adapter"
        assert info.project_id == "test_project"
        assert info.created_at == created_at
        assert info.last_trained == last_trained
        assert info.model_name == "microsoft/DialoGPT-small"
        assert info.rank == 8
        assert info.alpha == 16
        assert info.target_modules == ["q_proj", "v_proj"]
        assert info.training_steps == 100
        assert info.file_size_mb == 10.5
        assert info.status == "completed"


if __name__ == "__main__":
    pytest.main([__file__])