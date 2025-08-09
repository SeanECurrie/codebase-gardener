"""
Tests for Gradio web interface application.

This module tests the main Gradio application functionality including
project switching, chat interface, and code analysis features.
"""

from pathlib import Path
from unittest.mock import Mock, patch

import gradio as gr

from src.codebase_gardener.core.project_registry import TrainingStatus
from src.codebase_gardener.ui.gradio_app import (
    analyze_code,
    app_state,
    create_app,
    get_project_options,
    get_project_status,
    get_system_health,
    handle_chat,
    initialize_components,
    switch_project,
)


class TestComponentInitialization:
    """Test component initialization functionality."""

    @patch('src.codebase_gardener.ui.gradio_app.get_settings')
    @patch('src.codebase_gardener.ui.gradio_app.get_project_registry')
    @patch('src.codebase_gardener.ui.gradio_app.get_dynamic_model_loader')
    @patch('src.codebase_gardener.ui.gradio_app.get_project_context_manager')
    @patch('src.codebase_gardener.ui.gradio_app.get_project_vector_store_manager')
    def test_initialize_components_success(self, mock_vector, mock_context, mock_loader, mock_registry, mock_settings):
        """Test successful component initialization."""
        # Setup mocks
        mock_settings.return_value = Mock()
        mock_registry.return_value = Mock()
        mock_loader.return_value = Mock()
        mock_context.return_value = Mock()
        mock_vector.return_value = Mock()

        # Test initialization
        result = initialize_components()

        assert result is True
        assert app_state["settings"] is not None
        assert app_state["project_registry"] is not None
        assert app_state["model_loader"] is not None
        assert app_state["context_manager"] is not None
        assert app_state["vector_store_manager"] is not None

    @patch('src.codebase_gardener.ui.gradio_app.get_settings')
    def test_initialize_components_failure(self, mock_settings):
        """Test component initialization failure."""
        mock_settings.side_effect = Exception("Initialization failed")

        result = initialize_components()

        assert result is False


class TestProjectOptions:
    """Test project options functionality."""

    def test_get_project_options_no_registry(self):
        """Test getting project options when registry is not available."""
        app_state["project_registry"] = None

        options = get_project_options()

        assert options == [("No projects available", "")]

    def test_get_project_options_no_projects(self):
        """Test getting project options when no projects exist."""
        mock_registry = Mock()
        mock_registry.list_projects.return_value = []
        app_state["project_registry"] = mock_registry

        options = get_project_options()

        assert options == [("No projects available", "")]

    def test_get_project_options_with_projects(self):
        """Test getting project options with available projects."""
        # Create mock projects
        project1 = Mock()
        project1.name = "Test Project 1"
        project1.project_id = "test-1"
        project1.training_status = TrainingStatus.COMPLETED

        project2 = Mock()
        project2.name = "Test Project 2"
        project2.project_id = "test-2"
        project2.training_status = TrainingStatus.TRAINING

        mock_registry = Mock()
        mock_registry.list_projects.return_value = [project1, project2]
        app_state["project_registry"] = mock_registry

        options = get_project_options()

        assert len(options) == 2
        assert ("🟢 Test Project 1", "test-1") in options
        assert ("🟡 Test Project 2", "test-2") in options

    def test_get_project_options_error(self):
        """Test getting project options when an error occurs."""
        mock_registry = Mock()
        mock_registry.list_projects.side_effect = Exception("Registry error")
        app_state["project_registry"] = mock_registry

        options = get_project_options()

        assert options == [("Error loading projects", "")]


class TestProjectStatus:
    """Test project status functionality."""

    def test_get_project_status_no_project(self):
        """Test getting status when no project is selected."""
        result = get_project_status("")
        assert result == "No project selected"

    def test_get_project_status_project_not_found(self):
        """Test getting status when project is not found."""
        mock_registry = Mock()
        mock_registry.get_project.return_value = None
        app_state["project_registry"] = mock_registry

        result = get_project_status("nonexistent")

        assert result == "Project not found"

    def test_get_project_status_success(self):
        """Test successful project status retrieval."""
        from datetime import datetime

        # Create mock project
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.training_status = TrainingStatus.COMPLETED
        mock_project.created_at = datetime(2025, 1, 1, 12, 0, 0)
        mock_project.source_path = Path("/test/path")

        mock_registry = Mock()
        mock_registry.get_project.return_value = mock_project
        app_state["project_registry"] = mock_registry
        app_state["model_loader"] = Mock()
        app_state["model_loader"].get_loaded_adapters.return_value = []
        app_state["context_manager"] = Mock()
        app_state["context_manager"].get_current_context.return_value = None

        result = get_project_status("test-project")

        assert "Test Project" in result
        assert "Completed" in result
        assert "2025-01-01 12:00" in result


class TestProjectSwitching:
    """Test project switching functionality."""

    def test_switch_project_no_project(self):
        """Test switching when no project is selected."""
        result = switch_project("")

        assert result[0] == "No project selected"
        assert result[2] == "Please select a project"

    @patch('src.codebase_gardener.ui.gradio_app.get_project_status')
    def test_switch_project_success(self, mock_get_status):
        """Test successful project switching."""
        mock_get_status.return_value = "Project status"

        # Setup mock components
        mock_context = Mock()
        mock_context.switch_project.return_value = True
        mock_loader = Mock()
        mock_loader.switch_project.return_value = True
        mock_vector = Mock()
        mock_vector.switch_project.return_value = True

        app_state["context_manager"] = mock_context
        app_state["model_loader"] = mock_loader
        app_state["vector_store_manager"] = mock_vector

        result = switch_project("test-project")

        assert app_state["current_project"] == "test-project"
        assert "Successfully switched" in result[1]
        mock_context.switch_project.assert_called_once_with("test-project")
        mock_loader.switch_project.assert_called_once_with("test-project")
        mock_vector.switch_project.assert_called_once_with("test-project")

    @patch('src.codebase_gardener.ui.gradio_app.get_project_status')
    def test_switch_project_with_failures(self, mock_get_status):
        """Test project switching with component failures."""
        mock_get_status.return_value = "Project status"

        # Setup mock components that fail
        mock_context = Mock()
        mock_context.switch_project.return_value = False
        mock_loader = Mock()
        mock_loader.switch_project.return_value = False
        mock_vector = Mock()
        mock_vector.switch_project.return_value = False

        app_state["context_manager"] = mock_context
        app_state["model_loader"] = mock_loader
        app_state["vector_store_manager"] = mock_vector

        result = switch_project("test-project")

        # Should still succeed overall even if components fail
        assert app_state["current_project"] == "test-project"
        assert "Successfully switched" in result[1]


class TestChatInterface:
    """Test chat interface functionality."""

    def test_handle_chat_empty_message(self):
        """Test handling empty chat message."""
        history = []
        result = handle_chat("", history, "test-project")

        assert result == (history, "")

    def test_handle_chat_no_project(self):
        """Test handling chat message with no project selected."""
        history = []
        result = handle_chat("Hello", history, "")

        assert len(result[0]) == 2
        assert result[0][0]["role"] == "user"
        assert result[0][1]["role"] == "assistant"
        assert "Please select a project first" in result[0][1]["content"]

    def test_handle_chat_success(self):
        """Test successful chat message handling."""
        mock_context = Mock()
        app_state["context_manager"] = mock_context

        history = []
        result = handle_chat("Hello", history, "test-project")

        assert len(result[0]) == 2
        assert result[0][0]["role"] == "user"
        assert result[0][0]["content"] == "Hello"
        assert result[0][1]["role"] == "assistant"
        assert "test-project" in result[0][1]["content"]

        # Verify context manager calls
        assert mock_context.add_message.call_count == 2
        mock_context.add_message.assert_any_call("user", "Hello")

    def test_handle_chat_error(self):
        """Test chat message handling with error."""
        mock_context = Mock()
        mock_context.add_message.side_effect = Exception("Context error")
        app_state["context_manager"] = mock_context

        history = []
        result = handle_chat("Hello", history, "test-project")

        assert len(result[0]) == 2
        assert result[0][0]["role"] == "user"
        assert result[0][1]["role"] == "assistant"
        assert "Error processing message" in result[0][1]["content"]


class TestCodeAnalysis:
    """Test code analysis functionality."""

    def test_analyze_code_empty(self):
        """Test analyzing empty code."""
        result = analyze_code("", "test-project")

        assert "Please enter some code" in result

    def test_analyze_code_no_project(self):
        """Test analyzing code with no project selected."""
        result = analyze_code("print('hello')", "")

        assert "Please select a project first" in result

    def test_analyze_code_success(self):
        """Test successful code analysis."""
        code = "def hello():\n    return 'world'"
        result = analyze_code(code, "test-project")

        assert "Code Analysis for Project: test-project" in result
        assert str(len(code)) in result
        assert "2 lines" in result

    def test_analyze_code_error(self):
        """Test code analysis with error."""
        with patch('src.codebase_gardener.ui.gradio_app.logger') as mock_logger:
            mock_logger.info.side_effect = Exception("Analysis error")

            result = analyze_code("print('hello')", "test-project")

            assert "Error analyzing code" in result


class TestSystemHealth:
    """Test system health functionality."""

    def test_get_system_health_success(self):
        """Test successful system health retrieval."""
        mock_registry = Mock()
        mock_registry.list_projects.return_value = [Mock(), Mock()]

        app_state["project_registry"] = mock_registry
        app_state["model_loader"] = Mock()
        app_state["context_manager"] = Mock()
        app_state["vector_store_manager"] = Mock()
        app_state["current_project"] = "test-project"

        result = get_system_health()

        assert "System Health Status" in result
        assert "**Project Registry:** 🟢 OK" in result
        assert "**Model Loader:** 🟢 OK" in result
        assert "**Context Manager:** 🟢 OK" in result
        assert "**Vector Store Manager:** 🟢 OK" in result
        assert "**Projects:** 2 registered" in result
        assert "**Active Project:** test-project" in result

    def test_get_system_health_no_components(self):
        """Test system health with no components initialized."""
        app_state["project_registry"] = None
        app_state["model_loader"] = None
        app_state["context_manager"] = None
        app_state["vector_store_manager"] = None
        app_state["current_project"] = None

        result = get_system_health()

        assert "System Health Status" in result
        assert "**Project Registry:** 🔴 Not Initialized" in result
        assert "**Active Project:** None" in result

    def test_get_system_health_error(self):
        """Test system health with error."""
        app_state["project_registry"] = Mock()
        app_state["project_registry"].list_projects.side_effect = Exception("Health error")

        result = get_system_health()

        assert "Error getting system health" in result


class TestAppCreation:
    """Test Gradio app creation."""

    @patch('src.codebase_gardener.ui.gradio_app.initialize_components')
    def test_create_app_initialization_failure(self, mock_init):
        """Test app creation when initialization fails."""
        mock_init.return_value = False

        app = create_app()

        assert isinstance(app, gr.Blocks)
        # Should create error interface

    @patch('src.codebase_gardener.ui.gradio_app.initialize_components')
    @patch('src.codebase_gardener.ui.gradio_app.get_project_options')
    @patch('src.codebase_gardener.ui.gradio_app.get_system_health')
    def test_create_app_success(self, mock_health, mock_options, mock_init):
        """Test successful app creation."""
        mock_init.return_value = True
        mock_options.return_value = [("Test Project", "test-1")]
        mock_health.return_value = "System OK"

        app = create_app()

        assert isinstance(app, gr.Blocks)
        mock_init.assert_called_once()


class TestIntegration:
    """Integration tests for UI components."""

    @patch('src.codebase_gardener.ui.gradio_app.initialize_components')
    def test_full_workflow_simulation(self, mock_init):
        """Test a complete workflow simulation."""
        mock_init.return_value = True

        # Setup mock components
        mock_project = Mock()
        mock_project.name = "Test Project"
        mock_project.project_id = "test-1"
        mock_project.training_status = TrainingStatus.COMPLETED
        mock_project.created_at = Mock()
        mock_project.created_at.strftime.return_value = "2025-01-01 12:00"
        mock_project.source_path = Path("/test")

        mock_registry = Mock()
        mock_registry.list_projects.return_value = [mock_project]
        mock_registry.get_project.return_value = mock_project

        mock_context = Mock()
        mock_context.switch_project.return_value = True
        mock_loader = Mock()
        mock_loader.switch_project.return_value = True
        mock_loader.get_loaded_adapters.return_value = []
        mock_vector = Mock()
        mock_vector.switch_project.return_value = True

        app_state["project_registry"] = mock_registry
        app_state["context_manager"] = mock_context
        app_state["model_loader"] = mock_loader
        app_state["vector_store_manager"] = mock_vector

        # Test project options
        options = get_project_options()
        assert len(options) == 1
        assert options[0][1] == "test-1"

        # Test project switching
        result = switch_project("test-1")
        assert "Successfully switched" in result[1]

        # Test chat
        chat_result = handle_chat("Hello", [], "test-1")
        assert len(chat_result[0]) == 2

        # Test code analysis
        analysis_result = analyze_code("print('hello')", "test-1")
        assert "Code Analysis" in analysis_result

        # Test system health
        health_result = get_system_health()
        assert "System Health Status" in health_result
