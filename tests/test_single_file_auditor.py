#!/usr/bin/env python3
import os
from pathlib import Path
from unittest.mock import patch


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

