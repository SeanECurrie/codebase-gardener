# CLAUDE.md

## READ FIRST (Auto-Run)
- Always read (in order) the directives and spec before any action:
  `.kiro/specs/enhanced-codebase-auditor/claude-directives.md`
  `.kiro/specs/enhanced-codebase-auditor/requirements.md`
  `.kiro/specs/enhanced-codebase-auditor/design.md`
  `.kiro/specs/enhanced-codebase-auditor/tasks.md`
  `.kiro/steering/task-execution-framework.md`
- Non-interactive mode: never ask to proceed; use safe defaults.

## CRITICAL TASK COMPLETION REQUIREMENT
**ALWAYS UPDATE TASKS.MD FIRST** when completing any task:
- Change `- [ ] N. Task Name` to `- [x] N. Task Name **COMPLETED YYYY-MM-DD**`
- Add completion checkmarks to all Pre-Task, Implementation, Post-Task phases
- Document key findings and gaps directly in the task
- This is completion criteria #11 - the task is NOT complete without this update

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MVP Scope

**Current Focus**: Single-file CLI tool only (`codebase_auditor.py` + `simple_file_utils.py`)

The project is scoped to MVP - a working interactive CLI for immediate codebase analysis. Complex system components in `*_DISABLED/` directories are parked for post-MVP development.

**Core Components:**
1. **Single-file Auditor** (`codebase_auditor.py`) - Main interactive CLI with retry logic
2. **File Utilities** (`simple_file_utils.py`) - Source file discovery and filtering

## Quick Development Commands

## How to Run

### Lint/Format
```bash
ruff check --fix && ruff format
```

### Tests
```bash
pytest -q tests/test_single_file_auditor.py
python -m pytest -q tests/test_project_structure.py
```

### Smoke (no Ollama needed)
```bash
PYTHONPATH=. python scripts/smoke_cli.py
```

### Run CLI (requires Ollama running & model present)
```bash
python codebase_auditor.py
```

**Note:** CLI now includes retry behavior for Ollama connections with exponential backoff and clearer error messages.

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Lint with Ruff
ruff src/ tests/

# Run all quality checks
black . && isort . && mypy src/ && ruff .
```

### Running the Applications

#### Single-file Auditor (Recommended for immediate use)
```bash
# Interactive CLI mode
python codebase_auditor.py

# With specific Ollama settings
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b
python codebase_auditor.py
```

#### Full System (Development/Advanced)
```bash
# Setup development environment
./setup.sh

# Run main application
python -m codebase_gardener.main analyze /path/to/project
```

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev,performance]"
# OR minimal: pip install ollama

# Install requirements
pip install -r requirements.txt
```

## Architecture Overview

### Key Components

**Working Components:**
- `codebase_auditor.py` - Single-file interactive auditor (fully functional)
- `simple_file_utils.py` - File discovery and processing utilities
- `src/codebase_gardener/utils/file_utils.py` - Enhanced file utilities
- `src/codebase_gardener/config/` - Configuration management

**Complex System Components (varying completion states):**
- `src/codebase_gardener/core/` - Project registry, context management, training pipeline
- `src/codebase_gardener/models/` - AI model interfaces (some disabled)
- `src/codebase_gardener/data/` - Vector stores and preprocessing
- `src/codebase_gardener/ui/` - Gradio web interface
- `src/codebase_gardener/monitoring/` - Operational monitoring
- `src/codebase_gardener/performance/` - Load testing and benchmarking

### File Processing Architecture

The codebase uses a multi-stage file filtering approach:
1. **Discovery**: Find all files in target directory
2. **Filtering**: Exclude dependencies, build files, binaries using patterns in `EXCLUDE_PATTERNS`
3. **Size-based Analysis**: Different analysis depth based on project size:
   - Small (≤5 files): Brief analysis
   - Medium (6-100 files): Comprehensive analysis
   - Large (>100 files): High-level overview

### AI Integration

- **Primary Interface**: Direct `ollama` package usage
- **Model Support**: Ollama-compatible models (llama3.2:3b recommended for development)
- **Context Management**: Project-specific conversation states
- **Disabled Components**: Complex OllamaClient wrapper (use ollama package directly)

## Development Patterns

### File Utilities Usage
```python
# Use SimpleFileUtilities for basic operations
from simple_file_utils import SimpleFileUtilities
utils = SimpleFileUtilities()
files = utils.discover_files(directory_path)

# Use enhanced FileUtilities for advanced operations
from codebase_gardener.utils.file_utils import FileUtilities
utils = FileUtilities()
```

### Testing Strategy
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Performance tests for load scenarios
- Separate test configurations for different components

### Configuration Management
- Environment variables with `CODEBASE_GARDENER_` prefix
- Pydantic-based settings validation
- Development vs production configurations

## Dependencies

### Core Runtime
- `ollama` - LLM inference
- `pydantic` - Configuration validation
- `structlog` - Logging
- `click` - CLI interface
- `rich` - Console output

### Development
- `pytest` - Testing framework
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Type checking
- `ruff` - Linting

### Full System (when using advanced features)
- `transformers` + `peft` - Model loading and LoRA
- `lancedb` - Vector database
- `gradio` - Web interface
- `tree-sitter` - Code parsing

## Common Development Tasks

### Adding New File Types
1. Update `EXCLUDE_PATTERNS` in file utilities
2. Add parsing logic if needed
3. Update tests to include new file types

### Modifying Analysis Depth
- Edit size thresholds in `codebase_auditor.py`
- Update corresponding prompts for different analysis levels

### Extending CLI Commands
- Add commands to `src/codebase_gardener/main.py`
- Follow Click command patterns
- Include rich console output for user feedback

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check model availability: `ollama list`
- Set correct `OLLAMA_HOST` environment variable

### Import Errors
- Some components are intentionally disabled (e.g., `OllamaClient`)
- Use direct ollama package imports instead of wrapper classes
- Check PYTHONPATH includes `src/` directory

### Performance Issues
- Large projects (>100 files) automatically get high-level analysis
- Use specific subdirectories for detailed analysis
- Monitor memory usage with performance utilities
