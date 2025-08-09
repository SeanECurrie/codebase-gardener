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
### Single-file Auditor Quickstart (Task 2 & 3)

For a minimal, working auditor with interactive CLI:

```bash
# Optional: create a minimal venv
python -m venv .venv
source .venv/bin/activate
pip install ollama

# Ensure Ollama is running and you have a model
ollama serve &
ollama pull llama3.2:3b  # lightweight, reliable model

# Optional: select host/model
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b

# Run the interactive auditor
python codebase_auditor.py
```

**Interactive Commands:**
```
🔍 > help                              # Show all commands
🔍 > analyze ./my-project               # Analyze a codebase directory  
🔍 > status                             # Show analysis summary and files
🔍 > chat What are the main issues?     # Ask questions about the code
🔍 > export my-analysis.md              # Export markdown report
🔍 > quit                               # Exit the auditor
```

**Features:**
- ✅ **Context-aware analysis**: Different analysis depth based on project size
- ✅ **Smart file filtering**: Automatically excludes dependencies and build files
- ✅ **Real-time progress**: Visual feedback during analysis with file counts
- ✅ **Conversational Q&A**: Ask questions about your codebase after analysis
- ✅ **Markdown reports**: Export detailed analysis for documentation
- ✅ **Status tracking**: See which files were analyzed and processing stats

## Usage Examples

### Example 1: Analyzing a Small Project (3-5 files)
```bash
🔍 > analyze ./my-small-project
📊 Analysis Summary: 3/3 files, 1,247 bytes processed

🔍 > chat What does this code do?
💭 Response: This appears to be a simple utility project with a main.py file 
that defines a greeting function, a utils.py with helper classes, and a README. 
The code is straightforward and well-organized for its scope.

🔍 > export small-project-analysis.md
📄 Report exported to: small-project-analysis.md
```

### Example 2: Analyzing a Medium Project (20-40 files)  
```bash
🔍 > analyze ./my-web-app
📊 Analysis Summary: 28/28 files, 156,789 bytes processed

🔍 > status
✅ 📊 Analysis Summary: 28/28 files, 156,789 bytes processed
📁 Files analyzed: 28 files
   - src/components/Header.tsx
   - src/pages/Dashboard.tsx
   - src/utils/api.ts
   - package.json
   - ... and 24 more files

🔍 > chat What are the main architectural patterns used?
💭 Response: This React application follows a component-based architecture with:
- **Component Structure**: Organized in src/components/ with reusable UI elements
- **Page Routing**: Next.js pages in src/pages/ for different app sections  
- **API Layer**: Centralized API utilities in src/utils/api.ts
- **State Management**: Uses React hooks for local state management
```

### Example 3: Analyzing a Large Project (100+ files)
```bash
🔍 > analyze ./enterprise-app
📊 Analysis Summary: 247/312 files, 1,891,456 bytes processed

🔍 > chat What are the strategic recommendations for this codebase?
💭 Response: **System Overview**: This is a multi-service enterprise application 
with microservices architecture. **Key Recommendations**: 
1. Consolidate duplicate authentication logic across services
2. Implement centralized logging and monitoring
3. Standardize API response formats between services
4. Consider breaking down the largest monolith service into smaller components
```

### Analysis Depth by Project Size

The auditor automatically adjusts analysis depth:

- **Small projects (≤5 files)**: Brief purpose and structure analysis
- **Medium projects (6-100 files)**: Comprehensive architectural analysis  
- **Large projects (>100 files)**: High-level strategic overview

## What This Tool Does and Doesn't Do

### ✅ What It Does Well
- **Architectural Analysis**: Excellent at identifying modular structure and component relationships
- **Clean Projects**: Works best on well-organized codebases with clear structure  
- **Multiple Languages**: Supports Python, JavaScript, TypeScript, Java, Go, Rust, and more
- **Context Awareness**: Adjusts analysis depth automatically based on project size
- **File Filtering**: Smart exclusion of dependencies, build files, and virtual environments

### ⚠️ Current Limitations  
- **Dependency-Heavy Projects**: May struggle with projects that have many external dependencies
- **Large Binary Files**: Cannot analyze compiled code or large data files effectively
- **Real-Time Updates**: Analysis is point-in-time, doesn't track changes over time
- **Domain Expertise**: General code analysis, not specialized for specific frameworks
- **File Access Issues**: May have trouble with permission-restricted or timeout-prone files

### 🔧 When to Use Other Tools
- **For detailed debugging**: Use IDE tools or debuggers for step-through analysis
- **For performance profiling**: Use specialized profilers for performance bottlenecks  
- **For security audits**: Use dedicated security scanners for vulnerability detection
- **For code formatting**: Use language-specific linters and formatters
- **For real-time collaboration**: Use IDE extensions or collaborative development tools

### 💡 Best Results With
- **Clean, organized codebases** with clear directory structure
- **Projects between 10-100 files** for optimal analysis depth
- **Source code repositories** rather than compiled distributions
- **Well-documented projects** where README matches actual code

## Troubleshooting

### Common Issues

**"Model check warning (continuing anyway)"**
- This is normal - the auditor will continue and work fine
- To fix: Ensure Ollama is running with `ollama serve`

**"No analysis completed yet"**  
- Run `analyze <directory>` command first before using `chat` or `export`
- Check that the directory path exists and contains source files

**Analysis includes too many dependency files**
- The tool automatically excludes `.venv`, `node_modules`, `__pycache__` etc.
- If still seeing unwanted files, they may be in non-standard locations

**Timeout errors when reading files**
- Usually happens with very large files or restricted access
- The analysis will continue with other files

### Performance Tips
- Projects with 10-100 files give the best analysis quality
- For very large projects, focus on specific subdirectories
- Clean up build artifacts and dependencies before analysis

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
python -m venv .venv
source .venv/bin/activate  # On macOS/Linux
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