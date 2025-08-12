"""
Codebase Gardener - Enhanced AI-Powered Code Analysis

A comprehensive system for single-project deep code analysis using RAG and LoRA training.
Transforms from simple analysis to persistent, learning system that builds specialized
knowledge and improves analysis capabilities over time.

Architecture:
- Layer 1: Core CLI (Always Available) - Simple analysis and chat
- Layer 2: Enhancement Controller - Dynamic loading and graceful fallbacks
- Layer 3: Advanced Components - RAG, training, vector storage

This package provides the advanced components while maintaining full backwards
compatibility with the existing simple CLI functionality.
"""

__version__ = "0.2.0-alpha"
__author__ = "Codebase Gardener Team"
