"""
Test project structure and basic imports.
"""

from pathlib import Path

import pytest


def test_package_imports():
    """Test that all main package modules can be imported."""
    # Test main package import
    import codebase_gardener
    assert codebase_gardener.__version__ == "0.1.0"

    # Test config import
    from codebase_gardener.config import settings
    assert settings.app_name == "Codebase Gardener"

    # Test main entry point import
    from codebase_gardener.main import main
    assert callable(main)


def test_package_structure():
    """Test that the package structure is correct."""
    import codebase_gardener
    package_path = Path(codebase_gardener.__file__).parent

    # Check that all expected modules exist
    expected_modules = [
        "config",
        "core",
        "models",
        "data",
        "ui",
        "utils"
    ]

    for module in expected_modules:
        module_path = package_path / module
        assert module_path.exists(), f"Module {module} directory not found"
        assert (module_path / "__init__.py").exists(), f"Module {module} missing __init__.py"


def test_settings_configuration():
    """Test that settings can be loaded and configured."""
    from codebase_gardener.config import settings

    # Test default values
    assert settings.app_name == "Codebase Gardener"
    assert settings.debug is False
    assert settings.log_level == "INFO"
    assert settings.ollama_base_url == "http://localhost:11434"

    # Test that data directory is set
    assert settings.data_dir is not None
    assert isinstance(settings.data_dir, Path)


def test_cli_entry_points():
    """Test that CLI entry points are properly configured."""
    import subprocess
    import sys

    # Test main entry point
    result = subprocess.run([
        sys.executable, "-c",
        "from codebase_gardener.main import main; print('CLI import works')"
    ], capture_output=True, text=True)

    assert result.returncode == 0
    assert "CLI import works" in result.stdout


if __name__ == "__main__":
    pytest.main([__file__])
