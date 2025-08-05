"""
Tests for Dynamic Model Loader System

This module tests the dynamic loading and unloading of LoRA adapters
with memory management and caching functionality.
"""

import pytest
import threading
import time
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

from src.codebase_gardener.core.dynamic_model_loader import (
    DynamicModelLoader,
    LoaderStatus,
    AdapterInfo,
    LoaderMetrics,
    DynamicModelLoaderError,
    get_dynamic_model_loader,
    cleanup_global_loader
)
from src.codebase_gardener.config.settings import Settings
from src.codebase_gardener.core.project_registry import ProjectMetadata, TrainingStatus


@pytest.fixture
def mock_settings():
    """Create mock settings for testing."""
    settings = Mock(spec=Settings)
    settings.data_dir = Path("/tmp/test_data")
    settings.ollama_base_url = "http://localhost:11434"
    settings.ollama_timeout = 30
    return settings


@pytest.fixture
def mock_project_metadata():
    """Create mock project metadata."""
    project = Mock(spec=ProjectMetadata)
    project.project_id = "test-project-123"
    project.name = "Test Project"
    project.source_path = Path("/tmp/test_source")
    
    # Create a mock path object with exists method
    mock_path = Mock(spec=Path)
    mock_path.exists.return_value = True
    project.lora_adapter_path = mock_path
    
    project.training_status = TrainingStatus.COMPLETED
    return project


@pytest.fixture
def mock_ollama_client():
    """Create mock Ollama client."""
    client = Mock()
    client.health_check.return_value = True
    client.list_models.return_value = [{"name": "test-model"}]
    return client


@pytest.fixture
def mock_peft_manager():
    """Create mock PEFT manager."""
    manager = Mock()
    manager.load_adapter.return_value = Mock()
    manager.unload_adapter.return_value = True
    return manager


@pytest.fixture
def mock_project_registry():
    """Create mock project registry."""
    registry = Mock()
    return registry


@pytest.fixture
def loader(mock_settings, mock_ollama_client, mock_peft_manager, mock_project_registry):
    """Create dynamic model loader instance for testing."""
    return DynamicModelLoader(
        settings=mock_settings,
        ollama_client=mock_ollama_client,
        peft_manager=mock_peft_manager,
        project_registry=mock_project_registry
    )


class TestAdapterInfo:
    """Test AdapterInfo data class."""
    
    def test_adapter_info_creation(self):
        """Test creating AdapterInfo instance."""
        now = datetime.now()
        info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=now,
            last_accessed=now,
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        
        assert info.project_id == "test-project"
        assert info.adapter_name == "default"
        assert info.memory_usage_mb == 50.0
        assert info.base_model_name == "test-model"
    
    def test_update_access_time(self):
        """Test updating access time."""
        now = datetime.now()
        info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=now,
            last_accessed=now,
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        
        original_time = info.last_accessed
        time.sleep(0.01)  # Small delay
        info.update_access_time()
        
        assert info.last_accessed > original_time


class TestDynamicModelLoader:
    """Test DynamicModelLoader class."""
    
    def test_initialization(self, loader):
        """Test loader initialization."""
        assert loader.get_status() == LoaderStatus.IDLE
        assert loader.get_current_adapter() is None
        assert len(loader.get_loaded_adapters()) == 0
    
    def test_get_adapter_id(self, loader):
        """Test adapter ID generation."""
        adapter_id = loader._get_adapter_id("project-123", "custom")
        assert adapter_id == "project-123_custom"
        
        default_id = loader._get_adapter_id("project-456")
        assert default_id == "project-456_default"
    
    def test_memory_calculation(self, loader):
        """Test memory usage calculation."""
        # Initially no memory usage
        assert loader._calculate_memory_usage() == 0.0
        
        # Add mock adapter to cache
        adapter_info = AdapterInfo(
            project_id="test",
            adapter_name="default",
            model=Mock(),
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=100.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test_default"] = adapter_info
        
        # Should include adapter memory
        assert loader._calculate_memory_usage() == 100.0
    
    def test_memory_availability_check(self, loader):
        """Test memory availability checking."""
        # Should have plenty of memory initially
        assert loader._check_memory_availability(100.0) is True
        
        # Should fail if requesting more than limit
        assert loader._check_memory_availability(5000.0) is False
    
    @patch('src.codebase_gardener.core.dynamic_model_loader.PeftConfig')
    def test_adapter_compatibility_verification(self, mock_peft_config, loader):
        """Test adapter compatibility verification."""
        # Mock successful compatibility check
        mock_config = Mock()
        mock_config.base_model_name_or_path = "test-model"
        mock_peft_config.from_pretrained.return_value = mock_config
        
        result = loader._verify_adapter_compatibility(
            Path("/tmp/adapter"),
            "test-model"
        )
        assert result is True
        
        # Mock compatibility failure
        mock_config.base_model_name_or_path = "different-model"
        result = loader._verify_adapter_compatibility(
            Path("/tmp/adapter"),
            "test-model"
        )
        assert result is False
    
    def test_cache_management(self, loader):
        """Test LRU cache management."""
        # Set small cache size for testing
        loader._max_cache_size = 2
        
        # Add adapters to cache
        for i in range(3):
            adapter_info = AdapterInfo(
                project_id=f"project-{i}",
                adapter_name="default",
                model=Mock(),
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=50.0,
                base_model_name="test-model"
            )
            loader._adapter_cache[f"project-{i}_default"] = adapter_info
        
        # Trigger cache management
        loader._manage_cache()
        
        # Should only have max_cache_size adapters
        assert len(loader._adapter_cache) == loader._max_cache_size
        
        # First adapter should be evicted (LRU)
        assert "project-0_default" not in loader._adapter_cache
    
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoModelForCausalLM')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoTokenizer')
    def test_base_model_loading(self, mock_tokenizer, mock_model, loader):
        """Test base model loading."""
        mock_model_instance = Mock()
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        
        loader._load_base_model("test-model")
        
        assert loader._base_model == mock_model_instance
        assert loader._base_tokenizer == mock_tokenizer_instance
        assert loader._current_base_model_name == "test-model"
        assert mock_tokenizer_instance.pad_token == "<eos>"
    
    @patch('src.codebase_gardener.core.dynamic_model_loader.PeftModel')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoModelForCausalLM')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoTokenizer')
    def test_load_adapter_success(self, mock_tokenizer, mock_model, mock_peft, loader, mock_project_metadata):
        """Test successful adapter loading."""
        # Setup mocks
        loader.project_registry.get_project.return_value = mock_project_metadata
        mock_project_metadata.lora_adapter_path.exists.return_value = True
        
        mock_model_instance = Mock()
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_peft_instance = Mock()
        
        mock_model.from_pretrained.return_value = mock_model_instance
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_peft.from_pretrained.return_value = mock_peft_instance
        
        # Mock compatibility check
        with patch.object(loader, '_verify_adapter_compatibility', return_value=True):
            result = loader.load_adapter("test-project-123")
        
        assert result is True
        assert loader.get_current_adapter() == "test-project-123_default"
        assert len(loader.get_loaded_adapters()) == 1
    
    def test_load_adapter_project_not_found(self, loader):
        """Test adapter loading with non-existent project."""
        loader.project_registry.get_project.return_value = None
        
        with pytest.raises(DynamicModelLoaderError, match="Project not found"):
            loader.load_adapter("non-existent-project")
    
    def test_load_adapter_from_cache(self, loader):
        """Test loading adapter from cache."""
        # Add adapter to cache
        adapter_info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test-project_default"] = adapter_info
        
        result = loader.load_adapter("test-project")
        
        assert result is True
        assert loader.get_current_adapter() == "test-project_default"
        assert loader._metrics.cache_hits == 1
    
    def test_unload_adapter_success(self, loader):
        """Test successful adapter unloading."""
        # Add adapter to cache
        adapter_info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test-project_default"] = adapter_info
        loader._current_adapter = "test-project_default"
        
        result = loader.unload_adapter("test-project")
        
        assert result is True
        assert loader.get_current_adapter() is None
        assert len(loader.get_loaded_adapters()) == 0
    
    def test_unload_adapter_not_found(self, loader):
        """Test unloading non-existent adapter."""
        result = loader.unload_adapter("non-existent-project")
        assert result is False
    
    @patch('src.codebase_gardener.core.dynamic_model_loader.PeftModel')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoModelForCausalLM')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoTokenizer')
    def test_switch_project_success(self, mock_tokenizer, mock_model, mock_peft, loader, mock_project_metadata):
        """Test successful project switching."""
        # Setup mocks
        loader.project_registry.get_project.return_value = mock_project_metadata
        mock_project_metadata.lora_adapter_path.exists.return_value = True
        
        mock_model.from_pretrained.return_value = Mock()
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_peft.from_pretrained.return_value = Mock()
        
        with patch.object(loader, '_verify_adapter_compatibility', return_value=True):
            result = loader.switch_project("test-project-123")
        
        assert result is True
        assert loader.get_current_adapter() == "test-project-123_default"
    
    def test_get_loaded_adapters(self, loader):
        """Test getting loaded adapters information."""
        # Add adapters to cache
        for i in range(2):
            adapter_info = AdapterInfo(
                project_id=f"project-{i}",
                adapter_name="default",
                model=Mock(),
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=50.0,
                base_model_name="test-model"
            )
            loader._adapter_cache[f"project-{i}_default"] = adapter_info
        
        loader._current_adapter = "project-0_default"
        
        adapters = loader.get_loaded_adapters()
        
        assert len(adapters) == 2
        assert adapters[0]["is_current"] or adapters[1]["is_current"]
        assert all("adapter_id" in adapter for adapter in adapters)
        assert all("memory_usage_mb" in adapter for adapter in adapters)
    
    def test_clear_cache(self, loader):
        """Test clearing adapter cache."""
        # Add adapters to cache
        for i in range(2):
            adapter_info = AdapterInfo(
                project_id=f"project-{i}",
                adapter_name="default",
                model=Mock(),
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=50.0,
                base_model_name="test-model"
            )
            loader._adapter_cache[f"project-{i}_default"] = adapter_info
        
        loader._current_adapter = "project-0_default"
        
        loader.clear_cache()
        
        assert len(loader._adapter_cache) == 0
        assert loader.get_current_adapter() is None
    
    def test_adapter_context_manager(self, loader):
        """Test adapter context manager."""
        # Add adapter to cache
        mock_model = Mock()
        adapter_info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=mock_model,
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test-project_default"] = adapter_info
        
        with loader.adapter_context("test-project") as model:
            assert model == mock_model
    
    def test_health_check(self, loader):
        """Test health check functionality."""
        health = loader.health_check()
        
        assert "status" in health
        assert "loader_status" in health
        assert "memory_usage_mb" in health
        assert "cached_adapters" in health
        assert "metrics" in health
        
        assert health["status"] in ["healthy", "error"]
        assert health["cached_adapters"] == 0
    
    def test_cleanup(self, loader):
        """Test loader cleanup."""
        # Add some state
        adapter_info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test-project_default"] = adapter_info
        loader._current_adapter = "test-project_default"
        
        loader.cleanup()
        
        assert len(loader._adapter_cache) == 0
        assert loader.get_current_adapter() is None
    
    def test_metrics_tracking(self, loader):
        """Test metrics tracking."""
        initial_metrics = loader.get_metrics()
        
        assert initial_metrics.total_adapters_loaded == 0
        assert initial_metrics.cache_hits == 0
        assert initial_metrics.cache_misses == 0
        
        # Simulate cache hit
        adapter_info = AdapterInfo(
            project_id="test-project",
            adapter_name="default",
            model=Mock(),
            loaded_at=datetime.now(),
            last_accessed=datetime.now(),
            memory_usage_mb=50.0,
            base_model_name="test-model"
        )
        loader._adapter_cache["test-project_default"] = adapter_info
        loader._metrics.cache_hits += 1
        
        updated_metrics = loader.get_metrics()
        assert updated_metrics.cache_hits == 1
    
    def test_concurrent_access(self, loader):
        """Test thread safety with concurrent access."""
        results = []
        
        def load_adapter_worker(project_id):
            try:
                # Mock project registry for this test
                mock_project = Mock()
                mock_project.lora_adapter_path = Path("/tmp/test")
                mock_project.lora_adapter_path.exists.return_value = False
                loader.project_registry.get_project.return_value = mock_project
                
                result = loader.load_adapter(project_id)
                results.append(result)
            except Exception as e:
                results.append(str(e))
        
        # Start multiple threads
        threads = []
        for i in range(3):
            thread = threading.Thread(target=load_adapter_worker, args=[f"project-{i}"])
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Should have results from all threads
        assert len(results) == 3


class TestGlobalLoaderManagement:
    """Test global loader instance management."""
    
    def test_get_global_loader(self, mock_settings):
        """Test getting global loader instance."""
        # Clean up any existing instance
        cleanup_global_loader()
        
        loader1 = get_dynamic_model_loader(mock_settings)
        loader2 = get_dynamic_model_loader(mock_settings)
        
        # Should return same instance
        assert loader1 is loader2
        
        cleanup_global_loader()
    
    def test_cleanup_global_loader(self, mock_settings):
        """Test cleaning up global loader."""
        loader = get_dynamic_model_loader(mock_settings)
        assert loader is not None
        
        cleanup_global_loader()
        
        # Should create new instance after cleanup
        new_loader = get_dynamic_model_loader(mock_settings)
        assert new_loader is not loader


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_loader_status_error_handling(self, loader):
        """Test loader status during error conditions."""
        # Mock an error during loading
        loader.project_registry.get_project.side_effect = Exception("Test error")
        
        with pytest.raises(DynamicModelLoaderError):
            loader.load_adapter("test-project")
        
        # Status should be error after failed loading
        assert loader.get_status() == LoaderStatus.ERROR
    
    def test_memory_limit_exceeded(self, loader):
        """Test behavior when memory limit is exceeded."""
        # Set very low memory limit
        loader._memory_limit_mb = 100
        
        # Fill cache with high memory usage adapters
        for i in range(2):
            adapter_info = AdapterInfo(
                project_id=f"project-{i}",
                adapter_name="default",
                model=Mock(),
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=60.0,  # High memory usage
                base_model_name="test-model"
            )
            loader._adapter_cache[f"project-{i}_default"] = adapter_info
        
        # Should not have enough memory for new adapter
        assert not loader._check_memory_availability(50.0)
    
    def test_adapter_compatibility_failure(self, loader, mock_project_metadata):
        """Test handling of adapter compatibility failures."""
        loader.project_registry.get_project.return_value = mock_project_metadata
        
        with patch.object(loader, '_verify_adapter_compatibility', return_value=False):
            # Should still attempt to load despite compatibility warning
            with patch('src.codebase_gardener.core.dynamic_model_loader.AutoModelForCausalLM'):
                with patch('src.codebase_gardener.core.dynamic_model_loader.AutoTokenizer'):
                    with patch('src.codebase_gardener.core.dynamic_model_loader.PeftModel'):
                        result = loader.load_adapter("test-project-123")
                        assert result is True


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    @patch('src.codebase_gardener.core.dynamic_model_loader.PeftModel')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoModelForCausalLM')
    @patch('src.codebase_gardener.core.dynamic_model_loader.AutoTokenizer')
    def test_full_project_switching_workflow(self, mock_tokenizer, mock_model, mock_peft, loader):
        """Test complete project switching workflow."""
        # Increase memory limit for this test
        loader._memory_limit_mb = 8192  # 8GB for testing
        
        # Setup multiple projects
        projects = []
        for i in range(3):
            project = Mock()
            project.project_id = f"project-{i}"
            
            # Create mock path with exists method
            mock_path = Mock(spec=Path)
            mock_path.exists.return_value = True
            project.lora_adapter_path = mock_path
            
            projects.append(project)
        
        def get_project_side_effect(project_id):
            for project in projects:
                if project.project_id == project_id:
                    return project
            return None
        
        loader.project_registry.get_project.side_effect = get_project_side_effect
        
        # Mock model loading
        mock_model.from_pretrained.return_value = Mock()
        mock_tokenizer_instance = Mock()
        mock_tokenizer_instance.pad_token = None
        mock_tokenizer_instance.eos_token = "<eos>"
        mock_tokenizer.from_pretrained.return_value = mock_tokenizer_instance
        mock_peft.from_pretrained.return_value = Mock()
        
        with patch.object(loader, '_verify_adapter_compatibility', return_value=True):
            # Switch between projects
            for i in range(3):
                result = loader.switch_project(f"project-{i}")
                assert result is True
                assert loader.get_current_adapter() == f"project-{i}_default"
            
            # Verify cache management
            loaded_adapters = loader.get_loaded_adapters()
            assert len(loaded_adapters) <= loader._max_cache_size
    
    def test_memory_pressure_scenario(self, loader):
        """Test behavior under memory pressure."""
        # Set small cache size and memory limit
        loader._max_cache_size = 2
        loader._memory_limit_mb = 200
        
        # Add adapters that consume memory
        for i in range(4):
            adapter_info = AdapterInfo(
                project_id=f"project-{i}",
                adapter_name="default",
                model=Mock(),
                loaded_at=datetime.now(),
                last_accessed=datetime.now(),
                memory_usage_mb=60.0,
                base_model_name="test-model"
            )
            loader._adapter_cache[f"project-{i}_default"] = adapter_info
        
        # Trigger cache management
        loader._manage_cache()
        
        # Should respect cache size limit
        assert len(loader._adapter_cache) == loader._max_cache_size
        
        # Memory usage should be within reasonable bounds
        memory_usage = loader._calculate_memory_usage()
        assert memory_usage <= loader._memory_limit_mb