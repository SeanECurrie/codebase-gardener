"""
Reusable UI Components for Gradio Interface

This module provides reusable UI components for the Codebase Gardener web interface,
including status displays, progress indicators, and specialized input/output components.
"""

from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import gradio as gr
import structlog

logger = structlog.get_logger(__name__)

class StatusDisplay:
    """Component for displaying system and project status."""

    @staticmethod
    def create_project_status_card() -> gr.Markdown:
        """Create a project status card component."""
        return gr.Markdown(
            value="No project selected",
            elem_classes=["project-status-card"],
            elem_id="project-status"
        )

    @staticmethod
    def create_system_health_card() -> gr.Markdown:
        """Create a system health status card."""
        return gr.Markdown(
            value="System status loading...",
            elem_classes=["system-health-card"],
            elem_id="system-health"
        )

    @staticmethod
    def create_message_display(message_type: str = "info") -> gr.Markdown:
        """Create a message display component."""
        css_class = f"message-display {message_type}"
        return gr.Markdown(
            value="",
            elem_classes=[css_class],
            visible=False
        )

    @staticmethod
    def format_status_message(message: str, status_type: str = "info") -> str:
        """Format a status message with appropriate styling."""
        icons = {
            "success": "✅",
            "error": "❌",
            "warning": "⚠️",
            "info": "ℹ️",
            "loading": "⏳"
        }

        icon = icons.get(status_type, "ℹ️")
        timestamp = datetime.now().strftime("%H:%M:%S")

        return f"{icon} **{timestamp}** - {message}"

class ChatInterface:
    """Enhanced chat interface components."""

    @staticmethod
    def create_chatbot() -> gr.Chatbot:
        """Create an enhanced chatbot component."""
        return gr.Chatbot(
            label="Project-Specific AI Assistant",
            height=400,
            show_label=True,
            elem_id="main-chatbot",
            avatar_images=("👤", "🤖"),
            bubble_full_width=False
        )

    @staticmethod
    def create_chat_input() -> gr.Textbox:
        """Create chat input component."""
        return gr.Textbox(
            label="Message",
            placeholder="Ask about your code, architecture, or get project-specific help...",
            lines=2,
            max_lines=5,
            elem_id="chat-input"
        )

    @staticmethod
    def create_chat_controls() -> Tuple[gr.Button, gr.Button]:
        """Create chat control buttons."""
        send_btn = gr.Button(
            "Send",
            variant="primary",
            elem_id="chat-send"
        )

        clear_btn = gr.Button(
            "Clear Chat",
            variant="secondary",
            elem_id="chat-clear"
        )

        return send_btn, clear_btn

class CodeAnalysisInterface:
    """Code analysis interface components."""

    @staticmethod
    def create_code_input() -> gr.Code:
        """Create code input component."""
        return gr.Code(
            label="Code to Analyze",
            language="python",
            lines=15,
            placeholder="Paste your code here for analysis...",
            elem_id="code-input"
        )

    @staticmethod
    def create_analysis_output() -> gr.Markdown:
        """Create analysis output component."""
        return gr.Markdown(
            label="Analysis Results",
            value="Enter code and click 'Analyze Code' to see results.",
            elem_classes=["analysis-output"],
            elem_id="analysis-results"
        )

    @staticmethod
    def create_analysis_controls() -> Tuple[gr.Button, gr.Dropdown]:
        """Create analysis control components."""
        analyze_btn = gr.Button(
            "🔍 Analyze Code",
            variant="primary",
            elem_id="analyze-button"
        )

        analysis_type = gr.Dropdown(
            label="Analysis Type",
            choices=[
                ("General Analysis", "general"),
                ("Code Quality", "quality"),
                ("Security Review", "security"),
                ("Performance Analysis", "performance")
            ],
            value="general",
            elem_id="analysis-type"
        )

        return analyze_btn, analysis_type

class ProgressIndicator:
    """Progress indicator components."""

    @staticmethod
    def create_loading_indicator() -> gr.HTML:
        """Create a loading indicator."""
        return gr.HTML(
            value="""
            <div class="loading-indicator" style="display: none;">
                <div class="spinner"></div>
                <span>Processing...</span>
            </div>
            """,
            elem_id="loading-indicator"
        )

    @staticmethod
    def create_progress_bar() -> gr.Progress:
        """Create a progress bar component."""
        return gr.Progress()

class ProjectManagement:
    """Project management interface components."""

    @staticmethod
    def create_project_actions() -> Tuple[gr.Button, gr.Button, gr.Button]:
        """Create project action buttons."""
        add_btn = gr.Button(
            "➕ Add Project",
            variant="secondary",
            elem_id="add-project"
        )

        train_btn = gr.Button(
            "🎯 Train Model",
            variant="primary",
            elem_id="train-model"
        )

        remove_btn = gr.Button(
            "🗑️ Remove Project",
            variant="stop",
            elem_id="remove-project"
        )

        return add_btn, train_btn, remove_btn

    @staticmethod
    def create_project_form() -> Dict[str, gr.Component]:
        """Create project creation form components."""
        return {
            "name": gr.Textbox(
                label="Project Name",
                placeholder="Enter a descriptive name for your project",
                elem_id="project-name"
            ),
            "path": gr.Textbox(
                label="Source Path",
                placeholder="/path/to/your/codebase",
                elem_id="project-path"
            ),
            "description": gr.Textbox(
                label="Description (Optional)",
                placeholder="Brief description of the project",
                lines=3,
                elem_id="project-description"
            )
        }

class MetricsDisplay:
    """Components for displaying metrics and statistics."""

    @staticmethod
    def create_metrics_grid() -> gr.HTML:
        """Create a metrics display grid."""
        return gr.HTML(
            value="""
            <div class="metrics-grid">
                <div class="metric-card">
                    <h3>Projects</h3>
                    <div class="metric-value" id="project-count">0</div>
                </div>
                <div class="metric-card">
                    <h3>Active Models</h3>
                    <div class="metric-value" id="active-models">0</div>
                </div>
                <div class="metric-card">
                    <h3>Memory Usage</h3>
                    <div class="metric-value" id="memory-usage">0 MB</div>
                </div>
                <div class="metric-card">
                    <h3>Response Time</h3>
                    <div class="metric-value" id="response-time">0 ms</div>
                </div>
            </div>
            """,
            elem_id="metrics-display"
        )

    @staticmethod
    def create_health_indicators() -> gr.HTML:
        """Create system health indicators."""
        return gr.HTML(
            value="""
            <div class="health-indicators">
                <div class="health-item">
                    <span class="health-label">Model Loader:</span>
                    <span class="health-status" id="model-loader-status">🔴 Unknown</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Context Manager:</span>
                    <span class="health-status" id="context-manager-status">🔴 Unknown</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Vector Store:</span>
                    <span class="health-status" id="vector-store-status">🔴 Unknown</span>
                </div>
                <div class="health-item">
                    <span class="health-label">Project Registry:</span>
                    <span class="health-status" id="registry-status">🔴 Unknown</span>
                </div>
            </div>
            """,
            elem_id="health-indicators"
        )

class CustomCSS:
    """Custom CSS styles for the interface."""

    @staticmethod
    def get_styles() -> str:
        """Get custom CSS styles."""
        return """
        /* Project Status Card */
        .project-status-card {
            background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #007bff;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 10px 0;
        }

        /* System Health Card */
        .system-health-card {
            background: linear-gradient(135deg, #f1f8ff 0%, #e3f2fd 100%);
            padding: 20px;
            border-radius: 12px;
            border-left: 4px solid #28a745;
            box-shadow: 0 2px 8px rgba(0,0,0,0.1);
            margin: 10px 0;
        }

        /* Message Display */
        .message-display {
            padding: 12px 16px;
            border-radius: 8px;
            margin: 8px 0;
            border-left: 4px solid;
        }

        .message-display.success {
            background-color: #d4edda;
            color: #155724;
            border-left-color: #28a745;
        }

        .message-display.error {
            background-color: #f8d7da;
            color: #721c24;
            border-left-color: #dc3545;
        }

        .message-display.warning {
            background-color: #fff3cd;
            color: #856404;
            border-left-color: #ffc107;
        }

        .message-display.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border-left-color: #17a2b8;
        }

        /* Analysis Output */
        .analysis-output {
            background-color: #f8f9fa;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #dee2e6;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
            max-height: 500px;
            overflow-y: auto;
        }

        /* Loading Indicator */
        .loading-indicator {
            display: flex;
            align-items: center;
            justify-content: center;
            padding: 20px;
            gap: 10px;
        }

        .spinner {
            width: 20px;
            height: 20px;
            border: 2px solid #f3f3f3;
            border-top: 2px solid #007bff;
            border-radius: 50%;
            animation: spin 1s linear infinite;
        }

        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }

        /* Metrics Grid */
        .metrics-grid {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
            gap: 15px;
            margin: 15px 0;
        }

        .metric-card {
            background: white;
            padding: 20px;
            border-radius: 8px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            text-align: center;
            border-top: 3px solid #007bff;
        }

        .metric-card h3 {
            margin: 0 0 10px 0;
            color: #6c757d;
            font-size: 14px;
            font-weight: 600;
            text-transform: uppercase;
        }

        .metric-value {
            font-size: 24px;
            font-weight: bold;
            color: #007bff;
        }

        /* Health Indicators */
        .health-indicators {
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }

        .health-item {
            display: flex;
            justify-content: space-between;
            align-items: center;
            padding: 10px 15px;
            background: white;
            border-radius: 6px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        }

        .health-label {
            font-weight: 500;
            color: #495057;
        }

        .health-status {
            font-weight: 600;
        }

        /* Chat Interface Enhancements */
        #main-chatbot {
            border-radius: 12px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
        }

        #chat-input {
            border-radius: 8px;
        }

        /* Button Styling */
        .gradio-button {
            border-radius: 6px;
            font-weight: 500;
            transition: all 0.2s ease;
        }

        .gradio-button:hover {
            transform: translateY(-1px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }

        /* Code Input Styling */
        #code-input {
            border-radius: 8px;
            font-family: 'Monaco', 'Menlo', 'Ubuntu Mono', monospace;
        }

        /* Project Selector */
        #project-selector {
            border-radius: 8px;
        }
        """

# Convenience functions for creating common component combinations
def create_status_section() -> Tuple[gr.Markdown, gr.Markdown]:
    """Create a complete status section."""
    project_status = StatusDisplay.create_project_status_card()
    system_health = StatusDisplay.create_system_health_card()
    return project_status, system_health

def create_chat_section() -> Tuple[gr.Chatbot, gr.Textbox, gr.Button, gr.Button]:
    """Create a complete chat section."""
    chatbot = ChatInterface.create_chatbot()
    chat_input = ChatInterface.create_chat_input()
    send_btn, clear_btn = ChatInterface.create_chat_controls()
    return chatbot, chat_input, send_btn, clear_btn

def create_analysis_section() -> Tuple[gr.Code, gr.Markdown, gr.Button, gr.Dropdown]:
    """Create a complete code analysis section."""
    code_input = CodeAnalysisInterface.create_code_input()
    analysis_output = CodeAnalysisInterface.create_analysis_output()
    analyze_btn, analysis_type = CodeAnalysisInterface.create_analysis_controls()
    return code_input, analysis_output, analyze_btn, analysis_type
