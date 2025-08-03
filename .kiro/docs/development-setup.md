# Development Setup Guide

## Project Structure Overview

The Codebase Gardener MVP follows modern Python packaging standards with a src layout structure:

```
codebase-gardener-mvp/
├── pyproject.toml           # Project configuration and dependencies
├── README.md               # Project documentation
├── requirements.txt        # Generated dependency list
├── .gitignore             # Git ignore patterns
├── .python-version        # Python version specification
├── src/                   # Source code (src layout)
│   └── codebase_gardener/
│       ├── __init__.py    # Main package
│       ├── main.py        # CLI entry point
│       ├── config/        # Configuration management
│       ├── core/          # Core business logic
│       ├── models/        # AI/ML model interfaces
│       ├── data/          # Data processing
│       ├── ui/            # User interface
│       └── utils/         # Utility functions
├── tests/                 # Test suite
├── .kiro/                 # Kiro-specific files
│   ├── docs/             # Documentation
│   ├── memory/           # Task memory files
│   └── specs/            # Feature specifications
└── docs/                 # Additional documentation
```

## Prerequisites

- **Python**: 3.11 or higher
- **Operating System**: macOS (optimized for Mac Mini M4)
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space for models and dependencies

## Installation Steps

### 1. Clone and Setup

```bash
# Clone the repository
git clone https://github.com/codebase-gardener/codebase-gardener-mvp.git
cd codebase-gardener-mvp

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On macOS/Linux

# Verify Python version
python --version  # Should be 3.11+
```

### 2. Install Dependencies

```bash
# Install in development mode with all dependencies
pip install -e .[dev]

# Or install just the core dependencies
pip install -e .

# Verify installation
codebase-gardener --help
cgardener --help  # Short alias
```

### 3. Initialize Application

```bash
# Initialize directory structure
codebase-gardener init

# This creates ~/.codebase-gardener/ with:
# - base_models/     (for storing base AI models)
# - projects/        (for project-specific data)
# - active_project.json (current project state)
```

## Development Workflow

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/codebase_gardener

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only
pytest -m "not slow"    # Skip slow tests

# Run tests with verbose output
pytest -v
```

### Code Quality

```bash
# Format code with Black
black src/ tests/

# Sort imports with isort
isort src/ tests/

# Type checking with MyPy
mypy src/

# Lint with Ruff
ruff check src/ tests/

# Run all quality checks
black src/ tests/ && isort src/ tests/ && mypy src/ && ruff check src/ tests/
```

### Development Commands

```bash
# Add a project for testing
codebase-gardener add /path/to/test/project --name "Test Project"

# List registered projects
codebase-gardener list

# Start development server
codebase-gardener serve --debug

# Remove test project
codebase-gardener remove "Test Project"
```

## Configuration

### Environment Variables

All configuration can be overridden with environment variables using the `CODEBASE_GARDENER_` prefix:

```bash
# Application settings
export CODEBASE_GARDENER_DEBUG=true
export CODEBASE_GARDENER_LOG_LEVEL=DEBUG

# Model settings
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code

# Storage settings
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener
export CODEBASE_GARDENER_MEMORY_LIMIT_GB=6

# Performance settings
export CODEBASE_GARDENER_MAX_WORKERS=4
export CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE=32
```

### Configuration File

Settings are managed through `src/codebase_gardener/config/settings.py` using Pydantic BaseSettings for validation and type safety.

## Package Structure Details

### Src Layout Benefits

The project uses src layout (source code in `src/` directory) which provides:

- **Import Safety**: Prevents accidentally importing from source during development
- **Clean Separation**: Clear distinction between source code and project files
- **Testing Reliability**: Ensures tests run against installed package, not source
- **Distribution Ready**: Proper structure for packaging and distribution

### Module Organization

- **config/**: Configuration management with Pydantic validation
- **core/**: Core business logic (project registry, context management, model loading)
- **models/**: AI/ML model interfaces (Ollama, PEFT, embeddings)
- **data/**: Data processing (parsing, preprocessing, vector storage)
- **ui/**: User interface components (Gradio web interface)
- **utils/**: Utility functions (file operations, error handling, logging)

## Dependencies

### Core AI/ML Dependencies

- **ollama**: Local LLM inference
- **transformers**: HuggingFace model support
- **peft**: Parameter Efficient Fine-Tuning
- **lancedb**: Vector database
- **tree-sitter**: Code parsing
- **gradio**: Web interface
- **nomic**: Code embeddings

### Development Dependencies

- **pytest**: Testing framework
- **black**: Code formatting
- **mypy**: Type checking
- **ruff**: Fast linting
- **pre-commit**: Git hooks

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure you've installed in development mode with `pip install -e .`
2. **Missing Dependencies**: Run `pip install -e .[dev]` to install all dependencies
3. **Python Version**: Verify you're using Python 3.11+ with `python --version`
4. **Virtual Environment**: Ensure virtual environment is activated

### Dependency Conflicts

If you encounter dependency conflicts:

```bash
# Create fresh virtual environment
deactivate
rm -rf venv
python -m venv venv
source venv/bin/activate

# Reinstall
pip install --upgrade pip
pip install -e .[dev]
```

### Performance Issues

For Mac Mini M4 optimization:

- Set `CODEBASE_GARDENER_MEMORY_LIMIT_GB=6` for 8GB systems
- Use `CODEBASE_GARDENER_MAX_WORKERS=4` for optimal CPU usage
- Monitor memory usage during development

## Next Steps

After setup:

1. **Add Test Project**: Use `codebase-gardener add` to add a small test project
2. **Start Web Interface**: Run `codebase-gardener serve` to test the UI
3. **Run Tests**: Execute `pytest` to verify everything works
4. **Read Architecture**: Review `.kiro/specs/codebase-gardener-mvp/design.md`
5. **Check Tasks**: Look at `.kiro/specs/codebase-gardener-mvp/tasks.md` for next steps

## Support

- Check the main README.md for usage instructions
- Review test files for usage examples
- Consult the design document for architecture details
- Look at memory files in `.kiro/memory/` for implementation notes