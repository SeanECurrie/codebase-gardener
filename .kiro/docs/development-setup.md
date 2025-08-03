# Development Setup Guide

## Prerequisites

### System Requirements
- **macOS** (optimized for Mac Mini M4)
- **Python 3.9+** with pip
- **Git** for version control
- **Ollama** for local LLM inference
- **8GB+ RAM** (16GB recommended for multiple projects)

### Hardware Optimization
- **Apple Silicon M4** - Primary target platform
- **SSD Storage** - Fast model loading and vector operations
- **Unified Memory** - Efficient for dynamic model loading

## Development Environment Setup

### 1. Clone and Navigate
```bash
git clone https://github.com/seanc-codingtemple/codebase-gardener.git
cd codebase-gardener
```

### 2. Python Environment
```bash
# Create virtual environment
python -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows

# Verify Python version
python --version  # Should be 3.9+
```

### 3. Install Dependencies
```bash
# Install development dependencies
pip install -e ".[dev]"

# Verify installation
python -c "import codebase_gardener; print('Installation successful')"
```

### 4. Install Ollama
```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Download base model (in another terminal)
ollama pull codellama:7b
```

### 5. Development Tools Setup
```bash
# Install pre-commit hooks
pre-commit install

# Run initial code formatting
black src/ tests/

# Run type checking
mypy src/

# Run tests to verify setup
pytest tests/ -v
```

## IDE Configuration

### VS Code Setup
```json
// .vscode/settings.json
{
    "python.defaultInterpreterPath": "./venv/bin/python",
    "python.formatting.provider": "black",
    "python.linting.enabled": true,
    "python.linting.mypyEnabled": true,
    "python.testing.pytestEnabled": true,
    "python.testing.pytestArgs": ["tests/"]
}
```

### Kiro IDE Integration
- Memory files are automatically tracked in `.kiro/memory/`
- Steering documents provide context during development
- Task specifications guide implementation workflow

## Environment Variables

### Required Configuration
```bash
# Create .env file
cat > .env << EOF
# Application Configuration
CODEBASE_GARDENER_DEBUG=true
CODEBASE_GARDENER_LOG_LEVEL=DEBUG
CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener

# Model Configuration
CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code

# Development Configuration
CODEBASE_GARDENER_BATCH_SIZE=16  # Smaller for development
CODEBASE_GARDENER_MAX_WORKERS=2  # Conservative for development
EOF
```

### Load Environment
```bash
# Add to your shell profile (.bashrc, .zshrc, etc.)
export $(cat .env | xargs)
```

## Development Workflow

### Task-Based Development
1. **Review Task**: Read task specification in `.kiro/specs/codebase-gardener-mvp/tasks.md`
2. **Create Branch**: `git checkout -b feat/task-name`
3. **Create Memory File**: Document approach in `.kiro/memory/`
4. **Research**: Use MCP tools for documentation and examples
5. **Implement**: Follow incremental development approach
6. **Test**: Write and run comprehensive tests
7. **Document**: Update memory file with lessons learned
8. **Commit**: Use conventional commit format
9. **Update Steering**: Update patterns if new conventions established

### Memory File Workflow
```bash
# Create memory file for task
touch .kiro/memory/component_task_N.md

# Document approach and decisions
# (See memory file template)

# Update throughout implementation
# Commit memory file with implementation
git add .kiro/memory/component_task_N.md
git commit -m "feat: implement component with documented approach"
```

## Testing Setup

### Test Categories
```bash
# Unit tests (fast, isolated)
pytest tests/unit/ -v

# Integration tests (component interaction)
pytest tests/integration/ -v

# End-to-end tests (full system)
pytest tests/e2e/ -v

# Performance tests
pytest tests/performance/ --benchmark-only
```

### Test Data Setup
```bash
# Create test data directory
mkdir -p tests/data/sample_codebases

# Add sample Python project
mkdir -p tests/data/sample_codebases/python_project
echo "def hello(): return 'world'" > tests/data/sample_codebases/python_project/main.py
```

## Debugging Setup

### Logging Configuration
```python
# Development logging setup
import logging
import structlog

# Configure structured logging for development
logging.basicConfig(
    level=logging.DEBUG,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s"
)

logger = structlog.get_logger(__name__)
```

### Debug Tools
```bash
# Interactive debugging with ipdb
pip install ipdb

# Add breakpoint in code
import ipdb; ipdb.set_trace()

# Memory profiling
pip install memory-profiler
python -m memory_profiler your_script.py
```

## Performance Monitoring

### Mac Mini M4 Specific
```bash
# Monitor CPU and memory usage
top -pid $(pgrep -f "python.*codebase_gardener")

# Monitor thermal state
sudo powermetrics --samplers smc -n 1 | grep -i temp

# Monitor memory pressure
memory_pressure
```

### Application Metrics
```python
# Add to development code
import psutil
import time

def monitor_resources():
    process = psutil.Process()
    print(f"Memory: {process.memory_info().rss / 1024 / 1024:.1f} MB")
    print(f"CPU: {process.cpu_percent():.1f}%")
```

## Troubleshooting Common Issues

### Ollama Connection Issues
```bash
# Check Ollama status
ollama list

# Restart Ollama service
pkill ollama
ollama serve

# Test connection
curl http://localhost:11434/api/version
```

### Python Environment Issues
```bash
# Recreate virtual environment
rm -rf venv
python -m venv venv
source venv/bin/activate
pip install -e ".[dev]"
```

### Memory Issues on Mac Mini M4
```bash
# Monitor memory usage
vm_stat

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +
find . -name "*.pyc" -delete
```

## Development Best Practices

### Code Quality
- **Follow PEP 8** with black formatting
- **Type hints** for all public APIs
- **Docstrings** for all modules, classes, and functions
- **Error handling** with custom exceptions
- **Logging** instead of print statements

### Git Workflow
- **Feature branches** for each task
- **Conventional commits** with clear messages
- **Memory files** committed with implementation
- **Steering updates** when patterns change

### Testing Standards
- **Test-driven development** where appropriate
- **Mock external dependencies** (Ollama, file system)
- **Performance benchmarks** for critical paths
- **Edge case coverage** especially for AI components

## Next Steps

1. **Verify Setup**: Run `pytest tests/ -v` to ensure everything works
2. **Review Steering**: Read all documents in `.kiro/steering/`
3. **Start Task 1**: Follow the task workflow in the specifications
4. **Create Memory File**: Document your approach and decisions
5. **Implement Incrementally**: Build and test in small steps