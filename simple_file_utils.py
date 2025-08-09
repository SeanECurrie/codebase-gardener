"""
Simplified file utilities for codebase auditor.

This is a standalone version that doesn't depend on structlog or other heavy dependencies.
Extracted from the working FileUtilities.find_source_files() method.
"""

from collections.abc import Callable
from pathlib import Path


class SimpleFileUtilities:
    """Simplified file utilities for codebase analysis."""

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
        # Dependencies and virtual environments
        'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env', '.env', '.venv',
        'vendor', 'target', 'build', 'dist', '.tox', 'site-packages',
        # IDE files
        '.vscode', '.idea', '*.swp', '*.swo', '*~', '.DS_Store',
        # Compiled files
        '*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe',
        # Logs and temporary files
        '*.log', '*.tmp', '*.temp', '.cache'
    ]

    def __init__(self):
        """Initialize simple file utilities."""
        pass

    def is_source_code_file(self, file_path: Path) -> bool:
        """Check if a file is a source code file."""
        return file_path.suffix.lower() in self.SOURCE_CODE_EXTENSIONS

    def _should_exclude_directory(self, dir_path: Path, exclude_patterns: list[str]) -> bool:
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
            if pattern in ['node_modules', '__pycache__', '.git', '.svn', 'venv', 'env', '.venv',
                          'vendor', 'target', 'build', 'dist', '.tox', '.pytest_cache',
                          '.vscode', '.idea', '.cache', 'site-packages']:
                if dir_name == pattern:
                    return True

        return False

    def _recursive_scan_with_exclusions(self, dir_path: Path, patterns: list[str],
                                       include_hidden: bool, exclude_patterns: list[str]):
        """Recursively scan directory while excluding specified patterns."""
        try:
            # Check if current directory should be excluded
            if self._should_exclude_directory(dir_path, exclude_patterns):
                return

            # Scan files in current directory
            for pattern in patterns:
                for file_path in dir_path.glob(pattern):
                    if file_path.is_file():
                        if not include_hidden and file_path.name.startswith('.'):
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

    def find_source_files(self, dir_path: Path, languages: list[str] | None = None,
                         exclude_patterns: list[str] | None = None,
                         progress_callback: Callable[[str], None] | None = None) -> list[Path]:
        """
        Find source code files in a directory with progress feedback.

        Args:
            dir_path: Directory to search
            languages: List of languages to include (default: all)
            exclude_patterns: Additional exclusion patterns
            progress_callback: Optional callback for progress updates

        Returns:
            List of source code file paths
        """
        if not dir_path.exists() or not dir_path.is_dir():
            raise ValueError(f"Directory does not exist or is not accessible: {dir_path}")

        if progress_callback:
            progress_callback(f"Scanning directory: {dir_path}")

        source_files = []
        exclusion_patterns = self.DEFAULT_EXCLUSION_PATTERNS.copy()
        files_processed = 0

        if exclude_patterns:
            exclusion_patterns.extend(exclude_patterns)

        try:
            # Pass exclusion patterns to scan_directory to avoid scanning excluded directories
            for file_path in self._recursive_scan_with_exclusions(
                dir_path, ['*'], False, exclusion_patterns
            ):
                files_processed += 1

                # Provide progress feedback every 50 files for more responsive feedback
                if progress_callback and files_processed % 50 == 0:
                    progress_callback(f"Processed {files_processed} files, found {len(source_files)} source files")

                # Check if it's a source code file
                if not self.is_source_code_file(file_path):
                    continue

                # Check language filter (simplified - just check extension)
                if languages:
                    file_ext = file_path.suffix.lower()
                    # Simple language mapping
                    lang_map = {
                        '.py': 'python', '.js': 'javascript', '.ts': 'typescript',
                        '.java': 'java', '.go': 'go', '.rs': 'rust', '.cpp': 'cpp',
                        '.c': 'c', '.php': 'php', '.rb': 'ruby'
                    }
                    file_language = lang_map.get(file_ext)
                    if file_language and file_language not in languages:
                        continue

                source_files.append(file_path)

            if progress_callback:
                progress_callback(f"✅ Completed: found {len(source_files)} source files in {files_processed} total files")

            return source_files

        except (OSError, PermissionError, UnicodeDecodeError) as e:
            if progress_callback:
                progress_callback(f"❌ File discovery failed: {e}")
            raise ValueError(f"Could not discover files in {dir_path}: {e}") from e


def test_simple_file_utils():
    """Test the simplified file utilities."""
    print("Testing SimpleFileUtilities...")

    file_utils = SimpleFileUtilities()
    current_dir = Path(".")

    def progress_callback(message):
        print(f"  [INFO] {message}")

    print(f"Testing file discovery in: {current_dir.absolute()}")
    source_files = file_utils.find_source_files(
        current_dir,
        progress_callback=progress_callback
    )

    print(f"✓ Found {len(source_files)} source files")

    # Show a few examples
    if source_files:
        print("  Example files found:")
        for i, file_path in enumerate(source_files[:5]):
            print(f"    {i+1}. {file_path}")

    return True


if __name__ == "__main__":
    test_simple_file_utils()
