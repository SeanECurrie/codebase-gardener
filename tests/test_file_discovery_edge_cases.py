#!/usr/bin/env python3
"""
Comprehensive file discovery testing for edge cases and robustness.
Tests SimpleFileUtilities with various project structures and edge cases.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch
import pytest


def test_large_project_handling():
    """Test handling of large projects with many files."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create a large project structure
        for i in range(150):  # More than typical medium project
            (test_dir / f"file_{i:03d}.py").write_text(f"# File {i}\nprint({i})")
        
        # Create subdirectories with files
        for subdir in ["src", "tests", "docs"]:
            sub_path = test_dir / subdir
            sub_path.mkdir()
            for j in range(20):
                (sub_path / f"{subdir}_file_{j}.py").write_text(f"# {subdir} file {j}")
        
        progress_messages = []
        def progress_callback(msg):
            progress_messages.append(msg)
        
        files = utils.find_source_files(test_dir, progress_callback=progress_callback)
        
        # Verify large project handling
        expected_total = 150 + (3 * 20)  # 150 + 60 = 210 files
        assert len(files) == expected_total
        
        # Verify progress reporting
        assert len(progress_messages) > 0
        assert any("Scanning directory" in msg for msg in progress_messages)
        assert any("Completed" in msg for msg in progress_messages)


def test_binary_file_exclusion():
    """Test that binary files are properly excluded."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create source files (should be included)
        (test_dir / "main.py").write_text("print('hello')")
        (test_dir / "script.js").write_text("console.log('hello');")
        (test_dir / "style.css").write_text("body { color: red; }")
        
        # Create binary files (should be excluded)
        (test_dir / "image.png").write_bytes(b'\x89PNG\r\n\x1a\n')
        (test_dir / "executable.exe").write_bytes(b'MZ\x90\x00')
        (test_dir / "library.so").write_bytes(b'\x7fELF')
        (test_dir / "compiled.pyc").write_bytes(b'\x03\xf3\r\n')
        
        files = utils.find_source_files(test_dir)
        
        # Verify only source files are included
        file_names = [f.name for f in files]
        assert "main.py" in file_names
        assert "script.js" in file_names
        assert "style.css" in file_names
        assert "image.png" not in file_names
        assert "executable.exe" not in file_names
        assert "library.so" not in file_names
        assert "compiled.pyc" not in file_names


def test_directory_exclusion_patterns():
    """Test that excluded directories are properly skipped."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create normal source files
        (test_dir / "main.py").write_text("print('main')")
        (test_dir / "src").mkdir()
        (test_dir / "src" / "app.py").write_text("print('app')")
        
        # Create excluded directories with files
        excluded_dirs = [
            "node_modules", "__pycache__", ".git", "venv", ".venv", 
            "build", "dist", ".pytest_cache", ".vscode", ".idea"
        ]
        
        for exc_dir in excluded_dirs:
            dir_path = test_dir / exc_dir
            dir_path.mkdir()
            (dir_path / "should_be_excluded.py").write_text("print('excluded')")
        
        files = utils.find_source_files(test_dir)
        
        # Verify excluded directories are not scanned
        file_paths = [str(f) for f in files]
        assert any("main.py" in path for path in file_paths)
        assert any("app.py" in path for path in file_paths)
        
        # Verify excluded files are not included
        for exc_dir in excluded_dirs:
            assert not any(exc_dir in path for path in file_paths)


def test_permission_denied_handling():
    """Test handling of directories with restricted permissions."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create accessible files
        (test_dir / "accessible.py").write_text("print('accessible')")
        
        # Create directory and make it inaccessible
        restricted_dir = test_dir / "restricted"
        restricted_dir.mkdir()
        (restricted_dir / "hidden.py").write_text("print('hidden')")
        
        try:
            # Remove read and execute permissions
            restricted_dir.chmod(0o000)
            
            progress_messages = []
            def progress_callback(msg):
                progress_messages.append(msg)
            
            # Should handle permission errors gracefully
            files = utils.find_source_files(test_dir, progress_callback=progress_callback)
            
            # Should find accessible files but skip restricted directory
            file_names = [f.name for f in files]
            assert "accessible.py" in file_names
            assert "hidden.py" not in file_names
            
        finally:
            # Restore permissions for cleanup
            restricted_dir.chmod(0o755)


def test_file_encoding_handling():
    """Test handling of files with various encodings."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create files with different encodings
        (test_dir / "utf8.py").write_text("# UTF-8: Hello 世界", encoding="utf-8")
        (test_dir / "latin1.py").write_text("# Latin-1: Café", encoding="latin-1")
        
        # Create a file with problematic encoding
        with open(test_dir / "binary.py", "wb") as f:
            f.write(b"# Binary content with invalid UTF-8: \xff\xfe")
        
        # Should discover all files regardless of encoding
        files = utils.find_source_files(test_dir)
        
        file_names = [f.name for f in files]
        assert "utf8.py" in file_names
        assert "latin1.py" in file_names
        assert "binary.py" in file_names


def test_symbolic_link_handling():
    """Test handling of symbolic links."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create regular file
        source_file = test_dir / "original.py"
        source_file.write_text("print('original')")
        
        # Create symbolic link (if supported on platform)
        try:
            link_file = test_dir / "linked.py"
            link_file.symlink_to(source_file)
            
            files = utils.find_source_files(test_dir)
            
            # Should handle symlinks gracefully (may include or exclude based on implementation)
            # Main requirement is no crashes
            assert len(files) >= 1  # At least the original file
            
        except (OSError, NotImplementedError):
            # Symlinks not supported on this platform - skip test
            pytest.skip("Symbolic links not supported on this platform")


def test_empty_and_invalid_directories():
    """Test handling of edge case directory scenarios."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    utils = SimpleFileUtilities()
    
    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        
        # Test empty directory
        empty_dir = test_dir / "empty"
        empty_dir.mkdir()
        
        files = utils.find_source_files(empty_dir)
        assert len(files) == 0
        
        # Test directory with only excluded files
        only_excluded = test_dir / "only_excluded"
        only_excluded.mkdir()
        (only_excluded / "README.txt").write_text("Not a source file")  # .txt not in SOURCE_CODE_EXTENSIONS
        (only_excluded / "image.png").write_bytes(b'\x89PNG')
        
        files = utils.find_source_files(only_excluded)
        assert len(files) == 0
    
    # Test non-existent directory
    with pytest.raises(ValueError, match="Directory does not exist"):
        utils.find_source_files(Path("/nonexistent/directory"))
    
    # Test file instead of directory
    with tempfile.NamedTemporaryFile(suffix=".py") as tmp_file:
        with pytest.raises(ValueError, match="Directory does not exist"):
            utils.find_source_files(Path(tmp_file.name))


def test_language_filtering():
    """Test language-specific filtering functionality."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create files of different languages
        (test_dir / "script.py").write_text("print('python')")
        (test_dir / "app.js").write_text("console.log('javascript');")
        (test_dir / "style.css").write_text("body { color: blue; }")
        (test_dir / "Server.java").write_text("public class Server {}")
        (test_dir / "main.go").write_text("package main")
        
        # Test filtering for specific languages
        python_files = utils.find_source_files(test_dir, languages=["python"])
        js_files = utils.find_source_files(test_dir, languages=["javascript"])
        multi_lang_files = utils.find_source_files(test_dir, languages=["python", "java"])
        
        # Verify language filtering
        python_names = [f.name for f in python_files]
        assert "script.py" in python_names
        assert "app.js" not in python_names
        
        js_names = [f.name for f in js_files]
        assert "app.js" in js_names
        assert "script.py" not in js_names
        
        multi_names = [f.name for f in multi_lang_files]
        assert "script.py" in multi_names
        assert "Server.java" in multi_names
        assert "app.js" not in multi_names


def test_custom_exclusion_patterns():
    """Test custom exclusion patterns."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create test structure
        (test_dir / "main.py").write_text("print('main')")
        (test_dir / "temp").mkdir()
        (test_dir / "temp" / "temp_file.py").write_text("print('temp')")
        (test_dir / "custom_exclude").mkdir()
        (test_dir / "custom_exclude" / "excluded.py").write_text("print('excluded')")
        
        # Test with custom exclusion patterns
        files_default = utils.find_source_files(test_dir)
        files_custom = utils.find_source_files(test_dir, exclude_patterns=["custom_exclude", "temp"])
        
        # Default should include temp directory (not in default exclusions)
        default_paths = [str(f) for f in files_default]
        assert any("main.py" in path for path in default_paths)
        assert any("temp_file.py" in path for path in default_paths)
        
        # Custom exclusions should exclude both temp and custom_exclude
        custom_paths = [str(f) for f in files_custom]
        assert any("main.py" in path for path in custom_paths)
        assert not any("temp_file.py" in path for path in custom_paths)
        assert not any("excluded.py" in path for path in custom_paths)


def test_progress_callback_detail():
    """Test detailed progress callback functionality."""
    import sys
    sys.path.insert(0, str(Path(__file__).parents[1]))
    from simple_file_utils import SimpleFileUtilities

    with tempfile.TemporaryDirectory() as tmp_dir:
        test_dir = Path(tmp_dir)
        utils = SimpleFileUtilities()
        
        # Create enough files to trigger progress callbacks
        for i in range(75):  # Should trigger progress at 50 files
            (test_dir / f"file_{i:03d}.py").write_text(f"print({i})")
        
        progress_messages = []
        def detailed_progress(msg):
            progress_messages.append(msg)
        
        files = utils.find_source_files(test_dir, progress_callback=detailed_progress)
        
        # Verify progress reporting
        assert len(progress_messages) >= 3  # Start, intermediate, completion
        
        # Check for specific progress message patterns
        scanning_msgs = [msg for msg in progress_messages if "Scanning directory" in msg]
        assert len(scanning_msgs) >= 1
        
        progress_msgs = [msg for msg in progress_messages if "Processed" in msg and "files" in msg]
        assert len(progress_msgs) >= 1
        
        completion_msgs = [msg for msg in progress_messages if "Completed" in msg]
        assert len(completion_msgs) >= 1
        
        # Verify final count is accurate
        completion_msg = completion_msgs[-1]
        assert "75" in completion_msg  # Should mention total files found


if __name__ == "__main__":
    pytest.main([__file__, "-v"])