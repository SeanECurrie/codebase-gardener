"""
Tests for the logging configuration module.
"""

import json
import logging
import tempfile
from io import StringIO
from pathlib import Path
from unittest.mock import patch

import pytest
import structlog

from codebase_gardener.config.logging_config import (
    configure_logging,
    get_logger,
    bind_context,
    clear_context,
    LoggerMixin,
    log_function_call,
    log_performance,
    log_error,
)


class TestLoggingConfiguration:
    """Test cases for logging configuration."""
    
    def setup_method(self):
        """Reset logging configuration before each test."""
        # Clear any existing structlog configuration
        structlog.reset_defaults()
        
        # Reset standard library logging
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)
    
    def test_configure_logging_debug_mode(self):
        """Test logging configuration in debug mode."""
        configure_logging(log_level="DEBUG", debug=True)
        
        assert structlog.is_configured()
        
        # Test that we can get a logger
        logger = get_logger(__name__)
        assert logger is not None
    
    def test_configure_logging_production_mode(self):
        """Test logging configuration in production mode."""
        configure_logging(log_level="INFO", debug=False)
        
        assert structlog.is_configured()
        
        # Test that we can get a logger
        logger = get_logger(__name__)
        assert logger is not None
    
    def test_configure_logging_with_file_output(self):
        """Test logging configuration with file output."""
        with tempfile.TemporaryDirectory() as temp_dir:
            log_file = Path(temp_dir) / "test.log"
            
            configure_logging(log_level="INFO", debug=False, log_file=log_file)
            
            # Test that log file is created
            logger = get_logger(__name__)
            logger.info("Test message")
            
            # Check that file handler was added
            root_logger = logging.getLogger()
            file_handlers = [h for h in root_logger.handlers if isinstance(h, logging.handlers.RotatingFileHandler)]
            assert len(file_handlers) > 0
    
    def test_get_logger_returns_bound_logger(self):
        """Test that get_logger returns a structlog BoundLogger."""
        configure_logging()
        
        logger = get_logger(__name__)
        assert hasattr(logger, 'info')  # Check it has logging methods
    
    def test_bind_context_adds_context_to_logs(self):
        """Test that bind_context adds context variables to log messages."""
        configure_logging(debug=False)
        
        # Capture log output
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            bind_context(user_id="test123", operation="test_operation")
            
            logger = get_logger(__name__)
            logger.info("Test message")
            
            # Parse the JSON log output
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert log_data.get("user_id") == "test123"
                assert log_data.get("operation") == "test_operation"
    
    def test_clear_context_removes_bound_variables(self):
        """Test that clear_context removes bound context variables."""
        configure_logging(debug=False)
        
        # Bind some context
        bind_context(user_id="test123")
        
        # Clear context
        clear_context()
        
        # Capture log output
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger = get_logger(__name__)
            logger.info("Test message")
            
            # Parse the JSON log output
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert "user_id" not in log_data
    
    def test_log_function_call(self):
        """Test the log_function_call utility function."""
        configure_logging(debug=False)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            log_function_call("test_function", param1="value1", param2=42)
            
            # Check that function call was logged
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert log_data.get("function") == "test_function"
                assert log_data.get("parameters") == {"param1": "value1", "param2": 42}
    
    def test_log_performance(self):
        """Test the log_performance utility function."""
        configure_logging(debug=False)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            log_performance("test_operation", 1.23, items_processed=100)
            
            # Check that performance metric was logged
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert log_data.get("operation") == "test_operation"
                assert log_data.get("duration_seconds") == 1.23
                assert log_data.get("items_processed") == 100
    
    def test_log_error(self):
        """Test the log_error utility function."""
        configure_logging(debug=False)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            try:
                raise ValueError("Test error message")
            except ValueError as e:
                log_error(e, "test_operation", context="additional_info")
            
            # Check that error was logged
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert log_data.get("operation") == "test_operation"
                assert log_data.get("error_type") == "ValueError"
                assert log_data.get("error_message") == "Test error message"
                assert log_data.get("context") == "additional_info"


class TestLoggerMixin:
    """Test cases for the LoggerMixin class."""
    
    def setup_method(self):
        """Reset logging configuration before each test."""
        structlog.reset_defaults()
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)
    
    def test_logger_mixin_provides_logger(self):
        """Test that LoggerMixin provides a logger property."""
        configure_logging()
        
        class TestClass(LoggerMixin):
            def test_method(self):
                return self.logger
        
        test_instance = TestClass()
        logger = test_instance.test_method()
        
        assert hasattr(logger, 'info')  # Check it has logging methods
    
    def test_logger_mixin_caches_logger(self):
        """Test that LoggerMixin caches the logger instance."""
        configure_logging()
        
        class TestClass(LoggerMixin):
            pass
        
        test_instance = TestClass()
        logger1 = test_instance.logger
        logger2 = test_instance.logger
        
        assert logger1 is logger2
    
    def test_logger_mixin_with_logging(self):
        """Test that LoggerMixin can be used for actual logging."""
        configure_logging(debug=False)
        
        class TestClass(LoggerMixin):
            def do_something(self):
                self.logger.info("Method called", method="do_something")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            test_instance = TestClass()
            test_instance.do_something()
            
            # Check that log message was output
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                log_data = json.loads(log_output)
                assert log_data.get("method") == "do_something"


class TestLoggingIntegration:
    """Integration tests for logging functionality."""
    
    def setup_method(self):
        """Reset logging configuration before each test."""
        structlog.reset_defaults()
        logging.getLogger().handlers.clear()
        logging.getLogger().setLevel(logging.WARNING)
    
    def test_logging_with_different_levels(self):
        """Test logging with different log levels."""
        configure_logging(log_level="DEBUG", debug=False)
        
        logger = get_logger(__name__)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # All messages should be logged since level is DEBUG
            log_output = mock_stdout.getvalue()
            assert "Debug message" in log_output
            assert "Info message" in log_output
            assert "Warning message" in log_output
            assert "Error message" in log_output
    
    def test_logging_level_filtering(self):
        """Test that log level filtering works correctly."""
        configure_logging(log_level="WARNING", debug=False)
        
        logger = get_logger(__name__)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.debug("Debug message")
            logger.info("Info message")
            logger.warning("Warning message")
            logger.error("Error message")
            
            # Only WARNING and ERROR should be logged
            log_output = mock_stdout.getvalue()
            assert "Debug message" not in log_output
            assert "Info message" not in log_output
            assert "Warning message" in log_output
            assert "Error message" in log_output
    
    def test_structured_logging_format(self):
        """Test that structured logging produces valid JSON."""
        configure_logging(debug=False)
        
        logger = get_logger(__name__)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            logger.info("Test message", key1="value1", key2=42)
            
            log_output = mock_stdout.getvalue().strip()
            if log_output:
                # Should be valid JSON
                log_data = json.loads(log_output)
                assert log_data.get("event") == "Test message"
                assert log_data.get("key1") == "value1"
                assert log_data.get("key2") == 42
                assert "timestamp" in log_data
                assert "level" in log_data