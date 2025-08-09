#!/usr/bin/env python3
from pathlib import Path
from unittest.mock import patch


def test_basic_file_discovery(tmp_path: Path):
    """Test file discovery with various project sizes."""
    # Create small project
    (tmp_path / "main.py").write_text("print('hello')")
    (tmp_path / ".gitignore").write_text("*.pyc")
    (tmp_path / "node_modules").mkdir()
    (tmp_path / "node_modules" / "dep.js").write_text("// dependency")

    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    utils = SimpleFileUtilities()
    files = utils.find_source_files(tmp_path)

    # Should find .py but exclude node_modules and .gitignore
    assert len(files) == 1
    assert files[0].name == "main.py"


def test_analysis_prompt_generation(tmp_path: Path):
    """Test analysis prompts adapt to project size."""
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))
    from codebase_auditor import CodebaseAuditor

    auditor = CodebaseAuditor(model_name="test-model")

    # Test small project prompt
    small_prompt = auditor._generate_analysis_prompt(3, 1500)
    assert "small project" in small_prompt.lower()

    # Test medium project prompt
    medium_prompt = auditor._generate_analysis_prompt(25, 50000)
    assert "architecture" in medium_prompt.lower()

    # Test large project prompt
    large_prompt = auditor._generate_analysis_prompt(150, 500000)
    assert "strategic" in large_prompt.lower() or "high-level" in large_prompt.lower()


def test_chat_functionality():
    """Test chat requires analysis first."""
    import sys

    sys.path.insert(0, str(Path(__file__).parents[1]))

    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Mock chat response"}

        from codebase_auditor import CodebaseAuditor

        auditor = CodebaseAuditor(model_name="test-model")

        # Should fail without analysis
        result = auditor.chat("What is this?")
        assert "No codebase analysis available" in result

        # Mock analysis results
        auditor.analysis_results = {"full_analysis": "Test analysis"}

        result = auditor.chat("What is this?")
        assert result == "Mock chat response"


def test_single_file_auditor_basic(tmp_path: Path):
    # Create a tiny project
    (tmp_path / "a.py").write_text("def a():\n    return 1\n")
    (tmp_path / "b.js").write_text("function b() { return 2; }\n")

    # Mock ollama.Client.generate to avoid real model calls
    with patch("ollama.Client") as mock_client_cls:
        mock_client = mock_client_cls.return_value
        mock_client.generate.return_value = {"response": "Mock analysis"}

        # Import auditor
        import sys

        sys.path.insert(0, str(Path(__file__).parents[1]))
        from codebase_auditor import CodebaseAuditor

        auditor = CodebaseAuditor(model_name="test-model")
        result = auditor.analyze_codebase(str(tmp_path))
        assert "Analysis complete" in result
        assert auditor.analysis_results is not None
        assert auditor.analysis_results.get("full_analysis")

        # Chat
        answer = auditor.chat("What is here?")
        assert isinstance(answer, str)

        # Export
        md = auditor.export_markdown()
        assert "# Codebase Analysis Report" in md
        assert "Files Analyzed:" in md
