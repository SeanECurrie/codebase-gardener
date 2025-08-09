"""
Tests for the Project Registry System

This module contains comprehensive tests for the project registry functionality,
including unit tests, integration tests, and error scenario testing.
"""

import shutil
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
from codebase_gardener.core.project_registry import (
    ProjectMetadata,
    ProjectRegistry,
    ProjectRegistryError,
    RegistryData,
    TrainingStatus,
    get_project_registry,
)
from codebase_gardener.utils.error_handling import StorageError
from pydantic import ValidationError


class TestProjectMetadata:
    """Test the ProjectMetadata model."""

    def test_project_metadata_creation(self):
        """Test creating a valid ProjectMetadata instance."""
        source_path = Path("/tmp/test-project")
        metadata = ProjectMetadata(
            project_id="test-id",
            name="Test Project",
            source_path=source_path,
            language="python"
        )

        assert metadata.project_id == "test-id"
        assert metadata.name == "Test Project"
        assert metadata.source_path == source_path
        assert metadata.language == "python"
        assert metadata.training_status == TrainingStatus.NOT_STARTED
        assert isinstance(metadata.created_at, datetime)
        assert isinstance(metadata.last_updated, datetime)

    def test_project_metadata_path_conversion(self):
        """Test that string paths are converted to Path objects."""
        metadata = ProjectMetadata(
            project_id="test-id",
            name="Test Project",
            source_path="/tmp/test-project",  # String path
            lora_adapter_path="/tmp/adapter.bin"  # String path
        )

        assert isinstance(metadata.source_path, Path)
        assert isinstance(metadata.lora_adapter_path, Path)
        assert str(metadata.source_path) == "/tmp/test-project"

    def test_project_metadata_name_validation(self):
        """Test project name validation."""
        # Empty name should fail
        with pytest.raises(ValidationError):
            ProjectMetadata(
                project_id="test-id",
                name="",
                source_path="/tmp/test"
            )

        # Whitespace-only name should fail
        with pytest.raises(ValidationError):
            ProjectMetadata(
                project_id="test-id",
                name="   ",
                source_path="/tmp/test"
            )

        # Invalid characters should fail
        with pytest.raises(ValidationError):
            ProjectMetadata(
                project_id="test-id",
                name="Test<Project>",
                source_path="/tmp/test"
            )

    def test_update_timestamp(self):
        """Test updating the timestamp."""
        metadata = ProjectMetadata(
            project_id="test-id",
            name="Test Project",
            source_path="/tmp/test"
        )

        original_time = metadata.last_updated
        # Small delay to ensure timestamp difference
        import time
        time.sleep(0.01)

        metadata.update_timestamp()
        assert metadata.last_updated > original_time


class TestTrainingStatus:
    """Test the TrainingStatus enum."""

    def test_training_status_values(self):
        """Test all training status values."""
        assert TrainingStatus.NOT_STARTED == "not_started"
        assert TrainingStatus.TRAINING == "training"
        assert TrainingStatus.COMPLETED == "completed"
        assert TrainingStatus.FAILED == "failed"

    def test_training_status_in_metadata(self):
        """Test using TrainingStatus in ProjectMetadata."""
        metadata = ProjectMetadata(
            project_id="test-id",
            name="Test Project",
            source_path="/tmp/test",
            training_status=TrainingStatus.TRAINING
        )

        assert metadata.training_status == TrainingStatus.TRAINING


class TestRegistryData:
    """Test the RegistryData model."""

    def test_registry_data_creation(self):
        """Test creating a RegistryData instance."""
        data = RegistryData()

        assert data.version == "1.0"
        assert data.projects == {}
        assert data.active_project is None

    def test_registry_data_with_projects(self):
        """Test RegistryData with projects."""
        metadata = ProjectMetadata(
            project_id="test-id",
            name="Test Project",
            source_path="/tmp/test"
        )

        data = RegistryData(
            projects={"test-id": metadata},
            active_project="test-id"
        )

        assert len(data.projects) == 1
        assert data.active_project == "test-id"
        assert data.projects["test-id"] == metadata


class TestProjectRegistry:
    """Test the ProjectRegistry class."""

    @pytest.fixture
    def temp_registry_dir(self):
        """Create a temporary directory for registry testing."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)

    @pytest.fixture
    def temp_source_dir(self):
        """Create a temporary source directory."""
        temp_dir = Path(tempfile.mkdtemp())
        # Create some dummy files
        (temp_dir / "main.py").write_text("print('hello')")
        (temp_dir / "README.md").write_text("# Test Project")
        yield temp_dir
        # Robust cleanup that handles already-removed directories
        try:
            if temp_dir.exists():
                shutil.rmtree(temp_dir)
        except (FileNotFoundError, OSError):
            # Directory was already removed or inaccessible
            pass

    @pytest.fixture
    def registry(self, temp_registry_dir):
        """Create a ProjectRegistry instance with temporary directory."""
        registry_file = temp_registry_dir / "registry.json"
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = temp_registry_dir
            return ProjectRegistry(registry_file)

    def test_registry_initialization(self, temp_registry_dir):
        """Test registry initialization."""
        registry_file = temp_registry_dir / "registry.json"
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = temp_registry_dir
            registry = ProjectRegistry(registry_file)

        assert registry.registry_file == registry_file
        assert registry.get_project_count() == 0
        assert registry.get_active_project() is None

    def test_register_project_success(self, registry, temp_source_dir):
        """Test successful project registration."""
        project_id = registry.register_project(
            name="Test Project",
            source_path=temp_source_dir,
            language="python"
        )

        assert project_id is not None
        assert len(project_id) == 36  # UUID4 length

        project = registry.get_project(project_id)
        assert project is not None
        assert project.name == "Test Project"
        assert project.source_path == temp_source_dir
        assert project.language == "python"
        assert project.training_status == TrainingStatus.NOT_STARTED

        # Should be set as active project (first one)
        assert registry.get_active_project() == project_id

    def test_register_project_duplicate_name(self, registry, temp_source_dir):
        """Test registering project with duplicate name."""
        registry.register_project("Test Project", temp_source_dir)

        with pytest.raises(ProjectRegistryError, match="already exists"):
            registry.register_project("Test Project", temp_source_dir)

    def test_register_project_invalid_source_path(self, registry):
        """Test registering project with invalid source path."""
        invalid_path = Path("/nonexistent/path")

        with pytest.raises(ProjectRegistryError, match="does not exist"):
            registry.register_project("Test Project", invalid_path)

    def test_register_project_empty_name(self, registry, temp_source_dir):
        """Test registering project with empty name."""
        with pytest.raises(ProjectRegistryError, match="cannot be empty"):
            registry.register_project("", temp_source_dir)

    def test_get_project_not_found(self, registry):
        """Test getting a non-existent project."""
        result = registry.get_project("nonexistent-id")
        assert result is None

    def test_list_projects(self, registry, temp_source_dir):
        """Test listing all projects."""
        # Initially empty
        projects = registry.list_projects()
        assert len(projects) == 0

        # Add some projects
        id1 = registry.register_project("Project 1", temp_source_dir)
        id2 = registry.register_project("Project 2", temp_source_dir)

        projects = registry.list_projects()
        assert len(projects) == 2

        project_names = {p.name for p in projects}
        assert project_names == {"Project 1", "Project 2"}

    def test_update_project_status(self, registry, temp_source_dir):
        """Test updating project training status."""
        project_id = registry.register_project("Test Project", temp_source_dir)

        # Update status
        registry.update_project_status(project_id, TrainingStatus.TRAINING)

        project = registry.get_project(project_id)
        assert project.training_status == TrainingStatus.TRAINING

    def test_update_project_status_not_found(self, registry):
        """Test updating status of non-existent project."""
        with pytest.raises(ProjectRegistryError, match="not found"):
            registry.update_project_status("nonexistent", TrainingStatus.TRAINING)

    def test_update_project_metadata(self, registry, temp_source_dir):
        """Test updating project metadata."""
        project_id = registry.register_project("Test Project", temp_source_dir)

        registry.update_project_metadata(project_id, file_count=150, language="typescript")

        project = registry.get_project(project_id)
        assert project.file_count == 150
        assert project.language == "typescript"

    def test_update_project_metadata_not_found(self, registry):
        """Test updating metadata of non-existent project."""
        with pytest.raises(ProjectRegistryError, match="not found"):
            registry.update_project_metadata("nonexistent", file_count=100)

    def test_remove_project(self, registry, temp_source_dir):
        """Test removing a project."""
        project_id = registry.register_project("Test Project", temp_source_dir)

        # Verify project exists
        assert registry.get_project(project_id) is not None
        assert registry.get_project_count() == 1

        # Remove project
        registry.remove_project(project_id)

        # Verify project is gone
        assert registry.get_project(project_id) is None
        assert registry.get_project_count() == 0

    def test_remove_project_not_found(self, registry):
        """Test removing non-existent project."""
        with pytest.raises(ProjectRegistryError, match="not found"):
            registry.remove_project("nonexistent")

    def test_remove_active_project(self, registry, temp_source_dir):
        """Test removing the active project."""
        id1 = registry.register_project("Project 1", temp_source_dir)
        id2 = registry.register_project("Project 2", temp_source_dir)

        # Set first project as active
        registry.set_active_project(id1)
        assert registry.get_active_project() == id1

        # Remove active project
        registry.remove_project(id1)

        # Active project should switch to remaining project
        assert registry.get_active_project() == id2

    def test_set_active_project(self, registry, temp_source_dir):
        """Test setting active project."""
        id1 = registry.register_project("Project 1", temp_source_dir)
        id2 = registry.register_project("Project 2", temp_source_dir)

        # Initially first project should be active
        assert registry.get_active_project() == id1

        # Change active project
        registry.set_active_project(id2)
        assert registry.get_active_project() == id2

    def test_set_active_project_not_found(self, registry):
        """Test setting non-existent project as active."""
        with pytest.raises(ProjectRegistryError, match="not found"):
            registry.set_active_project("nonexistent")

    def test_get_projects_by_status(self, registry, temp_source_dir):
        """Test filtering projects by status."""
        id1 = registry.register_project("Project 1", temp_source_dir)
        id2 = registry.register_project("Project 2", temp_source_dir)
        id3 = registry.register_project("Project 3", temp_source_dir)

        # Update statuses
        registry.update_project_status(id1, TrainingStatus.TRAINING)
        registry.update_project_status(id2, TrainingStatus.COMPLETED)
        # id3 remains NOT_STARTED

        # Test filtering
        training_projects = registry.get_projects_by_status(TrainingStatus.TRAINING)
        assert len(training_projects) == 1
        assert training_projects[0].project_id == id1

        completed_projects = registry.get_projects_by_status(TrainingStatus.COMPLETED)
        assert len(completed_projects) == 1
        assert completed_projects[0].project_id == id2

        not_started_projects = registry.get_projects_by_status(TrainingStatus.NOT_STARTED)
        assert len(not_started_projects) == 1
        assert not_started_projects[0].project_id == id3

    def test_validate_registry(self, registry, temp_source_dir):
        """Test registry validation."""
        # Valid registry should have no issues
        issues = registry.validate_registry()
        assert len(issues) == 0

        # Add a project
        project_id = registry.register_project("Test Project", temp_source_dir)
        issues = registry.validate_registry()
        assert len(issues) == 0

        # Create a copy of the source directory path for validation
        source_path_copy = temp_source_dir

        # Simulate missing source directory by removing it
        # Note: We need to be careful here as the fixture cleanup might interfere
        try:
            shutil.rmtree(temp_source_dir)
            issues = registry.validate_registry()
            assert len(issues) == 1
            assert "source path no longer exists" in issues[0]
        except FileNotFoundError:
            # Directory was already removed, which is fine for this test
            issues = registry.validate_registry()
            assert len(issues) == 1
            assert "source path no longer exists" in issues[0]

    def test_registry_persistence(self, temp_registry_dir, temp_source_dir):
        """Test that registry data persists across instances."""
        registry_file = temp_registry_dir / "registry.json"

        # Create first registry instance and add project
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = temp_registry_dir
            registry1 = ProjectRegistry(registry_file)
            project_id = registry1.register_project("Test Project", temp_source_dir)

        # Create second registry instance
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = temp_registry_dir
            registry2 = ProjectRegistry(registry_file)

        # Project should still exist
        project = registry2.get_project(project_id)
        assert project is not None
        assert project.name == "Test Project"

    def test_registry_corrupted_file_recovery(self, temp_registry_dir):
        """Test recovery from corrupted registry file."""
        registry_file = temp_registry_dir / "registry.json"

        # Create corrupted JSON file
        registry_file.write_text("{ invalid json }")

        # Registry should start with empty data and backup corrupted file
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = temp_registry_dir
            registry = ProjectRegistry(registry_file)

        assert registry.get_project_count() == 0

        # Backup file should exist
        backup_file = registry_file.with_suffix('.backup')
        assert backup_file.exists()

    def test_atomic_file_operations(self, registry, temp_source_dir):
        """Test that file operations are atomic."""
        # Mock file operations to simulate failure
        with patch('pathlib.Path.open', side_effect=OSError("Disk full")):
            with pytest.raises(StorageError):
                registry.register_project("Test Project", temp_source_dir)

        # Registry should still be in consistent state
        assert registry.get_project_count() == 0

    def test_thread_safety(self, registry, temp_source_dir):
        """Test thread safety of registry operations."""
        import threading

        results = []
        errors = []

        def register_project(i):
            try:
                project_id = registry.register_project(f"Project {i}", temp_source_dir)
                results.append(project_id)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=register_project, args=(i,))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # Should have 5 successful registrations, no errors
        assert len(results) == 5
        assert len(errors) == 0
        assert registry.get_project_count() == 5


class TestGlobalRegistry:
    """Test the global registry singleton."""

    def test_get_project_registry_singleton(self):
        """Test that get_project_registry returns the same instance."""
        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = Path("/tmp")

            registry1 = get_project_registry()
            registry2 = get_project_registry()

            assert registry1 is registry2

    def test_get_project_registry_thread_safety(self):
        """Test thread safety of singleton creation."""
        import threading

        instances = []

        def get_instance():
            with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
                mock_settings.data_dir = Path("/tmp")
                instances.append(get_project_registry())

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=get_instance)
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for completion
        for thread in threads:
            thread.join()

        # All instances should be the same
        assert len(set(id(instance) for instance in instances)) == 1


class TestIntegration:
    """Integration tests for the project registry."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace with multiple projects."""
        workspace = Path(tempfile.mkdtemp())

        # Create multiple source directories
        projects = {}
        for i in range(3):
            project_dir = workspace / f"project_{i}"
            project_dir.mkdir()
            (project_dir / "main.py").write_text(f"# Project {i}")
            (project_dir / "README.md").write_text(f"# Project {i}")
            projects[f"project_{i}"] = project_dir

        yield workspace, projects
        shutil.rmtree(workspace)

    def test_full_project_lifecycle(self, temp_workspace):
        """Test complete project lifecycle."""
        workspace, projects = temp_workspace
        registry_dir = workspace / "registry"
        registry_dir.mkdir()

        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = registry_dir
            registry = ProjectRegistry()

        # Register multiple projects
        project_ids = []
        for name, path in projects.items():
            project_id = registry.register_project(name.replace('_', ' ').title(), path)
            project_ids.append(project_id)

        assert registry.get_project_count() == 3

        # Update training statuses
        registry.update_project_status(project_ids[0], TrainingStatus.TRAINING)
        registry.update_project_status(project_ids[1], TrainingStatus.COMPLETED)

        # Test filtering
        training_projects = registry.get_projects_by_status(TrainingStatus.TRAINING)
        assert len(training_projects) == 1

        completed_projects = registry.get_projects_by_status(TrainingStatus.COMPLETED)
        assert len(completed_projects) == 1

        # Test active project management
        registry.set_active_project(project_ids[1])
        assert registry.get_active_project() == project_ids[1]

        # Remove a project
        registry.remove_project(project_ids[2])
        assert registry.get_project_count() == 2

        # Validate registry
        issues = registry.validate_registry()
        assert len(issues) == 0

    def test_registry_recovery_scenarios(self, temp_workspace):
        """Test various recovery scenarios."""
        workspace, projects = temp_workspace
        registry_dir = workspace / "registry"
        registry_dir.mkdir()
        registry_file = registry_dir / "registry.json"

        with patch('codebase_gardener.core.project_registry.settings') as mock_settings:
            mock_settings.data_dir = registry_dir

            # Test with missing registry file
            registry1 = ProjectRegistry(registry_file)
            assert registry1.get_project_count() == 0

            # Add a project
            project_id = registry1.register_project("Test Project", list(projects.values())[0])
            assert registry1.get_project_count() == 1

            # Test loading existing registry
            registry2 = ProjectRegistry(registry_file)
            assert registry2.get_project_count() == 1
            assert registry2.get_project(project_id) is not None

            # Test with corrupted registry
            registry_file.write_text("corrupted data")
            registry3 = ProjectRegistry(registry_file)
            assert registry3.get_project_count() == 0

            # Backup should exist
            backup_file = registry_file.with_suffix('.backup')
            assert backup_file.exists()
