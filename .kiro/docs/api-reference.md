# API Reference

This document provides comprehensive API reference for all Codebase Gardener components.

## File Utilities API

### FileUtilities Class

The main class for comprehensive file system operations.

```python
from codebase_gardener.utils import FileUtilities

file_utils = FileUtilities()
```

#### File Type Detection

```python
# Detect file type
file_type = file_utils.detect_file_type(Path("script.py"))
# Returns: FileType.SOURCE_CODE

# Check if file is source code
is_source = file_utils.is_source_code_file(Path("script.py"))
# Returns: True

# Get programming language
language = file_utils.get_language_from_file(Path("script.py"))
# Returns: "python"
```

#### File Metadata

```python
# Get comprehensive file information
file_info = file_utils.get_file_info(Path("script.py"))
# Returns: FileInfo object with size, type, encoding, etc.

# Calculate directory size
total_size = file_utils.calculate_directory_size(Path("project/"))
# Returns: total size in bytes

# Detect file encoding
encoding = file_utils.get_file_encoding(Path("text.txt"))
# Returns: "utf-8" or detected encoding
```

#### Directory Traversal

```python
# Scan directory for files
files = list(file_utils.scan_directory(Path("project/"), patterns=["*.py"]))
# Returns: List of Python files

# Find source code files
source_files = file_utils.find_source_files(Path("project/"), languages=["python"])
# Returns: List of Python source files

# Apply exclusion patterns
filtered = file_utils.apply_exclusion_patterns(files, ["*.pyc", "__pycache__"])
# Returns: Filtered file list
```

#### Safe File Operations

```python
# Safely read file with encoding detection
content = file_utils.safe_read_file(Path("file.txt"))
# Returns: File content as string

# Atomically write file with backup
file_utils.atomic_write_file(Path("file.txt"), "content", backup=True)

# Create file backup
backup_path = file_utils.create_backup(Path("important.txt"))
# Returns: Path to backup file
```

#### File Monitoring

```python
# Get file changes since timestamp
changes = file_utils.get_file_changes(Path("project/"), since=datetime.now())
# Returns: List of FileChange objects

# Create directory snapshot
snapshot = file_utils.create_file_snapshot(Path("project/"))
# Returns: FileSnapshot object

# Compare snapshots
changes = file_utils.compare_snapshots(old_snapshot, new_snapshot)
# Returns: List of changes between snapshots
```

#### Cross-platform Utilities

```python
# Normalize path for cross-platform compatibility
normalized = file_utils.normalize_path("./path/../file.txt")
# Returns: Normalized Path object

# Check if file is hidden
is_hidden = file_utils.is_hidden_file(Path(".gitignore"))
# Returns: True

# Check file permissions
permissions = file_utils.check_file_permissions(Path("file.txt"))
# Returns: Dict with readable, writable, executable flags

# Generate file hash
hash_value = file_utils.generate_file_hash(Path("file.txt"))
# Returns: SHA256 hash as hex string
```

### Convenience Functions

For common operations, use the convenience functions:

```python
from codebase_gardener.utils import (
    detect_file_type, is_source_code_file, get_file_info,
    find_source_files, safe_read_file, atomic_write_file,
    normalize_path
)

# These functions use the global file_utilities instance
file_type = detect_file_type(Path("script.py"))
source_files = find_source_files(Path("project/"))
content = safe_read_file(Path("file.txt"))
```

### Data Classes

#### FileInfo

```python
@dataclass
class FileInfo:
    path: Path
    size: int
    modified_time: datetime
    file_type: FileType
    encoding: Optional[str] = None
    line_count: Optional[int] = None
    is_hidden: bool = False
    permissions: Optional[str] = None
```

#### FileChange

```python
@dataclass
class FileChange:
    path: Path
    change_type: str  # 'created', 'modified', 'deleted'
    timestamp: datetime
    old_size: Optional[int] = None
    new_size: Optional[int] = None
```

#### FileSnapshot

```python
@dataclass
class FileSnapshot:
    directory: Path
    timestamp: datetime
    files: Dict[Path, FileInfo]
    total_size: int
    file_count: int
```

### Enums

#### FileType

```python
class FileType(Enum):
    SOURCE_CODE = "source_code"
    TEXT = "text"
    BINARY = "binary"
    IMAGE = "image"
    DOCUMENT = "document"
    ARCHIVE = "archive"
    UNKNOWN = "unknown"
```

### Error Handling

All file utility operations may raise `FileUtilityError` for various failure conditions:

```python
from codebase_gardener.utils import FileUtilityError, safe_read_file
from pathlib import Path

try:
    content = safe_read_file(Path("nonexistent.txt"))
except FileUtilityError as e:
    print(f"File operation failed: {e}")
```

### Integration Examples

#### Project Analysis Workflow

```python
from pathlib import Path
from codebase_gardener.utils import FileUtilities

def analyze_project(project_path: Path):
    file_utils = FileUtilities()
    
    # Find all source files
    source_files = file_utils.find_source_files(project_path)
    
    # Analyze each file
    for file_path in source_files:
        file_info = file_utils.get_file_info(file_path)
        print(f"{file_path.name}: {file_info.file_type.value}, {file_info.size} bytes")
        
        if file_info.file_type == FileType.SOURCE_CODE:
            language = file_utils.get_language_from_file(file_path)
            print(f"  Language: {language}")
    
    # Create snapshot for monitoring
    snapshot = file_utils.create_file_snapshot(project_path)
    print(f"Project snapshot: {snapshot.file_count} files, {snapshot.total_size} bytes")
```

#### Safe Configuration Management

```python
from pathlib import Path
from codebase_gardener.utils import safe_read_file, atomic_write_file
import json

def update_config(config_path: Path, updates: dict):
    # Safely read existing config
    try:
        config_text = safe_read_file(config_path)
        config = json.loads(config_text)
    except FileUtilityError:
        config = {}
    
    # Apply updates
    config.update(updates)
    
    # Atomically write updated config with backup
    atomic_write_file(config_path, json.dumps(config, indent=2), backup=True)
```

#### File Change Monitoring

```python
from datetime import datetime
from codebase_gardener.utils import FileUtilities

def monitor_project_changes(project_path: Path):
    file_utils = FileUtilities()
    
    # Create initial snapshot
    initial_snapshot = file_utils.create_file_snapshot(project_path)
    
    # ... time passes, files are modified ...
    
    # Create new snapshot and compare
    current_snapshot = file_utils.create_file_snapshot(project_path)
    changes = file_utils.compare_snapshots(initial_snapshot, current_snapshot)
    
    for change in changes:
        print(f"{change.change_type}: {change.path.name} at {change.timestamp}")
```