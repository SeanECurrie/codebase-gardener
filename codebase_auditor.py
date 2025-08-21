#!/usr/bin/env python3
"""
Codebase Intelligence Auditor - Single File Implementation

A simple, pragmatic codebase analysis tool that uses gpt-oss-20b via Ollama
to provide comprehensive intelligence about code architecture, tech debt,
and documentation gaps.

Usage:
    auditor = CodebaseAuditor()
    result = auditor.analyze_codebase(".")
    response = auditor.chat("What are the main architecture issues?")
    report = auditor.export_markdown()
"""

import os
import sys
import time
from collections.abc import Callable
from datetime import datetime
from pathlib import Path
from typing import Any, TypeVar

T = TypeVar("T")


def with_retries(fn: Callable[[], T], attempts: int = 5, base_sleep: float = 0.5) -> T:
    """
    Retry `fn` with exponential backoff. Raises last error if all attempts fail.
    """
    last = None
    for i in range(attempts):
        try:
            return fn()
        except Exception as e:  # narrow this if you have a specific Ollama error class
            last = e
            time.sleep(base_sleep * (2**i))
    raise last


# Add the src directory to Python path for imports
src_path = str(Path(__file__).parent / "src")
if src_path not in sys.path:
    sys.path.insert(0, src_path)

try:
    import ollama
except ImportError:
    print("Error: ollama package not found. Install with: pip install ollama")
    sys.exit(1)

try:
    from simple_file_utils import SimpleFileUtilities
except ImportError:
    print(
        "Error: Could not import SimpleFileUtilities. Make sure simple_file_utils.py is in the same directory."
    )
    sys.exit(1)


class CodebaseAuditor:
    """
    Single-file codebase auditor that analyzes code using gpt-oss-20b.

    Provides comprehensive analysis, chat functionality, and markdown export.
    """

    def __init__(self, ollama_host: str = None, model_name: str = None):
        """Initialize the auditor with Ollama client and file utilities.

        Environment overrides:
        - OLLAMA_HOST: base URL for Ollama (default http://localhost:11434)
        - OLLAMA_MODEL: model name to use (default gpt-oss-20b)
        """
        ollama_host = ollama_host or os.environ.get(
            "OLLAMA_HOST", "http://localhost:11434"
        )
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "gpt-oss-20b")

        self.client = ollama.Client(ollama_host)
        self.file_utils = SimpleFileUtilities()
        self.analysis_results: dict[str, Any] | None = None
        self._advanced_mode_requested: bool = False
        self._current_project_id: str | None = None
        self._project_manager = None

        # Simple, hardcoded caps to avoid huge prompts (pragmatic POC)
        self.max_files: int = 250
        self.max_file_bytes: int = 100 * 1024  # 100 KB per file
        self.max_total_bytes: int = 2 * 1024 * 1024  # 2 MB total

        # Chat prompt for follow-up questions
        self.chat_prompt = """Based on your previous analysis of this codebase:

{previous_analysis}

User question: {user_question}

Provide a helpful, specific answer based on your analysis. Reference specific files, functions, or code patterns when relevant."""

    def _generate_analysis_prompt(self, file_count: int, total_bytes: int) -> str:
        """Generate context-appropriate analysis prompt based on codebase size."""

        # Determine analysis depth based on codebase size
        if file_count <= 5:
            depth = "minimal"
        elif file_count <= 20:
            depth = "focused"
        elif file_count <= 100:
            depth = "comprehensive"
        else:
            depth = "high-level"

        base_prompt = """You are an expert code auditor analyzing a codebase for an AI agent that will work on it later.

Codebase context: {file_count} files, {size_desc}

"""

        if depth == "minimal":
            specific_prompt = """This appears to be a small project or test codebase. Provide a brief analysis focusing on:
- What the code does (main purpose/functionality)
- Basic structure and organization
- Any obvious issues or improvements needed
Keep the analysis concise and proportional to the codebase size."""

        elif depth == "focused":
            specific_prompt = """This is a focused project. Analyze the main aspects:
- **Primary Purpose**: What this codebase accomplishes
- **Architecture**: Key components and their relationships
- **Code Quality**: Notable patterns, issues, or strengths
- **Recommendations**: 2-3 most important improvements"""

        elif depth == "comprehensive":
            specific_prompt = """This is a substantial codebase requiring detailed analysis:

**Architecture Overview**
- Main components and their responsibilities
- How components interact with each other
- Overall design patterns used
- Key architectural decisions

**Code Quality Assessment**
- Naming conventions and consistency
- Error handling patterns
- Code organization and modularity
- Notable strengths and weaknesses

**Key Recommendations**
- Prioritized list of critical issues to address
- Specific improvements for AI agent work
- Technical debt concerns"""

        else:  # high-level
            specific_prompt = """This is a large codebase. Provide a high-level strategic analysis:
- **System Overview**: Primary purpose and major subsystems
- **Architecture Patterns**: Key design decisions and patterns
- **Integration Points**: How major components connect
- **Strategic Recommendations**: Most important areas for improvement
Focus on the big picture rather than detailed code issues."""

        return (
            base_prompt.format(
                file_count=file_count,
                size_desc=(
                    f"~{total_bytes // 1024}KB"
                    if total_bytes < 1024 * 1024
                    else f"~{total_bytes // (1024 * 1024)}MB"
                ),
            )
            + specific_prompt
            + "\n\nCodebase to analyze:\n{file_contents}"
        )

    def analyze_codebase(self, directory_path: str, progress_callback=None) -> str:
        """
        Analyze the entire codebase and store results.

        Args:
            directory_path: Path to the codebase directory
            progress_callback: Optional callback for progress updates

        Returns:
            Summary message about the analysis
        """
        try:
            # Input validation and sanitization
            if not directory_path or not directory_path.strip():
                return "Error: Directory path cannot be empty."

            dir_path = Path(directory_path).resolve()

            # Security: Validate resolved path is safe
            try:
                # Ensure we're not accessing system directories
                str_path = str(dir_path)
                if (
                    str_path
                    in [
                        "/",
                        "/etc",
                        "/usr",
                        "/bin",
                        "/sbin",
                        "/root",
                    ]
                    or str_path.startswith("/proc")
                    or str_path.startswith("/private/etc")
                ):
                    return "Error: Access to system directories is not allowed."
            except (OSError, ValueError, TypeError) as e:
                return f"Error: Invalid directory path: {e}"

            if not dir_path.exists() or not dir_path.is_dir():
                return "Error: Directory does not exist or is not accessible."

            if progress_callback:
                progress_callback("Starting codebase analysis...")

            # Find source files using existing FileUtilities
            print("🔍 Discovering source files...")
            source_files = self.file_utils.find_source_files(
                dir_path, progress_callback=progress_callback
            )

            if not source_files:
                return f"No source files found in '{directory_path}'"

            print(f"📁 Found {len(source_files)} source files")

            # Optional preflight: verify model is available with a tiny check
            if progress_callback:
                progress_callback(
                    f"Verifying model '{self.model_name}' is available..."
                )
            if not self._preflight_model_check():
                warn_msg = (
                    f"⚠️ Preflight for model '{self.model_name}' failed. Continuing anyway. "
                    "Ensure Ollama is running and the model is pulled if analysis fails."
                )
                if progress_callback:
                    progress_callback(warn_msg)
                else:
                    print(warn_msg)

            # Read and combine file contents with simple caps
            if progress_callback:
                progress_callback(
                    f"Reading up to {min(len(source_files), self.max_files)} source files (caps applied)..."
                )

            file_contents, stats = self._read_and_combine_files_with_caps(
                source_files, progress_callback, base_dir=dir_path
            )

            if not file_contents.strip():
                return "Error: No readable content found in source files"

            # Send to model for analysis
            print(f"🤖 Analyzing codebase with {self.model_name}...")
            if progress_callback:
                progress_callback(
                    f"Sending codebase to {self.model_name} for analysis..."
                )

            # Generate context-appropriate prompt
            analysis_prompt = self._generate_analysis_prompt(
                len(source_files), stats["bytes_included"]
            )
            full_prompt = analysis_prompt.format(file_contents=file_contents)

            response = with_retries(
                lambda: self.client.generate(model=self.model_name, prompt=full_prompt)
            )

            analysis_text = response["response"]

            # Store results
            self.analysis_results = {
                "full_analysis": analysis_text,
                "file_list": [str(f) for f in source_files],
                "directory_path": str(dir_path),
                "timestamp": datetime.now().isoformat(),
                "file_count": len(source_files),
                "caps": stats,
            }

            # Integrate with project management
            self._integrate_with_project_management(dir_path)

            # Check for advanced features and enhance analysis if available
            self._try_enhance_analysis(dir_path)

            print("✅ Analysis complete!")
            if progress_callback:
                progress_callback(
                    "Analysis complete! You can now ask questions or export the report."
                )

            return f"Analysis complete! Analyzed {len(source_files)} files. Ask me questions or export markdown report."

        except Exception as e:
            # Better error messaging with retry context
            error_msg = (
                "Ollama connection failed after retries. "
                f"Ensure Ollama is running and model is pulled. "
                f"Host={self.client._client.base_url}, Model={self.model_name}, Error={e}"
            )
            print(f"❌ {error_msg}")
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return f"Analysis failed: {error_msg}"

    def _read_and_combine_files_with_caps(
        self,
        source_files: list[Path],
        progress_callback=None,
        base_dir: Path | None = None,
    ) -> tuple[str, dict[str, Any]]:
        """Read and combine files with simple caps to avoid huge prompts."""
        combined_content: list[str] = []
        files_read = 0
        total_bytes = 0
        truncated_files = 0

        limited_files = source_files[: self.max_files]

        for idx, file_path in enumerate(limited_files):
            try:
                # Progress feedback every 10 files
                if progress_callback and idx % 10 == 0:
                    progress_callback(
                        f"Reading files... {idx}/{len(limited_files)} (total ~{total_bytes // 1024} KB)"
                    )

                with open(file_path, encoding="utf-8", errors="replace") as f:
                    content = f.read()

                # Enforce per-file cap
                content_bytes = content.encode("utf-8")
                if len(content_bytes) > self.max_file_bytes:
                    content = content_bytes[: self.max_file_bytes].decode(
                        "utf-8", errors="ignore"
                    )
                    truncated_files += 1
                    content += "\n... [TRUNCATED] ...\n"
                    content_bytes = content.encode("utf-8")

                # Enforce total cap
                if total_bytes + len(content_bytes) > self.max_total_bytes:
                    combined_content.append(
                        "\n... [GLOBAL CONTENT LIMIT REACHED, REMAINING FILES SKIPPED] ...\n"
                    )
                    break

                # Add file header and content
                root = base_dir or (
                    Path(self.analysis_results["directory_path"])
                    if self.analysis_results
                    else file_path.parent
                )
                try:
                    relative_path = file_path.relative_to(root)
                except ValueError:
                    relative_path = file_path.name
                combined_content.append(f"\n=== FILE: {relative_path} ===\n{content}\n")

                files_read += 1
                total_bytes += len(content_bytes)

            except Exception as e:
                print(f"⚠️  Warning: Could not read {file_path}: {e}")
                continue

        if progress_callback:
            progress_callback(
                f"Included {files_read} files (~{total_bytes // 1024} KB). Truncated: {truncated_files}"
            )

        stats = {
            "max_files": self.max_files,
            "max_file_bytes": self.max_file_bytes,
            "max_total_bytes": self.max_total_bytes,
            "files_included": files_read,
            "bytes_included": total_bytes,
            "files_truncated": truncated_files,
            "files_skipped": max(0, len(source_files) - files_read),
        }

        return "\n".join(combined_content), stats

    def _preflight_model_check(self) -> bool:
        """Simple model availability check using a tiny generation call."""
        try:
            test_prompt = "You are alive? Answer 'yes'."
            resp = self.client.generate(model=self.model_name, prompt=test_prompt)
            return bool(resp and isinstance(resp, dict) and resp.get("response"))
        except (ConnectionError, TimeoutError, OSError):
            return False

    def chat(self, question: str) -> str:
        """
        Ask questions about the analyzed codebase with project context.

        Args:
            question: User's question about the codebase

        Returns:
            AI response based on the analysis and project context
        """
        if not self.analysis_results:
            return "Error: No codebase analysis available. Please run analyze_codebase() first."

        try:
            # Integrate with project context
            context_info = self._get_project_context_for_chat()

            # Enhanced prompt with project context
            enhanced_prompt = self._build_enhanced_chat_prompt(question, context_info)

            response = self.client.generate(
                model=self.model_name, prompt=enhanced_prompt
            )
            answer = response["response"]

            # Store chat in project context
            self._store_chat_in_project_context(question, answer)

            return answer

        except Exception as e:
            return f"Chat failed: {str(e)}"

    def _get_project_context_for_chat(self) -> str:
        """Get project context information for enhanced chat."""
        pm = self._get_project_manager()
        if not pm or not self._current_project_id:
            return ""

        try:
            context = pm["context_manager"].get_context(self._current_project_id)
            if not context or not context.conversation_history:
                return ""

            # Get recent conversation history (last 5 messages)
            recent_messages = context.conversation_history[-5:]
            context_lines = []

            for msg in recent_messages:
                if msg.role in ["user", "assistant"]:
                    role_label = "User" if msg.role == "user" else "Assistant"
                    context_lines.append(f"{role_label}: {msg.content[:200]}...")

            if context_lines:
                return (
                    "\nRecent conversation context:\n" + "\n".join(context_lines) + "\n"
                )

        except (AttributeError, KeyError, TypeError):
            pass  # Context not available, continue without it

        return ""

    def _build_enhanced_chat_prompt(self, question: str, context_info: str) -> str:
        """Build enhanced chat prompt with project context."""
        base_prompt = self.chat_prompt.format(
            previous_analysis=self.analysis_results["full_analysis"],
            user_question=question,
        )

        if context_info:
            return f"{base_prompt}\n{context_info}\nContinue the conversation naturally, building on previous context where relevant."
        else:
            return base_prompt

    def _store_chat_in_project_context(self, question: str, answer: str) -> None:
        """Store chat interaction in project context."""
        pm = self._get_project_manager()
        if not pm or not self._current_project_id:
            return

        try:
            from codebase_gardener.core.project_context_manager import (
                ConversationMessage,
            )

            # Store user question
            user_message = ConversationMessage(
                role="user",
                content=question,
                timestamp=datetime.now(),
                metadata={"type": "chat_question"},
            )
            pm["context_manager"].add_message(
                self._current_project_id,
                user_message.role,
                user_message.content,
                user_message.metadata,
            )

            # Store assistant response
            assistant_message = ConversationMessage(
                role="assistant",
                content=answer,
                timestamp=datetime.now(),
                metadata={"type": "chat_response"},
            )
            pm["context_manager"].add_message(
                self._current_project_id,
                assistant_message.role,
                assistant_message.content,
                assistant_message.metadata,
            )

        except (AttributeError, KeyError, TypeError):
            pass  # Don't fail chat if context storage fails

    def export_markdown(self) -> str:
        """
        Export analysis results as formatted markdown.

        Returns:
            Markdown-formatted analysis report
        """
        if not self.analysis_results:
            return "Error: No analysis results to export. Please run analyze_codebase() first."

        timestamp = datetime.fromisoformat(self.analysis_results["timestamp"]).strftime(
            "%Y-%m-%d %H:%M:%S"
        )

        markdown_report = f"""# Codebase Analysis Report

**Generated:** {timestamp}
**Directory:** `{self.analysis_results["directory_path"]}`
**Files Analyzed:** {self.analysis_results["file_count"]}

---

{self.analysis_results["full_analysis"]}

---

## Files Analyzed

The following {self.analysis_results["file_count"]} source files were included in this analysis:

"""

        # Add file list
        for file_path in sorted(self.analysis_results["file_list"]):
            try:
                relative_path = Path(file_path).relative_to(
                    self.analysis_results["directory_path"]
                )
                markdown_report += f"- `{relative_path}`\n"
            except ValueError:
                # Fallback to just the filename if relative path fails
                markdown_report += f"- `{Path(file_path).name}`\n"

        markdown_report += """
---

*Report generated by Codebase Intelligence Auditor using gpt-oss-20b*
"""

        return markdown_report

    def _get_project_manager(self):
        """Get or create project manager instance."""
        if self._project_manager is None:
            try:
                # Try to import project management components
                sys.path.insert(0, str(Path(__file__).parent / "src"))
                from codebase_gardener.core.project_context_manager import (
                    ProjectContextManager,
                )
                from codebase_gardener.core.project_registry import ProjectRegistry

                registry = ProjectRegistry()
                context_manager = ProjectContextManager()

                self._project_manager = {
                    "registry": registry,
                    "context_manager": context_manager,
                    # Helper methods for compatibility
                    "get_project_by_path": self._get_project_by_path,
                    "update_analysis_date": self._update_analysis_date,
                }
            except ImportError as e:
                print(f"⚠️  Project management not available: {e}")
                return None
        return self._project_manager

    def _get_project_by_path(self, source_path: str):
        """Helper method to find project by source path."""
        pm = self._get_project_manager()
        if not pm:
            return None

        for project in pm["registry"].list_projects():
            if str(project.source_path) == source_path:
                return project
        return None

    def _update_analysis_date(self, project_id: str, analysis_date):
        """Helper method to update project's last_updated timestamp."""
        pm = self._get_project_manager()
        if not pm:
            return

        # Get the project and update its last_updated field
        project = pm["registry"].get_project(project_id)
        if project:
            project.last_updated = analysis_date
            # Save the registry to persist the change
            pm["registry"]._save_registry()

    def _handle_projects_command(self):
        """Handle the 'projects' command to list all registered projects."""
        pm = self._get_project_manager()
        if not pm:
            print("❌ Project management not available")
            return

        try:
            projects = pm["registry"].list_projects()
            if not projects:
                print("📂 No projects registered yet")
                print(
                    "   Use 'project create <directory>' to create your first project"
                )
                return

            print(f"\n📂 Registered Projects ({len(projects)}):")
            print("=" * 60)

            for project in projects:
                status_icon = (
                    "✅"
                    if project.training_status.value == "completed"
                    else "🔄"
                    if project.training_status.value == "training"
                    else "📝"
                )
                current_indicator = (
                    " ← CURRENT"
                    if project.project_id == self._current_project_id
                    else ""
                )

                print(f"{status_icon} {project.name}")
                print(f"   ID: {project.project_id}{current_indicator}")
                print(f"   Path: {project.source_path}")
                print(f"   Created: {project.created_at.strftime('%Y-%m-%d %H:%M')}")
                print(f"   Status: {project.training_status.value}")

                if project.last_updated:
                    print(
                        f"   Last Updated: {project.last_updated.strftime('%Y-%m-%d %H:%M')}"
                    )
                print()

        except Exception as e:
            print(f"❌ Failed to list projects: {e}")

    def _handle_project_command(self, subcommand: str, args: list[str]):
        """Handle project subcommands."""
        pm = self._get_project_manager()
        if not pm:
            print("❌ Project management not available")
            return

        try:
            if subcommand == "create":
                self._project_create(pm, args)
            elif subcommand == "info":
                self._project_info(pm, args)
            elif subcommand == "switch":
                self._project_switch(pm, args)
            elif subcommand == "cleanup":
                self._project_cleanup(pm, args)
            elif subcommand == "health":
                self._project_health(pm, args)
            else:
                print(f"❌ Unknown project subcommand: {subcommand}")
                print("   Available: create, info, switch, cleanup, health")

        except Exception as e:
            print(f"❌ Project command failed: {e}")

    def _project_create(self, pm, args: list[str]):
        """Create a new project."""
        if not args:
            print("❌ Please specify a directory path")
            print("   Example: project create ./my-project")
            return

        directory = " ".join(args)
        dir_path = Path(directory).resolve()

        if not dir_path.exists() or not dir_path.is_dir():
            print(f"❌ Directory not found: {directory}")
            return

        # Check if project already exists
        existing_project = self._get_project_by_path(str(dir_path))
        if existing_project:
            print(f"📂 Project already exists: {existing_project.name}")
            print(f"   ID: {existing_project.project_id}")
            self._current_project_id = existing_project.project_id
            print("✅ Switched to existing project")
            return

        # Create new project
        project_name = dir_path.name
        project_id = pm["registry"].register_project(project_name, dir_path)
        project = pm["registry"].get_project(project_id)

        self._current_project_id = project_id
        print(f"✅ Created new project: {project.name}")
        print(f"   ID: {project.project_id}")
        print(f"   Path: {project.source_path}")
        print("🔄 Project is now active for analysis")

    def _project_info(self, pm, args: list[str]):
        """Show project information."""
        if args:
            project_id = args[0]
            project = pm["registry"].get_project(project_id)
        elif self._current_project_id:
            project = pm["registry"].get_project(self._current_project_id)
        else:
            print("❌ No project ID specified and no current project")
            print("   Example: project info abc123")
            return

        if not project:
            print(
                f"❌ Project not found: {args[0] if args else self._current_project_id}"
            )
            return

        print("\n📂 Project Information")
        print("=" * 40)
        print(f"Name: {project.name}")
        print(f"ID: {project.project_id}")
        print(f"Path: {project.source_path}")
        print(f"Created: {project.created_at.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"Training Status: {project.training_status.value}")

        if project.last_updated:
            print(f"Last Updated: {project.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
        if project.lora_adapter_path:
            print(f"LoRA Adapter: {project.lora_adapter_path}")
        if project.vector_store_path:
            print(f"Vector Store: {project.vector_store_path}")

        # Show context information
        try:
            context = pm["context_manager"].get_context(project.project_id)
            if context and context.conversation_history:
                print(
                    f"Conversation History: {len(context.conversation_history)} messages"
                )
        except (AttributeError, KeyError, TypeError):
            pass  # Context manager might not be available

    def _project_switch(self, pm, args: list[str]):
        """Switch to a different project."""
        if not args:
            print("❌ Please specify a project ID")
            print("   Example: project switch abc123")
            print("   Use 'projects' to see available project IDs")
            return

        project_id = args[0]
        project = pm["registry"].get_project(project_id)

        if not project:
            print(f"❌ Project not found: {project_id}")
            print("   Use 'projects' to see available projects")
            return

        self._current_project_id = project_id
        print(f"✅ Switched to project: {project.name}")
        print(f"   ID: {project.project_id}")
        print(f"   Path: {project.source_path}")

    def _project_cleanup(self, pm, args: list[str]):
        """Clean up old project data."""
        # For now, just show what would be cleaned up
        print("🧹 Project Cleanup Analysis:")

        projects = pm["registry"].list_projects()
        old_projects = []

        for project in projects:
            if project.last_updated:
                days_old = (datetime.now() - project.last_updated).days
                if days_old > 30:  # Consider projects older than 30 days
                    old_projects.append((project, days_old))

        if not old_projects:
            print("✅ No cleanup needed - all projects are recent")
            return

        print(f"📋 Found {len(old_projects)} projects that haven't been used recently:")
        for project, days_old in old_projects:
            print(
                f"   • {project.name} (ID: {project.project_id[:8]}...) - {days_old} days old"
            )

        print("\n💡 Manual cleanup required:")
        print("   - Use project management commands to remove unused projects")
        print("   - Check vector store and LoRA adapter files manually")

    def _project_health(self, pm, args: list[str]):
        """Check project health status."""
        print("🔍 Project Health Check:")
        print("=" * 40)

        # Check registry health
        try:
            projects = pm["registry"].list_projects()
            print(f"✅ Project Registry: {len(projects)} projects registered")
        except Exception as e:
            print(f"❌ Project Registry: Error - {e}")

        # Check context manager health
        try:
            # Test context manager by creating a temporary context
            pm["context_manager"].get_context("health-check")
            print("✅ Context Manager: Available")
        except Exception as e:
            print(f"❌ Context Manager: Error - {e}")

        # Check current project
        if self._current_project_id:
            try:
                current_project = pm["registry"].get_project(self._current_project_id)
                if current_project:
                    print(f"✅ Current Project: {current_project.name}")

                    # Check if project path still exists
                    if Path(current_project.source_path).exists():
                        print("✅ Project Path: Accessible")
                    else:
                        print("⚠️  Project Path: Directory no longer exists")
                else:
                    print("⚠️  Current Project: Invalid project ID")
            except Exception as e:
                print(f"❌ Current Project: Error - {e}")
        else:
            print("ℹ️  Current Project: None selected")

    def _integrate_with_project_management(self, dir_path: Path) -> None:
        """Integrate analysis with project management system."""
        pm = self._get_project_manager()
        if not pm:
            return  # Project management not available

        try:
            # Check if project already exists for this path
            existing_project = self._get_project_by_path(str(dir_path))

            if not existing_project:
                # Auto-create project if it doesn't exist
                project_name = dir_path.name
                project_id = pm["registry"].register_project(project_name, dir_path)
                project = pm["registry"].get_project(project_id)
                self._current_project_id = project_id
                print(
                    f"📂 Auto-created project: {project.name} (ID: {project.project_id[:8]}...)"
                )
            else:
                # Use existing project
                self._current_project_id = existing_project.project_id
                print(
                    f"📂 Using existing project: {existing_project.name} (ID: {existing_project.project_id[:8]}...)"
                )

            # Update project with analysis results
            if self._current_project_id:
                self._update_analysis_date(self._current_project_id, datetime.now())

                # Store analysis in project context
                if self.analysis_results:
                    # Add analysis as a system message
                    pm["context_manager"].add_message(
                        self._current_project_id,
                        "system",
                        f"Analysis completed: {self.analysis_results['file_count']} files processed",
                        {
                            "type": "analysis_completion",
                            "file_count": self.analysis_results["file_count"],
                            "bytes_processed": self.analysis_results["caps"].get(
                                "bytes_included", 0
                            ),
                        },
                    )

        except Exception as e:
            print(f"⚠️  Project integration failed: {e}")
            # Don't fail the analysis, just continue without project management

    def _try_enhance_analysis(self, dir_path: Path) -> None:
        """
        Try to enhance analysis using advanced features if available.

        This method attempts to load the AdvancedFeaturesController and
        apply enhancements to the analysis results. If advanced features
        are not available, it gracefully continues without enhancement.

        Args:
            dir_path: Path to the analyzed directory
        """
        try:
            # Try to import and use advanced features
            sys.path.insert(0, str(Path(__file__).parent / "src"))

            from codebase_gardener.core import (
                advanced_features_controller,
                check_advanced_features,
            )

            # Check if user requested advanced mode specifically
            advanced_mode_requested = getattr(self, "_advanced_mode_requested", False)

            # Check if any advanced features are available
            features_available = check_advanced_features()

            if not features_available:
                if advanced_mode_requested:
                    print(
                        "⚠️  Advanced mode requested but features not available - using standard analysis"
                    )
                return

            # Enhanced feedback when features are available
            if advanced_mode_requested:
                print("🚀 Advanced features detected - applying enhanced analysis...")
            else:
                print("🚀 Advanced features detected - enhancing analysis...")

            # Get enhancement level for this codebase
            enhancement_level = advanced_features_controller.get_enhancement_level(
                dir_path
            )

            # Enhance the analysis context
            enhanced_context = advanced_features_controller.enhance_analysis(
                self.analysis_results
            )

            # Update analysis results with enhancements
            if enhanced_context != self.analysis_results:
                self.analysis_results.update(enhanced_context)
                enhancement_count = len(
                    [k for k in enhanced_context.keys() if k.startswith("enhanced_")]
                )

                if advanced_mode_requested:
                    print(
                        f"✨ Advanced analysis complete! Enhancement level: '{enhancement_level}' with {enhancement_count} features applied"
                    )
                else:
                    print(
                        f"✨ Analysis enhanced to '{enhancement_level}' level with {enhancement_count} advanced features"
                    )

                # Show what enhancements were applied
                if enhancement_count > 0:
                    applied_features = [
                        k.replace("enhanced_", "")
                        for k in enhanced_context.keys()
                        if k.startswith("enhanced_")
                    ]
                    print(f"🎯 Applied enhancements: {', '.join(applied_features)}")

        except ImportError:
            # Advanced features not available - this is expected for MVP mode
            if getattr(self, "_advanced_mode_requested", False):
                print(
                    "⚠️  Advanced features not available - continuing with standard analysis"
                )
        except Exception as e:
            # Log but don't fail - advanced features should never break basic functionality
            print(
                f"⚠️ Advanced feature enhancement failed (continuing with basic analysis): {e}"
            )


def print_welcome():
    """Print welcome message and system info."""
    print("🔍 Codebase Intelligence Auditor")
    print("=" * 50)
    print("A simple interface for AI-powered code analysis")
    print(f"Model: {os.environ.get('OLLAMA_MODEL', 'llama3.2:3b')}")
    print(f"Host: {os.environ.get('OLLAMA_HOST', 'http://localhost:11434')}")
    print("=" * 50)


def print_help():
    """Print available commands and usage examples."""
    print("\n📋 Available Commands:")
    print("  analyze <directory>     - Analyze a codebase directory")
    print(
        "  analyze --advanced <directory> - Analyze with advanced features (if available)"
    )
    print("  chat <question>         - Ask questions about the analysis")
    print("  export [filename]       - Export markdown report")
    print("  status                  - Show current analysis status")
    print("  features                - Show available advanced features")
    print("\n📂 Project Management:")
    print("  projects                - List all registered projects")
    print("  project create <dir>    - Create/register a new project")
    print("  project info [id]       - Show project information")
    print("  project switch <id>     - Switch to a different project context")
    print("  project cleanup         - Clean up old project data")
    print("  project health          - Check project health status")
    print("\n🔧 System:")
    print("  help                    - Show this help message")
    print("  quit/exit/q             - Exit the auditor")
    print("\n💡 Examples:")
    print("  > analyze ./my-project")
    print("  > analyze --advanced ./my-project")
    print("  > project create ./my-project")
    print("  > project switch abc123")
    print("  > chat What are the main architecture patterns?")
    print("  > export my-analysis.md")
    print("  > status")
    print("  > features")


def format_analysis_summary(analysis_results):
    """Format a brief summary of analysis results."""
    if not analysis_results:
        return "No analysis completed yet."

    caps = analysis_results.get("caps", {})
    files_included = caps.get("files_included", 0)
    files_skipped = caps.get("files_skipped", 0)
    bytes_included = caps.get("bytes_included", 0)
    files_truncated = caps.get("files_truncated", 0)

    total_files = files_included + files_skipped
    truncated_note = f" ({files_truncated} truncated)" if files_truncated > 0 else ""

    return f"📊 Analysis Summary: {files_included}/{total_files} files{truncated_note}, {bytes_included:,} bytes processed"


def main():
    """Enhanced CLI interface for the codebase auditor."""
    print_welcome()
    print_help()

    auditor = CodebaseAuditor()

    while True:
        try:
            # Show current status
            if auditor.analysis_results:
                print(f"\n{format_analysis_summary(auditor.analysis_results)}")

            command = input("\n🔍 > ").strip()

            if not command:
                continue

            if command.lower() in ["quit", "exit", "q"]:
                print("👋 Goodbye!")
                break

            elif command.lower() == "help":
                print_help()

            elif command.lower() == "status":
                # Show analysis status
                if auditor.analysis_results:
                    print(f"\n✅ {format_analysis_summary(auditor.analysis_results)}")
                    files_list = auditor.analysis_results.get("file_list", [])
                    if files_list:
                        print(f"📁 Files analyzed: {len(files_list)} files")
                        if len(files_list) <= 10:
                            for f in files_list:
                                print(f"   - {f}")
                        else:
                            for f in files_list[:5]:
                                print(f"   - {f}")
                            print(f"   ... and {len(files_list) - 5} more files")
                else:
                    print(
                        "❌ No analysis completed yet. Use 'analyze <directory>' to start."
                    )

                # Show project status
                pm = auditor._get_project_manager()
                if pm and auditor._current_project_id:
                    try:
                        project = pm["registry"].get_project(
                            auditor._current_project_id
                        )
                        if project:
                            print(f"\n📂 Current Project: {project.name}")
                            print(f"   ID: {project.project_id}")
                            print(f"   Path: {project.source_path}")
                            print(f"   Status: {project.training_status.value}")

                            # Show conversation context
                            context = pm["context_manager"].get_context(
                                auditor._current_project_id
                            )
                            if context and context.conversation_history:
                                chat_messages = [
                                    msg
                                    for msg in context.conversation_history
                                    if msg.role in ["user", "assistant"]
                                ]
                                if chat_messages:
                                    print(
                                        f"   Chat History: {len(chat_messages)} messages"
                                    )
                    except (AttributeError, KeyError, TypeError):
                        pass
                elif pm:
                    print("\n📂 Project Management: Available (no current project)")
                    try:
                        projects = pm["registry"].list_projects()
                        if projects:
                            print(f"   Registered Projects: {len(projects)}")
                        else:
                            print(
                                "   Use 'project create <dir>' to create your first project"
                            )
                    except (AttributeError, KeyError, TypeError):
                        pass
                else:
                    print("\n📂 Project Management: Not available")

            elif command.startswith("analyze "):
                # Parse analyze command with optional --advanced flag
                command_parts = command[8:].strip().split()

                # Check for --advanced flag
                advanced_mode = False
                directory = None

                if command_parts and command_parts[0] == "--advanced":
                    advanced_mode = True
                    directory = (
                        " ".join(command_parts[1:]) if len(command_parts) > 1 else ""
                    )
                else:
                    directory = " ".join(command_parts)

                if not directory:
                    print("❌ Please specify a directory to analyze")
                    print("   Example: analyze ./my-project")
                    print("   Example: analyze --advanced ./my-project")
                    continue

                # Input validation for directory argument
                if len(directory) > 1000:  # Reasonable path length limit
                    print("❌ Directory path too long")
                    continue

                # Basic sanitization - remove potentially dangerous characters
                if any(char in directory for char in ["|", "&", ";", "`", "$"]):
                    print("❌ Invalid characters in directory path")
                    continue

                if not os.path.exists(directory):
                    print("❌ Directory not found")
                    continue

                # Check for advanced features and provide user feedback
                if advanced_mode:
                    print(f"\n🚀 Starting advanced analysis of: {directory}")
                    try:
                        # Try to import advanced features for availability check
                        sys.path.insert(0, str(Path(__file__).parent / "src"))
                        from codebase_gardener.core import (
                            check_advanced_features,
                            get_enhancement_level,
                        )

                        if check_advanced_features():
                            enhancement_level = get_enhancement_level(Path(directory))
                            print(
                                f"✨ Advanced features available - enhancement level: {enhancement_level}"
                            )
                        else:
                            print(
                                "⚠️  Advanced features requested but not available - falling back to standard analysis"
                            )
                            print(
                                "   (This is expected behavior - advanced features are not yet fully implemented)"
                            )
                    except ImportError:
                        print(
                            "⚠️  Advanced features not available - using standard analysis"
                        )
                else:
                    print(f"\n🔄 Starting analysis of: {directory}")

                print("   This may take a moment...")

                def progress_callback(msg):
                    if "Preflight" in msg and "failed" in msg:
                        print("⚠️  Model check warning (continuing anyway)")
                    elif msg.startswith("⚠️"):
                        print(f"⚠️  {msg}")
                    else:
                        print(f"📝 {msg}")

                # Store the advanced mode preference for potential enhancement logic
                auditor._advanced_mode_requested = advanced_mode

                auditor.analyze_codebase(directory, progress_callback=progress_callback)
                print("\n✅ Analysis complete!")
                print(f"{format_analysis_summary(auditor.analysis_results)}")

                # Reset the mode preference
                auditor._advanced_mode_requested = False

            elif command.startswith("chat "):
                question = command[5:].strip()
                if not question:
                    print("❌ Please ask a question")
                    print("   Example: chat What are the main issues in this codebase?")
                    continue

                # Input validation for question
                if len(question) > 5000:  # Reasonable question length limit
                    print("❌ Question too long (max 5000 characters)")
                    continue

                if not auditor.analysis_results:
                    print("❌ No analysis available. Run 'analyze <directory>' first.")
                    continue

                print(f"\n🤖 Thinking about: {question}")
                response = auditor.chat(question)
                print(f"\n💭 Response:\n{response}")

            elif command.startswith("export"):
                if not auditor.analysis_results:
                    print("❌ No analysis available. Run 'analyze <directory>' first.")
                    continue

                # Parse optional filename
                parts = command.split(" ", 1)
                if len(parts) > 1 and parts[1].strip():
                    filename = parts[1].strip()
                    if not filename.endswith(".md"):
                        filename += ".md"
                else:
                    filename = f"codebase_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

                report = auditor.export_markdown()
                try:
                    with open(filename, "w", encoding="utf-8") as f:
                        f.write(report)
                    print(f"📄 Report exported to: {filename}")
                    print(f"   Size: {len(report):,} characters")
                except OSError:
                    print("❌ Failed to write report file")

            elif command.lower() == "features":
                print("\n🔧 Advanced Features Status:")
                try:
                    # Try to import and check advanced features
                    sys.path.insert(0, str(Path(__file__).parent / "src"))
                    from codebase_gardener.core import (
                        advanced_features_controller,
                        check_advanced_features,
                    )

                    if check_advanced_features():
                        print("✨ Advanced features are available!")
                        available_features = (
                            advanced_features_controller.get_available_features()
                        )
                        for feature in available_features:
                            print(f"   ✅ {feature}")

                        # Show resource status
                        resource_status = (
                            advanced_features_controller.get_resource_status()
                        )
                        if resource_status and "memory_used_gb" in resource_status:
                            print("\n💾 Resource Status:")
                            print(
                                f"   Memory: {resource_status['memory_used_gb']:.1f}GB used, {resource_status['memory_available_gb']:.1f}GB available"
                            )
                            print(
                                f"   Disk: {resource_status['disk_free_gb']:.1f}GB free"
                            )
                            constraint_status = (
                                "✅ Within constraints"
                                if resource_status.get("within_constraints")
                                else "⚠️ Near limits"
                            )
                            print(f"   Status: {constraint_status}")

                    else:
                        print("⚠️  Advanced features are not currently available")
                        print("   Available features: 0/6")
                        print("\n📋 Feature Requirements:")
                        print(
                            "   🔄 rag_retrieval: Requires vector_store, project_vector_store_manager"
                        )
                        print("   🔍 semantic_search: Requires vector_store")
                        print(
                            "   🧠 training_pipeline: Requires peft_manager, training_pipeline, dynamic_model_loader"
                        )
                        print(
                            "   📂 project_management: Requires project_registry, project_context_manager"
                        )
                        print("   💾 vector_storage: Requires vector_store")
                        print(
                            "   🎯 embedding_generation: Requires vector_store, dynamic_model_loader"
                        )
                        print(
                            "\n💡 Note: This is expected behavior during MVP development"
                        )

                except ImportError:
                    print("⚠️  Advanced features system not available")
                    print("   Running in basic MVP mode")
                    print("   All core functionality is available")

            elif command.lower() == "projects":
                auditor._handle_projects_command()

            elif command.startswith("project "):
                parts = command[8:].strip().split()
                if not parts:
                    print("❌ Please specify a project subcommand")
                    print("   Available: create, info, switch, cleanup, health")
                    print("   Example: project create ./my-project")
                    continue

                subcommand = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                auditor._handle_project_command(subcommand, args)

            else:
                print(f"❌ Unknown command: {command}")
                print("   Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ An unexpected error occurred: {type(e).__name__}")
            print("   Type 'help' for available commands")


if __name__ == "__main__":
    main()
