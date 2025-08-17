#!/usr/bin/env python3
"""
Comprehensive CLI command testing for the MVP codebase auditor.
Tests all CLI commands and their validation logic.
"""

import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest


def test_cli_command_parsing():
    """Test CLI command parsing and validation."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    # Test command parsing would happen in main() function
    # We test the underlying functionality that commands depend on
    auditor = CodebaseAuditor(model_name="test-model")

    # Test initialization
    assert auditor.model_name == "test-model"
    assert auditor.max_files == 250
    assert auditor.max_file_bytes == 100 * 1024
    assert auditor.analysis_results is None


def test_analyze_command_validation():
    """Test analyze command input validation."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Test analysis"}

        auditor = CodebaseAuditor(model_name="test-model")

        # Test empty directory path
        result = auditor.analyze_codebase("")
        assert "Directory path cannot be empty" in result

        # Test whitespace-only path
        result = auditor.analyze_codebase("   ")
        assert "Directory path cannot be empty" in result

        # Test non-existent directory
        result = auditor.analyze_codebase("/nonexistent/path")
        assert "Directory does not exist" in result

        # Test system directory protection
        result = auditor.analyze_codebase("/etc")
        assert "Access to system directories is not allowed" in result

        result = auditor.analyze_codebase("/")
        assert "Access to system directories is not allowed" in result


def test_chat_command_validation():
    """Test chat command validation."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Test response"}

        auditor = CodebaseAuditor(model_name="test-model")

        # Test chat without analysis
        result = auditor.chat("What is this?")
        assert "No codebase analysis available" in result

        # Test chat with analysis
        auditor.analysis_results = {"full_analysis": "Test analysis"}
        result = auditor.chat("What is this?")
        assert result == "Test response"

        # Test empty question handling would be in main() CLI loop
        # The chat() method itself doesn't validate empty questions


def test_export_command_validation():
    """Test export command validation."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    # Test export without analysis
    result = auditor.export_markdown()
    assert "No analysis results to export" in result

    # Test export with analysis
    auditor.analysis_results = {
        "full_analysis": "Test analysis content",
        "directory_path": "/test/path",
        "file_count": 5,
        "file_list": ["/test/file1.py", "/test/file2.js"],
        "timestamp": "2025-08-09T12:00:00",
    }

    result = auditor.export_markdown()
    assert "# Codebase Analysis Report" in result
    assert "Test analysis content" in result
    assert "Files Analyzed" in result
    assert "file1.py" in result


def test_progress_callback_functionality():
    """Test progress callback mechanism."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        # Create test files
        test_dir = Path(tmp_dir)
        (test_dir / "test.py").write_text("print('test')")
        (test_dir / "test.js").write_text("console.log('test');")

        progress_messages = []

        def progress_callback(msg):
            progress_messages.append(msg)

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Test analysis"}

            auditor = CodebaseAuditor(model_name="test-model")
            auditor.analyze_codebase(str(test_dir), progress_callback=progress_callback)

            # Verify progress messages were generated
            assert len(progress_messages) > 0
            assert any("Starting codebase analysis" in msg for msg in progress_messages)
            assert any("Scanning directory" in msg for msg in progress_messages)


def test_file_caps_enforcement():
    """Test file size and count caps are enforced."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create a large file that exceeds max_file_bytes
        large_content = "x" * (200 * 1024)  # 200KB, exceeds 100KB limit
        (test_dir / "large.py").write_text(large_content)

        # Create many small files to test max_files limit
        for i in range(260):  # Exceeds 250 file limit
            (test_dir / f"file_{i:03d}.py").write_text(f"# File {i}")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Test analysis"}

            auditor = CodebaseAuditor(model_name="test-model")
            auditor.analyze_codebase(str(test_dir))

            # Verify caps were applied
            assert auditor.analysis_results is not None
            caps = auditor.analysis_results["caps"]

            # Should be limited to max_files
            assert caps["files_included"] <= auditor.max_files

            # Should have truncated files due to size limits
            assert caps["files_truncated"] > 0 or caps["files_skipped"] > 0


def test_security_input_sanitization():
    """Test security measures for input sanitization."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    # Test path traversal attempts
    dangerous_paths = [
        "../../../etc/passwd",
        "../../.ssh/id_rsa",
        "/proc/self/environ",
        "/bin/sh",
        "/usr/bin/python",
    ]

    for path in dangerous_paths:
        result = auditor.analyze_codebase(path)
        # Should either fail with "does not exist" or "system directories not allowed"
        assert (
            "does not exist" in result
            or "system directories is not allowed" in result
            or "Invalid directory path" in result
        )


def test_model_preflight_check():
    """Test model availability preflight check."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        (test_dir / "test.py").write_text("print('test')")

        # Test successful preflight
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "yes"}

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor._preflight_model_check()
            assert result is True

        # Test failed preflight
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.side_effect = Exception("Model not found")

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor._preflight_model_check()
            assert result is False


def test_analysis_prompt_generation_edge_cases():
    """Test analysis prompt generation for various project sizes."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    # Test boundary conditions
    test_cases = [
        (1, 500, "minimal"),  # Very small
        (5, 2000, "minimal"),  # Boundary of small
        (6, 10000, "focused"),  # Just above small
        (20, 50000, "focused"),  # Upper focused
        (21, 100000, "comprehensive"),  # Just above focused
        (100, 500000, "comprehensive"),  # Upper comprehensive
        (101, 1000000, "high-level"),  # Large project
        (500, 5000000, "high-level"),  # Very large
    ]

    for file_count, byte_count, expected_depth in test_cases:
        prompt = auditor._generate_analysis_prompt(file_count, byte_count)

        # Verify appropriate depth-specific language is used
        if expected_depth == "minimal":
            assert (
                "small project" in prompt.lower() or "brief analysis" in prompt.lower()
            )
        elif expected_depth == "focused":
            assert (
                "focused project" in prompt.lower() or "main aspects" in prompt.lower()
            )
        elif expected_depth == "comprehensive":
            assert (
                "comprehensive" in prompt.lower()
                or "detailed analysis" in prompt.lower()
            )
        elif expected_depth == "high-level":
            assert "strategic" in prompt.lower() or "high-level" in prompt.lower()

        # Verify file count and size are mentioned
        assert str(file_count) in prompt
        assert "KB" in prompt or "MB" in prompt


def test_error_handling_robustness():
    """Test error handling in various failure scenarios."""
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    # Test ollama connection failure
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.side_effect = Exception("Connection failed")

        auditor = CodebaseAuditor(model_name="test-model")

        # Mock analysis_results to test chat failure
        auditor.analysis_results = {"full_analysis": "Test analysis"}

        result = auditor.chat("Test question")
        assert "Chat failed" in result

    # Test file reading errors
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create a file and then make it unreadable
        test_file = test_dir / "unreadable.py"
        test_file.write_text("print('test')")
        test_file.chmod(0o000)  # Remove all permissions

        try:
            with patch("ollama.Client") as mock_client_cls:
                mock_client = mock_client_cls.return_value
                mock_client.generate.return_value = {"response": "Test analysis"}

                auditor = CodebaseAuditor(model_name="test-model")
                # Should handle unreadable files gracefully
                result = auditor.analyze_codebase(str(test_dir))
                # Should still complete, just skip unreadable files
                assert (
                    "Analysis complete" in result
                    or "Analysis failed" in result
                    or "Error: No readable content found" in result
                )
        finally:
            # Restore permissions for cleanup
            test_file.chmod(0o644)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
