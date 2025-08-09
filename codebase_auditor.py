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
from datetime import datetime
from pathlib import Path
from typing import Any

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
    print("Error: Could not import SimpleFileUtilities. Make sure simple_file_utils.py is in the same directory.")
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
        ollama_host = ollama_host or os.environ.get("OLLAMA_HOST", "http://localhost:11434")
        self.model_name = model_name or os.environ.get("OLLAMA_MODEL", "gpt-oss-20b")

        self.client = ollama.Client(ollama_host)
        self.file_utils = SimpleFileUtilities()
        self.analysis_results: dict[str, Any] | None = None

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

        return base_prompt.format(
            file_count=file_count,
            size_desc=f"~{total_bytes//1024}KB" if total_bytes < 1024*1024 else f"~{total_bytes//(1024*1024)}MB"
        ) + specific_prompt + "\n\nCodebase to analyze:\n{file_contents}"

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
            dir_path = Path(directory_path).resolve()

            if not dir_path.exists() or not dir_path.is_dir():
                return f"Error: Directory '{directory_path}' does not exist or is not accessible."

            if progress_callback:
                progress_callback("Starting codebase analysis...")

            # Find source files using existing FileUtilities
            print("🔍 Discovering source files...")
            source_files = self.file_utils.find_source_files(
                dir_path,
                progress_callback=progress_callback
            )

            if not source_files:
                return f"No source files found in '{directory_path}'"

            print(f"📁 Found {len(source_files)} source files")

            # Optional preflight: verify model is available with a tiny check
            if progress_callback:
                progress_callback(f"Verifying model '{self.model_name}' is available...")
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
                progress_callback(f"Reading up to {min(len(source_files), self.max_files)} source files (caps applied)...")

            file_contents, stats = self._read_and_combine_files_with_caps(
                source_files, progress_callback, base_dir=dir_path
            )

            if not file_contents.strip():
                return "Error: No readable content found in source files"

            # Send to model for analysis
            print(f"🤖 Analyzing codebase with {self.model_name}...")
            if progress_callback:
                progress_callback(f"Sending codebase to {self.model_name} for analysis...")

            # Generate context-appropriate prompt
            analysis_prompt = self._generate_analysis_prompt(len(source_files), stats['bytes_included'])
            full_prompt = analysis_prompt.format(file_contents=file_contents)

            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt
            )

            analysis_text = response['response']

            # Store results
            self.analysis_results = {
                'full_analysis': analysis_text,
                'file_list': [str(f) for f in source_files],
                'directory_path': str(dir_path),
                'timestamp': datetime.now().isoformat(),
                'file_count': len(source_files),
                'caps': stats
            }

            print("✅ Analysis complete!")
            if progress_callback:
                progress_callback("Analysis complete! You can now ask questions or export the report.")

            return f"Analysis complete! Analyzed {len(source_files)} files. Ask me questions or export markdown report."

        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return error_msg

    def _read_and_combine_files_with_caps(
        self,
        source_files: list[Path],
        progress_callback=None,
        base_dir: Path | None = None
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
                        f"Reading files... {idx}/{len(limited_files)} (total ~{total_bytes//1024} KB)"
                    )

                with open(file_path, encoding='utf-8', errors='ignore') as f:
                    content = f.read()

                # Enforce per-file cap
                content_bytes = content.encode('utf-8')
                if len(content_bytes) > self.max_file_bytes:
                    content = content_bytes[: self.max_file_bytes].decode('utf-8', errors='ignore')
                    truncated_files += 1
                    content += "\n... [TRUNCATED] ...\n"
                    content_bytes = content.encode('utf-8')

                # Enforce total cap
                if total_bytes + len(content_bytes) > self.max_total_bytes:
                    combined_content.append("\n... [GLOBAL CONTENT LIMIT REACHED, REMAINING FILES SKIPPED] ...\n")
                    break

                # Add file header and content
                root = base_dir or (
                    Path(self.analysis_results['directory_path']) if self.analysis_results else file_path.parent
                )
                try:
                    relative_path = file_path.relative_to(root)
                except Exception:
                    relative_path = file_path.name
                combined_content.append(f"\n=== FILE: {relative_path} ===\n{content}\n")

                files_read += 1
                total_bytes += len(content_bytes)

            except Exception as e:
                print(f"⚠️  Warning: Could not read {file_path}: {e}")
                continue

        if progress_callback:
            progress_callback(f"Included {files_read} files (~{total_bytes//1024} KB). Truncated: {truncated_files}")

        stats = {
            'max_files': self.max_files,
            'max_file_bytes': self.max_file_bytes,
            'max_total_bytes': self.max_total_bytes,
            'files_included': files_read,
            'bytes_included': total_bytes,
            'files_truncated': truncated_files,
            'files_skipped': max(0, len(source_files) - files_read),
        }

        return "\n".join(combined_content), stats

    def _preflight_model_check(self) -> bool:
        """Simple model availability check using a tiny generation call."""
        try:
            test_prompt = "You are alive? Answer 'yes'."
            resp = self.client.generate(model=self.model_name, prompt=test_prompt)
            return bool(resp and isinstance(resp, dict) and resp.get('response'))
        except Exception:
            return False

    def chat(self, question: str) -> str:
        """
        Ask questions about the analyzed codebase.

        Args:
            question: User's question about the codebase

        Returns:
            AI response based on the analysis
        """
        if not self.analysis_results:
            return "Error: No codebase analysis available. Please run analyze_codebase() first."

        try:
            full_prompt = self.chat_prompt.format(
                previous_analysis=self.analysis_results['full_analysis'],
                user_question=question
            )

            response = self.client.generate(
                model=self.model_name,
                prompt=full_prompt
            )

            return response['response']

        except Exception as e:
            return f"Chat failed: {str(e)}"

    def export_markdown(self) -> str:
        """
        Export analysis results as formatted markdown.

        Returns:
            Markdown-formatted analysis report
        """
        if not self.analysis_results:
            return "Error: No analysis results to export. Please run analyze_codebase() first."

        timestamp = datetime.fromisoformat(self.analysis_results['timestamp']).strftime("%Y-%m-%d %H:%M:%S")

        markdown_report = f"""# Codebase Analysis Report

**Generated:** {timestamp}
**Directory:** `{self.analysis_results['directory_path']}`
**Files Analyzed:** {self.analysis_results['file_count']}

---

{self.analysis_results['full_analysis']}

---

## Files Analyzed

The following {self.analysis_results['file_count']} source files were included in this analysis:

"""

        # Add file list
        for file_path in sorted(self.analysis_results['file_list']):
            relative_path = Path(file_path).relative_to(self.analysis_results['directory_path'])
            markdown_report += f"- `{relative_path}`\n"

        markdown_report += """
---

*Report generated by Codebase Intelligence Auditor using gpt-oss-20b*
"""

        return markdown_report


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
    print("  chat <question>         - Ask questions about the analysis")
    print("  export [filename]       - Export markdown report")
    print("  status                  - Show current analysis status")
    print("  help                    - Show this help message")
    print("  quit/exit/q             - Exit the auditor")
    print("\n💡 Examples:")
    print("  > analyze ./my-project")
    print("  > chat What are the main architecture patterns?")
    print("  > export my-analysis.md")
    print("  > status")


def format_analysis_summary(analysis_results):
    """Format a brief summary of analysis results."""
    if not analysis_results:
        return "No analysis completed yet."

    caps = analysis_results.get('caps', {})
    files_included = caps.get('files_included', 0)
    files_skipped = caps.get('files_skipped', 0)
    bytes_included = caps.get('bytes_included', 0)
    files_truncated = caps.get('files_truncated', 0)

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

            if command.lower() in ['quit', 'exit', 'q']:
                print("👋 Goodbye!")
                break

            elif command.lower() == 'help':
                print_help()

            elif command.lower() == 'status':
                if auditor.analysis_results:
                    print(f"\n✅ {format_analysis_summary(auditor.analysis_results)}")
                    files_list = auditor.analysis_results.get('file_list', [])
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
                    print("❌ No analysis completed yet. Use 'analyze <directory>' to start.")

            elif command.startswith('analyze '):
                directory = command[8:].strip()
                if not directory:
                    print("❌ Please specify a directory to analyze")
                    print("   Example: analyze ./my-project")
                    continue

                if not os.path.exists(directory):
                    print(f"❌ Directory not found: {directory}")
                    continue

                print(f"\n🔄 Starting analysis of: {directory}")
                print("   This may take a moment...")

                def progress_callback(msg):
                    if "Preflight" in msg and "failed" in msg:
                        print("⚠️  Model check warning (continuing anyway)")
                    elif msg.startswith("⚠️"):
                        print(f"⚠️  {msg}")
                    else:
                        print(f"📝 {msg}")

                auditor.analyze_codebase(directory, progress_callback=progress_callback)
                print("\n✅ Analysis complete!")
                print(f"{format_analysis_summary(auditor.analysis_results)}")

            elif command.startswith('chat '):
                question = command[5:].strip()
                if not question:
                    print("❌ Please ask a question")
                    print("   Example: chat What are the main issues in this codebase?")
                    continue

                if not auditor.analysis_results:
                    print("❌ No analysis available. Run 'analyze <directory>' first.")
                    continue

                print(f"\n🤖 Thinking about: {question}")
                response = auditor.chat(question)
                print(f"\n💭 Response:\n{response}")

            elif command.startswith('export'):
                if not auditor.analysis_results:
                    print("❌ No analysis available. Run 'analyze <directory>' first.")
                    continue

                # Parse optional filename
                parts = command.split(' ', 1)
                if len(parts) > 1 and parts[1].strip():
                    filename = parts[1].strip()
                    if not filename.endswith('.md'):
                        filename += '.md'
                else:
                    filename = f"codebase_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"

                report = auditor.export_markdown()
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"📄 Report exported to: {filename}")
                print(f"   Size: {len(report):,} characters")

            else:
                print(f"❌ Unknown command: {command}")
                print("   Type 'help' for available commands")

        except KeyboardInterrupt:
            print("\n👋 Goodbye!")
            break
        except Exception as e:
            print(f"❌ Error: {e}")
            print("   Type 'help' for available commands")


if __name__ == "__main__":
    main()
