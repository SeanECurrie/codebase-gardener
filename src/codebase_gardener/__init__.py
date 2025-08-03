"""
Codebase Gardener MVP - AI-powered project-specific codebase analysis.

This package provides specialized AI assistants for individual codebases through
LoRA (Low-Rank Adaptation) adapters trained on specific projects. Each codebase
gets its own "brain" that understands project-specific patterns, conventions,
and context.

Core Features:
- Project-specific LoRA adapter training and management
- Dynamic model loading for efficient resource utilization
- Local-first processing for privacy and control
- Gradio web interface for project switching and analysis
- Vector-based code similarity search and retrieval
"""

__version__ = "0.1.0"
__author__ = "Codebase Gardener Team"
__email__ = "team@codebase-gardener.dev"

# Core package imports
from codebase_gardener.config import settings

__all__ = [
    "__version__",
    "__author__", 
    "__email__",
    "settings",
]