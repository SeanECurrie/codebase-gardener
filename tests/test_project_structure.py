# tests/test_project_structure.py
import importlib
from pathlib import Path


def test_repo_layout_files_exist():
    assert Path("codebase_auditor.py").is_file()
    assert Path("simple_file_utils.py").is_file()


def test_imports_work():
    assert importlib.import_module("codebase_auditor")
    assert importlib.import_module("simple_file_utils")


def test_entry_point_declared():
    # lightweight check that pyproject declares the console entry
    text = Path("pyproject.toml").read_text(encoding="utf-8")
    assert 'codebase-auditor = "codebase_auditor:main"' in text


def test_smoke_script_present():
    p = Path("scripts/smoke_cli.py")
    assert p.is_file()
    body = p.read_text(encoding="utf-8")
    # must use SimpleFileUtilities and write project-analysis.md
    assert "SimpleFileUtilities" in body and "project-analysis.md" in body
