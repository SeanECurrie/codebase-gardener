# File Utilities Component

## Overview

The File Utilities component provides comprehensive file system operations and utilities that complement the directory setup functionality. It includes file type detection, safe file operations, directory traversal, cross-platform path handling, and file monitoring capabilities.

## Architecture

### Core Components

```
FileUtilities
├── File Type Detection
│   ├── Extension-based detection
│   ├── MIME type analysis
│   └── Content-based detection
├── File Metadata Extraction
│   ├── Size and timestamps
│   ├── Encoding detection
│   ├── Line counting
│   └── Permission analysis
├── Directory Traversal
│   ├── Recursive scanning
│   ├── Pattern matching
│   └── Exclusion filtering
├── Safe File Operations
│   ├── Atomic writes
│   ├── Backup creation
│   └── Encoding-aware reads
├── File Monitoring
│   ├── Change detection
│   ├── Snapshot comparison
│   └── Timestamp tracking
└── Cross-platform Utilities
    ├── Path normalization
    ├── Hidden file detection
    ├── Permission checking
    └── Hash generation
```

### Design Principles

1. **Complementary Design**: Extends rather than replaces directory_setup.py functionality
2. **Cross-Platform Compatibility**: Uses pathlib.Path for all operations with OS-specific handling
3. **Error Handling Integration**: Uses existing error handling framework and custom exceptions
4. **Atomic Operations**: Safe file operations with backup and rollback capabilities
5. **Memory Efficiency**: Generator-based directory traversal for large codebases

## Key Features

### File Type Detection

- **Multi-layered Detection**: Uses extension, MIME type, and content analysis
- **Source Code Recognition**: Comprehensive support for programming languages
- **Language Identification**: Maps file extensions to programming languages
- **Fallback Mechanisms**: Graceful handling when detection fails

### Safe File Operations

- **Atomic Writes**: Temporary file + atomic move pattern
- **Automatic Backups**: Optional backup creation with timestamps
- **Encoding Detection**: Automatic encoding detection with fallbacks
- **Error Recovery**: Rollback capabilities for failed operations

### Directory Traversal

- **Pattern Matching**: Glob patterns and regex support
- **Exclusion Filters**: Built-in patterns for common build artifacts
- **Language Filtering**: Find files by programming language
- **Memory Efficient**: Generator-based iteration for large directories

### File Monitoring

- **Change Detection**: Track file modifications, creations, and deletions
- **Snapshot Comparison**: Compare directory states over time
- **Timestamp Tracking**: Efficient change detection using modification times
- **Batch Operations**: Process multiple changes efficiently

## Integration Points

### With Directory Setup

```python
# Complements DirectoryManager without duplication
from codebase_gardener.utils.directory_setup import DirectoryManager
from codebase_gardener.utils.file_utils import FileUtilities

# Directory manager handles structure creation
dir_manager = DirectoryManager()
dir_manager.initialize_directories()

# File utilities handle file operations within structure
file_utils = FileUtilities()
source_files = file_utils.find_source_files(dir_manager.projects_dir)
```

### With Parser and Preprocessing

```python
# Provides file discovery for parsing pipeline
from codebase_gardener.data.parser import TreeSitterParser
from codebase_gardener.utils.file_utils import find_source_files

# Find files to parse
source_files = find_source_files(project_dir, languages=['python'])

# Parse each file
parser = TreeSitterParser('python')
for file_path in source_files:
    content = safe_read_file(file_path)
    result = parser.parse(content, file_path)
```

### With Project Registry

```python
# Enables file-based project management
from codebase_gardener.core.project_registry import get_project_registry
from codebase_gardener.utils.file_utils import FileUtilities

registry = get_project_registry()
file_utils = FileUtilities()

# Analyze project files
for project in registry.list_projects():
    project_path = Path(project.source_path)
    snapshot = file_utils.create_file_snapshot(project_path)
    print(f"{project.name}: {snapshot.file_count} files")
```

### With UI Components

```python
# Supports file management in web interface
from codebase_gardener.utils.file_utils import FileUtilities

def handle_project_upload(project_path: str):
    file_utils = FileUtilities()
    
    # Validate project structure
    source_files = file_utils.find_source_files(Path(project_path))
    if not source_files:
        raise ValueError("No source files found in project")
    
    # Create project snapshot
    snapshot = file_utils.create_file_snapshot(Path(project_path))
    return {
        'file_count': snapshot.file_count,
        'total_size': snapshot.total_size,
        'languages': list(set(
            file_utils.get_language_from_file(f) 
            for f in source_files 
            if file_utils.get_language_from_file(f)
        ))
    }
```

## Configuration

### Default Exclusion Patterns

The component includes sensible defaults for excluding common build artifacts:

```python
DEFAULT_EXCLUSION_PATTERNS = [
    # Version control
    '.git', '.svn', '.hg', '.bzr',
    # Dependencies
    'node_modules', '__pycache__', '.pytest_cache', 'venv', 'env',
    'vendor', 'target', 'build', 'dist', '.tox',
    # IDE files
    '.vscode', '.idea', '*.swp', '*.swo', '*~', '.DS_Store',
    # Compiled files
    '*.pyc', '*.pyo', '*.class', '*.o', '*.so', '*.dll', '*.exe',
    # Logs and temporary files
    '*.log', '*.tmp', '*.temp', '.cache'
]
```

### Source Code Extensions

Comprehensive support for programming languages:

```python
SOURCE_CODE_EXTENSIONS = {
    '.py', '.js', '.ts', '.jsx', '.tsx', '.java', '.c', '.cpp', '.h', '.hpp',
    '.cs', '.php', '.rb', '.go', '.rs', '.swift', '.kt', '.scala', '.clj',
    '.hs', '.ml', '.fs', '.vb', '.pl', '.sh', '.bash', '.zsh', '.fish',
    '.ps1', '.bat', '.cmd', '.r', '.m', '.mm', '.sql', '.html', '.htm',
    '.css', '.scss', '.sass', '.less', '.xml', '.json', '.yaml', '.yml',
    '.toml', '.ini', '.cfg', '.conf', '.md', '.rst', '.tex', '.vue'
}
```

## Performance Characteristics

### Memory Usage

- **Generator-based Traversal**: Constant memory usage for large directories
- **Efficient Caching**: Minimal memory overhead for file metadata
- **Streaming Operations**: Large files processed in chunks

### CPU Utilization

- **Optimized File I/O**: Minimal system calls for file operations
- **Batch Processing**: Efficient handling of multiple files
- **Lazy Evaluation**: Operations performed only when needed

### Cross-Platform Performance

- **Native Path Operations**: Uses pathlib for optimal performance
- **OS-Specific Optimizations**: Platform-specific code paths where beneficial
- **Efficient Permission Checking**: Minimal overhead for permission operations

## Error Handling

### Exception Hierarchy

```python
FileUtilityError
├── File operation failures
├── Permission errors
├── Encoding errors
└── Path resolution errors
```

### Error Recovery

- **Graceful Degradation**: Continue operation when individual files fail
- **Automatic Fallbacks**: Try alternative approaches when primary method fails
- **Detailed Error Context**: Provide actionable error messages and suggestions

### Logging Integration

```python
# Structured logging for all operations
logger.debug("File operation completed", file_path=str(file_path), operation="read")
logger.error("File operation failed", file_path=str(file_path), error=str(e))
```

## Testing Strategy

### Unit Tests

- **File Type Detection**: Test all supported file types and edge cases
- **Safe Operations**: Test atomic writes, backups, and error recovery
- **Cross-Platform**: Test path handling across different operating systems
- **Error Conditions**: Test all error scenarios and recovery mechanisms

### Integration Tests

- **Component Integration**: Test with directory setup, parser, and registry
- **Realistic Scenarios**: Test with actual project structures
- **Performance Tests**: Verify performance with large codebases
- **Concurrent Access**: Test thread safety and concurrent operations

### Test Coverage

- **49 Unit Tests**: Comprehensive coverage of all functionality
- **Integration Scenarios**: Real-world usage patterns
- **Error Handling**: All error conditions and recovery paths
- **Cross-Platform**: Platform-specific behavior verification

## Usage Examples

### Basic File Operations

```python
from codebase_gardener.utils import FileUtilities

file_utils = FileUtilities()

# Detect file type
file_type = file_utils.detect_file_type(Path("script.py"))

# Get file information
file_info = file_utils.get_file_info(Path("script.py"))

# Safe file operations
content = file_utils.safe_read_file(Path("config.txt"))
file_utils.atomic_write_file(Path("output.txt"), "data", backup=True)
```

### Project Analysis

```python
# Find and analyze source files
source_files = file_utils.find_source_files(
    Path("project/"), 
    languages=["python", "javascript"]
)

for file_path in source_files:
    file_info = file_utils.get_file_info(file_path)
    language = file_utils.get_language_from_file(file_path)
    print(f"{file_path.name}: {language}, {file_info.size} bytes")
```

### File Monitoring

```python
# Create snapshots and monitor changes
initial = file_utils.create_file_snapshot(Path("project/"))
# ... time passes ...
current = file_utils.create_file_snapshot(Path("project/"))

changes = file_utils.compare_snapshots(initial, current)
for change in changes:
    print(f"{change.change_type}: {change.path.name}")
```

## Future Enhancements

### Potential Improvements

1. **Advanced File Watching**: Real-time file system event monitoring
2. **Content Analysis**: More sophisticated file content analysis
3. **Compression Support**: Built-in support for compressed archives
4. **Network File Systems**: Support for remote file systems
5. **Metadata Caching**: Persistent caching of file metadata

### Extension Points

- **Custom File Types**: Plugin system for custom file type detection
- **Custom Filters**: User-defined exclusion and inclusion patterns
- **Custom Analyzers**: Pluggable file content analyzers
- **Custom Monitors**: Extensible file monitoring backends

## Troubleshooting

### Common Issues

1. **Permission Errors**: Check file and directory permissions
2. **Encoding Issues**: Verify file encoding and use fallback options
3. **Large Directory Performance**: Use exclusion patterns to filter files
4. **Cross-Platform Paths**: Use normalize_path() for path compatibility

### Debug Information

Enable debug logging to see detailed file operation information:

```python
import logging
logging.getLogger().setLevel(logging.DEBUG)
```

### Performance Tuning

- Use exclusion patterns to skip unnecessary files
- Process files in batches for better performance
- Consider using generators for memory efficiency
- Monitor system resources during large operations