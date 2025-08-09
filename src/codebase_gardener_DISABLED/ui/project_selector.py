"""
Project Selector Component for Gradio Interface

This module provides a reusable project selector component with status indicators
and real-time updates for the Codebase Gardener web interface.
"""

from typing import Any

import gradio as gr
import structlog

from ..core.project_registry import (
    ProjectMetadata,
    TrainingStatus,
    get_project_registry,
)

logger = structlog.get_logger(__name__)

class ProjectSelector:
    """Reusable project selector component with status indicators."""

    def __init__(self):
        self.project_registry = None
        self._initialize()

    def _initialize(self):
        """Initialize the project registry."""
        try:
            self.project_registry = get_project_registry()
            logger.info("ProjectSelector initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize ProjectSelector: {e}")

    def get_project_choices(self) -> list[tuple[str, str]]:
        """Get formatted project choices for dropdown."""
        try:
            if not self.project_registry:
                return [("⚠️ Registry not available", "")]

            projects = self.project_registry.list_projects()
            if not projects:
                return [("📝 No projects found - Add a project to get started", "")]

            choices = []
            for project in projects:
                status_icon = self._get_status_icon(project.training_status)
                display_name = f"{status_icon} {project.name}"
                choices.append((display_name, project.project_id))

            # Sort by status (completed first) then by name
            choices.sort(key=lambda x: (
                0 if "🟢" in x[0] else 1 if "🟡" in x[0] else 2,
                x[0].lower()
            ))

            return choices

        except Exception as e:
            logger.error(f"Error getting project choices: {e}")
            return [("❌ Error loading projects", "")]

    def _get_status_icon(self, status: TrainingStatus) -> str:
        """Get status icon for training status."""
        status_icons = {
            TrainingStatus.COMPLETED: "🟢",
            TrainingStatus.TRAINING: "🟡",
            TrainingStatus.NOT_STARTED: "⚪",
            TrainingStatus.FAILED: "🔴"
        }
        return status_icons.get(status, "❓")

    def get_project_info(self, project_id: str) -> dict[str, Any]:
        """Get detailed project information."""
        if not project_id or not self.project_registry:
            return {
                "exists": False,
                "name": "",
                "status": "",
                "details": "No project selected"
            }

        try:
            project = self.project_registry.get_project(project_id)
            if not project:
                return {
                    "exists": False,
                    "name": "",
                    "status": "",
                    "details": "Project not found"
                }

            return {
                "exists": True,
                "name": project.name,
                "status": project.training_status.value,
                "details": self._format_project_details(project),
                "project": project
            }

        except Exception as e:
            logger.error(f"Error getting project info: {e}")
            return {
                "exists": False,
                "name": "",
                "status": "error",
                "details": f"Error: {str(e)}"
            }

    def _format_project_details(self, project: ProjectMetadata) -> str:
        """Format project details for display."""
        status_icon = self._get_status_icon(project.training_status)

        details = [
            f"**{status_icon} {project.name}**",
            "",
            f"**Project ID:** `{project.project_id}`",
            f"**Status:** {project.training_status.value.title()}",
            f"**Created:** {project.created_at.strftime('%Y-%m-%d at %H:%M')}",
            f"**Source Path:** `{project.source_path}`"
        ]

        if project.last_trained:
            details.append(f"**Last Trained:** {project.last_trained.strftime('%Y-%m-%d at %H:%M')}")

        # Add status-specific information
        if project.training_status == TrainingStatus.COMPLETED:
            details.append("")
            details.append("✅ **Ready for Analysis**")
            details.append("This project has a trained LoRA adapter and is ready for specialized AI analysis.")
        elif project.training_status == TrainingStatus.TRAINING:
            details.append("")
            details.append("⏳ **Training in Progress**")
            details.append("The LoRA adapter is currently being trained. Analysis will use the base model until training completes.")
        elif project.training_status == TrainingStatus.NOT_STARTED:
            details.append("")
            details.append("⚪ **Training Not Started**")
            details.append("Training has not been initiated. Analysis will use the base model.")
        elif project.training_status == TrainingStatus.FAILED:
            details.append("")
            details.append("❌ **Training Failed**")
            details.append("Training encountered an error. Analysis will use the base model.")

        return "\n".join(details)

    def create_selector_component(
        self,
        label: str = "Select Project",
        info: str = "Choose a project to switch to its specialized AI context"
    ) -> gr.Dropdown:
        """Create a project selector dropdown component."""
        return gr.Dropdown(
            label=label,
            choices=self.get_project_choices(),
            value=None,
            interactive=True,
            info=info,
            elem_id="project-selector"
        )

    def create_status_component(self) -> gr.Markdown:
        """Create a project status display component."""
        return gr.Markdown(
            value="No project selected",
            elem_classes=["project-status"],
            elem_id="project-status-display"
        )

    def refresh_choices(self) -> gr.update:
        """Refresh project choices for dropdown update."""
        return gr.update(choices=self.get_project_choices())

    def update_status_display(self, project_id: str) -> str:
        """Update status display for selected project."""
        project_info = self.get_project_info(project_id)
        return project_info["details"]

# Global instance for reuse
_project_selector_instance = None

def get_project_selector() -> ProjectSelector:
    """Get global project selector instance."""
    global _project_selector_instance
    if _project_selector_instance is None:
        _project_selector_instance = ProjectSelector()
    return _project_selector_instance

# Convenience functions for direct use in Gradio interfaces
def get_project_choices() -> list[tuple[str, str]]:
    """Get project choices for dropdown."""
    return get_project_selector().get_project_choices()

def get_project_info(project_id: str) -> dict[str, Any]:
    """Get project information."""
    return get_project_selector().get_project_info(project_id)

def refresh_project_choices() -> gr.update:
    """Refresh project choices."""
    return get_project_selector().refresh_choices()

def update_project_status(project_id: str) -> str:
    """Update project status display."""
    return get_project_selector().update_status_display(project_id)
