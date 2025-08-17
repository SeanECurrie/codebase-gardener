#!/usr/bin/env python3
"""
Integration tests for end-to-end CLI workflows.
Tests complete user scenarios and multi-step interactions.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def create_sample_project(base_dir: Path, size: str = "small"):
    """Create sample projects of different sizes for testing."""
    if size == "small":
        # Small project: ≤5 files
        (base_dir / "main.py").write_text(
            """
#!/usr/bin/env python3
\"\"\"Main application entry point.\"\"\"

def main():
    print("Hello, World!")
    return 0

if __name__ == "__main__":
    main()
"""
        )
        (base_dir / "utils.py").write_text(
            """
\"\"\"Utility functions.\"\"\"

def helper_function(data):
    return data.strip().lower()
"""
        )
        (base_dir / "README.md").write_text("# Sample Project\nA simple test project.")

    elif size == "medium":
        # Medium project: 6-100 files
        create_sample_project(base_dir, "small")  # Include small files

        # Add more structure
        (base_dir / "src").mkdir()
        (base_dir / "tests").mkdir()
        (base_dir / "config").mkdir()

        for i in range(15):
            (base_dir / "src" / f"module_{i}.py").write_text(
                f"""
\"\"\"Module {i} implementation.\"\"\"

class Module{i}:
    def __init__(self):
        self.value = {i}

    def process(self, data):
        return data * {i}
"""
            )

        for i in range(10):
            (base_dir / "tests" / f"test_module_{i}.py").write_text(
                f"""
\"\"\"Tests for module {i}.\"\"\"
import unittest

class TestModule{i}(unittest.TestCase):
    def test_basic(self):
        self.assertEqual({i}, {i})
"""
            )

        (base_dir / "config" / "settings.py").write_text(
            "DEBUG = True\nLOG_LEVEL = 'INFO'"
        )
        (base_dir / "requirements.txt").write_text("requests>=2.25.0\nnumpy>=1.20.0")

    elif size == "large":
        # Large project: >100 files
        create_sample_project(base_dir, "medium")  # Include medium structure

        # Add many more files to exceed 100
        for subdir in ["lib", "tools", "scripts", "docs"]:
            (base_dir / subdir).mkdir()
            for i in range(30):
                (base_dir / subdir / f"{subdir}_file_{i}.py").write_text(
                    f"""
# {subdir.title()} file {i}
def {subdir}_function_{i}():
    return "{subdir}_{i}"
"""
                )


def test_complete_analysis_workflow_small_project():
    """Test complete analysis workflow on a small project."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        create_sample_project(test_dir, "small")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {
                "response": "This is a small Python project with a main entry point and utility functions. The code is well-structured with proper docstrings. Main components: main.py (entry point), utils.py (helper functions), README.md (documentation)."
            }

            auditor = CodebaseAuditor(model_name="test-model")

            # Step 1: Analyze codebase
            result = auditor.analyze_codebase(str(test_dir))
            assert "Analysis complete" in result
            assert auditor.analysis_results is not None

            # Verify analysis results structure
            assert "full_analysis" in auditor.analysis_results
            assert "file_list" in auditor.analysis_results
            assert "directory_path" in auditor.analysis_results
            assert "timestamp" in auditor.analysis_results
            assert auditor.analysis_results["file_count"] > 0

            # Step 2: Chat about the analysis
            mock_client.generate.return_value = {
                "response": "The main architectural pattern is a simple procedural design with utility functions separated from the main logic. The main.py file serves as the entry point."
            }

            chat_result = auditor.chat("What are the main architectural patterns?")
            assert "architectural pattern" in chat_result

            # Step 3: Export markdown report
            markdown = auditor.export_markdown()
            assert "# Codebase Analysis Report" in markdown
            assert "main.py" in markdown
            assert "utils.py" in markdown
            assert str(test_dir) in markdown


def test_complete_analysis_workflow_medium_project():
    """Test complete analysis workflow on a medium project."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        create_sample_project(test_dir, "medium")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {
                "response": "This is a well-structured medium-sized Python project with clear separation of concerns. Architecture includes: src/ for source code with multiple modules, tests/ for test files, config/ for configuration. The project follows standard Python packaging conventions."
            }

            auditor = CodebaseAuditor(model_name="test-model")

            # Analyze medium project
            result = auditor.analyze_codebase(str(test_dir))
            assert "Analysis complete" in result

            # Verify it detected many files
            assert auditor.analysis_results["file_count"] > 20

            # Verify proper directory structure detection
            file_list = auditor.analysis_results["file_list"]
            has_src = any("src/" in f for f in file_list)
            has_tests = any("tests/" in f or "test_" in f for f in file_list)
            has_config = any("config/" in f for f in file_list)

            assert (
                has_src or has_tests or has_config
            )  # Should detect organized structure


def test_multiple_chat_interactions():
    """Test multiple sequential chat interactions."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        create_sample_project(test_dir, "small")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value

            # Mock analysis response
            mock_client.generate.return_value = {"response": "Analysis complete"}
            auditor = CodebaseAuditor(model_name="test-model")
            auditor.analyze_codebase(str(test_dir))

            # Multiple chat interactions with different responses
            chat_responses = [
                "The code uses Python with standard library functions.",
                "The main entry point is in main.py which calls helper functions.",
                "There are 2 Python files and 1 documentation file.",
                "The code quality appears good with proper documentation.",
            ]

            questions = [
                "What programming language is used?",
                "How is the code organized?",
                "How many files are there?",
                "What's the code quality like?",
            ]

            for question, expected_response in zip(
                questions, chat_responses, strict=False
            ):
                mock_client.generate.return_value = {"response": expected_response}

                result = auditor.chat(question)
                assert result == expected_response

                # Verify the chat prompt includes previous analysis
                call_args = mock_client.generate.call_args
                assert "previous analysis" in call_args[1]["prompt"].lower()
                assert question in call_args[1]["prompt"]


def test_export_to_file_workflow():
    """Test exporting analysis to markdown file."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        create_sample_project(test_dir, "small")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Test analysis content"}

            auditor = CodebaseAuditor(model_name="test-model")
            auditor.analyze_codebase(str(test_dir))

            # Test export functionality
            markdown_content = auditor.export_markdown()

            # Verify markdown structure
            assert "# Codebase Analysis Report" in markdown_content
            assert "**Generated:**" in markdown_content
            assert "**Directory:**" in markdown_content
            assert "**Files Analyzed:**" in markdown_content
            assert "Test analysis content" in markdown_content
            assert "## Files Analyzed" in markdown_content

            # Verify file list is included
            for file_path in auditor.analysis_results["file_list"]:
                try:
                    # Handle macOS /private/var vs /var symlink issue
                    file_path_resolved = Path(file_path).resolve()
                    test_dir_resolved = test_dir.resolve()
                    relative_path = file_path_resolved.relative_to(test_dir_resolved)
                    assert f"`{relative_path}`" in markdown_content
                except ValueError:
                    # If relative_to fails, just check the filename is included
                    filename = Path(file_path).name
                    assert filename in markdown_content


def test_error_recovery_workflow():
    """Test error handling and recovery in workflows."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    # Test 1: Chat without analysis should fail gracefully
    auditor = CodebaseAuditor(model_name="test-model")
    result = auditor.chat("What is this?")
    assert "No codebase analysis available" in result

    # Test 2: Export without analysis should fail gracefully
    result = auditor.export_markdown()
    assert "No analysis results to export" in result

    # Test 3: Invalid directory should fail gracefully
    result = auditor.analyze_codebase("/nonexistent/directory")
    assert "does not exist" in result

    # Test 4: Network error during analysis should fail gracefully
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        create_sample_project(test_dir, "small")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.side_effect = Exception("Network error")

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor.analyze_codebase(str(test_dir))
            assert "Analysis failed" in result or "internal error" in result

    # Test 5: Network error during chat should fail gracefully
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.side_effect = Exception("Network error")

        auditor = CodebaseAuditor(model_name="test-model")
        auditor.analysis_results = {"full_analysis": "Test analysis"}

        result = auditor.chat("Test question")
        assert "Chat failed" in result


def test_environment_configuration_workflow():
    """Test different environment configurations."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    # Test default configuration
    auditor1 = CodebaseAuditor()
    assert auditor1.model_name == "gpt-oss-20b"  # Default from code

    # Test environment variable override
    with patch.dict(
        os.environ,
        {"OLLAMA_MODEL": "custom-model", "OLLAMA_HOST": "http://custom-host:11434"},
    ):
        auditor2 = CodebaseAuditor()
        assert auditor2.model_name == "custom-model"

    # Test explicit parameter override
    auditor3 = CodebaseAuditor(
        ollama_host="http://explicit-host:11434", model_name="explicit-model"
    )
    assert auditor3.model_name == "explicit-model"


def test_large_project_handling_workflow():
    """Test workflow with large project that triggers caps."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create project that exceeds file limits
        for i in range(260):  # Exceeds 250 file limit
            (test_dir / f"file_{i:03d}.py").write_text(f"# File {i}\nprint({i})")

        # Also create files that exceed size limits
        large_content = "# Large file\n" + ("x" * 200000)  # 200KB
        (test_dir / "large_file.py").write_text(large_content)

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {
                "response": "This is a large codebase with many files. The project appears to have repetitive structure with numbered files."
            }

            auditor = CodebaseAuditor(model_name="test-model")

            progress_messages = []

            def progress_callback(msg):
                progress_messages.append(msg)

            result = auditor.analyze_codebase(
                str(test_dir), progress_callback=progress_callback
            )

            # Should complete successfully despite size limits
            assert "Analysis complete" in result

            # Verify caps were applied
            caps = auditor.analysis_results["caps"]
            assert caps["files_included"] <= 250  # File count limit
            assert (
                caps["files_skipped"] > 0 or caps["files_truncated"] > 0
            )  # Some limiting occurred

            # Verify progress was reported
            assert len(progress_messages) > 0
            assert any("caps applied" in msg.lower() for msg in progress_messages)


def test_mixed_file_types_workflow():
    """Test workflow with mixed file types and languages."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create mixed language project
        (test_dir / "backend.py").write_text("# Python backend\ndef api(): pass")
        (test_dir / "frontend.js").write_text(
            "// JavaScript frontend\nfunction render() {}"
        )
        (test_dir / "styles.css").write_text("/* CSS styles */\nbody { margin: 0; }")
        (test_dir / "config.json").write_text('{"env": "development"}')
        (test_dir / "README.md").write_text("# Mixed Project\nPython + JavaScript")

        # Add some files that should be excluded
        (test_dir / "package-lock.json").write_text('{"lockfileVersion": 1}')
        (test_dir / "image.png").write_bytes(b"\x89PNG\r\n\x1a\n")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {
                "response": "This is a multi-language web application with Python backend, JavaScript frontend, CSS styling, and JSON configuration."
            }

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor.analyze_codebase(str(test_dir))

            assert "Analysis complete" in result

            # Verify it found the source files but excluded binaries
            file_list = auditor.analysis_results["file_list"]
            file_names = [Path(f).name for f in file_list]

            assert "backend.py" in file_names
            assert "frontend.js" in file_names
            assert "styles.css" in file_names
            assert "config.json" in file_names
            assert "README.md" in file_names

            # Should not include excluded files
            assert "image.png" not in file_names


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
