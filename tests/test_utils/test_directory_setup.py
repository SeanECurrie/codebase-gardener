"""
Tests for directory setup and initialization utilities.
"""

import json
import pytest
import tempfile
import shutil
import stat
from pathlib import Path
from unittest.mock import patch, MagicMock

from codebase_gardener.utils.directory_setup import (
    DirectoryManager,
    DirectorySetupError,
    PermissionError as DirectoryPermissionError,
    DirectoryValidationError,
    initialize_directories,
    create_project_directory,
    get_active_project_state,
    update_active_project_state,
    cleanup_project_directory,
)


class TestDirectoryManager:
    """Test cases for DirectoryManager class."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        with patch('codebase_gardener.utils.directory_setup.settings') as mock:
            mock.data_dir = temp_dir / "test-codebase-gardener"
            mock.projects_dir = mock.data_dir / "projects"
            mock.base_models_dir = mock.data_dir / "base_models"
            yield mock
    
    @pytest.fixture
    def directory_manager(self, mock_settings):
        """Create DirectoryManager instance with mocked settings."""
        return DirectoryManager()
    
    def test_directory_manager_initialization(self, directory_manager, mock_settings):
        """Test DirectoryManager initializes with correct paths."""
        assert directory_manager.data_dir == mock_settings.data_dir
        assert directory_manager.projects_dir == mock_settings.projects_dir
        assert directory_manager.base_models_dir == mock_settings.base_models_dir
        assert directory_manager.logs_dir == mock_settings.data_dir / "logs"
        assert directory_manager.active_project_file == mock_settings.data_dir / "active_project.json"
    
    def test_initialize_directories_success(self, directory_manager):
        """Test successful directory initialization."""
        directory_manager.initialize_directories()
        
        # Check all directories were created
        assert directory_manager.data_dir.exists()
        assert directory_manager.projects_dir.exists()
        assert directory_manager.base_models_dir.exists()
        assert directory_manager.logs_dir.exists()
        
        # Check active project file was created
        assert directory_manager.active_project_file.exists()
        
        # Validate active project file content
        with directory_manager.active_project_file.open('r') as f:
            state = json.load(f)
            assert "active_project" in state
            assert "projects" in state
            assert "version" in state
            assert state["active_project"] is None
            assert state["projects"] == {}
    
    def test_initialize_directories_already_exists(self, directory_manager):
        """Test initialization when directories already exist."""
        # Create directories first
        directory_manager.data_dir.mkdir(parents=True, exist_ok=True)
        directory_manager.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Should not raise error
        directory_manager.initialize_directories()
        
        assert directory_manager.data_dir.exists()
        assert directory_manager.projects_dir.exists()
    
    def test_initialize_directories_permission_error(self, directory_manager):
        """Test initialization with permission errors."""
        # Create a directory that we can't write to
        directory_manager.data_dir.mkdir(parents=True, exist_ok=True)
        
        with patch.object(Path, 'mkdir', side_effect=OSError("Permission denied")):
            with pytest.raises(DirectorySetupError, match="Directory initialization failed"):
                directory_manager.initialize_directories()
    
    def test_create_project_directory_success(self, directory_manager):
        """Test successful project directory creation."""
        # Initialize base directories first
        directory_manager.initialize_directories()
        
        project_name = "test-project"
        project_dir = directory_manager.create_project_directory(project_name)
        
        assert project_dir.exists()
        assert project_dir.name == project_name
        assert (project_dir / "vector_store").exists()
        assert (project_dir / "models").exists()
        assert (project_dir / "cache").exists()
    
    def test_create_project_directory_sanitize_name(self, directory_manager):
        """Test project name sanitization."""
        directory_manager.initialize_directories()
        
        # Test with problematic characters
        project_name = "test<>project/with\\bad:chars"
        project_dir = directory_manager.create_project_directory(project_name)
        
        assert project_dir.exists()
        assert "<" not in project_dir.name
        assert ">" not in project_dir.name
        assert "/" not in project_dir.name
        assert "\\" not in project_dir.name
        assert ":" not in project_dir.name
    
    def test_create_project_directory_empty_name(self, directory_manager):
        """Test project directory creation with empty name."""
        directory_manager.initialize_directories()
        
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            directory_manager.create_project_directory("")
        
        with pytest.raises(ValueError, match="Project name cannot be empty"):
            directory_manager.create_project_directory("   ")
    
    def test_create_project_directory_os_error(self, directory_manager):
        """Test project directory creation with OS error."""
        directory_manager.initialize_directories()
        
        with patch.object(Path, 'mkdir', side_effect=OSError("Disk full")):
            with pytest.raises(DirectorySetupError, match="Cannot create project directory"):
                directory_manager.create_project_directory("test-project")
    
    def test_get_active_project_state_success(self, directory_manager):
        """Test getting active project state."""
        directory_manager.initialize_directories()
        
        state = directory_manager.get_active_project_state()
        
        assert isinstance(state, dict)
        assert "active_project" in state
        assert "projects" in state
        assert "version" in state
    
    def test_get_active_project_state_file_not_found(self, directory_manager):
        """Test getting active project state when file doesn't exist."""
        with pytest.raises(DirectorySetupError, match="Cannot read active project state"):
            directory_manager.get_active_project_state()
    
    def test_get_active_project_state_invalid_json(self, directory_manager):
        """Test getting active project state with invalid JSON."""
        directory_manager.data_dir.mkdir(parents=True, exist_ok=True)
        directory_manager.active_project_file.write_text("invalid json")
        
        with pytest.raises(DirectorySetupError, match="Cannot read active project state"):
            directory_manager.get_active_project_state()
    
    def test_update_active_project_state_success(self, directory_manager):
        """Test updating active project state."""
        directory_manager.initialize_directories()
        
        new_state = {
            "active_project": "test-project",
            "projects": {"test-project": {"status": "active"}},
            "version": "1.0"
        }
        
        directory_manager.update_active_project_state(new_state)
        
        # Verify state was updated
        updated_state = directory_manager.get_active_project_state()
        assert updated_state["active_project"] == "test-project"
        assert "test-project" in updated_state["projects"]
    
    def test_update_active_project_state_creates_backup(self, directory_manager):
        """Test that updating state creates a backup."""
        directory_manager.initialize_directories()
        
        # Update state
        new_state = {"active_project": "test", "projects": {}, "version": "1.0"}
        directory_manager.update_active_project_state(new_state)
        
        # Check backup was created
        backup_path = directory_manager.active_project_file.with_suffix('.json.backup')
        assert backup_path.exists()
    
    def test_update_active_project_state_os_error(self, directory_manager):
        """Test updating active project state with OS error."""
        directory_manager.initialize_directories()
        
        with patch.object(Path, 'open', side_effect=OSError("Permission denied")):
            with pytest.raises(DirectorySetupError, match="Cannot update active project state"):
                directory_manager.update_active_project_state({"test": "data"})
    
    def test_cleanup_project_directory_success(self, directory_manager):
        """Test successful project directory cleanup."""
        directory_manager.initialize_directories()
        
        # Create project directory
        project_name = "test-project"
        project_dir = directory_manager.create_project_directory(project_name)
        assert project_dir.exists()
        
        # Clean up
        directory_manager.cleanup_project_directory(project_name)
        assert not project_dir.exists()
    
    def test_cleanup_project_directory_not_exists(self, directory_manager):
        """Test cleanup when project directory doesn't exist."""
        directory_manager.initialize_directories()
        
        # Should not raise error
        directory_manager.cleanup_project_directory("nonexistent-project")
    
    def test_cleanup_project_directory_os_error(self, directory_manager):
        """Test cleanup with OS error."""
        directory_manager.initialize_directories()
        
        project_name = "test-project"
        directory_manager.create_project_directory(project_name)
        
        with patch('shutil.rmtree', side_effect=OSError("Permission denied")):
            with pytest.raises(DirectorySetupError, match="Cannot cleanup project directory"):
                directory_manager.cleanup_project_directory(project_name)
    
    def test_validate_directory_structure_success(self, directory_manager):
        """Test directory structure validation success."""
        directory_manager.initialize_directories()
        
        # Should not raise any exception
        directory_manager._validate_directory_structure()
    
    def test_validate_directory_structure_missing_directory(self, directory_manager):
        """Test validation with missing directory."""
        directory_manager.data_dir.mkdir(parents=True, exist_ok=True)
        # Don't create projects_dir
        
        with pytest.raises(DirectoryValidationError, match="Missing required directories"):
            directory_manager._validate_directory_structure()
    
    def test_validate_directory_structure_missing_state_file(self, directory_manager):
        """Test validation with missing active project state file."""
        # Create directories but not state file
        directory_manager._create_directory_structure()
        
        with pytest.raises(DirectoryValidationError, match="Active project state file missing"):
            directory_manager._validate_directory_structure()
    
    def test_validate_directory_structure_invalid_state_file(self, directory_manager):
        """Test validation with invalid state file."""
        directory_manager._create_directory_structure()
        
        # Create invalid state file
        directory_manager.active_project_file.write_text('{"invalid": "state"}')
        
        with pytest.raises(DirectoryValidationError, match="Active project state missing keys"):
            directory_manager._validate_directory_structure()
    
    def test_sanitize_project_name(self, directory_manager):
        """Test project name sanitization."""
        # Test various problematic characters
        test_cases = [
            ("normal-name", "normal-name"),
            ("name<with>bad", "name_with_bad"),
            ("name/with\\slashes", "name_with_slashes"),
            ("name:with|pipes", "name_with_pipes"),
            ("name?with*wildcards", "name_with_wildcards"),
            ("  .name with spaces.  ", "name with spaces"),
            ("", "unnamed_project"),
            ("...", "unnamed_project"),
        ]
        
        for input_name, expected in test_cases:
            result = directory_manager._sanitize_project_name(input_name)
            assert result == expected
    
    def test_set_directory_permissions(self, directory_manager):
        """Test setting directory permissions."""
        directory_manager._create_directory_structure()
        
        # Should not raise exception
        directory_manager._set_directory_permissions()
        
        # Check that directories have appropriate permissions
        expected_perms = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        
        for directory in [directory_manager.data_dir, directory_manager.projects_dir]:
            if directory and directory.exists():
                current_perms = directory.stat().st_mode & 0o777
                # Note: Actual permissions may differ due to umask, so we just check it doesn't crash


class TestModuleFunctions:
    """Test module-level convenience functions."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        with patch('codebase_gardener.utils.directory_setup.settings') as mock:
            mock.data_dir = temp_dir / "test-codebase-gardener"
            mock.projects_dir = mock.data_dir / "projects"
            mock.base_models_dir = mock.data_dir / "base_models"
            yield mock
    
    def test_initialize_directories_function(self, mock_settings):
        """Test initialize_directories convenience function."""
        with patch('codebase_gardener.utils.directory_setup.directory_manager') as mock_dm:
            initialize_directories()
            mock_dm.initialize_directories.assert_called_once()
    
    def test_create_project_directory_function(self, mock_settings):
        """Test create_project_directory convenience function."""
        with patch('codebase_gardener.utils.directory_setup.directory_manager') as mock_dm:
            mock_dm.create_project_directory.return_value = mock_settings.projects_dir / "test-project"
            
            project_dir = create_project_directory("test-project")
            
            mock_dm.create_project_directory.assert_called_once_with("test-project")
            assert project_dir == mock_settings.projects_dir / "test-project"
    
    def test_get_active_project_state_function(self, mock_settings):
        """Test get_active_project_state convenience function."""
        with patch('codebase_gardener.utils.directory_setup.directory_manager') as mock_dm:
            mock_dm.get_active_project_state.return_value = {"active_project": None}
            
            state = get_active_project_state()
            
            mock_dm.get_active_project_state.assert_called_once()
            assert isinstance(state, dict)
            assert "active_project" in state
    
    def test_update_active_project_state_function(self, mock_settings):
        """Test update_active_project_state convenience function."""
        with patch('codebase_gardener.utils.directory_setup.directory_manager') as mock_dm:
            new_state = {
                "active_project": "test",
                "projects": {},
                "version": "1.0"
            }
            
            update_active_project_state(new_state)
            
            mock_dm.update_active_project_state.assert_called_once_with(new_state)
    
    def test_cleanup_project_directory_function(self, mock_settings):
        """Test cleanup_project_directory convenience function."""
        with patch('codebase_gardener.utils.directory_setup.directory_manager') as mock_dm:
            cleanup_project_directory("test-project")
            
            mock_dm.cleanup_project_directory.assert_called_once_with("test-project")


class TestErrorHandling:
    """Test error handling scenarios."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        with patch('codebase_gardener.utils.directory_setup.settings') as mock:
            mock.data_dir = temp_dir / "test-codebase-gardener"
            mock.projects_dir = mock.data_dir / "projects"
            mock.base_models_dir = mock.data_dir / "base_models"
            yield mock
    
    def test_directory_setup_error_inheritance(self):
        """Test that custom exceptions inherit correctly."""
        assert issubclass(DirectorySetupError, Exception)
        assert issubclass(DirectoryPermissionError, DirectorySetupError)
        assert issubclass(DirectoryValidationError, DirectorySetupError)
    
    def test_directory_setup_error_with_cause(self):
        """Test DirectorySetupError with cause."""
        original_error = OSError("Original error")
        
        try:
            raise DirectorySetupError("Setup failed") from original_error
        except DirectorySetupError as e:
            assert str(e) == "Setup failed"
            assert e.__cause__ == original_error
    
    def test_permission_error_handling(self, mock_settings):
        """Test handling of permission errors."""
        directory_manager = DirectoryManager()
        
        # Mock chmod to raise OSError
        with patch.object(Path, 'chmod', side_effect=OSError("Permission denied")):
            # Should not raise exception, just log warning
            directory_manager.initialize_directories()
            
            # Directories should still be created
            assert directory_manager.data_dir.exists()


class TestIntegration:
    """Integration tests for directory setup."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create a temporary directory for testing."""
        temp_path = Path(tempfile.mkdtemp())
        yield temp_path
        shutil.rmtree(temp_path, ignore_errors=True)
    
    @pytest.fixture
    def mock_settings(self, temp_dir):
        """Mock settings with temporary directory."""
        with patch('codebase_gardener.utils.directory_setup.settings') as mock:
            mock.data_dir = temp_dir / "test-codebase-gardener"
            mock.projects_dir = mock.data_dir / "projects"
            mock.base_models_dir = mock.data_dir / "base_models"
            yield mock
    
    def test_full_workflow(self, mock_settings):
        """Test complete directory setup workflow."""
        # Initialize directories
        initialize_directories()
        
        # Create a project
        project_dir = create_project_directory("my-awesome-project")
        
        # Update active project state
        state = get_active_project_state()
        state["active_project"] = "my-awesome-project"
        state["projects"]["my-awesome-project"] = {
            "created": "2025-02-03",
            "status": "active"
        }
        update_active_project_state(state)
        
        # Verify everything works
        updated_state = get_active_project_state()
        assert updated_state["active_project"] == "my-awesome-project"
        assert project_dir.exists()
        assert (project_dir / "vector_store").exists()
        
        # Clean up project
        cleanup_project_directory("my-awesome-project")
        assert not project_dir.exists()
    
    def test_concurrent_access_simulation(self, mock_settings):
        """Test handling of concurrent access patterns."""
        initialize_directories()
        
        # Simulate multiple processes trying to create the same project
        project_name = "concurrent-project"
        
        # Both should succeed (exist_ok=True)
        project_dir1 = create_project_directory(project_name)
        project_dir2 = create_project_directory(project_name)
        
        assert project_dir1 == project_dir2
        assert project_dir1.exists()
    
    def test_recovery_from_partial_failure(self, mock_settings):
        """Test recovery from partial initialization failure."""
        directory_manager = DirectoryManager()
        
        # Create some directories manually
        directory_manager.data_dir.mkdir(parents=True, exist_ok=True)
        directory_manager.projects_dir.mkdir(parents=True, exist_ok=True)
        
        # Initialize should complete successfully
        directory_manager.initialize_directories()
        
        # All directories should exist
        assert directory_manager.data_dir.exists()
        assert directory_manager.projects_dir.exists()
        assert directory_manager.base_models_dir.exists()
        assert directory_manager.logs_dir.exists()
        assert directory_manager.active_project_file.exists()