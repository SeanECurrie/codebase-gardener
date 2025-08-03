# Codebase Gardener MVP 🌱

AI-powered project-specific codebase analysis through specialized LoRA adapters.

## Overview

Codebase Gardener creates **specialized AI assistants** for individual codebases, not generic code analysis tools. Each codebase gets its own "brain" - a LoRA (Low-Rank Adaptation) adapter trained specifically on that project's patterns, conventions, and context.

### Core Concept: Project-Specific Intelligence

- **Specialized LoRA Adapters**: Each project gets its own LoRA adapter trained on that codebase's unique patterns
- **Project Switching**: Switch between different specialized AI assistants via a dropdown interface
- **Local-First Processing**: All processing happens locally on your Mac Mini M4 for privacy and control
- **Context Awareness**: Each project maintains its own conversation history and analysis state

## Features

- 🧠 **Project-Specific AI**: LoRA adapters trained on individual codebases
- 🔄 **Dynamic Model Loading**: Efficient switching between project-specific models
- 🏠 **Local Processing**: Complete privacy with local Ollama integration
- 🌐 **Web Interface**: Gradio-based UI for easy project switching and analysis
- 🔍 **Vector Search**: LanceDB-powered semantic code search
- 📊 **Multi-Language Support**: Tree-sitter parsing for Python, JavaScript, TypeScript, and more
- ⚡ **Mac Mini M4 Optimized**: Efficient resource utilization for Apple Silicon

## Quick Start

### Prerequisites

- Python 3.11 or higher
- Mac Mini M4 (or compatible Apple Silicon Mac)
- [Ollama](https://ollama.ai) installed and running locally

### Installation

1. Clone the repository:
```bash
git clone https://github.com/codebase-gardener/codebase-gardener-mvp.git
cd codebase-gardener-mvp
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On macOS/Linux
```

3. Install the package:
```bash
pip install -e .
```

4. Initialize the application:
```bash
codebase-gardener init
```

### Usage

1. **Add a project**:
```bash
codebase-gardener add /path/to/your/codebase --name "My Project"
```

2. **Start the web interface**:
```bash
codebase-gardener serve
```

3. **Open your browser** to `http://localhost:7860` and start analyzing!

### Command Line Interface

```bash
# List all commands
codebase-gardener --help

# Add a new project
codebase-gardener add /path/to/project

# List registered projects
codebase-gardener list

# Remove a project
codebase-gardener remove "project-name"

# Start web interface
codebase-gardener serve --host 0.0.0.0 --port 8080
```

## Architecture

### Project Structure

```
codebase-gardener-mvp/
├── src/codebase_gardener/
│   ├── config/          # Configuration management
│   ├── core/            # Core business logic
│   ├── models/          # AI/ML model interfaces
│   ├── data/            # Data processing and storage
│   ├── ui/              # Gradio web interface
│   └── utils/           # Utility functions
├── tests/               # Test suite
├── docs/                # Documentation
└── pyproject.toml       # Project configuration
```

### Key Components

- **Project Registry**: Manages multiple processed codebases and their metadata
- **Dynamic Model Loader**: Efficiently loads/unloads LoRA adapters based on project selection
- **LoRA Training Pipeline**: Trains project-specific adapters automatically
- **Vector Store**: LanceDB-based storage for semantic code search
- **Context Manager**: Maintains separate conversation states per project

## Development

### Setup Development Environment

```bash
# Install with development dependencies
pip install -e .[dev]

# Install pre-commit hooks
pre-commit install

# Run tests
pytest

# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/codebase_gardener

# Run only unit tests
pytest -m unit

# Run only integration tests
pytest -m integration
```

## Configuration

Configuration is managed through environment variables with the `CODEBASE_GARDENER_` prefix:

```bash
# Application settings
export CODEBASE_GARDENER_DEBUG=true
export CODEBASE_GARDENER_LOG_LEVEL=DEBUG

# Model settings
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code

# Storage settings
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener
```

## Requirements

### System Requirements

- **OS**: macOS (optimized for Mac Mini M4)
- **Python**: 3.11 or higher
- **Memory**: 8GB RAM minimum (16GB recommended)
- **Storage**: 10GB free space for models and vector stores

### Dependencies

- **Ollama**: Local LLM inference
- **HuggingFace Transformers**: Model loading and PEFT
- **LanceDB**: Vector database for embeddings
- **Tree-sitter**: Multi-language code parsing
- **Gradio**: Web interface framework
- **Pydantic**: Configuration validation

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Workflow

1. Fork the repository
2. Create a feature branch: `git checkout -b feat/amazing-feature`
3. Make your changes and add tests
4. Run the test suite: `pytest`
5. Format your code: `black src/ tests/`
6. Submit a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

- 📖 [Documentation](https://docs.codebase-gardener.dev)
- 🐛 [Issue Tracker](https://github.com/codebase-gardener/codebase-gardener-mvp/issues)
- 💬 [Discussions](https://github.com/codebase-gardener/codebase-gardener-mvp/discussions)

## Roadmap

- [ ] Support for additional programming languages
- [ ] Advanced LoRA training configurations
- [ ] Integration with popular IDEs
- [ ] Performance optimizations for larger codebases
- [ ] Multi-user support and collaboration features

---

**Made with ❤️ for developers who want AI that truly understands their code.**