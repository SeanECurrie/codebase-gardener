"""
Tests for project selector component.

This module tests the project selector functionality including
project choice generation, status indicators, and UI updates.
"""

from datetime import datetime
from pathlib import Path
from unittest.mock import Mock, patch

from src.codebase_gardener.core.project_registry import TrainingStatus
from src.codebase_gardener.ui.project_selector import (
    ProjectSelector,
    get_project_choices,
    get_project_info,
    get_project_selector,
    refresh_project_choices,
    update_project_status,
)


class TestProjectSelector:
    """Test ProjectSelector class functionality."""

    @patch('src.codebase_gardener.ui.project_selector.get_project_registry')
    def test_initialization_success(self, mock_get_registry):
        """Test successful ProjectSelector initialization."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        selector = ProjectSelector()

        assert selector.project_registry == mock_registry
        mock_get_registry.assert_called_once()

    @patch('src.codebase_gardener.ui.project_selector.get_project_registry')
    def test_initialization_failure(self, mock_get_registry):
        """Test ProjectSelector initialization failure."""
        mock_get_registry.side_effect = Exception("Registry error")

        selector = ProjectSelector()

        assert selector.project_registry is None

    def test_get_status_icon(self):
        """Test status icon generation."""
        selector = ProjectSelector()

        assert selector._get_status_icon(TrainingStatus.COMPLETED) == "🟢"
        assert selector._get_status_icon(TrainingStatus.TRAINING) == "🟡"
        assert selector._get_status_icon(TrainingStatus.NOT_STARTED) == "⚪"
        assert selector._get_status_icon(TrainingStatus.FAILED) == "🔴"

    def test_get_project_choices_no_registry(self):
        """Test getting project choices when registry is not available."""
        selector = ProjectSelector()
        selector.project_registry = None

        choices = selector.get_project_choices()

        assert choices == [("⚠️ Registry not available", "")]

    def test_get_project_choices_no_projects(self):
        """Test getting project choices when no projects exist."""
        mock_registry = Mock()
        mock_registry.list_projects.return_value = []

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        choices = selector.get_project_choices()

        assert choices == [("📝 No projects found - Add a project to get started", "")]

    def test_get_project_choices_with_projects(self):
        """Test getting project choices with available projects."""
        # Create mock projects
        project1 = Mock()
        project1.name = "Alpha Project"
        project1.project_id = "alpha"
        project1.training_status = TrainingStatus.COMPLETED

        project2 = Mock()
        project2.name = "Beta Project"
        project2.project_id = "beta"
        project2.training_status = TrainingStatus.TRAINING

        project3 = Mock()
        project3.name = "Gamma Project"
        project3.project_id = "gamma"
        project3.training_status = TrainingStatus.FAILED

        mock_registry = Mock()
        mock_registry.list_projects.return_value = [project2, project3, project1]  # Unsorted

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        choices = selector.get_project_choices()

        assert len(choices) == 3
        # Should be sorted with completed first, then by name
        assert choices[0] == ("🟢 Alpha Project", "alpha")
        assert choices[1] == ("🟡 Beta Project", "beta")
        assert choices[2] == ("🔴 Gamma Project", "gamma")

    def test_get_project_choices_error(self):
        """Test getting project choices when an error occurs."""
        mock_registry = Mock()
        mock_registry.list_projects.side_effect = Exception("Registry error")

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        choices = selector.get_project_choices()

        assert choices == [("❌ Error loading projects", "")]

    def test_get_project_info_no_project(self):
        """Test getting project info when no project is selected."""
        selector = ProjectSelector()

        info = selector.get_project_info("")

        assert info["exists"] is False
        assert info["details"] == "No project selected"

    def test_get_project_info_no_registry(self):
        """Test getting project info when registry is not available."""
        selector = ProjectSelector()
        selector.project_registry = None

        info = selector.get_project_info("test-project")

        assert info["exists"] is False
        assert info["details"] == "No project selected"

    def test_get_project_info_project_not_found(self):
        """Test getting project info when project is not found."""
        mock_registry = Mock()
        mock_registry.get_project.return_value = None

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        info = selector.get_project_info("nonexistent")

        assert info["exists"] is False
        assert info["details"] == "Project not found"

    def test_get_project_info_success(self):
        """Test successful project info retrieval."""
        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.project_id = "test-1"
        mock_project.training_status = TrainingStatus.COMPLETED
        mock_project.created_at = datetime(2025, 1, 1, 12, 0, 0)
        mock_project.source_path = Path("/test/path")
        mock_project.last_trained = datetime(2025, 1, 2, 14, 30, 0)

        mock_registry = Mock()
        mock_registry.get_project.return_value = mock_project

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        info = selector.get_project_info("test-1")

        assert info["exists"] is True
        assert info["name"] == "Test Project"
        assert info["status"] == "completed"
        assert "🟢 Test Project" in info["details"]
        assert "test-1" in info["details"]
        assert "Ready for Analysis" in info["details"]
        assert info["project"] == mock_project

    def test_get_project_info_different_statuses(self):
        """Test project info with different training statuses."""
        selector = ProjectSelector()
        mock_registry = Mock()
        selector.project_registry = mock_registry

        # Test different statuses
        statuses_and_messages = [
            (TrainingStatus.TRAINING, "Training in Progress"),
            (TrainingStatus.NOT_STARTED, "Training Not Started"),
            (TrainingStatus.FAILED, "Training Failed")
        ]

        for status, expected_message in statuses_and_messages:
            mock_project = Mock()
            mock_project.name = "Test Project"
            mock_project.project_id = "test-1"
            mock_project.training_status = status
            mock_project.created_at = datetime(2025, 1, 1, 12, 0, 0)
            mock_project.source_path = Path("/test/path")
            mock_project.last_trained = None

            mock_registry.get_project.return_value = mock_project

            info = selector.get_project_info("test-1")

            assert expected_message in info["details"]

    def test_get_project_info_error(self):
        """Test getting project info when an error occurs."""
        mock_registry = Mock()
        mock_registry.get_project.side_effect = Exception("Registry error")

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        info = selector.get_project_info("test-1")

        assert info["exists"] is False
        assert info["status"] == "error"
        assert "Error: Registry error" in info["details"]

    def test_format_project_details(self):
        """Test project details formatting."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.project_id = "test-1"
        mock_project.training_status = TrainingStatus.COMPLETED
        mock_project.created_at = datetime(2025, 1, 1, 12, 0, 0)
        mock_project.source_path = Path("/test/path")
        mock_project.last_trained = datetime(2025, 1, 2, 14, 30, 0)

        selector = ProjectSelector()
        details = selector._format_project_details(mock_project)

        assert "🟢 Test Project" in details
        assert "test-1" in details
        assert "Completed" in details
        assert "2025-01-01 at 12:00" in details
        assert "/test/path" in details
        assert "2025-01-02 at 14:30" in details
        assert "Ready for Analysis" in details

    def test_create_selector_component(self):
        """Test creating selector component."""
        selector = ProjectSelector()

        component = selector.create_selector_component()

        assert hasattr(component, 'label')
        assert hasattr(component, 'choices')
        assert hasattr(component, 'interactive')

    def test_create_status_component(self):
        """Test creating status component."""
        selector = ProjectSelector()

        component = selector.create_status_component()

        assert hasattr(component, 'value')

    def test_refresh_choices(self):
        """Test refreshing choices."""
        mock_registry = Mock()
        mock_registry.list_projects.return_value = []

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        update = selector.refresh_choices()

        assert 'choices' in update

    def test_update_status_display(self):
        """Test updating status display."""
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.project_id = "test-1"
        mock_project.training_status = TrainingStatus.COMPLETED
        mock_project.created_at = datetime(2025, 1, 1, 12, 0, 0)
        mock_project.source_path = Path("/test/path")
        mock_project.last_trained = None

        mock_registry = Mock()
        mock_registry.get_project.return_value = mock_project

        selector = ProjectSelector()
        selector.project_registry = mock_registry

        status = selector.update_status_display("test-1")

        assert "Test Project" in status


class TestGlobalFunctions:
    """Test global convenience functions."""

    @patch('src.codebase_gardener.ui.project_selector.get_project_registry')
    def test_get_project_selector_singleton(self, mock_get_registry):
        """Test that get_project_selector returns singleton instance."""
        mock_registry = Mock()
        mock_get_registry.return_value = mock_registry

        # Clear any existing instance
        import src.codebase_gardener.ui.project_selector as ps_module
        ps_module._project_selector_instance = None

        selector1 = get_project_selector()
        selector2 = get_project_selector()

        assert selector1 is selector2
        assert isinstance(selector1, ProjectSelector)

    @patch('src.codebase_gardener.ui.project_selector.get_project_selector')
    def test_get_project_choices_function(self, mock_get_selector):
        """Test get_project_choices convenience function."""
        mock_selector = Mock()
        mock_selector.get_project_choices.return_value = [("Test", "test")]
        mock_get_selector.return_value = mock_selector

        choices = get_project_choices()

        assert choices == [("Test", "test")]
        mock_selector.get_project_choices.assert_called_once()

    @patch('src.codebase_gardener.ui.project_selector.get_project_selector')
    def test_get_project_info_function(self, mock_get_selector):
        """Test get_project_info convenience function."""
        mock_selector = Mock()
        mock_selector.get_project_info.return_value = {"exists": True}
        mock_get_selector.return_value = mock_selector

        info = get_project_info("test-1")

        assert info == {"exists": True}
        mock_selector.get_project_info.assert_called_once_with("test-1")

    @patch('src.codebase_gardener.ui.project_selector.get_project_selector')
    def test_refresh_project_choices_function(self, mock_get_selector):
        """Test refresh_project_choices convenience function."""
        mock_selector = Mock()
        mock_update = Mock()
        mock_selector.refresh_choices.return_value = mock_update
        mock_get_selector.return_value = mock_selector

        update = refresh_project_choices()

        assert update == mock_update
        mock_selector.refresh_choices.assert_called_once()

    @patch('src.codebase_gardener.ui.project_selector.get_project_selector')
    def test_update_project_status_function(self, mock_get_selector):
        """Test update_project_status convenience function."""
        mock_selector = Mock()
        mock_selector.update_status_display.return_value = "Status"
        mock_get_selector.return_value = mock_selector

        status = update_project_status("test-1")

        assert status == "Status"
        mock_selector.update_status_display.assert_called_once_with("test-1")


class TestIntegration:
    """Integration tests for project selector."""

    @patch('src.codebase_gardener.ui.project_selector.get_project_registry')
    def test_full_project_selector_workflow(self, mock_get_registry):
        """Test complete project selector workflow."""
        # Create mock projects
        project1 = Mock()
        project1.name = "Project A"
        project1.project_id = "proj-a"
        project1.training_status = TrainingStatus.COMPLETED
        project1.created_at = datetime(2025, 1, 1, 12, 0, 0)
        project1.source_path = Path("/path/a")
        project1.last_trained = None

        project2 = Mock()
        project2.name = "Project B"
        project2.project_id = "proj-b"
        project2.training_status = TrainingStatus.TRAINING
        project2.created_at = datetime(2025, 1, 2, 14, 0, 0)
        project2.source_path = Path("/path/b")
        project2.last_trained = None

        mock_registry = Mock()
        mock_registry.list_projects.return_value = [project2, project1]  # Unsorted
        mock_registry.get_project.side_effect = lambda pid: project1 if pid == "proj-a" else project2
        mock_get_registry.return_value = mock_registry

        # Clear singleton
        import src.codebase_gardener.ui.project_selector as ps_module
        ps_module._project_selector_instance = None

        selector = get_project_selector()

        # Test getting choices
        choices = selector.get_project_choices()
        assert len(choices) == 2
        assert choices[0] == ("🟢 Project A", "proj-a")  # Completed first
        assert choices[1] == ("🟡 Project B", "proj-b")  # Training second

        # Test getting project info
        info_a = selector.get_project_info("proj-a")
        assert info_a["exists"] is True
        assert info_a["name"] == "Project A"
        assert info_a["status"] == "completed"
        assert "Ready for Analysis" in info_a["details"]

        info_b = selector.get_project_info("proj-b")
        assert info_b["exists"] is True
        assert info_b["name"] == "Project B"
        assert info_b["status"] == "training"
        assert "Training in Progress" in info_b["details"]

        # Test status display update
        status_a = selector.update_status_display("proj-a")
        assert "Project A" in status_a
        assert "🟢" in status_a

        # Test component creation
        dropdown = selector.create_selector_component()
        assert hasattr(dropdown, 'choices')

        status_display = selector.create_status_component()
        assert hasattr(status_display, 'value')

    @patch('src.codebase_gardener.ui.project_selector.get_project_registry')
    def test_error_handling_throughout_workflow(self, mock_get_registry):
        """Test error handling throughout the workflow."""
        # Setup registry that fails
        mock_registry = Mock()
        mock_registry.list_projects.side_effect = Exception("Registry error")
        mock_get_registry.return_value = mock_registry

        # Clear singleton
        import src.codebase_gardener.ui.project_selector as ps_module
        ps_module._project_selector_instance = None

        selector = get_project_selector()

        # Test that errors are handled gracefully
        choices = selector.get_project_choices()
        assert choices == [("❌ Error loading projects", "")]

        # Test project info with error
        mock_registry.get_project.side_effect = Exception("Get project error")
        info = selector.get_project_info("test-1")
        assert info["exists"] is False
        assert "Error: Get project error" in info["details"]
