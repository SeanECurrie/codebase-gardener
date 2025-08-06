"""
User interface components for Codebase Gardener.

This module provides the Gradio-based web interface including:

- Project selector dropdown for switching between codebases
- Analysis interface for interacting with project-specific AI
- Real-time feedback for model loading and training progress
- Reusable UI components and layouts
"""

from .gradio_app import create_app
from .project_selector import ProjectSelector, get_project_selector
from .components import (
    StatusDisplay,
    ChatInterface, 
    CodeAnalysisInterface,
    ProgressIndicator,
    ProjectManagement,
    MetricsDisplay,
    CustomCSS,
    create_status_section,
    create_chat_section,
    create_analysis_section
)

__all__ = [
    "create_app",
    "ProjectSelector",
    "get_project_selector", 
    "StatusDisplay",
    "ChatInterface",
    "CodeAnalysisInterface",
    "ProgressIndicator",
    "ProjectManagement",
    "MetricsDisplay",
    "CustomCSS",
    "create_status_section",
    "create_chat_section",
    "create_analysis_section"
]