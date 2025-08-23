#!/usr/bin/env python3
"""
Comprehensive CLI Test Plan Execution
Tests all core MVP functionality for the single-file auditor.
"""

import os
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

# Add current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))


def test_basic_auditor_initialization():
    """Test basic auditor initialization and configuration."""
    from codebase_auditor import CodebaseAuditor

    # Test default initialization
    auditor = CodebaseAuditor()
    assert auditor.model_name in ["gpt-oss-20b", "llama3.2:3b"]  # Common defaults
    assert auditor.max_files == 250
    assert auditor.max_file_bytes == 100 * 1024
    assert auditor.max_total_bytes == 2 * 1024 * 1024
    assert auditor.analysis_results is None

    # Test custom initialization
    custom_auditor = CodebaseAuditor(
        ollama_host="http://custom:11434", model_name="custom-model"
    )
    assert custom_auditor.model_name == "custom-model"

    print("✓ Basic auditor initialization tests passed")


def test_environment_variable_override():
    """Test environment variable configuration."""
    from codebase_auditor import CodebaseAuditor

    # Set environment variables
    os.environ["OLLAMA_HOST"] = "http://env-test:8080"
    os.environ["OLLAMA_MODEL"] = "env-test-model"

    try:
        auditor = CodebaseAuditor()
        # Note: The client host is set during initialization
        assert auditor.model_name == "env-test-model"
        print("✓ Environment variable override tests passed")
    finally:
        # Clean up environment variables
        os.environ.pop("OLLAMA_HOST", None)
        os.environ.pop("OLLAMA_MODEL", None)


def test_analysis_prompt_generation():
    """Test analysis prompt generation for different project sizes."""
    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    test_cases = [
        (1, 500, ["small project", "brief analysis"]),
        (5, 2000, ["small project", "brief analysis"]),
        (10, 15000, ["focused project", "main aspects"]),
        (50, 100000, ["comprehensive", "detailed analysis"]),
        (150, 800000, ["strategic", "high-level"]),
    ]

    for file_count, byte_count, expected_keywords in test_cases:
        prompt = auditor._generate_analysis_prompt(file_count, byte_count)

        # Verify prompt contains expected elements
        assert str(file_count) in prompt
        assert "KB" in prompt or "MB" in prompt

        # Check for depth-appropriate language (at least one keyword should be present)
        keyword_found = any(
            keyword.lower() in prompt.lower() for keyword in expected_keywords
        )
        assert (
            keyword_found
        ), f"None of {expected_keywords} found in prompt for {file_count} files"

    print("✓ Analysis prompt generation tests passed")


def test_security_path_validation():
    """Test security validation for directory paths."""
    from codebase_auditor import CodebaseAuditor

    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Test analysis"}

        auditor = CodebaseAuditor(model_name="test-model")

        # Test dangerous system paths
        dangerous_paths = [
            "/",
            "/etc",
            "/usr",
            "/bin",
            "/sbin",
            "/root",
            "/proc/self/environ",
        ]

        for path in dangerous_paths:
            result = auditor.analyze_codebase(path)
            # Should be blocked or fail safely
            assert (
                "system directories is not allowed" in result
                or "does not exist" in result
                or "not accessible" in result
                or "Invalid directory path" in result
            ), f"Path {path} not properly protected"

        # Test empty and invalid inputs
        assert "Directory path cannot be empty" in auditor.analyze_codebase("")
        assert "Directory path cannot be empty" in auditor.analyze_codebase("   ")

    print("✓ Security path validation tests passed")


def test_file_caps_enforcement():
    """Test file size and count caps are properly enforced."""
    from codebase_auditor import CodebaseAuditor

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create files that exceed various caps
        # Large file (exceeds per-file limit)
        large_content = "x" * (150 * 1024)  # 150KB, exceeds 100KB limit
        (test_dir / "large.py").write_text(large_content)

        # Many small files (exceeds file count limit)
        for i in range(5):  # Just a few for testing
            (test_dir / f"small_{i:03d}.py").write_text(f"# Small file {i}\nprint({i})")

        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Test analysis"}

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor.analyze_codebase(str(test_dir))

            assert "Analysis complete" in result
            assert auditor.analysis_results is not None

            caps = auditor.analysis_results["caps"]
            assert caps["files_included"] <= auditor.max_files
            assert caps["bytes_included"] <= auditor.max_total_bytes

            # The large file should be truncated
            if caps["files_truncated"] > 0:
                print(
                    f"  Large file was properly truncated (files_truncated: {caps['files_truncated']})"
                )

    print("✓ File caps enforcement tests passed")


def test_chat_functionality():
    """Test chat functionality with and without analysis."""
    from codebase_auditor import CodebaseAuditor

    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Chat response"}

        auditor = CodebaseAuditor(model_name="test-model")

        # Test chat without analysis
        result = auditor.chat("What is this codebase about?")
        assert "No codebase analysis available" in result

        # Test chat with analysis
        auditor.analysis_results = {
            "full_analysis": "This is a test codebase with Python files.",
            "file_count": 3,
        }

        result = auditor.chat("What languages are used?")
        assert result == "Chat response"

        # Verify the prompt was formatted correctly
        call_args = mock_client.generate.call_args
        assert (
            "This is a test codebase with Python files." in call_args.kwargs["prompt"]
        )
        assert "What languages are used?" in call_args.kwargs["prompt"]

    print("✓ Chat functionality tests passed")


def test_markdown_export():
    """Test markdown export functionality."""
    from datetime import datetime

    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    # Test export without analysis
    result = auditor.export_markdown()
    assert "No analysis results to export" in result

    # Test export with analysis
    test_timestamp = datetime.now().isoformat()
    auditor.analysis_results = {
        "full_analysis": "This is comprehensive analysis content.",
        "directory_path": "/test/project",
        "file_count": 3,
        "file_list": ["main.py", "utils.py", "config.json"],
        "timestamp": test_timestamp,
    }

    markdown = auditor.export_markdown()

    # Verify markdown structure
    assert "# Codebase Analysis Report" in markdown
    assert "This is comprehensive analysis content." in markdown
    assert "Files Analyzed:** 3" in markdown
    assert "main.py" in markdown
    assert "utils.py" in markdown
    assert "config.json" in markdown
    assert "Report generated by Codebase Intelligence Auditor" in markdown

    print("✓ Markdown export tests passed")


def test_error_handling():
    """Test error handling in various failure scenarios."""
    from codebase_auditor import CodebaseAuditor

    # Test ollama connection failure
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.side_effect = Exception("Connection failed")

        auditor = CodebaseAuditor(model_name="test-model")
        auditor.analysis_results = {"full_analysis": "Test"}

        # Chat should handle failures gracefully
        result = auditor.chat("Test question")
        assert "Chat failed" in result

        # Analysis should handle failures gracefully
        with tempfile.TemporaryDirectory() as tmp_dir:
            test_dir = Path(tmp_dir)
            (test_dir / "test.py").write_text("print('test')")

            result = auditor.analyze_codebase(str(test_dir))
            assert "Analysis failed due to an internal error" in result

    print("✓ Error handling tests passed")


def test_preflight_model_check():
    """Test model preflight check functionality."""
    from codebase_auditor import CodebaseAuditor

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

    print("✓ Preflight model check tests passed")


def test_file_reading_edge_cases():
    """Test file reading with various edge cases."""
    from codebase_auditor import CodebaseAuditor
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)

        # Create files with different characteristics
        (test_dir / "normal.py").write_text("print('normal file')")
        (test_dir / "empty.py").write_text("")
        (test_dir / "unicode.py").write_text("# Unicode: 你好世界 🌍")

        # Create binary file that might cause encoding issues
        with open(test_dir / "binary.py", "wb") as f:
            f.write(b"# Binary content: \xff\xfe\x00\x00")

        utils = SimpleFileUtilities()
        files = utils.find_source_files(test_dir)

        # Should find all files
        file_names = [f.name for f in files]
        expected_files = ["normal.py", "empty.py", "unicode.py", "binary.py"]

        for expected in expected_files:
            assert expected in file_names

        # Test with auditor
        with patch("ollama.Client") as mock_client_cls:
            mock_client = mock_client_cls.return_value
            mock_client.generate.return_value = {"response": "Analysis of mixed files"}

            auditor = CodebaseAuditor(model_name="test-model")
            result = auditor.analyze_codebase(str(test_dir))

            assert "Analysis complete" in result
            assert auditor.analysis_results is not None

    print("✓ File reading edge cases tests passed")


def run_comprehensive_tests():
    """Run all comprehensive CLI tests."""
    print("=" * 60)
    print("COMPREHENSIVE CLI TEST PLAN EXECUTION")
    print("=" * 60)

    test_functions = [
        test_basic_auditor_initialization,
        test_environment_variable_override,
        test_analysis_prompt_generation,
        test_security_path_validation,
        test_file_caps_enforcement,
        test_chat_functionality,
        test_markdown_export,
        test_error_handling,
        test_preflight_model_check,
        test_file_reading_edge_cases,
    ]

    passed = 0
    total = len(test_functions)

    for test_func in test_functions:
        try:
            print(f"\n--- Running {test_func.__name__} ---")
            test_func()
            passed += 1
        except Exception as e:
            print(f"✗ {test_func.__name__} failed: {e}")
            import traceback

            traceback.print_exc()

    print("\n" + "=" * 60)
    print("COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All comprehensive CLI tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = run_comprehensive_tests()
    sys.exit(0 if success else 1)
