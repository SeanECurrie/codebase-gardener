"""
Tests for the error handling framework.

This module tests:
- Custom exception hierarchy
- Retry decorators with exponential backoff
- Error handling decorators
- Integration with structured logging
- User-friendly error messages
"""

import time
from datetime import datetime
from unittest.mock import patch

import pytest
from codebase_gardener.utils.error_handling import (
    # Base exceptions
    CodebaseGardenerError,
    ConfigurationError,
    DirectorySetupError,
    ModelError,
    ModelInferenceError,
    ModelLoadingError,
    NetworkError,
    ParsingError,
    ProjectError,
    StorageError,
    TrainingError,
    TreeSitterError,
    VectorStoreError,
    # Utility functions
    format_error_for_user,
    get_error_context,
    graceful_fallback,
    # Error handling decorators
    handle_errors,
    is_retryable_error,
    log_errors,
    model_retry,
    network_retry,
    # Retry decorators
    retry_with_backoff,
    storage_retry,
)


class TestExceptionHierarchy:
    """Test the custom exception hierarchy."""

    def test_base_exception_creation(self):
        """Test basic CodebaseGardenerError creation."""
        message = "Test error message"
        details = {"key": "value"}
        user_message = "User-friendly message"
        suggestions = ["Suggestion 1", "Suggestion 2"]

        with patch('codebase_gardener.utils.error_handling.logger') as mock_logger:
            error = CodebaseGardenerError(
                message=message,
                details=details,
                user_message=user_message,
                suggestions=suggestions
            )

        assert error.message == message
        assert error.details == details
        assert error.user_message == user_message
        assert error.suggestions == suggestions
        assert isinstance(error.timestamp, datetime)

        # Verify logging was called
        mock_logger.error.assert_called_once()
        call_args = mock_logger.error.call_args
        assert "Codebase Gardener error occurred" in call_args[0]

    def test_base_exception_defaults(self):
        """Test CodebaseGardenerError with default values."""
        message = "Test error"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = CodebaseGardenerError(message)

        assert error.message == message
        assert error.details == {}
        assert error.user_message == message
        assert error.suggestions == []

    def test_exception_to_dict(self):
        """Test error serialization to dictionary."""
        message = "Test error"
        details = {"test": "data"}

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = CodebaseGardenerError(message, details=details)

        error_dict = error.to_dict()

        assert error_dict["error_type"] == "CodebaseGardenerError"
        assert error_dict["message"] == message
        assert error_dict["details"] == details
        assert "timestamp" in error_dict

    def test_configuration_error(self):
        """Test ConfigurationError with default suggestions."""
        message = "Config error"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = ConfigurationError(message)

        assert isinstance(error, CodebaseGardenerError)
        assert len(error.suggestions) > 0
        assert "configuration" in error.suggestions[0].lower()

    def test_model_loading_error(self):
        """Test ModelLoadingError with model-specific details."""
        model_name = "test-model"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = ModelLoadingError(model_name)

        assert isinstance(error, ModelError)
        assert model_name in error.message
        assert error.details["model_name"] == model_name
        assert any(model_name in suggestion for suggestion in error.suggestions)

    def test_model_inference_error(self):
        """Test ModelInferenceError with operation details."""
        operation = "text_generation"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = ModelInferenceError(operation)

        assert isinstance(error, ModelError)
        assert operation in error.message
        assert error.details["operation"] == operation

    def test_tree_sitter_error(self):
        """Test TreeSitterError with file and language details."""
        file_path = "/test/file.py"
        language = "python"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = TreeSitterError(file_path, language)

        assert isinstance(error, ParsingError)
        assert file_path in error.message
        assert language in error.message
        assert error.details["file_path"] == file_path
        assert error.details["language"] == language

    def test_vector_store_error(self):
        """Test VectorStoreError with operation details."""
        operation = "similarity_search"

        with patch('codebase_gardener.utils.error_handling.logger'):
            error = VectorStoreError(operation)

        assert isinstance(error, StorageError)
        assert operation in error.message
        assert error.details["operation"] == operation

    def test_exception_inheritance(self):
        """Test that all exceptions inherit from CodebaseGardenerError."""
        exception_classes_simple = [
            ConfigurationError,
            ModelError,
            ParsingError,
            StorageError,
            DirectorySetupError,
            NetworkError,
            ProjectError,
            TrainingError,
        ]

        # Test simple constructors
        for exc_class in exception_classes_simple:
            with patch('codebase_gardener.utils.error_handling.logger'):
                error = exc_class("test message")
            assert isinstance(error, CodebaseGardenerError)

        # Test special constructors
        with patch('codebase_gardener.utils.error_handling.logger'):
            model_loading_error = ModelLoadingError("test-model")
            assert isinstance(model_loading_error, CodebaseGardenerError)

            model_inference_error = ModelInferenceError("test-operation")
            assert isinstance(model_inference_error, CodebaseGardenerError)

            tree_sitter_error = TreeSitterError("/test/file.py", "python")
            assert isinstance(tree_sitter_error, CodebaseGardenerError)

            vector_store_error = VectorStoreError("test-operation")
            assert isinstance(vector_store_error, CodebaseGardenerError)


class TestRetryDecorators:
    """Test retry decorators and exponential backoff."""

    def test_retry_with_backoff_success_after_failure(self):
        """Test successful retry after initial failures."""
        call_count = 0

        @retry_with_backoff(max_attempts=3, min_wait=0.1, max_wait=0.2)
        def failing_function():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ConnectionError("Temporary failure")
            return "success"

        result = failing_function()
        assert result == "success"
        assert call_count == 3

    def test_retry_with_backoff_exhaustion(self):
        """Test behavior when all retry attempts are exhausted."""
        call_count = 0

        @retry_with_backoff(max_attempts=2, min_wait=0.1, max_wait=0.2)
        def always_failing_function():
            nonlocal call_count
            call_count += 1
            raise ConnectionError("Persistent failure")

        with pytest.raises(ConnectionError):
            always_failing_function()

        assert call_count == 2

    def test_retry_with_backoff_no_retry_on_different_exception(self):
        """Test that retry doesn't occur for non-specified exceptions."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.2,
            retry_exceptions=(ConnectionError,)
        )
        def function_with_different_error():
            nonlocal call_count
            call_count += 1
            raise ValueError("Different error type")

        with pytest.raises(ValueError):
            function_with_different_error()

        assert call_count == 1  # No retries for ValueError

    def test_model_retry_decorator(self):
        """Test model-specific retry decorator."""
        call_count = 0

        @model_retry
        def failing_model_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise ModelError("Model temporarily unavailable")
            return "model_result"

        result = failing_model_operation()
        assert result == "model_result"
        assert call_count == 2

    def test_network_retry_decorator(self):
        """Test network-specific retry decorator."""
        call_count = 0

        @network_retry
        def failing_network_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise NetworkError("Network temporarily unavailable")
            return "network_result"

        result = failing_network_operation()
        assert result == "network_result"
        assert call_count == 3

    def test_storage_retry_decorator(self):
        """Test storage-specific retry decorator."""
        call_count = 0

        @storage_retry
        def failing_storage_operation():
            nonlocal call_count
            call_count += 1
            if call_count < 2:
                raise StorageError("Storage temporarily unavailable")
            return "storage_result"

        result = failing_storage_operation()
        assert result == "storage_result"
        assert call_count == 2

    def test_exponential_backoff_timing(self):
        """Test that exponential backoff timing works correctly."""
        call_times = []

        @retry_with_backoff(max_attempts=3, min_wait=0.1, max_wait=0.5, multiplier=2)
        def timing_test_function():
            call_times.append(time.time())
            if len(call_times) < 3:
                raise ConnectionError("Timing test")
            return "success"

        start_time = time.time()
        result = timing_test_function()

        assert result == "success"
        assert len(call_times) == 3

        # Check that delays increase (allowing for some timing variance)
        delay1 = call_times[1] - call_times[0]
        delay2 = call_times[2] - call_times[1]

        assert delay1 >= 0.1  # At least min_wait
        # Allow for some timing variance in exponential increase
        assert delay2 >= delay1 * 0.8  # Should be roughly exponential


class TestErrorHandlingDecorators:
    """Test error handling decorators."""

    def test_handle_errors_decorator(self):
        """Test handle_errors decorator converts exceptions."""
        @handle_errors(error_type=ModelError, user_message="Model operation failed")
        def function_with_generic_error():
            raise ValueError("Generic error")

        with pytest.raises(ModelError) as exc_info:
            function_with_generic_error()

        error = exc_info.value
        assert error.user_message == "Model operation failed"
        assert "function_with_generic_error" in error.details["function"]
        assert error.details["original_error_type"] == "ValueError"

    def test_handle_errors_preserves_structured_errors(self):
        """Test that handle_errors doesn't double-wrap structured errors."""
        @handle_errors(error_type=ModelError)
        def function_with_structured_error():
            raise ModelError("Already structured")

        with pytest.raises(ModelError) as exc_info:
            function_with_structured_error()

        # Should be the original error, not wrapped
        assert exc_info.value.message == "Already structured"

    def test_handle_errors_no_reraise(self):
        """Test handle_errors with reraise=False."""
        @handle_errors(error_type=ModelError, reraise=False)
        def function_returning_none_on_error():
            raise ValueError("Error to handle")

        result = function_returning_none_on_error()
        assert result is None

    def test_graceful_fallback_decorator(self):
        """Test graceful_fallback decorator."""
        @graceful_fallback(fallback_value="fallback_result")
        def function_with_fallback():
            raise RuntimeError("Something went wrong")

        result = function_with_fallback()
        assert result == "fallback_result"

    def test_graceful_fallback_success(self):
        """Test graceful_fallback when function succeeds."""
        @graceful_fallback(fallback_value="fallback_result")
        def successful_function():
            return "success_result"

        result = successful_function()
        assert result == "success_result"

    def test_log_errors_decorator(self):
        """Test log_errors decorator logs but doesn't handle errors."""
        with patch('codebase_gardener.utils.error_handling.logger') as mock_logger:
            @log_errors
            def function_that_logs_errors():
                raise RuntimeError("Error to log")

            with pytest.raises(RuntimeError):
                function_that_logs_errors()

            mock_logger.error.assert_called_once()
            call_args = mock_logger.error.call_args
            assert "Error occurred in function" in call_args[0]


class TestUtilityFunctions:
    """Test utility functions for error handling."""

    def test_format_error_for_user(self):
        """Test user-friendly error formatting."""
        with patch('codebase_gardener.utils.error_handling.logger'):
            error = CodebaseGardenerError(
                message="Internal error",
                user_message="Something went wrong",
                suggestions=["Try restarting", "Check configuration"]
            )

        formatted = format_error_for_user(error)

        assert "Something went wrong" in formatted
        assert "Try restarting" in formatted
        assert "Check configuration" in formatted
        assert "1." in formatted  # Numbered suggestions
        assert "2." in formatted

    def test_format_error_for_user_no_suggestions(self):
        """Test error formatting without suggestions."""
        with patch('codebase_gardener.utils.error_handling.logger'):
            error = CodebaseGardenerError(
                message="Internal error",
                user_message="Something went wrong"
            )

        formatted = format_error_for_user(error)

        assert "Something went wrong" in formatted
        assert "Suggestions:" not in formatted

    def test_is_retryable_error(self):
        """Test retryable error detection."""
        # Retryable errors
        retryable_errors = [
            NetworkError("Network issue"),
            ConnectionError("Connection failed"),
            TimeoutError("Request timed out"),
            ModelLoadingError("test-model"),
            VectorStoreError("search"),
            OSError("File system error"),
            OSError("I/O error"),
        ]

        for error in retryable_errors:
            with patch('codebase_gardener.utils.error_handling.logger'):
                assert is_retryable_error(error), f"{type(error).__name__} should be retryable"

        # Non-retryable errors
        non_retryable_errors = [
            ValueError("Invalid value"),
            TypeError("Type error"),
            ConfigurationError("Config error"),
        ]

        for error in non_retryable_errors:
            with patch('codebase_gardener.utils.error_handling.logger'):
                assert not is_retryable_error(error), f"{type(error).__name__} should not be retryable"

    def test_get_error_context_structured_error(self):
        """Test error context extraction for structured errors."""
        with patch('codebase_gardener.utils.error_handling.logger'):
            error = ModelError(
                message="Model failed",
                details={"model": "test"},
                user_message="Model is unavailable",
                suggestions=["Restart model"]
            )

        context = get_error_context(error)

        assert context["error_type"] == "ModelError"
        assert context["error_message"] == "Model failed"
        assert context["details"] == {"model": "test"}
        assert context["user_message"] == "Model is unavailable"
        assert context["suggestions"] == ["Restart model"]
        assert "timestamp" in context

    def test_get_error_context_generic_error(self):
        """Test error context extraction for generic errors."""
        error = ValueError("Generic error")

        context = get_error_context(error)

        assert context["error_type"] == "ValueError"
        assert context["error_message"] == "Generic error"
        assert "timestamp" in context
        assert "details" not in context  # Only for structured errors


class TestIntegration:
    """Test integration between different error handling components."""

    def test_retry_with_structured_errors(self):
        """Test retry logic with structured errors."""
        call_count = 0

        @retry_with_backoff(
            max_attempts=3,
            min_wait=0.1,
            max_wait=0.2,
            retry_exceptions=(ModelError,)
        )
        def function_with_structured_errors():
            nonlocal call_count
            call_count += 1
            if call_count < 3:
                raise ModelError("Temporary model failure")
            return "success"

        result = function_with_structured_errors()
        assert result == "success"
        assert call_count == 3

    def test_combined_decorators(self):
        """Test combining multiple error handling decorators."""
        call_count = 0

        @graceful_fallback(fallback_value="fallback")
        @handle_errors(error_type=ModelError, reraise=True)
        @retry_with_backoff(max_attempts=2, min_wait=0.1, max_wait=0.2)
        def complex_function():
            nonlocal call_count
            call_count += 1
            if call_count == 1:
                raise ConnectionError("Retryable error")
            elif call_count == 2:
                raise ValueError("Non-retryable error")
            return "success"

        # Should retry once on ConnectionError, then convert ValueError to ModelError,
        # but graceful_fallback should catch it and return fallback
        result = complex_function()
        assert result == "fallback"
        assert call_count == 2

    def test_logging_integration(self):
        """Test that all error handling integrates with logging."""
        with patch('codebase_gardener.utils.error_handling.logger') as mock_logger:
            # Test that creating structured errors logs
            error = ModelError("Test error")
            mock_logger.error.assert_called()

            # Test that retry decorators log
            @retry_with_backoff(max_attempts=2, min_wait=0.1, max_wait=0.2)
            def failing_function():
                raise ConnectionError("Test failure")

            with pytest.raises(ConnectionError):
                failing_function()

            # Should have logged the retry attempts and final failure
            assert mock_logger.error.call_count > 1


class TestErrorRecovery:
    """Test error recovery mechanisms."""

    def test_circuit_breaker_pattern(self):
        """Test implementing circuit breaker pattern with error handling."""
        failure_count = 0
        circuit_open = False

        def circuit_breaker_function():
            nonlocal failure_count, circuit_open

            if circuit_open:
                raise ModelError("Circuit breaker is open")

            failure_count += 1
            if failure_count < 3:
                raise NetworkError("Service unavailable")
            elif failure_count == 3:
                circuit_open = True
                raise ModelError("Too many failures, opening circuit")

            return "success"

        # First two calls should retry and fail
        with pytest.raises(NetworkError):
            circuit_breaker_function()

        with pytest.raises(NetworkError):
            circuit_breaker_function()

        # Third call should open circuit
        with pytest.raises(ModelError) as exc_info:
            circuit_breaker_function()
        assert "opening circuit" in str(exc_info.value)

        # Fourth call should fail immediately due to open circuit
        with pytest.raises(ModelError) as exc_info:
            circuit_breaker_function()
        assert "Circuit breaker is open" in str(exc_info.value)

    def test_error_aggregation(self):
        """Test aggregating multiple errors for batch operations."""
        errors = []

        def process_item(item):
            if item == "error1":
                raise ParsingError("Parse error 1")
            elif item == "error2":
                raise StorageError("Storage error 2")
            return f"processed_{item}"

        items = ["success1", "error1", "success2", "error2", "success3"]
        results = []

        for item in items:
            try:
                result = process_item(item)
                results.append(result)
            except CodebaseGardenerError as e:
                errors.append(e)

        assert len(results) == 3  # 3 successful items
        assert len(errors) == 2   # 2 failed items
        assert isinstance(errors[0], ParsingError)
        assert isinstance(errors[1], StorageError)

    def test_partial_failure_handling(self):
        """Test handling partial failures in batch operations."""
        @graceful_fallback(fallback_value=None)
        def process_with_fallback(item):
            if "error" in item:
                raise ProcessingError(f"Failed to process {item}")
            return f"processed_{item}"

        items = ["item1", "error_item", "item2", "another_error", "item3"]
        results = [process_with_fallback(item) for item in items]

        expected = ["processed_item1", None, "processed_item2", None, "processed_item3"]
        assert results == expected


# Mock ProcessingError for the test
class ProcessingError(CodebaseGardenerError):
    """Mock error for testing."""
    pass
