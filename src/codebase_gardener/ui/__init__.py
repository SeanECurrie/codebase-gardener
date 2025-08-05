"""
User interface components for Codebase Gardener.

This module provides the Gradio-based web interface including:

- Project selector dropdown for switching between codebases
- Analysis interface for interacting with project-specific AI
- Real-time feedback for model loading and training progress
- Reusable UI components and layouts
"""

from .gradio_app import create_app

__all__ = [
    "create_app"
]