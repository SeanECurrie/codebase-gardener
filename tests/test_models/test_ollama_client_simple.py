"""
Simplified tests for the Ollama client integration.

This module tests the core OllamaClient functionality without retry complications.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime
import ollama

from codebase_gardener.models.ollama_client import (
    OllamaClient,
    get_ollama_client,
    ensure_model_available
)
from codebase_gardener.config.settings import Settings
from codebase_gardener.utils.error_handling import (
    ModelError,
    ModelLoadingError,
    ModelInferenceError,
    NetworkError
)


class TestOllamaClientCore:
    """Test core OllamaClient functionality."""
    
    @pytest.fixture
    def mock_settings(self):
        """Mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.ollama_base_url = "http://localhost:11434"
        settings.ollama_timeout = 30
        return settings
    
    @pytest.fixture
    def ollama_client(self, mock_settings):
        """Create OllamaClient instance for testing."""
        return OllamaClient(mock_settings)
    
    def test_client_initialization(self, mock_settings):
        """Test OllamaClient initialization."""
        client = OllamaClient(mock_settings)
        
        assert client.settings == mock_settings
        assert client._client is None
        assert client._async_client is None
        assert client._last_health_check is None
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_client_property_creation(self, mock_client_class, ollama_client):
        """Test that client property creates Client instance."""
        # Access client property
        client = ollama_client.client
        
        # Verify Client was created with correct parameters
        mock_client_class.assert_called_once_with(
            host="http://localhost:11434",
            timeout=30
        )
        
        # Verify same instance is returned on subsequent calls
        client2 = ollama_client.client
        assert client == client2
        assert mock_client_class.call_count == 1
    
    @patch('codebase_gardener.models.ollama_client.AsyncClient')
    def test_async_client_property_creation(self, mock_async_client_class, ollama_client):
        """Test that async_client property creates AsyncClient instance."""
        # Access async_client property
        client = ollama_client.async_client
        
        # Verify AsyncClient was created with correct parameters
        mock_async_client_class.assert_called_once_with(
            host="http://localhost:11434",
            timeout=30
        )
        
        # Verify same instance is returned on subsequent calls
        client2 = ollama_client.async_client
        assert client == client2
        assert mock_async_client_class.call_count == 1
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_list_models_success(self, mock_client_class, ollama_client):
        """Test successful model listing."""
        # Mock successful list response
        expected_models = [
            {'name': 'model1', 'size': 1000},
            {'name': 'model2', 'size': 2000}
        ]
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': expected_models}
        mock_client_class.return_value = mock_client_instance
        
        # Disable retry decorator for this test
        with patch('codebase_gardener.utils.error_handling.model_retry', lambda f: f):
            models = ollama_client.list_models()
        
        assert models == expected_models
        mock_client_instance.list.assert_called_once()
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_show_model_success(self, mock_client_class, ollama_client):
        """Test successful model show."""
        # Mock successful show response
        expected_info = {
            'model': 'test-model',
            'parameters': {'temperature': 0.8},
            'template': 'test template'
        }
        mock_client_instance = Mock()
        mock_client_instance.show.return_value = expected_info
        mock_client_class.return_value = mock_client_instance
        
        # Disable retry decorator for this test
        with patch('codebase_gardener.utils.error_handling.model_retry', lambda f: f):
            info = ollama_client.show_model('test-model')
        
        assert info == expected_info
        mock_client_instance.show.assert_called_once_with('test-model')
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_show_model_not_found(self, mock_client_class, ollama_client):
        """Test show model with 404 error."""
        # Mock 404 ResponseError
        mock_client_instance = Mock()
        mock_client_instance.show.side_effect = ollama.ResponseError("Model not found", 404)
        mock_client_class.return_value = mock_client_instance
        
        # Disable retry decorator for this test
        with patch('codebase_gardener.utils.error_handling.model_retry', lambda f: f):
            # Show model should raise ModelLoadingError
            with pytest.raises(ModelLoadingError) as exc_info:
                ollama_client.show_model('nonexistent-model')
        
        assert "nonexistent-model" in str(exc_info.value)
        assert exc_info.value.details["status_code"] == 404
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_chat_success(self, mock_client_class, ollama_client):
        """Test successful chat inference."""
        # Mock successful chat response
        expected_response = {
            'message': {'role': 'assistant', 'content': 'Hello!'},
            'done': True
        }
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = expected_response
        mock_client_class.return_value = mock_client_instance
        
        # Mock model availability check and disable retry
        with patch.object(ollama_client, '_validate_model_available'), \
             patch('codebase_gardener.utils.error_handling.model_retry', lambda f: f):
            messages = [{'role': 'user', 'content': 'Hi'}]
            response = ollama_client.chat('test-model', messages)
        
        assert response == expected_response
        mock_client_instance.chat.assert_called_once_with(
            model='test-model',
            messages=messages,
            stream=False
        )
    
    @patch('codebase_gardener.models.ollama_client.Client')
    def test_generate_success(self, mock_client_class, ollama_client):
        """Test successful text generation."""
        # Mock successful generate response
        expected_response = {
            'response': 'Generated text',
            'done': True
        }
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = expected_response
        mock_client_class.return_value = mock_client_instance
        
        # Mock model availability check and disable retry
        with patch.object(ollama_client, '_validate_model_available'), \
             patch('codebase_gardener.utils.error_handling.model_retry', lambda f: f):
            response = ollama_client.generate('test-model', 'Test prompt')
        
        assert response == expected_response
        mock_client_instance.generate.assert_called_once_with(
            model='test-model',
            prompt='Test prompt',
            stream=False
        )
    
    def test_is_model_available_true(self, ollama_client):
        """Test is_model_available returns True for available model."""
        # Mock list_models to return available models
        with patch.object(ollama_client, 'list_models') as mock_list:
            mock_list.return_value = [
                {'name': 'model1'},
                {'name': 'model2'},
                {'name': 'test-model'}
            ]
            
            result = ollama_client.is_model_available('test-model')
            
            assert result is True
    
    def test_is_model_available_false(self, ollama_client):
        """Test is_model_available returns False for unavailable model."""
        # Mock list_models to return available models
        with patch.object(ollama_client, 'list_models') as mock_list:
            mock_list.return_value = [
                {'name': 'model1'},
                {'name': 'model2'}
            ]
            
            result = ollama_client.is_model_available('nonexistent-model')
            
            assert result is False
    
    def test_validate_model_available_success(self, ollama_client):
        """Test _validate_model_available passes for available model."""
        # Mock is_model_available to return True
        with patch.object(ollama_client, 'is_model_available', return_value=True):
            # Should not raise exception
            ollama_client._validate_model_available('test-model')
    
    def test_validate_model_available_failure(self, ollama_client):
        """Test _validate_model_available raises error for unavailable model."""
        # Mock is_model_available to return False
        with patch.object(ollama_client, 'is_model_available', return_value=False):
            # Mock list_models for error details
            with patch.object(ollama_client, 'list_models', return_value=[{'name': 'other-model'}]):
                
                with pytest.raises(ModelLoadingError) as exc_info:
                    ollama_client._validate_model_available('nonexistent-model')
                
                assert "nonexistent-model" in str(exc_info.value)
                assert "other-model" in str(exc_info.value.suggestions)
    
    def test_close(self, ollama_client):
        """Test client cleanup."""
        # Set some state
        ollama_client._client = Mock()
        ollama_client._async_client = Mock()
        ollama_client._last_health_check = datetime.now()
        
        # Close client
        ollama_client.close()
        
        # Verify state is reset
        assert ollama_client._client is None
        assert ollama_client._async_client is None
        assert ollama_client._last_health_check is None
    
    def test_context_manager(self, mock_settings):
        """Test context manager functionality."""
        with patch.object(OllamaClient, 'close') as mock_close:
            with OllamaClient(mock_settings) as client:
                assert isinstance(client, OllamaClient)
            
            mock_close.assert_called_once()


class TestConvenienceFunctions:
    """Test cases for convenience functions."""
    
    def test_get_ollama_client_default(self):
        """Test get_ollama_client with default settings."""
        with patch('codebase_gardener.models.ollama_client.get_settings') as mock_get_settings:
            mock_settings = Mock()
            mock_get_settings.return_value = mock_settings
            
            client = get_ollama_client()
            
            assert isinstance(client, OllamaClient)
            assert client.settings == mock_settings
    
    def test_get_ollama_client_custom_settings(self):
        """Test get_ollama_client with custom settings."""
        custom_settings = Mock()
        
        client = get_ollama_client(custom_settings)
        
        assert isinstance(client, OllamaClient)
        assert client.settings == custom_settings
    
    def test_ensure_model_available_already_available(self):
        """Test ensure_model_available when model is already available."""
        mock_client = Mock()
        mock_client.is_model_available.return_value = True
        
        # Disable retry decorator for this test
        with patch('codebase_gardener.utils.error_handling.retry_with_backoff', lambda **kwargs: lambda f: f):
            result = ensure_model_available('test-model', mock_client)
        
        assert result is True
        mock_client.is_model_available.assert_called_once_with('test-model')
        mock_client.pull_model.assert_not_called()
    
    def test_ensure_model_available_pull_success(self):
        """Test ensure_model_available pulls model successfully."""
        mock_client = Mock()
        # First call returns False (not available), second returns True (after pull)
        mock_client.is_model_available.side_effect = [False, True]
        mock_client.pull_model.return_value = {'status': 'success'}
        
        # Disable retry decorator for this test
        with patch('codebase_gardener.utils.error_handling.retry_with_backoff', lambda **kwargs: lambda f: f):
            result = ensure_model_available('test-model', mock_client)
        
        assert result is True
        assert mock_client.is_model_available.call_count == 2
        mock_client.pull_model.assert_called_once_with('test-model', stream=False)