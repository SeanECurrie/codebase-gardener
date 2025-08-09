"""
Tests for project-specific vector store management.

This module tests the ProjectVectorStoreManager class and related functionality
for managing separate LanceDB vector stores per project with data isolation.
"""

import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

import pytest
from codebase_gardener.core.project_registry import ProjectMetadata, TrainingStatus
from codebase_gardener.data.project_vector_store import (
    ProjectVectorStoreInfo,
    ProjectVectorStoreManager,
    get_project_vector_store_manager,
    reset_project_vector_store_manager,
)
from codebase_gardener.data.vector_store import VectorStore


class TestProjectVectorStoreInfo:
    """Test ProjectVectorStoreInfo data class."""

    def test_creation(self):
        """Test creating ProjectVectorStoreInfo."""
        mock_vector_store = Mock(spec=VectorStore)
        now = datetime.now()

        info = ProjectVectorStoreInfo(
            project_id="test-project",
            table_name="project_test_project",
            vector_store=mock_vector_store,
            last_accessed=now,
            chunk_count=10
        )

        assert info.project_id == "test-project"
        assert info.table_name == "project_test_project"
        assert info.vector_store == mock_vector_store
        assert info.last_accessed == now
        assert info.chunk_count == 10
        assert info.health_status == "healthy"

    def test_to_dict(self):
        """Test converting ProjectVectorStoreInfo to dictionary."""
        mock_vector_store = Mock(spec=VectorStore)
        now = datetime.now()

        info = ProjectVectorStoreInfo(
            project_id="test-project",
            table_name="project_test_project",
            vector_store=mock_vector_store,
            last_accessed=now,
            chunk_count=10,
            health_status="degraded"
        )

        result = info.to_dict()

        assert result["project_id"] == "test-project"
        assert result["table_name"] == "project_test_project"
        assert result["last_accessed"] == now.isoformat()
        assert result["chunk_count"] == 10
        assert result["health_status"] == "degraded"


class TestProjectVectorStoreManager:
    """Test ProjectVectorStoreManager class."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        mock_settings = Mock()
        mock_settings.data_dir = temp_dir
        return mock_settings

    @pytest.fixture
    def mock_project_registry(self):
        """Mock project registry."""
        mock_registry = Mock()

        # Create sample project metadata
        project = ProjectMetadata(
            project_id="test-project",
            name="Test Project",
            source_path=Path("/test/path"),
            created_at=datetime.now(),
            training_status=TrainingStatus.COMPLETED
        )

        mock_registry.get_project.return_value = project
        return mock_registry

    @pytest.fixture
    def manager(self, mock_settings, mock_project_registry):
        """Create ProjectVectorStoreManager with mocked dependencies."""
        with patch('codebase_gardener.data.project_vector_store.get_settings', return_value=mock_settings):
            with patch('codebase_gardener.data.project_vector_store.get_project_registry', return_value=mock_project_registry):
                return ProjectVectorStoreManager(max_cache_size=2)

    def test_initialization(self, manager, mock_settings):
        """Test manager initialization."""
        assert manager.settings == mock_settings
        assert manager._max_cache_size == 2
        assert len(manager._vector_store_cache) == 0
        assert manager._active_project_id is None
        assert manager._active_vector_store is None
        assert manager.db_path == mock_settings.data_dir / "vector_stores"

    def test_get_table_name(self, manager):
        """Test table name generation."""
        assert manager._get_table_name("test-project") == "project_test_project"
        assert manager._get_table_name("my project") == "project_my_project"
        assert manager._get_table_name("test_project") == "project_test_project"


class TestBasicFunctionality:
    """Test basic functionality with simpler test cases."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        mock_settings = Mock()
        mock_settings.data_dir = temp_dir
        return mock_settings

    @pytest.fixture
    def mock_project_registry(self):
        """Mock project registry."""
        mock_registry = Mock()

        # Create sample project metadata
        project = ProjectMetadata(
            project_id="test-project",
            name="Test Project",
            source_path=Path("/test/path"),
            created_at=datetime.now(),
            training_status=TrainingStatus.COMPLETED
        )

        mock_registry.get_project.return_value = project
        return mock_registry

    @pytest.fixture
    def manager(self, mock_settings, mock_project_registry):
        """Create ProjectVectorStoreManager with mocked dependencies."""
        with patch('codebase_gardener.data.project_vector_store.get_settings', return_value=mock_settings):
            with patch('codebase_gardener.data.project_vector_store.get_project_registry', return_value=mock_project_registry):
                return ProjectVectorStoreManager(max_cache_size=2)

    def test_basic_operations(self, manager):
        """Test basic manager operations."""
        # Test active project management
        assert manager.get_active_project_id() is None
        assert manager.get_active_vector_store() is None

        # Test table name generation
        assert manager._get_table_name("test-project") == "project_test_project"

    def test_close_all(self, manager):
        """Test closing all vector stores."""
        # Add mock projects to cache
        mock_vs1 = Mock(spec=VectorStore)
        mock_vs2 = Mock(spec=VectorStore)

        manager._vector_store_cache["project1"] = ProjectVectorStoreInfo(
            "project1", "table1", mock_vs1, datetime.now(), 10
        )
        manager._vector_store_cache["project2"] = ProjectVectorStoreInfo(
            "project2", "table2", mock_vs2, datetime.now(), 20
        )

        manager._active_project_id = "project1"
        manager._active_vector_store = mock_vs1

        # Close all
        manager.close_all()

        # Verify
        assert len(manager._vector_store_cache) == 0
        assert manager._active_project_id is None
        assert manager._active_vector_store is None
        assert manager.db is None

        # Verify vector stores were closed
        mock_vs1.close.assert_called_once()
        mock_vs2.close.assert_called_once()


class TestGlobalManagerFunctions:
    """Test global manager instance functions."""

    def teardown_method(self):
        """Reset global manager after each test."""
        reset_project_vector_store_manager()

    @patch('codebase_gardener.data.project_vector_store.get_settings')
    @patch('codebase_gardener.data.project_vector_store.get_project_registry')
    def test_get_project_vector_store_manager_singleton(self, mock_registry, mock_settings):
        """Test singleton behavior of global manager."""
        mock_settings.return_value.data_dir = Path("/tmp")
        mock_registry.return_value = Mock()

        # Get manager twice
        manager1 = get_project_vector_store_manager()
        manager2 = get_project_vector_store_manager()

        # Should be the same instance
        assert manager1 is manager2

    def test_reset_project_vector_store_manager(self):
        """Test resetting global manager."""
        with patch('codebase_gardener.data.project_vector_store.get_settings'):
            with patch('codebase_gardener.data.project_vector_store.get_project_registry'):
                # Get manager
                manager1 = get_project_vector_store_manager()

                # Reset
                reset_project_vector_store_manager()

                # Get manager again
                manager2 = get_project_vector_store_manager()

                # Should be different instances
                assert manager1 is not manager2
