"""
Tests for the Ollama client integration.

This module tests the OllamaClient class including:
- Connection management and health checks
- Model operations (list, show, pull)
- Chat and generation inference
- Error handling and retry logic
- Both sync and async operations
"""

from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

import ollama
import pytest
from codebase_gardener.config.settings import Settings
from codebase_gardener.models.ollama_client import (
    OllamaClient,
    ensure_model_available,
    get_ollama_client,
)
from codebase_gardener.utils.error_handling import (
    ModelError,
    ModelInferenceError,
    ModelLoadingError,
    NetworkError,
)


# Mock retry decorators to disable retries in tests
def no_retry(func):
    """Mock retry decorator that doesn't retry."""
    return func


# Patch retry decorators at module level
@pytest.fixture(autouse=True)
def disable_retries():
    """Disable retry logic for all tests."""
    with patch('codebase_gardener.utils.error_handling.model_retry', no_retry), \
         patch('codebase_gardener.utils.error_handling.network_retry', no_retry), \
         patch('codebase_gardener.utils.error_handling.retry_with_backoff', lambda **kwargs: no_retry):
        yield


class TestOllamaClient:
    """Test cases for OllamaClient class."""

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

    @pytest.fixture
    def mock_ollama_client(self):
        """Mock ollama.Client for testing."""
        with patch('codebase_gardener.models.ollama_client.Client') as mock:
            yield mock

    @pytest.fixture
    def mock_async_ollama_client(self):
        """Mock ollama.AsyncClient for testing."""
        with patch('codebase_gardener.models.ollama_client.AsyncClient') as mock:
            yield mock

    def test_client_initialization(self, mock_settings):
        """Test OllamaClient initialization."""
        client = OllamaClient(mock_settings)

        assert client.settings == mock_settings
        assert client._client is None
        assert client._async_client is None
        assert client._last_health_check is None

    def test_client_property_creation(self, ollama_client, mock_ollama_client):
        """Test that client property creates Client instance."""
        # Access client property
        client = ollama_client.client

        # Verify Client was created with correct parameters
        mock_ollama_client.assert_called_once_with(
            host="http://localhost:11434",
            timeout=30
        )

        # Verify same instance is returned on subsequent calls
        client2 = ollama_client.client
        assert client == client2
        assert mock_ollama_client.call_count == 1

    def test_async_client_property_creation(self, ollama_client, mock_async_ollama_client):
        """Test that async_client property creates AsyncClient instance."""
        # Access async_client property
        client = ollama_client.async_client

        # Verify AsyncClient was created with correct parameters
        mock_async_ollama_client.assert_called_once_with(
            host="http://localhost:11434",
            timeout=30
        )

        # Verify same instance is returned on subsequent calls
        client2 = ollama_client.async_client
        assert client == client2
        assert mock_async_ollama_client.call_count == 1

    def test_health_check_success(self, ollama_client, mock_ollama_client):
        """Test successful health check."""
        # Mock successful list response
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': [{'name': 'test-model'}]}
        mock_ollama_client.return_value = mock_client_instance

        # Perform health check
        result = ollama_client.health_check()

        assert result is True
        mock_client_instance.list.assert_called_once()
        assert ollama_client._last_health_check is not None

    def test_health_check_skip_recent(self, ollama_client, mock_ollama_client):
        """Test health check skips when recently performed."""
        # Set recent health check
        ollama_client._last_health_check = datetime.now()

        # Mock client (should not be called)
        mock_client_instance = Mock()
        mock_ollama_client.return_value = mock_client_instance

        # Perform health check
        result = ollama_client.health_check()

        assert result is True
        mock_client_instance.list.assert_not_called()

    def test_health_check_force(self, ollama_client, mock_ollama_client):
        """Test forced health check ignores recent check."""
        # Set recent health check
        ollama_client._last_health_check = datetime.now()

        # Mock successful list response
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': []}
        mock_ollama_client.return_value = mock_client_instance

        # Perform forced health check
        result = ollama_client.health_check(force=True)

        assert result is True
        mock_client_instance.list.assert_called_once()

    def test_health_check_ollama_response_error(self, ollama_client, mock_ollama_client):
        """Test health check with Ollama ResponseError."""
        # Mock ResponseError
        mock_client_instance = Mock()
        mock_client_instance.list.side_effect = ollama.ResponseError("Service unavailable", 503)
        mock_ollama_client.return_value = mock_client_instance

        # Health check should raise NetworkError
        with pytest.raises(NetworkError) as exc_info:
            ollama_client.health_check()

        assert "Service unavailable" in str(exc_info.value)
        assert exc_info.value.details["status_code"] == 503

    def test_health_check_connection_error(self, ollama_client, mock_ollama_client):
        """Test health check with connection error."""
        # Mock connection error
        mock_client_instance = Mock()
        mock_client_instance.list.side_effect = ConnectionError("Connection refused")
        mock_ollama_client.return_value = mock_client_instance

        # Health check should raise NetworkError
        with pytest.raises(NetworkError) as exc_info:
            ollama_client.health_check()

        assert "Connection refused" in str(exc_info.value)

    def test_list_models_success(self, ollama_client, mock_ollama_client):
        """Test successful model listing."""
        # Mock successful list response
        expected_models = [
            {'name': 'model1', 'size': 1000},
            {'name': 'model2', 'size': 2000}
        ]
        mock_client_instance = Mock()
        mock_client_instance.list.return_value = {'models': expected_models}
        mock_ollama_client.return_value = mock_client_instance

        # List models
        models = ollama_client.list_models()

        assert models == expected_models
        mock_client_instance.list.assert_called_once()

    def test_list_models_error(self, ollama_client, mock_ollama_client):
        """Test model listing with error."""
        # Mock ResponseError
        mock_client_instance = Mock()
        mock_client_instance.list.side_effect = ollama.ResponseError("Access denied", 403)
        mock_ollama_client.return_value = mock_client_instance

        # List models should raise ModelError
        with pytest.raises(ModelError) as exc_info:
            ollama_client.list_models()

        assert "Access denied" in str(exc_info.value)

    def test_show_model_success(self, ollama_client, mock_ollama_client):
        """Test successful model show."""
        # Mock successful show response
        expected_info = {
            'model': 'test-model',
            'parameters': {'temperature': 0.8},
            'template': 'test template'
        }
        mock_client_instance = Mock()
        mock_client_instance.show.return_value = expected_info
        mock_ollama_client.return_value = mock_client_instance

        # Show model
        info = ollama_client.show_model('test-model')

        assert info == expected_info
        mock_client_instance.show.assert_called_once_with('test-model')

    def test_show_model_not_found(self, ollama_client, mock_ollama_client):
        """Test show model with 404 error."""
        # Mock 404 ResponseError
        mock_client_instance = Mock()
        mock_client_instance.show.side_effect = ollama.ResponseError("Model not found", 404)
        mock_ollama_client.return_value = mock_client_instance

        # Show model should raise ModelLoadingError
        with pytest.raises(ModelLoadingError) as exc_info:
            ollama_client.show_model('nonexistent-model')

        assert "nonexistent-model" in str(exc_info.value)
        assert exc_info.value.details["status_code"] == 404

    def test_pull_model_success(self, ollama_client, mock_ollama_client):
        """Test successful model pull."""
        # Mock successful pull response
        expected_response = {'status': 'success'}
        mock_client_instance = Mock()
        mock_client_instance.pull.return_value = expected_response
        mock_ollama_client.return_value = mock_client_instance

        # Pull model
        response = ollama_client.pull_model('test-model')

        assert response == expected_response
        mock_client_instance.pull.assert_called_once_with('test-model', stream=False)

    def test_pull_model_streaming(self, ollama_client, mock_ollama_client):
        """Test model pull with streaming."""
        # Mock streaming pull response
        mock_generator = iter([{'status': 'downloading'}, {'status': 'complete'}])
        mock_client_instance = Mock()
        mock_client_instance.pull.return_value = mock_generator
        mock_ollama_client.return_value = mock_client_instance

        # Pull model with streaming
        response = ollama_client.pull_model('test-model', stream=True)

        assert response == mock_generator
        mock_client_instance.pull.assert_called_once_with('test-model', stream=True)

    def test_pull_model_error(self, ollama_client, mock_ollama_client):
        """Test model pull with error."""
        # Mock ResponseError
        mock_client_instance = Mock()
        mock_client_instance.pull.side_effect = ollama.ResponseError("Network error", 500)
        mock_ollama_client.return_value = mock_client_instance

        # Pull model should raise ModelLoadingError
        with pytest.raises(ModelLoadingError) as exc_info:
            ollama_client.pull_model('test-model')

        assert "test-model" in str(exc_info.value)

    def test_chat_success(self, ollama_client, mock_ollama_client):
        """Test successful chat inference."""
        # Mock successful chat response
        expected_response = {
            'message': {'role': 'assistant', 'content': 'Hello!'},
            'done': True
        }
        mock_client_instance = Mock()
        mock_client_instance.chat.return_value = expected_response
        mock_ollama_client.return_value = mock_client_instance

        # Mock model availability check
        with patch.object(ollama_client, '_validate_model_available'):
            messages = [{'role': 'user', 'content': 'Hi'}]
            response = ollama_client.chat('test-model', messages)

        assert response == expected_response
        mock_client_instance.chat.assert_called_once_with(
            model='test-model',
            messages=messages,
            stream=False
        )

    def test_chat_model_not_found(self, ollama_client, mock_ollama_client):
        """Test chat with model not found error."""
        # Mock 404 ResponseError
        mock_client_instance = Mock()
        mock_client_instance.chat.side_effect = ollama.ResponseError("Model not found", 404)
        mock_ollama_client.return_value = mock_client_instance

        # Mock model availability check to pass
        with patch.object(ollama_client, '_validate_model_available'):
            messages = [{'role': 'user', 'content': 'Hi'}]

            # Chat should raise ModelLoadingError
            with pytest.raises(ModelLoadingError):
                ollama_client.chat('nonexistent-model', messages)

    def test_chat_inference_error(self, ollama_client, mock_ollama_client):
        """Test chat with inference error."""
        # Mock ResponseError
        mock_client_instance = Mock()
        mock_client_instance.chat.side_effect = ollama.ResponseError("Inference failed", 500)
        mock_ollama_client.return_value = mock_client_instance

        # Mock model availability check to pass
        with patch.object(ollama_client, '_validate_model_available'):
            messages = [{'role': 'user', 'content': 'Hi'}]

            # Chat should raise ModelInferenceError
            with pytest.raises(ModelInferenceError):
                ollama_client.chat('test-model', messages)

    def test_generate_success(self, ollama_client, mock_ollama_client):
        """Test successful text generation."""
        # Mock successful generate response
        expected_response = {
            'response': 'Generated text',
            'done': True
        }
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = expected_response
        mock_ollama_client.return_value = mock_client_instance

        # Mock model availability check
        with patch.object(ollama_client, '_validate_model_available'):
            response = ollama_client.generate('test-model', 'Test prompt')

        assert response == expected_response
        mock_client_instance.generate.assert_called_once_with(
            model='test-model',
            prompt='Test prompt',
            stream=False
        )

    def test_generate_streaming(self, ollama_client, mock_ollama_client):
        """Test text generation with streaming."""
        # Mock streaming generate response
        mock_generator = iter([{'response': 'Gen'}, {'response': 'erated'}])
        mock_client_instance = Mock()
        mock_client_instance.generate.return_value = mock_generator
        mock_ollama_client.return_value = mock_client_instance

        # Mock model availability check
        with patch.object(ollama_client, '_validate_model_available'):
            response = ollama_client.generate('test-model', 'Test prompt', stream=True)

        assert response == mock_generator
        mock_client_instance.generate.assert_called_once_with(
            model='test-model',
            prompt='Test prompt',
            stream=True
        )

    def test_get_running_models_success(self, ollama_client, mock_ollama_client):
        """Test successful running models retrieval."""
        # Mock successful ps response
        expected_models = [
            {'name': 'model1', 'cpu': 50, 'memory': 1000},
            {'name': 'model2', 'cpu': 30, 'memory': 800}
        ]
        mock_client_instance = Mock()
        mock_client_instance.ps.return_value = {'models': expected_models}
        mock_ollama_client.return_value = mock_client_instance

        # Get running models
        models = ollama_client.get_running_models()

        assert models == expected_models
        mock_client_instance.ps.assert_called_once()

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

    def test_is_model_available_error_fallback(self, ollama_client):
        """Test is_model_available returns False on error."""
        # Mock list_models to raise exception
        with patch.object(ollama_client, 'list_models') as mock_list:
            mock_list.side_effect = ModelError("Connection failed")

            result = ollama_client.is_model_available('test-model')

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


class TestAsyncOllamaClient:
    """Test cases for async OllamaClient methods."""

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

    @pytest.mark.asyncio
    async def test_async_health_check_success(self, ollama_client):
        """Test successful async health check."""
        # Mock async client
        mock_async_client = AsyncMock()
        mock_async_client.list.return_value = {'models': [{'name': 'test-model'}]}

        with patch.object(ollama_client, 'async_client', mock_async_client):
            result = await ollama_client.async_health_check()

            assert result is True
            mock_async_client.list.assert_called_once()

    @pytest.mark.asyncio
    async def test_async_health_check_error(self, ollama_client):
        """Test async health check with error."""
        # Mock async client to raise exception
        mock_async_client = AsyncMock()
        mock_async_client.list.side_effect = ConnectionError("Connection failed")

        with patch.object(ollama_client, 'async_client', mock_async_client):
            with pytest.raises(NetworkError):
                await ollama_client.async_health_check()

    @pytest.mark.asyncio
    async def test_async_chat_success(self, ollama_client):
        """Test successful async chat."""
        # Mock async client
        mock_async_client = AsyncMock()
        expected_response = {'message': {'role': 'assistant', 'content': 'Hello!'}}
        mock_async_client.chat.return_value = expected_response

        with patch.object(ollama_client, 'async_client', mock_async_client):
            messages = [{'role': 'user', 'content': 'Hi'}]
            response = await ollama_client.async_chat('test-model', messages)

            assert response == expected_response
            mock_async_client.chat.assert_called_once_with(
                model='test-model',
                messages=messages,
                stream=False
            )

    @pytest.mark.asyncio
    async def test_async_generate_success(self, ollama_client):
        """Test successful async generation."""
        # Mock async client
        mock_async_client = AsyncMock()
        expected_response = {'response': 'Generated text'}
        mock_async_client.generate.return_value = expected_response

        with patch.object(ollama_client, 'async_client', mock_async_client):
            response = await ollama_client.async_generate('test-model', 'Test prompt')

            assert response == expected_response
            mock_async_client.generate.assert_called_once_with(
                model='test-model',
                prompt='Test prompt',
                stream=False
            )


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

        result = ensure_model_available('test-model', mock_client)

        assert result is True
        assert mock_client.is_model_available.call_count == 2
        mock_client.pull_model.assert_called_once_with('test-model', stream=False)

    def test_ensure_model_available_pull_failure(self):
        """Test ensure_model_available when pull fails."""
        mock_client = Mock()
        mock_client.is_model_available.return_value = False
        mock_client.pull_model.side_effect = ModelLoadingError('test-model')

        with pytest.raises(ModelLoadingError):
            ensure_model_available('test-model', mock_client)

    def test_ensure_model_available_verification_failure(self):
        """Test ensure_model_available when verification after pull fails."""
        mock_client = Mock()
        # Always returns False (model never becomes available)
        mock_client.is_model_available.return_value = False
        mock_client.pull_model.return_value = {'status': 'success'}

        with pytest.raises(ModelLoadingError) as exc_info:
            ensure_model_available('test-model', mock_client)

        assert "pull_verification" in str(exc_info.value.details)

    def test_ensure_model_available_default_client(self):
        """Test ensure_model_available creates default client when none provided."""
        with patch('codebase_gardener.models.ollama_client.get_ollama_client') as mock_get_client:
            mock_client = Mock()
            mock_client.is_model_available.return_value = True
            mock_get_client.return_value = mock_client

            result = ensure_model_available('test-model')

            assert result is True
            mock_get_client.assert_called_once()
            mock_client.is_model_available.assert_called_once_with('test-model')


class TestErrorHandling:
    """Test cases for error handling scenarios."""

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

    def test_retry_logic_success_after_failure(self, ollama_client, mock_ollama_client):
        """Test retry logic succeeds after initial failure."""
        # Mock client that fails once then succeeds
        mock_client_instance = Mock()
        mock_client_instance.list.side_effect = [
            ConnectionError("Connection failed"),
            {'models': [{'name': 'test-model'}]}
        ]
        mock_ollama_client.return_value = mock_client_instance

        # Health check should succeed after retry
        result = ollama_client.health_check()

        assert result is True
        assert mock_client_instance.list.call_count == 2

    def test_retry_logic_exhaustion(self, ollama_client, mock_ollama_client):
        """Test retry logic exhaustion raises final error."""
        # Mock client that always fails
        mock_client_instance = Mock()
        mock_client_instance.list.side_effect = ConnectionError("Connection failed")
        mock_ollama_client.return_value = mock_client_instance

        # Health check should raise NetworkError after retries exhausted
        with pytest.raises(NetworkError):
            ollama_client.health_check()

        # Should have attempted multiple times due to retry logic
        assert mock_client_instance.list.call_count >= 2

    def test_structured_error_details(self, ollama_client, mock_ollama_client):
        """Test that structured errors contain proper details."""
        # Mock ResponseError with specific details
        mock_client_instance = Mock()
        mock_client_instance.show.side_effect = ollama.ResponseError("Model not found", 404)
        mock_ollama_client.return_value = mock_client_instance

        # Should raise ModelLoadingError with proper details
        with pytest.raises(ModelLoadingError) as exc_info:
            ollama_client.show_model('nonexistent-model')

        error = exc_info.value
        assert error.details["status_code"] == 404
        assert error.details["error"] == "Model not found"
        assert "nonexistent-model" in error.message
        assert len(error.suggestions) > 0

    def test_graceful_fallback_on_availability_check(self, ollama_client):
        """Test graceful fallback when model availability check fails."""
        # Mock list_models to raise exception
        with patch.object(ollama_client, 'list_models') as mock_list:
            mock_list.side_effect = NetworkError("Connection failed")

            # Should return False instead of raising exception
            result = ollama_client.is_model_available('test-model')

            assert result is False
