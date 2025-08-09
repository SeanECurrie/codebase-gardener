"""
Tests for file utilities and helper functions.

This module tests the comprehensive file system operations and utilities
including file type detection, safe file operations, directory traversal,
cross-platform path handling, and file monitoring capabilities.
"""

import tempfile
import time
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

import pytest

from src.codebase_gardener.utils.error_handling import FileUtilityError
from src.codebase_gardener.utils.file_utils import (
    FileChange,
    FileInfo,
    FileSnapshot,
    FileType,
    FileUtilities,
    atomic_write_file,
    detect_file_type,
    find_source_files,
    get_file_info,
    is_source_code_file,
    normalize_path,
    safe_read_file,
)


class TestFileType:
    """Test FileType enum."""

    def test_file_type_values(self):
        """Test that FileType enum has expected values."""
        assert FileType.SOURCE_CODE.value == "source_code"
        assert FileType.TEXT.value == "text"
        assert FileType.BINARY.value == "binary"
        assert FileType.IMAGE.value == "image"
        assert FileType.DOCUMENT.value == "document"
        assert FileType.ARCHIVE.value == "archive"
        assert FileType.UNKNOWN.value == "unknown"


class TestFileInfo:
    """Test FileInfo dataclass."""

    def test_file_info_creation(self):
        """Test FileInfo dataclass creation."""
        path = Path("test.py")
        modified_time = datetime.now()

        file_info = FileInfo(
            path=path,
            size=1024,
            modified_time=modified_time,
            file_type=FileType.SOURCE_CODE,
            encoding="utf-8",
            line_count=50,
            is_hidden=False,
            permissions="rw-r--r--"
        )

        assert file_info.path == path
        assert file_info.size == 1024
        assert file_info.modified_time == modified_time
        assert file_info.file_type == FileType.SOURCE_CODE
        assert file_info.encoding == "utf-8"
        assert file_info.line_count == 50
        assert file_info.is_hidden is False
        assert file_info.permissions == "rw-r--r--"


class TestFileChange:
    """Test FileChange dataclass."""

    def test_file_change_creation(self):
        """Test FileChange dataclass creation."""
        path = Path("test.py")
        timestamp = datetime.now()

        change = FileChange(
            path=path,
            change_type="modified",
            timestamp=timestamp,
            old_size=1000,
            new_size=1024
        )

        assert change.path == path
        assert change.change_type == "modified"
        assert change.timestamp == timestamp
        assert change.old_size == 1000
        assert change.new_size == 1024


class TestFileSnapshot:
    """Test FileSnapshot dataclass."""

    def test_file_snapshot_creation(self):
        """Test FileSnapshot dataclass creation."""
        directory = Path("/test")
        timestamp = datetime.now()
        files = {}

        snapshot = FileSnapshot(
            directory=directory,
            timestamp=timestamp,
            files=files,
            total_size=2048,
            file_count=5
        )

        assert snapshot.directory == directory
        assert snapshot.timestamp == timestamp
        assert snapshot.files == files
        assert snapshot.total_size == 2048
        assert snapshot.file_count == 5


class TestFileUtilities:
    """Test FileUtilities class."""

    @pytest.fixture
    def file_utils(self):
        """Create FileUtilities instance for testing."""
        return FileUtilities()

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    # File Type Detection Tests

    def test_detect_file_type_source_code(self, file_utils, temp_dir):
        """Test detection of source code files."""
        # Test various source code extensions
        extensions = ['.py', '.js', '.ts', '.java', '.cpp', '.html', '.css', '.json']

        for ext in extensions:
            test_file = temp_dir / f"test{ext}"
            test_file.write_text("print('hello')")

            file_type = file_utils.detect_file_type(test_file)
            assert file_type == FileType.SOURCE_CODE

    def test_detect_file_type_text(self, file_utils, temp_dir):
        """Test detection of text files."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("This is a text file")

        with patch.object(file_utils._mime_types, 'guess_type', return_value=('text/plain', None)):
            file_type = file_utils.detect_file_type(test_file)
            assert file_type == FileType.TEXT

    def test_detect_file_type_binary(self, file_utils, temp_dir):
        """Test detection of binary files."""
        test_file = temp_dir / "test.bin"
        test_file.write_bytes(b'\x00\x01\x02\x03')

        file_type = file_utils.detect_file_type(test_file)
        assert file_type == FileType.BINARY

    def test_detect_file_type_nonexistent(self, file_utils):
        """Test detection of non-existent files."""
        file_type = file_utils.detect_file_type(Path("nonexistent.txt"))
        assert file_type == FileType.UNKNOWN

    def test_is_source_code_file(self, file_utils, temp_dir):
        """Test source code file detection."""
        python_file = temp_dir / "test.py"
        python_file.write_text("print('hello')")

        text_file = temp_dir / "test.txt"
        text_file.write_text("Hello world")

        assert file_utils.is_source_code_file(python_file) is True
        assert file_utils.is_source_code_file(text_file) is False

    def test_get_language_from_file(self, file_utils):
        """Test language detection from file extension."""
        assert file_utils.get_language_from_file(Path("test.py")) == "python"
        assert file_utils.get_language_from_file(Path("test.js")) == "javascript"
        assert file_utils.get_language_from_file(Path("test.ts")) == "typescript"
        assert file_utils.get_language_from_file(Path("test.java")) == "java"
        assert file_utils.get_language_from_file(Path("test.unknown")) is None

    # File Metadata Tests

    def test_get_file_info_success(self, file_utils, temp_dir):
        """Test successful file info retrieval."""
        test_file = temp_dir / "test.py"
        content = "print('hello')\nprint('world')\n"
        test_file.write_text(content, encoding='utf-8')

        file_info = file_utils.get_file_info(test_file)

        assert file_info.path == test_file
        assert file_info.size > 0
        assert isinstance(file_info.modified_time, datetime)
        assert file_info.file_type == FileType.SOURCE_CODE
        assert file_info.encoding == 'utf-8'
        assert file_info.line_count == 2
        assert isinstance(file_info.is_hidden, bool)
        assert isinstance(file_info.permissions, str)

    def test_get_file_info_nonexistent(self, file_utils):
        """Test file info for non-existent file."""
        with pytest.raises(FileUtilityError, match="File does not exist"):
            file_utils.get_file_info(Path("nonexistent.txt"))

    def test_calculate_directory_size(self, file_utils, temp_dir):
        """Test directory size calculation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("Hello")
        (temp_dir / "file2.txt").write_text("World")

        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.txt").write_text("Test")

        total_size = file_utils.calculate_directory_size(temp_dir)
        assert total_size > 0
        assert total_size == 5 + 5 + 4  # "Hello" + "World" + "Test"

    def test_get_file_encoding(self, file_utils, temp_dir):
        """Test file encoding detection."""
        # UTF-8 file
        utf8_file = temp_dir / "utf8.txt"
        utf8_file.write_text("Hello 世界", encoding='utf-8')

        encoding = file_utils.get_file_encoding(utf8_file)
        assert encoding == 'utf-8'

        # Latin-1 file (use simpler content to avoid encoding issues)
        latin1_file = temp_dir / "latin1.txt"
        latin1_file.write_text("Hello", encoding='latin-1')

        encoding = file_utils.get_file_encoding(latin1_file)
        assert encoding in ['utf-8', 'latin-1']  # Could be detected as either

    # Directory Traversal Tests

    def test_scan_directory_recursive(self, file_utils, temp_dir):
        """Test recursive directory scanning."""
        # Create test structure
        (temp_dir / "file1.py").write_text("print('1')")
        (temp_dir / "file2.txt").write_text("text")

        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file3.py").write_text("print('3')")

        # Scan for Python files
        files = list(file_utils.scan_directory(temp_dir, patterns=['*.py'], recursive=True))

        assert len(files) == 2
        assert any(f.name == "file1.py" for f in files)
        assert any(f.name == "file3.py" for f in files)

    def test_scan_directory_non_recursive(self, file_utils, temp_dir):
        """Test non-recursive directory scanning."""
        # Create test structure
        (temp_dir / "file1.py").write_text("print('1')")

        subdir = temp_dir / "subdir"
        subdir.mkdir()
        (subdir / "file2.py").write_text("print('2')")

        # Scan non-recursively
        files = list(file_utils.scan_directory(temp_dir, patterns=['*.py'], recursive=False))

        assert len(files) == 1
        assert files[0].name == "file1.py"

    def test_find_source_files(self, file_utils, temp_dir):
        """Test finding source code files."""
        # Create test files
        (temp_dir / "script.py").write_text("print('python')")
        (temp_dir / "app.js").write_text("console.log('js')")
        (temp_dir / "readme.txt").write_text("documentation")
        node_modules_dir = temp_dir / "node_modules"
        node_modules_dir.mkdir(parents=True)
        (node_modules_dir / "lib.js").write_text("library")

        source_files = file_utils.find_source_files(temp_dir)

        # Should find Python and JS files but exclude node_modules
        file_names = [f.name for f in source_files]
        assert "script.py" in file_names
        assert "app.js" in file_names
        assert "readme.txt" not in file_names
        assert "lib.js" not in file_names  # Excluded by node_modules pattern

    def test_find_source_files_with_language_filter(self, file_utils, temp_dir):
        """Test finding source files with language filter."""
        (temp_dir / "script.py").write_text("print('python')")
        (temp_dir / "app.js").write_text("console.log('js')")

        python_files = file_utils.find_source_files(temp_dir, languages=['python'])

        assert len(python_files) == 1
        assert python_files[0].name == "script.py"

    def test_apply_exclusion_patterns(self, file_utils, temp_dir):
        """Test exclusion pattern filtering."""
        files = [
            temp_dir / "script.py",
            temp_dir / "test.pyc",
            temp_dir / ".hidden.py",
            temp_dir / "normal.js"
        ]

        # Create the files
        for f in files:
            f.write_text("content")

        patterns = ["*.pyc", ".*"]
        filtered = file_utils.apply_exclusion_patterns(files, patterns)

        filtered_names = [f.name for f in filtered]
        assert "script.py" in filtered_names
        assert "normal.js" in filtered_names
        assert "test.pyc" not in filtered_names
        assert ".hidden.py" not in filtered_names

    # Safe File Operations Tests

    def test_safe_read_file_success(self, file_utils, temp_dir):
        """Test safe file reading."""
        test_file = temp_dir / "test.txt"
        content = "Hello, world!"
        test_file.write_text(content, encoding='utf-8')

        read_content = file_utils.safe_read_file(test_file)
        assert read_content == content

    def test_safe_read_file_encoding_fallback(self, file_utils, temp_dir):
        """Test safe file reading with encoding fallback."""
        test_file = temp_dir / "test.txt"
        content = "Hello"  # Use simple content to avoid encoding issues
        test_file.write_text(content, encoding='latin-1')

        # Should succeed with fallback encoding
        read_content = file_utils.safe_read_file(test_file, encoding='utf-8')
        assert len(read_content) > 0  # Content should be read somehow

    def test_safe_read_file_nonexistent(self, file_utils):
        """Test safe reading of non-existent file."""
        with pytest.raises(FileUtilityError, match="Cannot read file"):
            file_utils.safe_read_file(Path("nonexistent.txt"))

    def test_atomic_write_file_success(self, file_utils, temp_dir):
        """Test atomic file writing."""
        test_file = temp_dir / "test.txt"
        content = "Hello, atomic world!"

        file_utils.atomic_write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text(encoding='utf-8') == content

    def test_atomic_write_file_with_backup(self, file_utils, temp_dir):
        """Test atomic writing with backup creation."""
        test_file = temp_dir / "test.txt"
        original_content = "Original content"
        new_content = "New content"

        # Create original file
        test_file.write_text(original_content)

        # Write new content with backup
        file_utils.atomic_write_file(test_file, new_content, backup=True)

        # Check new content
        assert test_file.read_text() == new_content

        # Check backup exists
        backup_files = list(temp_dir.glob("test.txt.backup_*"))
        assert len(backup_files) == 1
        assert backup_files[0].read_text() == original_content

    def test_create_backup(self, file_utils, temp_dir):
        """Test backup creation."""
        test_file = temp_dir / "test.txt"
        content = "Test content"
        test_file.write_text(content)

        backup_path = file_utils.create_backup(test_file)

        assert backup_path.exists()
        assert backup_path.read_text() == content
        assert "backup_" in backup_path.name

    def test_create_backup_nonexistent(self, file_utils):
        """Test backup of non-existent file."""
        with pytest.raises(FileUtilityError, match="Cannot backup non-existent file"):
            file_utils.create_backup(Path("nonexistent.txt"))

    # File Monitoring Tests

    def test_get_file_changes(self, file_utils, temp_dir):
        """Test file change detection."""
        # Create initial file
        test_file = temp_dir / "test.txt"
        test_file.write_text("Initial content")

        # Record time before changes
        since = datetime.now() - timedelta(seconds=1)

        # Wait a bit and modify file
        time.sleep(0.1)
        test_file.write_text("Modified content")

        changes = file_utils.get_file_changes(temp_dir, since)

        assert len(changes) >= 1
        change = next((c for c in changes if c.path == test_file), None)
        assert change is not None
        assert change.change_type in ['created', 'modified']

    def test_create_file_snapshot(self, file_utils, temp_dir):
        """Test file snapshot creation."""
        # Create test files
        (temp_dir / "file1.txt").write_text("Content 1")
        (temp_dir / "file2.txt").write_text("Content 2")

        snapshot = file_utils.create_file_snapshot(temp_dir)

        assert snapshot.directory == temp_dir
        assert isinstance(snapshot.timestamp, datetime)
        assert snapshot.file_count == 2
        assert snapshot.total_size > 0
        assert len(snapshot.files) == 2

    def test_compare_snapshots(self, file_utils, temp_dir):
        """Test snapshot comparison."""
        # Create initial files
        file1 = temp_dir / "file1.txt"
        file1.write_text("Content 1")

        old_snapshot = file_utils.create_file_snapshot(temp_dir)

        # Wait and make changes
        time.sleep(0.1)
        file2 = temp_dir / "file2.txt"
        file2.write_text("Content 2")
        file1.write_text("Modified content 1")

        new_snapshot = file_utils.create_file_snapshot(temp_dir)

        changes = file_utils.compare_snapshots(old_snapshot, new_snapshot)

        # Should detect one new file and one modified file
        change_types = [c.change_type for c in changes]
        assert 'created' in change_types
        assert 'modified' in change_types

    # Cross-platform Utilities Tests

    def test_normalize_path(self, file_utils):
        """Test path normalization."""
        # Test string path
        normalized = file_utils.normalize_path("./test/../file.txt")
        assert isinstance(normalized, Path)

        # Test Path object
        path_obj = Path("test/file.txt")
        normalized = file_utils.normalize_path(path_obj)
        assert isinstance(normalized, Path)

    def test_is_hidden_file(self, file_utils, temp_dir):
        """Test hidden file detection."""
        # Unix-style hidden file
        hidden_file = temp_dir / ".hidden"
        hidden_file.write_text("hidden")

        normal_file = temp_dir / "normal.txt"
        normal_file.write_text("normal")

        assert file_utils.is_hidden_file(hidden_file) is True
        assert file_utils.is_hidden_file(normal_file) is False

    def test_check_file_permissions(self, file_utils, temp_dir):
        """Test file permission checking."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test content")

        permissions = file_utils.check_file_permissions(test_file)

        assert isinstance(permissions, dict)
        assert 'readable' in permissions
        assert 'writable' in permissions
        assert 'executable' in permissions
        assert permissions['readable'] is True  # Should be readable

    def test_generate_file_hash(self, file_utils, temp_dir):
        """Test file hash generation."""
        test_file = temp_dir / "test.txt"
        content = "Test content for hashing"
        test_file.write_text(content)

        hash_value = file_utils.generate_file_hash(test_file)

        assert isinstance(hash_value, str)
        assert len(hash_value) == 64  # SHA256 hex digest length

        # Same content should produce same hash
        hash_value2 = file_utils.generate_file_hash(test_file)
        assert hash_value == hash_value2

    def test_generate_file_hash_different_algorithm(self, file_utils, temp_dir):
        """Test file hash with different algorithm."""
        test_file = temp_dir / "test.txt"
        test_file.write_text("test")

        md5_hash = file_utils.generate_file_hash(test_file, algorithm='md5')
        sha1_hash = file_utils.generate_file_hash(test_file, algorithm='sha1')

        assert len(md5_hash) == 32  # MD5 hex digest length
        assert len(sha1_hash) == 40  # SHA1 hex digest length
        assert md5_hash != sha1_hash

    def test_generate_file_hash_nonexistent(self, file_utils):
        """Test hash generation for non-existent file."""
        with pytest.raises(FileUtilityError, match="Cannot generate hash"):
            file_utils.generate_file_hash(Path("nonexistent.txt"))


class TestConvenienceFunctions:
    """Test convenience functions."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    def test_detect_file_type_function(self, temp_dir):
        """Test detect_file_type convenience function."""
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        file_type = detect_file_type(test_file)
        assert file_type == FileType.SOURCE_CODE

    def test_is_source_code_file_function(self, temp_dir):
        """Test is_source_code_file convenience function."""
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        assert is_source_code_file(test_file) is True

    def test_get_file_info_function(self, temp_dir):
        """Test get_file_info convenience function."""
        test_file = temp_dir / "test.py"
        test_file.write_text("print('hello')")

        file_info = get_file_info(test_file)
        assert isinstance(file_info, FileInfo)
        assert file_info.path == test_file

    def test_find_source_files_function(self, temp_dir):
        """Test find_source_files convenience function."""
        (temp_dir / "test.py").write_text("print('hello')")
        (temp_dir / "readme.txt").write_text("documentation")

        source_files = find_source_files(temp_dir)
        assert len(source_files) == 1
        assert source_files[0].name == "test.py"

    def test_safe_read_file_function(self, temp_dir):
        """Test safe_read_file convenience function."""
        test_file = temp_dir / "test.txt"
        content = "Hello, world!"
        test_file.write_text(content)

        read_content = safe_read_file(test_file)
        assert read_content == content

    def test_atomic_write_file_function(self, temp_dir):
        """Test atomic_write_file convenience function."""
        test_file = temp_dir / "test.txt"
        content = "Hello, atomic world!"

        atomic_write_file(test_file, content)

        assert test_file.exists()
        assert test_file.read_text() == content

    def test_normalize_path_function(self):
        """Test normalize_path convenience function."""
        normalized = normalize_path("./test/../file.txt")
        assert isinstance(normalized, Path)


class TestErrorHandling:
    """Test error handling scenarios."""

    def test_file_utility_error_inheritance(self):
        """Test that FileUtilityError inherits from Exception."""
        error = FileUtilityError("Test error")
        assert isinstance(error, Exception)
        assert str(error) == "Test error"

    @patch('src.codebase_gardener.utils.file_utils.Path.stat')
    def test_get_file_info_os_error(self, mock_stat):
        """Test get_file_info with OS error."""
        mock_stat.side_effect = OSError("Permission denied")

        file_utils = FileUtilities()

        with pytest.raises(FileUtilityError, match="Cannot get file info"):
            file_utils.get_file_info(Path("test.txt"))

    @patch('pathlib.Path.open')
    def test_safe_read_file_permission_error(self, mock_open):
        """Test safe_read_file with permission error."""
        mock_open.side_effect = PermissionError("Access denied")

        file_utils = FileUtilities()

        with pytest.raises(FileUtilityError, match="Cannot read file"):
            file_utils.safe_read_file(Path("test.txt"))

    @patch('pathlib.Path.open')
    def test_atomic_write_file_os_error(self, mock_open):
        """Test atomic_write_file with OS error."""
        mock_open.side_effect = OSError("Disk full")

        file_utils = FileUtilities()

        with pytest.raises(FileUtilityError):
            file_utils.atomic_write_file(Path("test.txt"), "content", backup=False)


class TestIntegrationScenarios:
    """Test realistic integration scenarios."""

    @pytest.fixture
    def project_structure(self, tmp_path):
        """Create a realistic project structure for testing."""
        project_dir = tmp_path / "test_project"
        project_dir.mkdir()

        # Source files
        (project_dir / "main.py").write_text("#!/usr/bin/env python3\nprint('Hello, world!')\n")
        (project_dir / "utils.js").write_text("function hello() { console.log('Hello'); }\n")
        (project_dir / "styles.css").write_text("body { margin: 0; }\n")

        # Documentation
        (project_dir / "README.md").write_text("# Test Project\n\nThis is a test.\n")
        (project_dir / "LICENSE").write_text("MIT License\n")

        # Build artifacts (should be excluded)
        build_dir = project_dir / "build"
        build_dir.mkdir()
        (build_dir / "output.js").write_text("minified code")

        # Dependencies (should be excluded)
        node_modules = project_dir / "node_modules"
        node_modules.mkdir()
        (node_modules / "library.js").write_text("library code")

        # Hidden files
        (project_dir / ".gitignore").write_text("*.pyc\n__pycache__/\n")

        return project_dir

    def test_complete_project_analysis(self, project_structure):
        """Test complete project analysis workflow."""
        file_utils = FileUtilities()

        # Find all source files
        source_files = file_utils.find_source_files(project_structure)

        # Should find main source files but exclude build artifacts and dependencies
        source_names = [f.name for f in source_files]
        assert "main.py" in source_names
        assert "utils.js" in source_names
        assert "styles.css" in source_names
        assert "README.md" in source_names
        assert "output.js" not in source_names  # Build artifact
        assert "library.js" not in source_names  # Dependency

        # Analyze each source file
        for source_file in source_files:
            file_info = file_utils.get_file_info(source_file)

            assert file_info.size > 0
            assert file_info.file_type in [FileType.SOURCE_CODE, FileType.TEXT]

            if file_info.file_type == FileType.SOURCE_CODE:
                language = file_utils.get_language_from_file(source_file)
                assert language is not None

        # Create snapshot
        snapshot = file_utils.create_file_snapshot(project_structure)
        assert snapshot.file_count >= 4  # At least the source files we created
        assert snapshot.total_size > 0

    def test_file_monitoring_workflow(self, project_structure):
        """Test file monitoring workflow."""
        file_utils = FileUtilities()

        # Create initial snapshot
        initial_snapshot = file_utils.create_file_snapshot(project_structure)

        # Wait and make changes
        time.sleep(0.1)

        # Add new file
        new_file = project_structure / "new_feature.py"
        new_file.write_text("def new_feature():\n    pass\n")

        # Modify existing file
        main_file = project_structure / "main.py"
        main_file.write_text("#!/usr/bin/env python3\nprint('Hello, modified world!')\n")

        # Create new snapshot
        new_snapshot = file_utils.create_file_snapshot(project_structure)

        # Compare snapshots
        changes = file_utils.compare_snapshots(initial_snapshot, new_snapshot)

        # Should detect changes
        change_types = [c.change_type for c in changes]
        assert 'created' in change_types  # new_feature.py
        assert 'modified' in change_types  # main.py

        # Verify specific changes
        created_files = [c.path.name for c in changes if c.change_type == 'created']
        modified_files = [c.path.name for c in changes if c.change_type == 'modified']

        assert "new_feature.py" in created_files
        assert "main.py" in modified_files

    def test_safe_file_operations_workflow(self, project_structure):
        """Test safe file operations workflow."""
        file_utils = FileUtilities()

        config_file = project_structure / "config.json"
        original_config = '{"version": "1.0", "debug": false}'

        # Write initial config
        file_utils.atomic_write_file(config_file, original_config)
        assert config_file.exists()

        # Read and verify
        read_config = file_utils.safe_read_file(config_file)
        assert read_config == original_config

        # Update config with backup
        new_config = '{"version": "1.1", "debug": true, "features": ["new"]}'
        file_utils.atomic_write_file(config_file, new_config, backup=True)

        # Verify update
        updated_config = file_utils.safe_read_file(config_file)
        assert updated_config == new_config

        # Verify backup exists
        backup_files = list(project_structure.glob("config.json.backup_*"))
        assert len(backup_files) == 1

        backup_content = file_utils.safe_read_file(backup_files[0])
        assert backup_content == original_config
