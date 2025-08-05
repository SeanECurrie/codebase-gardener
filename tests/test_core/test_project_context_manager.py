"""
Tests for the Project Context Manager.

This module tests the ProjectContextManager class and related components
for maintaining separate conversation states per project.
"""

import json
import tempfile
import threading
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock

import pytest

from src.codebase_gardener.core.project_context_manager import (
    ConversationMessage,
    ProjectContext,
    ProjectContextManager,
    ContextManagerError,
    get_project_context_manager,
    setup_context_manager_integration
)
from src.codebase_gardener.core.project_registry import ProjectMetadata, TrainingStatus


class TestConversationMessage:
    """Test the ConversationMessage dataclass."""
    
    def test_message_creation(self):
        """Test creating a conversation message."""
        timestamp = datetime.now()
        message = ConversationMessage(
            role="user",
            content="Hello, world!",
            timestamp=timestamp,
            metadata={"source": "test"}
        )
        
        assert message.role == "user"
        assert message.content == "Hello, world!"
        assert message.timestamp == timestamp
        assert message.metadata == {"source": "test"}
    
    def test_message_to_dict(self):
        """Test converting message to dictionary."""
        timestamp = datetime.now()
        message = ConversationMessage(
            role="assistant",
            content="Hi there!",
            timestamp=timestamp,
            metadata={"confidence": 0.9}
        )
        
        result = message.to_dict()
        
        assert result["role"] == "assistant"
        assert result["content"] == "Hi there!"
        assert result["timestamp"] == timestamp.isoformat()
        assert result["metadata"] == {"confidence": 0.9}
    
    def test_message_from_dict(self):
        """Test creating message from dictionary."""
        timestamp = datetime.now()
        data = {
            "role": "user",
            "content": "Test message",
            "timestamp": timestamp.isoformat(),
            "metadata": {"test": True}
        }
        
        message = ConversationMessage.from_dict(data)
        
        assert message.role == "user"
        assert message.content == "Test message"
        assert message.timestamp == timestamp
        assert message.metadata == {"test": True}
    
    def test_importance_score(self):
        """Test importance score calculation."""
        # Recent message should have high score
        recent_message = ConversationMessage(
            role="user",
            content="This is important!",
            timestamp=datetime.now()
        )
        
        # Old message should have lower score
        old_message = ConversationMessage(
            role="assistant",
            content="Old response",
            timestamp=datetime.now() - timedelta(days=7)
        )
        
        recent_score = recent_message.importance_score()
        old_score = old_message.importance_score()
        
        assert recent_score > old_score
        assert 0 <= recent_score <= 1
        assert 0 <= old_score <= 1


class TestProjectContext:
    """Test the ProjectContext dataclass."""
    
    def test_context_creation(self):
        """Test creating a project context."""
        context = ProjectContext(project_id="test-project")
        
        assert context.project_id == "test-project"
        assert context.conversation_history == []
        assert context.analysis_cache == {}
        assert isinstance(context.last_accessed, datetime)
        assert context.metadata == {}
    
    def test_add_message(self):
        """Test adding messages to context."""
        context = ProjectContext(project_id="test-project")
        
        context.add_message("user", "Hello!")
        context.add_message("assistant", "Hi there!", {"confidence": 0.9})
        
        assert len(context.conversation_history) == 2
        assert context.conversation_history[0].role == "user"
        assert context.conversation_history[0].content == "Hello!"
        assert context.conversation_history[1].role == "assistant"
        assert context.conversation_history[1].content == "Hi there!"
        assert context.conversation_history[1].metadata == {"confidence": 0.9}
    
    def test_prune_history(self):
        """Test conversation history pruning."""
        context = ProjectContext(project_id="test-project")
        
        # Add many messages
        for i in range(100):
            context.add_message("user", f"Message {i}")
            context.add_message("assistant", f"Response {i}")
        
        # Prune to 50 messages
        context.prune_history(50)
        
        assert len(context.conversation_history) <= 50
        # Should keep recent messages
        assert "Message 99" in [msg.content for msg in context.conversation_history]
    
    def test_get_recent_messages(self):
        """Test getting recent messages."""
        context = ProjectContext(project_id="test-project")
        
        for i in range(10):
            context.add_message("user", f"Message {i}")
        
        # Get last 5 messages
        recent = context.get_recent_messages(5)
        assert len(recent) == 5
        assert recent[-1].content == "Message 9"
        
        # Get all messages
        all_messages = context.get_recent_messages()
        assert len(all_messages) == 10
    
    def test_context_serialization(self):
        """Test context to/from dict conversion."""
        context = ProjectContext(project_id="test-project")
        context.add_message("user", "Test message")
        context.analysis_cache = {"key": "value"}
        context.metadata = {"version": "1.0"}
        
        # Convert to dict
        data = context.to_dict()
        
        assert data["project_id"] == "test-project"
        assert len(data["conversation_history"]) == 1
        assert data["analysis_cache"] == {"key": "value"}
        assert data["metadata"] == {"version": "1.0"}
        
        # Convert back from dict
        restored_context = ProjectContext.from_dict(data)
        
        assert restored_context.project_id == "test-project"
        assert len(restored_context.conversation_history) == 1
        assert restored_context.conversation_history[0].content == "Test message"
        assert restored_context.analysis_cache == {"key": "value"}
        assert restored_context.metadata == {"version": "1.0"}


class TestProjectContextManager:
    """Test the ProjectContextManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        settings = Mock()
        settings.data_dir = temp_dir
        return settings
    
    @pytest.fixture
    def context_manager(self, mock_settings):
        """Create a context manager for testing."""
        with patch('src.codebase_gardener.core.project_context_manager.get_settings', return_value=mock_settings):
            manager = ProjectContextManager()
            yield manager
    
    @pytest.fixture
    def mock_registry(self):
        """Mock project registry."""
        registry = Mock()
        project = Mock()
        project.project_id = "test-project"
        registry.get_project.return_value = project
        return registry
    
    def test_context_manager_initialization(self, context_manager, temp_dir):
        """Test context manager initialization."""
        assert context_manager._contexts_dir == temp_dir / "contexts"
        assert context_manager._contexts_dir.exists()
        assert context_manager._max_cache_size == 3
        assert context_manager._active_context is None
        assert len(context_manager._context_cache) == 0
    
    def test_switch_project_success(self, context_manager, mock_registry):
        """Test successful project switching."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Switch to project
            result = context_manager.switch_project("test-project")
            
            assert result is True
            assert context_manager._active_context is not None
            assert context_manager._active_context.project_id == "test-project"
            assert "test-project" in context_manager._context_cache
    
    def test_switch_project_invalid_project(self, context_manager):
        """Test switching to invalid project."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            registry.get_project.return_value = None
            mock_get_registry.return_value = registry
            
            with pytest.raises(ContextManagerError, match="Project invalid-project not found"):
                context_manager.switch_project("invalid-project")
    
    def test_add_message_success(self, context_manager, mock_registry):
        """Test adding message to active context."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Switch to project first
            context_manager.switch_project("test-project")
            
            # Add message
            context_manager.add_message("user", "Hello, world!")
            
            history = context_manager.get_conversation_history()
            assert len(history) == 1
            assert history[0].role == "user"
            assert history[0].content == "Hello, world!"
    
    def test_add_message_no_active_context(self, context_manager):
        """Test adding message without active context."""
        with pytest.raises(ContextManagerError, match="No active project context"):
            context_manager.add_message("user", "Hello!")
    
    def test_get_conversation_history(self, context_manager, mock_registry):
        """Test getting conversation history."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Switch to project and add messages
            context_manager.switch_project("test-project")
            context_manager.add_message("user", "Message 1")
            context_manager.add_message("assistant", "Response 1")
            context_manager.add_message("user", "Message 2")
            
            # Get all history
            history = context_manager.get_conversation_history()
            assert len(history) == 3
            
            # Get limited history
            limited_history = context_manager.get_conversation_history(limit=2)
            assert len(limited_history) == 2
            assert limited_history[-1].content == "Message 2"
    
    def test_get_conversation_history_no_context(self, context_manager):
        """Test getting history without active context."""
        history = context_manager.get_conversation_history()
        assert history == []
    
    def test_context_persistence(self, context_manager, mock_registry, temp_dir):
        """Test context persistence to disk."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Switch to project and add message
            context_manager.switch_project("test-project")
            context_manager.add_message("user", "Persistent message")
            
            # Save context
            context_manager.save_all_contexts()
            
            # Check file exists
            context_file = temp_dir / "contexts" / "test-project_context.json"
            assert context_file.exists()
            
            # Check file content
            with context_file.open('r') as f:
                data = json.load(f)
            
            assert data["project_id"] == "test-project"
            assert len(data["conversation_history"]) == 1
            assert data["conversation_history"][0]["content"] == "Persistent message"
    
    def test_context_loading(self, context_manager, mock_registry, temp_dir):
        """Test loading context from disk."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Create context file manually
            context_file = temp_dir / "contexts" / "test-project_context.json"
            context_file.parent.mkdir(exist_ok=True)
            
            context_data = {
                "project_id": "test-project",
                "conversation_history": [
                    {
                        "role": "user",
                        "content": "Loaded message",
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {}
                    }
                ],
                "analysis_cache": {},
                "last_accessed": datetime.now().isoformat(),
                "metadata": {}
            }
            
            with context_file.open('w') as f:
                json.dump(context_data, f)
            
            # Switch to project (should load from disk)
            context_manager.switch_project("test-project")
            
            history = context_manager.get_conversation_history()
            assert len(history) == 1
            assert history[0].content == "Loaded message"
    
    def test_context_cache_management(self, context_manager, mock_registry):
        """Test LRU cache management."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Create projects for cache testing
            projects = ["project1", "project2", "project3", "project4"]
            for project_id in projects:
                project = Mock()
                project.project_id = project_id
                mock_registry.get_project.return_value = project
                context_manager.switch_project(project_id)
            
            # Cache should only hold max_cache_size items
            assert len(context_manager._context_cache) <= context_manager._max_cache_size
            
            # Most recent project should be in cache
            assert "project4" in context_manager._context_cache
    
    def test_clear_context(self, context_manager, mock_registry, temp_dir):
        """Test clearing project context."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Switch to project and add message
            context_manager.switch_project("test-project")
            context_manager.add_message("user", "To be cleared")
            context_manager.save_all_contexts()
            
            # Clear context
            result = context_manager.clear_context("test-project")
            
            assert result is True
            assert context_manager._active_context is None
            assert "test-project" not in context_manager._context_cache
            
            # Context file should be removed
            context_file = temp_dir / "contexts" / "test-project_context.json"
            assert not context_file.exists()
    
    def test_get_context_stats(self, context_manager, mock_registry):
        """Test getting context statistics."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            mock_get_registry.return_value = mock_registry
            
            # Initially no active context
            stats = context_manager.get_context_stats()
            assert stats["active_project"] is None
            assert stats["cached_contexts"] == 0
            
            # Switch to project
            context_manager.switch_project("test-project")
            context_manager.add_message("user", "Test message")
            
            stats = context_manager.get_context_stats()
            assert stats["active_project"] == "test-project"
            assert stats["cached_contexts"] == 1
            assert stats["active_context"]["message_count"] == 1
    
    def test_switch_observers(self, context_manager):
        """Test project switch observers."""
        observer_calls = []
        
        def test_observer(project_id: str):
            observer_calls.append(project_id)
        
        # Add observer
        context_manager.add_switch_observer(test_observer)
        
        # Mock registry and switch project
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            project = Mock()
            project.project_id = "test-project"
            registry.get_project.return_value = project
            mock_get_registry.return_value = registry
            
            context_manager.switch_project("test-project")
        
        assert "test-project" in observer_calls
        
        # Remove observer
        context_manager.remove_switch_observer(test_observer)
        observer_calls.clear()
        
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            project = Mock()
            project.project_id = "test-project-2"
            registry.get_project.return_value = project
            mock_get_registry.return_value = registry
            
            context_manager.switch_project("test-project-2")
        
        assert len(observer_calls) == 0
    
    def test_cleanup_orphaned_contexts(self, context_manager, temp_dir):
        """Test cleanup of orphaned context files."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            # Create mock registry with one project
            registry = Mock()
            project = Mock()
            project.project_id = "valid-project"
            registry.list_projects.return_value = [project]
            mock_get_registry.return_value = registry
            
            # Create context files (one valid, one orphaned)
            contexts_dir = temp_dir / "contexts"
            contexts_dir.mkdir(exist_ok=True)
            
            valid_file = contexts_dir / "valid-project_context.json"
            orphaned_file = contexts_dir / "orphaned-project_context.json"
            
            valid_file.write_text('{"project_id": "valid-project"}')
            orphaned_file.write_text('{"project_id": "orphaned-project"}')
            
            # Cleanup orphaned contexts
            removed_count = context_manager.cleanup_orphaned_contexts()
            
            assert removed_count == 1
            assert valid_file.exists()
            assert not orphaned_file.exists()


class TestThreadSafety:
    """Test thread safety of context manager."""
    
    @pytest.fixture
    def context_manager(self):
        """Create a context manager for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            mock_settings = Mock()
            mock_settings.data_dir = Path(temp_dir)
            
            with patch('src.codebase_gardener.core.project_context_manager.get_settings', return_value=mock_settings):
                manager = ProjectContextManager()
                yield manager
    
    def test_concurrent_project_switching(self, context_manager):
        """Test concurrent project switching."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            
            def mock_get_project(project_id):
                project = Mock()
                project.project_id = project_id
                return project
            
            registry.get_project.side_effect = mock_get_project
            mock_get_registry.return_value = registry
            
            results = []
            errors = []
            
            def switch_project(project_id):
                try:
                    result = context_manager.switch_project(project_id)
                    results.append((project_id, result))
                except Exception as e:
                    errors.append((project_id, str(e)))
            
            # Start multiple threads switching projects
            threads = []
            for i in range(5):
                thread = threading.Thread(target=switch_project, args=(f"project-{i}",))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # All switches should succeed
            assert len(results) == 5
            assert len(errors) == 0
            assert all(result for _, result in results)
    
    def test_concurrent_message_adding(self, context_manager):
        """Test concurrent message adding."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            project = Mock()
            project.project_id = "test-project"
            registry.get_project.return_value = project
            mock_get_registry.return_value = registry
            
            # Switch to project first
            context_manager.switch_project("test-project")
            
            def add_messages(thread_id):
                for i in range(10):
                    context_manager.add_message("user", f"Message {thread_id}-{i}")
            
            # Start multiple threads adding messages
            threads = []
            for i in range(3):
                thread = threading.Thread(target=add_messages, args=(i,))
                threads.append(thread)
                thread.start()
            
            # Wait for all threads to complete
            for thread in threads:
                thread.join()
            
            # Should have all messages
            history = context_manager.get_conversation_history()
            assert len(history) == 30  # 3 threads * 10 messages each


class TestGlobalContextManager:
    """Test global context manager functions."""
    
    def test_get_project_context_manager_singleton(self):
        """Test that get_project_context_manager returns singleton."""
        with patch('src.codebase_gardener.core.project_context_manager.ProjectContextManager') as mock_class:
            mock_instance = Mock()
            mock_class.return_value = mock_instance
            
            # Clear global instance
            import src.codebase_gardener.core.project_context_manager as module
            module._context_manager = None
            
            # Get manager twice
            manager1 = get_project_context_manager()
            manager2 = get_project_context_manager()
            
            # Should be same instance
            assert manager1 is manager2
            assert mock_class.call_count == 1
    
    def test_setup_context_manager_integration(self):
        """Test setting up integration with other components."""
        with patch('src.codebase_gardener.core.dynamic_model_loader.get_dynamic_model_loader') as mock_get_model_loader:
            with patch('src.codebase_gardener.core.project_context_manager.get_project_context_manager') as mock_get_context_manager:
                mock_context_manager = Mock()
                mock_model_loader = Mock()
                mock_get_context_manager.return_value = mock_context_manager
                mock_get_model_loader.return_value = mock_model_loader
                
                # Should not raise exception
                setup_context_manager_integration()
    
    def test_setup_integration_failure(self):
        """Test integration setup with failure."""
        with patch('src.codebase_gardener.core.dynamic_model_loader.get_dynamic_model_loader') as mock_get_model_loader:
            mock_get_model_loader.side_effect = Exception("Integration failed")
            
            # Should not raise exception, just log warning
            setup_context_manager_integration()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def context_manager(self, temp_dir):
        """Create a context manager for testing."""
        mock_settings = Mock()
        mock_settings.data_dir = temp_dir
        
        with patch('src.codebase_gardener.core.project_context_manager.get_settings', return_value=mock_settings):
            manager = ProjectContextManager()
            yield manager
    
    def test_corrupted_context_file_recovery(self, context_manager, temp_dir):
        """Test recovery from corrupted context file."""
        # Create corrupted context file
        contexts_dir = temp_dir / "contexts"
        contexts_dir.mkdir(exist_ok=True)
        context_file = contexts_dir / "test-project_context.json"
        context_file.write_text("invalid json content")
        
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            project = Mock()
            project.project_id = "test-project"
            registry.get_project.return_value = project
            mock_get_registry.return_value = registry
            
            # Should create new context instead of failing
            result = context_manager.switch_project("test-project")
            assert result is True
            
            # Should have empty conversation history
            history = context_manager.get_conversation_history()
            assert len(history) == 0
    
    def test_file_permission_error(self, context_manager):
        """Test handling of file permission errors."""
        with patch('src.codebase_gardener.core.project_registry.get_project_registry') as mock_get_registry:
            registry = Mock()
            project = Mock()
            project.project_id = "test-project"
            registry.get_project.return_value = project
            mock_get_registry.return_value = registry
            
            # Switch to project
            context_manager.switch_project("test-project")
            context_manager.add_message("user", "Test message")
            
            # Mock file permission error during save
            with patch('pathlib.Path.open', side_effect=PermissionError("Permission denied")):
                with pytest.raises(ContextManagerError, match="Failed to save context"):
                    context_manager.save_all_contexts()