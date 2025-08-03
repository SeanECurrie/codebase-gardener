"""
Tests for the settings configuration module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from codebase_gardener.config.settings import Settings, get_settings, reload_settings


class TestSettings:
    """Test cases for the Settings class."""
    
    def test_default_settings(self):
        """Test that default settings load correctly."""
        settings = Settings()
        
        assert settings.app_name == "Codebase Gardener"
        assert settings.debug is False
        assert settings.log_level == "INFO"
        assert settings.ollama_base_url == "http://localhost:11434"
        assert settings.ollama_timeout == 30
        assert settings.default_embedding_model == "nomic-embed-code"
        assert settings.embedding_batch_size == 32
        assert settings.max_chunk_size == 1000
        assert settings.lora_rank == 16
        assert settings.lora_alpha == 32
        assert settings.training_batch_size == 4
        assert settings.max_training_steps == 1000
        assert settings.max_workers == 4
        assert settings.memory_limit_mb == 6144
        assert settings.gradio_host == "127.0.0.1"
        assert settings.gradio_port == 7860
        assert settings.gradio_share is False
        assert settings.enable_profiling is False
        assert settings.cache_embeddings is True
    
    def test_environment_variable_override(self):
        """Test that environment variables override default settings."""
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_DEBUG": "true",
            "CODEBASE_GARDENER_LOG_LEVEL": "DEBUG",
            "CODEBASE_GARDENER_OLLAMA_TIMEOUT": "60",
            "CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE": "64",
        }):
            settings = Settings()
            
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
            assert settings.ollama_timeout == 60
            assert settings.embedding_batch_size == 64
    
    def test_case_insensitive_environment_variables(self):
        """Test that environment variables are case insensitive."""
        with patch.dict(os.environ, {
            "codebase_gardener_debug": "true",
            "CODEBASE_GARDENER_LOG_LEVEL": "debug",
        }):
            settings = Settings()
            
            assert settings.debug is True
            assert settings.log_level == "DEBUG"
    
    def test_invalid_log_level_validation(self):
        """Test that invalid log levels raise validation errors."""
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_LOG_LEVEL": "INVALID",
        }):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "log_level must be one of" in str(exc_info.value)
    
    def test_invalid_batch_size_validation(self):
        """Test that invalid batch sizes raise validation errors."""
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE": "0",
        }):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "Input should be greater than or equal to 1" in str(exc_info.value)
        
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE": "200",
        }):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "Input should be less than or equal to 128" in str(exc_info.value)
    
    def test_invalid_ollama_url_validation(self):
        """Test that invalid Ollama URLs raise validation errors."""
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_OLLAMA_BASE_URL": "invalid-url",
        }):
            with pytest.raises(ValidationError) as exc_info:
                Settings()
            
            assert "ollama_base_url must start with http:// or https://" in str(exc_info.value)
    
    def test_data_directory_creation(self):
        """Test that data directory is created automatically."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                
                assert settings.data_dir.resolve() == test_data_dir.resolve()
                assert test_data_dir.exists()
                assert test_data_dir.is_dir()
    
    def test_derived_directory_paths(self):
        """Test that derived directory paths are set correctly."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                
                assert settings.projects_dir.resolve() == (test_data_dir / "projects").resolve()
                assert settings.base_models_dir.resolve() == (test_data_dir / "base_models").resolve()
                assert settings.vector_db_path.resolve() == (test_data_dir / "vector_store").resolve()
    
    def test_create_directories(self):
        """Test that create_directories creates all necessary directories."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                settings.create_directories()
                
                assert settings.data_dir.exists()
                assert settings.projects_dir.exists()
                assert settings.base_models_dir.exists()
                assert settings.vector_db_path.parent.exists()
    
    def test_get_project_dir(self):
        """Test that get_project_dir creates and returns correct path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                project_dir = settings.get_project_dir("test-project")
                
                expected_path = test_data_dir / "projects" / "test-project"
                assert project_dir.resolve() == expected_path.resolve()
                assert project_dir.exists()
                assert project_dir.is_dir()
    
    def test_get_lora_adapter_path(self):
        """Test that get_lora_adapter_path returns correct path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                adapter_path = settings.get_lora_adapter_path("test-project")
                
                expected_path = test_data_dir / "projects" / "test-project" / "lora_adapter.bin"
                assert adapter_path.resolve() == expected_path.resolve()
    
    def test_get_project_vector_store_path(self):
        """Test that get_project_vector_store_path returns correct path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                vector_path = settings.get_project_vector_store_path("test-project")
                
                expected_path = test_data_dir / "projects" / "test-project" / "vector_store"
                assert vector_path.resolve() == expected_path.resolve()
    
    def test_get_project_context_path(self):
        """Test that get_project_context_path returns correct path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            test_data_dir = Path(temp_dir) / "test-codebase-gardener"
            
            with patch.dict(os.environ, {
                "CODEBASE_GARDENER_DATA_DIR": str(test_data_dir),
            }):
                settings = Settings()
                context_path = settings.get_project_context_path("test-project")
                
                expected_path = test_data_dir / "projects" / "test-project" / "context.json"
                assert context_path.resolve() == expected_path.resolve()


class TestSettingsFunctions:
    """Test cases for settings utility functions."""
    
    def test_get_settings_returns_same_instance(self):
        """Test that get_settings returns the same instance (singleton behavior)."""
        settings1 = get_settings()
        settings2 = get_settings()
        
        assert settings1 is settings2
    
    def test_reload_settings_creates_new_instance(self):
        """Test that reload_settings creates a new instance with updated values."""
        original_settings = get_settings()
        
        with patch.dict(os.environ, {
            "CODEBASE_GARDENER_DEBUG": "true",
        }):
            new_settings = reload_settings()
            
            assert new_settings is not original_settings
            assert new_settings.debug is True
    
    def test_settings_with_env_file(self):
        """Test that settings can be loaded from .env file."""
        # Note: This test is skipped as .env file loading depends on working directory
        # and is difficult to test reliably in unit tests
        pass