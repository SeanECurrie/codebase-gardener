"""
File utilities and helper functions.

This module provides comprehensive file system operations and utilities that complement
the directory setup functionality. It includes file type detection, safe file operations,
directory traversal, cross-platform path handling, and file monitoring capabilities.
"""

import hashlib
import mimetypes
import os
import re
import signal
import stat
import tempfile
import time
from dataclasses import dataclass
from datetime import datetime
from enum import Enum
from functools import wraps
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional, Set, Tuple, Union

import structlog

from ..config import settings
from .error_handling import FileUtilityError

logger = structlog.get_logger(__name__)


# Remove timeout functionality - we want progress, not timeouts


class FileType(Enum):
    """Enumeration of file types for classification."""
    SOURCE_CODE = "source_code"
    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"


@dataclass
class FileInfo:
    """Information about a file."""
    path: Path
    size: int
    modified_time: datetime
    file_type: FileType
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    is_hidden: bool = False
    permissions: Optional[str] = None


@dataclass
class FileChange:
    """Represents a file system change."""
    path: Path
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime
    old_size: Optional[int] = None
    new_size: Optional[int] = None


@dataclass
class FileSnapshot:
    """Snapshot of directory state at a point in time."""
    directory: Path
    timestamp: datetime
    files: Dict[Path, FileInfo]
    total_size: int
    file_count: int


class FileUtilities:
    """
    Comprehensive file utilities for cross-platform file operations.

    This class provides:
    - File type detection and metadata extraction
    - Safe file operations with atomic operations
    - Directory traversal with filtering and exclusion patterns
    - Cross-platform path handling and normalization
    - File monitoring and change detection
    - Integration with existing error handling framework
    """

    # Common source code file extensions
    SOURCE_CODE_EXTENSIONS = {
        '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
        '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
        '.hs', '.ml', '.fs', '.vb', '.pl', '.sh', '.bash', '.zsh', '.fish',
        '.ps1', '.bat', '.cmd', '.r', '.m', '.mm', '.sql', '.html', '.htm',
        '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml',
        '.toml', '.ini', '.cfg', '.conf', '.md', '.rst', '.tex', '.vue'
    }

    # Common exclusion patterns for code projects
    DEFAULT_EXCLUSION_PATTERNS = [
        # Version control
        '.git', '.svn', '.hg', '.bzr',
        # Dependencies
        'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env', '.env',
        'vendor', 'target', 'build', 'dist', '.tox',
        # IDE files
        '.vscode', '.idea', '*.swp', '*.swo', '*~', '.DS_Store',
        # Compiled files
        '*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe',
        # Logs and temporary files
        '*.log', '*.tmp', '*.temp', '.cache'
    ]

    def __init__(self, settings_obj=None):
        """Initialize file utilities with configuration."""
        self.settings = settings_obj or settings
        self._mime_types = mimetypes.MimeTypes()
        logger.debug("FileUtilities initialized")

    # File Type Detection Methods

    def detect_file_type(self, file_path: Path) -> FileType:
        """
        Detect file type based on extension and content.

        Args:
            file_path: Path to the file

        Returns:
            FileType enum value
        """
        if not file_path.exists() or not file_path.is_file():
            return FileType.UNKNOWN

        # Check by extension first
        extension = file_path.suffix.lower()

        if extension in self.SOURCE_CODE_EXTENSIONS:
            return FileType.SOURCE_CODE

        # Use MIME type detection
        mime_type, _ = self._mime_types.guess_type(str(file_path))

        if mime_type:
            if mime_type.startswith('text/'):
                return FileType.TEXT
            elif mime_type.startswith('image/'):
                return FileType.IMAGE
            elif mime_type in ['application/pdf', 'application/msword',
                              'application/vnd.openxmlformats-officedocument']:
                return FileType.DOCUMENT
            elif mime_type in ['application/zip', 'application/x-tar',
                              'application/gzip', 'application/x-rar']:
                return FileType.ARCHIVE
            elif not mime_type.startswith('text/'):
                return FileType.BINARY

        # Fallback to content-based detection for small files
        try:
            if file_path.stat().st_size < 1024 * 1024:  # 1MB limit
                with file_path.open('rb') as f:
                    sample = f.read(1024)
                    if b'\x00' in sample:
                        return FileType.BINARY
                    else:
                        return FileType.TEXT
        except (OSError, PermissionError):
            pass

        return FileType.UNKNOWN

    def is_source_code_file(self, file_path: Path) -> bool:
        """Check if a file is a source code file."""
        return self.detect_file_type(file_path) == FileType.SOURCE_CODE

    def get_language_from_file(self, file_path: Path) -> Optional[str]:
        """
        Get programming language from file extension.

        Args:
            file_path: Path to the file

        Returns:
            Language name or None if not detected
        """
        extension = file_path.suffix.lower()

        language_map = {
            '.py': 'python',
            '.js': 'javascript',
            '.ts': 'typescript',
            '.jsx': 'javascript',
            '.tsx': 'typescript',
            '.java': 'java',
            '.c': 'c',
            '.cpp': 'cpp',
            '.h': 'c',
            '.hpp': 'cpp',
            '.cs': 'csharp',
            '.php': 'php',
            '.rb': 'ruby',
            '.go': 'go',
            '.rs': 'rust',
            '.swift': 'swift',
            '.kt': 'kotlin',
            '.scala': 'scala',
            '.r': 'r',
            '.sql': 'sql',
            '.html': 'html',
            '.htm': 'html',
            '.css': 'css',
            '.scss': 'scss',
            '.xml': 'xml',
            '.json': 'json',
            '.yaml': 'yaml',
            '.yml': 'yaml',
            '.md': 'markdown',
            '.sh': 'bash',
            '.bash': 'bash',
        }

        return language_map.get(extension)

    # File Metadata Methods

    def get_file_info(self, file_path: Path) -> FileInfo:
        """
        Get comprehensive information about a file.

        Args:
            file_path: Path to the file

        Returns:
            FileInfo object with file metadata

        Raises:
            FileUtilityError: If file information cannot be retrieved
        """
        try:
            if not file_path.exists():
                raise FileUtilityError(f"File does not exist: {file_path}")

            stat_info = file_path.stat()
            file_type = self.detect_file_type(file_path)

            # Get encoding for text files
            encoding = None
            line_count = None
            if file_type in [FileType.TEXT, FileType.SOURCE_CODE]:
                encoding = self.get_file_encoding(file_path)
                if encoding:
                    line_count = self._count_lines(file_path, encoding)

            # Check if file is hidden
            is_hidden = self.is_hidden_file(file_path)

            # Get permissions
            permissions = self._format_permissions(stat_info.st_mode)

            return FileInfo(
                path=file_path,
                size=stat_info.st_size,
                modified_time=datetime.fromtimestamp(stat_info.st_mtime),
                file_type=file_type,
                encoding=encoding,
                line_count=line_count,
                is_hidden=is_hidden,
                permissions=permissions
            )

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to get file info: {e}", file_path=str(file_path))
            raise FileUtilityError(f"Cannot get file info for {file_path}: {e}") from e

    def calculate_directory_size(self, dir_path: Path) -> int:
        """
        Calculate total size of all files in a directory recursively.

        Args:
            dir_path: Path to the directory

        Returns:
            Total size in bytes
        """
        total_size = 0

        try:
            for file_path in dir_path.rglob('*'):
                if file_path.is_file():
                    try:
                        total_size += file_path.stat().st_size
                    except (OSError, PermissionError):
                        # Skip files we can't access
                        continue
        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot access directory: {e}", dir_path=str(dir_path))

        return total_size

    def get_file_encoding(self, file_path: Path) -> Optional[str]:
        """
        Detect file encoding.

        Args:
            file_path: Path to the file

        Returns:
            Encoding name or None if detection fails
        """
        try:
            # Try common encodings
            encodings = ['utf-8', 'latin-1', 'cp1252']

            for encoding in encodings:
                try:
                    with file_path.open('r', encoding=encoding) as f:
                        f.read(1024)  # Try to read a sample
                    return encoding
                except (UnicodeDecodeError, UnicodeError):
                    continue

            return None

        except (OSError, PermissionError):
            return None

    def _count_lines(self, file_path: Path, encoding: str) -> Optional[int]:
        """Count lines in a text file."""
        try:
            with file_path.open('r', encoding=encoding) as f:
                return sum(1 for _ in f)
        except (OSError, UnicodeDecodeError):
            return None

    def _format_permissions(self, mode: int) -> str:
        """Format file permissions as a string."""
        permissions = []

        # Owner permissions
        permissions.append('r' if mode & stat.S_IRUSR else '-')
        permissions.append('w' if mode & stat.S_IWUSR else '-')
        permissions.append('x' if mode & stat.S_IXUSR else '-')

        # Group permissions
        permissions.append('r' if mode & stat.S_IRGRP else '-')
        permissions.append('w' if mode & stat.S_IWGRP else '-')
        permissions.append('x' if mode & stat.S_IXGRP else '-')

        # Other permissions
        permissions.append('r' if mode & stat.S_IROTH else '-')
        permissions.append('w' if mode & stat.S_IWOTH else '-')
        permissions.append('x' if mode & stat.S_IXOTH else '-')

        return ''.join(permissions)

    # Directory Traversal Methods

    def scan_directory(self, dir_path: Path, patterns: Optional[List[str]] = None,
                      recursive: bool = True, include_hidden: bool = False,
                      exclude_patterns: Optional[List[str]] = None) -> Iterator[Path]:
        """
        Scan directory for files matching patterns, excluding specified directories.

        Args:
            dir_path: Directory to scan
            patterns: List of glob patterns to match (default: all files)
            recursive: Whether to scan recursively
            include_hidden: Whether to include hidden files
            exclude_patterns: Directory patterns to exclude during scan

        Yields:
            Path objects for matching files
        """
        if not dir_path.exists() or not dir_path.is_dir():
            logger.warning(f"Directory does not exist: {dir_path}")
            return

        # Use default exclusion patterns if none provided
        if exclude_patterns is None:
            exclude_patterns = self.DEFAULT_EXCLUSION_PATTERNS

        try:
            if recursive:
                # Custom recursive scan that respects exclusions
                yield from self._recursive_scan_with_exclusions(
                    dir_path, patterns or ['*'], include_hidden, exclude_patterns
                )
            else:
                # Non-recursive scan
                if patterns is None:
                    patterns = ['*']

                for pattern in patterns:
                    files = dir_path.glob(pattern)
                    for file_path in files:
                        if file_path.is_file():
                            if not include_hidden and self.is_hidden_file(file_path):
                                continue
                            yield file_path

        except (OSError, PermissionError) as e:
            logger.error(f"Error scanning directory: {e}", dir_path=str(dir_path))

    def _recursive_scan_with_exclusions(self, dir_path: Path, patterns: List[str], 
                                       include_hidden: bool, exclude_patterns: List[str]) -> Iterator[Path]:
        """Recursively scan directory while excluding specified patterns."""
        try:
            # Check if current directory should be excluded
            if self._should_exclude_directory(dir_path, exclude_patterns):
                return

            # Scan files in current directory
            for pattern in patterns:
                for file_path in dir_path.glob(pattern):
                    if file_path.is_file():
                        if not include_hidden and self.is_hidden_file(file_path):
                            continue
                        yield file_path

            # Recursively scan subdirectories
            for subdir in dir_path.iterdir():
                if subdir.is_dir():
                    if not self._should_exclude_directory(subdir, exclude_patterns):
                        yield from self._recursive_scan_with_exclusions(
                            subdir, patterns, include_hidden, exclude_patterns
                        )

        except (OSError, PermissionError):
            # Skip directories we can't access
            pass

    def _should_exclude_directory(self, dir_path: Path, exclude_patterns: List[str]) -> bool:
        """Check if a directory should be excluded from scanning."""
        dir_name = dir_path.name
        
        for pattern in exclude_patterns:
            # Skip file patterns (those with extensions or wildcards for files)
            if '.' in pattern and not pattern.startswith('.'):
                continue
                
            # Direct name match
            if pattern == dir_name:
                return True
                
            # Pattern match for directories
            if pattern.startswith('.') and dir_name.startswith('.'):
                if pattern == dir_name or (len(pattern) == 1 and pattern == '.'):
                    return True
                    
            # Common directory exclusions
            if pattern in ['node_modules', '__pycache__', '.git', '.svn', 'venv', 'env', 
                          'vendor', 'target', 'build', 'dist', '.tox', '.pytest_cache',
                          '.vscode', '.idea', '.cache']:
                if dir_name == pattern:
                    return True
        
        return False

    def find_source_files(self, dir_path: Path, languages: Optional[List[str]] = None,
                         exclude_patterns: Optional[List[str]] = None, 
                         progress_callback=None) -> List[Path]:
        """
        Find source code files in a directory with progress feedback.

        Args:
            dir_path: Directory to search
            languages: List of languages to include (default: all)
            exclude_patterns: Additional exclusion patterns
            progress_callback: Optional callback for progress updates

        Returns:
            List of source code file paths
            
        Raises:
            FileUtilityError: If directory cannot be accessed
        """
        if not dir_path.exists() or not dir_path.is_dir():
            raise FileUtilityError(f"Directory does not exist or is not accessible: {dir_path}")
        
        logger.info(f"Starting file discovery in {dir_path}")
        
        if progress_callback:
            progress_callback(f"Scanning directory: {dir_path}")
        
        source_files = []
        exclusion_patterns = self.DEFAULT_EXCLUSION_PATTERNS.copy()
        files_processed = 0

        if exclude_patterns:
            exclusion_patterns.extend(exclude_patterns)

        try:
            # Pass exclusion patterns to scan_directory to avoid scanning excluded directories
            for file_path in self.scan_directory(dir_path, recursive=True, exclude_patterns=exclusion_patterns):
                files_processed += 1
                
                # Provide progress feedback every 50 files for more responsive feedback
                if progress_callback and files_processed % 50 == 0:
                    progress_callback(f"Processed {files_processed} files, found {len(source_files)} source files")
                
                # Check if it's a source code file
                if not self.is_source_code_file(file_path):
                    continue

                # Check language filter
                if languages:
                    file_language = self.get_language_from_file(file_path)
                    if file_language not in languages:
                        continue

                # Final exclusion check for file patterns (not directory patterns)
                if self._matches_file_exclusion_patterns(file_path, exclusion_patterns):
                    continue

                source_files.append(file_path)

            if progress_callback:
                progress_callback(f"✅ Completed: found {len(source_files)} source files in {files_processed} total files")
            
            logger.info(f"File discovery completed: found {len(source_files)} source files")
            return source_files
            
        except Exception as e:
            logger.error(f"File discovery failed: {e}", dir_path=str(dir_path))
            if progress_callback:
                progress_callback(f"❌ File discovery failed: {e}")
            raise FileUtilityError(f"Could not discover files in {dir_path}: {e}") from e
    
# Remove the internal implementation method - it's now in the main method

    def apply_exclusion_patterns(self, files: List[Path],
                                patterns: List[str]) -> List[Path]:
        """
        Filter files by exclusion patterns.

        Args:
            files: List of file paths
            patterns: List of exclusion patterns

        Returns:
            Filtered list of file paths
        """
        return [f for f in files if not self._matches_exclusion_patterns(f, patterns)]

    def _matches_exclusion_patterns(self, file_path: Path, patterns: List[str]) -> bool:
        """Check if a file matches any exclusion pattern (legacy method)."""
        return self._matches_file_exclusion_patterns(file_path, patterns)

    def _matches_file_exclusion_patterns(self, file_path: Path, patterns: List[str]) -> bool:
        """Check if a file matches any file-specific exclusion pattern."""
        file_str = str(file_path)
        file_name = file_path.name

        for pattern in patterns:
            # Skip directory-only patterns
            if pattern in ['node_modules', '__pycache__', '.git', '.svn', 'venv', 'env',
                          'vendor', 'target', 'build', 'dist', '.tox', '.pytest_cache',
                          '.vscode', '.idea', '.cache']:
                continue

            # Direct name match
            if pattern == file_name:
                return True

            # Glob pattern match for files
            if file_path.match(pattern):
                return True

            # Simple wildcard match for files
            if '*' in pattern:
                import fnmatch
                if fnmatch.fnmatch(file_name, pattern):
                    return True

        return False

    # Safe File Operations

    def safe_read_file(self, file_path: Path, encoding: str = 'utf-8',
                      fallback_encoding: str = 'latin-1') -> str:
        """
        Safely read a text file with encoding detection.

        Args:
            file_path: Path to the file
            encoding: Primary encoding to try
            fallback_encoding: Fallback encoding

        Returns:
            File content as string

        Raises:
            FileUtilityError: If file cannot be read
        """
        try:
            # Try primary encoding
            try:
                with file_path.open('r', encoding=encoding) as f:
                    return f.read()
            except (UnicodeDecodeError, UnicodeError):
                # Try detected encoding
                detected_encoding = self.get_file_encoding(file_path)
                if detected_encoding and detected_encoding != encoding:
                    with file_path.open('r', encoding=detected_encoding) as f:
                        return f.read()

                # Try fallback encoding
                with file_path.open('r', encoding=fallback_encoding) as f:
                    return f.read()

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to read file: {e}", file_path=str(file_path))
            raise FileUtilityError(f"Cannot read file {file_path}: {e}") from e

    def atomic_write_file(self, file_path: Path, content: str,
                         encoding: str = 'utf-8', backup: bool = True) -> None:
        """
        Atomically write content to a file.

        Args:
            file_path: Path to the file
            content: Content to write
            encoding: Text encoding
            backup: Whether to create a backup

        Raises:
            FileUtilityError: If write operation fails
        """
        try:
            # Create backup if requested and file exists
            backup_path = None
            if backup and file_path.exists():
                backup_path = self.create_backup(file_path)

            # Write to temporary file first
            temp_path = file_path.with_suffix(file_path.suffix + '.tmp')

            try:
                with temp_path.open('w', encoding=encoding) as f:
                    f.write(content)

                # Atomic move
                temp_path.replace(file_path)

                logger.debug(f"Atomically wrote file: {file_path}")

            except Exception as e:
                # Cleanup temporary file
                if temp_path.exists():
                    temp_path.unlink()

                # Restore backup if write failed
                if backup_path and backup_path.exists():
                    backup_path.replace(file_path)

                raise

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to write file: {e}", file_path=str(file_path))
            raise FileUtilityError(f"Cannot write file {file_path}: {e}") from e

    def create_backup(self, file_path: Path) -> Path:
        """
        Create a backup of a file.

        Args:
            file_path: Path to the file to backup

        Returns:
            Path to the backup file

        Raises:
            FileUtilityError: If backup creation fails
        """
        if not file_path.exists():
            raise FileUtilityError(f"Cannot backup non-existent file: {file_path}")

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        backup_path = file_path.with_suffix(f"{file_path.suffix}.backup_{timestamp}")

        try:
            # Copy file content
            backup_path.write_bytes(file_path.read_bytes())
            logger.debug(f"Created backup: {backup_path}")
            return backup_path

        except (OSError, PermissionError) as e:
            logger.error(f"Failed to create backup: {e}", file_path=str(file_path))
            raise FileUtilityError(f"Cannot create backup of {file_path}: {e}") from e

    # File Monitoring Methods

    def get_file_changes(self, dir_path: Path, since: datetime) -> List[FileChange]:
        """
        Get file changes since a specific time.

        Args:
            dir_path: Directory to check
            since: Timestamp to check changes since

        Returns:
            List of file changes
        """
        changes = []
        since_timestamp = since.timestamp()

        try:
            for file_path in self.scan_directory(dir_path, recursive=True):
                try:
                    stat_info = file_path.stat()
                    if stat_info.st_mtime > since_timestamp:
                        change_type = 'modified' if stat_info.st_ctime < since_timestamp else 'created'
                        changes.append(FileChange(
                            path=file_path,
                            change_type=change_type,
                            timestamp=datetime.fromtimestamp(stat_info.st_mtime),
                            new_size=stat_info.st_size
                        ))
                except (OSError, PermissionError):
                    continue

        except (OSError, PermissionError) as e:
            logger.warning(f"Cannot check file changes: {e}", dir_path=str(dir_path))

        return changes

    def create_file_snapshot(self, dir_path: Path) -> FileSnapshot:
        """
        Create a snapshot of directory state.

        Args:
            dir_path: Directory to snapshot

        Returns:
            FileSnapshot object
        """
        files = {}
        total_size = 0
        file_count = 0

        try:
            for file_path in self.scan_directory(dir_path, recursive=True):
                try:
                    file_info = self.get_file_info(file_path)
                    files[file_path] = file_info
                    total_size += file_info.size
                    file_count += 1
                except FileUtilityError:
                    continue

        except Exception as e:
            logger.warning(f"Error creating snapshot: {e}", dir_path=str(dir_path))

        return FileSnapshot(
            directory=dir_path,
            timestamp=datetime.now(),
            files=files,
            total_size=total_size,
            file_count=file_count
        )

    def compare_snapshots(self, old: FileSnapshot, new: FileSnapshot) -> List[FileChange]:
        """
        Compare two file snapshots to find changes.

        Args:
            old: Previous snapshot
            new: Current snapshot

        Returns:
            List of file changes
        """
        changes = []

        # Find new and modified files
        for path, new_info in new.files.items():
            if path not in old.files:
                changes.append(FileChange(
                    path=path,
                    change_type='created',
                    timestamp=new_info.modified_time,
                    new_size=new_info.size
                ))
            else:
                old_info = old.files[path]
                if new_info.modified_time > old_info.modified_time:
                    changes.append(FileChange(
                        path=path,
                        change_type='modified',
                        timestamp=new_info.modified_time,
                        old_size=old_info.size,
                        new_size=new_info.size
                    ))

        # Find deleted files
        for path, old_info in old.files.items():
            if path not in new.files:
                changes.append(FileChange(
                    path=path,
                    change_type='deleted',
                    timestamp=new.timestamp,
                    old_size=old_info.size
                ))

        return changes

    # Cross-platform Utilities

    def normalize_path(self, path: Union[str, Path]) -> Path:
        """
        Normalize path for cross-platform compatibility.

        Args:
            path: Path to normalize

        Returns:
            Normalized Path object
        """
        if isinstance(path, str):
            path = Path(path)

        # Resolve to absolute path and normalize
        try:
            return path.resolve()
        except (OSError, RuntimeError):
            # Fallback for broken symlinks or other issues
            return Path(os.path.normpath(str(path)))

    def is_hidden_file(self, file_path: Path) -> bool:
        """
        Check if a file is hidden (cross-platform).

        Args:
            file_path: Path to check

        Returns:
            True if file is hidden
        """
        # Unix-style hidden files (start with dot)
        if file_path.name.startswith('.'):
            return True

        # Windows hidden files
        if os.name == 'nt':
            try:
                import ctypes
                attrs = ctypes.windll.kernel32.GetFileAttributesW(str(file_path))
                return attrs != -1 and attrs & 2  # FILE_ATTRIBUTE_HIDDEN
            except (AttributeError, OSError):
                pass

        return False

    def check_file_permissions(self, file_path: Path) -> Dict[str, bool]:
        """
        Check file permissions cross-platform.

        Args:
            file_path: Path to check

        Returns:
            Dictionary with permission flags
        """
        permissions = {
            'readable': False,
            'writable': False,
            'executable': False
        }

        try:
            permissions['readable'] = os.access(file_path, os.R_OK)
            permissions['writable'] = os.access(file_path, os.W_OK)
            permissions['executable'] = os.access(file_path, os.X_OK)
        except (OSError, PermissionError):
            pass

        return permissions

    def generate_file_hash(self, file_path: Path, algorithm: str = 'sha256') -> str:
        """
        Generate hash of file content.

        Args:
            file_path: Path to the file
            algorithm: Hash algorithm to use

        Returns:
            Hex digest of file hash

        Raises:
            FileUtilityError: If hash generation fails
        """
        try:
            hash_obj = hashlib.new(algorithm)

            with file_path.open('rb') as f:
                for chunk in iter(lambda: f.read(8192), b''):
                    hash_obj.update(chunk)

            return hash_obj.hexdigest()

        except (OSError, PermissionError, ValueError) as e:
            logger.error(f"Failed to generate file hash: {e}", file_path=str(file_path))
            raise FileUtilityError(f"Cannot generate hash for {file_path}: {e}") from e


# Global file utilities instance
file_utilities = FileUtilities()


# Convenience functions
def detect_file_type(file_path: Path) -> FileType:
    """Detect file type."""
    return file_utilities.detect_file_type(file_path)


def is_source_code_file(file_path: Path) -> bool:
    """Check if file is source code."""
    return file_utilities.is_source_code_file(file_path)


def get_file_info(file_path: Path) -> FileInfo:
    """Get file information."""
    return file_utilities.get_file_info(file_path)


def find_source_files(dir_path: Path, languages: Optional[List[str]] = None, 
                     progress_callback=None) -> List[Path]:
    """Find source code files in directory with progress feedback."""
    return file_utilities.find_source_files(dir_path, languages, progress_callback=progress_callback)


def safe_read_file(file_path: Path, encoding: str = 'utf-8') -> str:
    """Safely read a text file."""
    return file_utilities.safe_read_file(file_path, encoding)


def atomic_write_file(file_path: Path, content: str, encoding: str = 'utf-8') -> None:
    """Atomically write content to file."""
    file_utilities.atomic_write_file(file_path, content, encoding)


def normalize_path(path: Union[str, Path]) -> Path:
    """Normalize path for cross-platform compatibility."""
    return file_utilities.normalize_path(path)
