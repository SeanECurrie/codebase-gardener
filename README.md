# Codebase Gardener MVP

> **Specialized AI assistants for your codebases** - Each project gets its own "brain" trained specifically on that codebase's patterns, conventions, and context.

## 🎯 Project Vision

The Codebase Gardener MVP is fundamentally different from generic code analysis tools. Instead of providing one-size-fits-all responses, it creates **specialized AI assistants** for individual codebases using LoRA (Low-Rank Adaptation) adapters trained specifically on each project.

### Core Concept: Project Switching

- **Each codebase gets its own specialized LoRA adapter** trained on that project's unique patterns
- **Switch between projects = switch between specialized AI assistants**
- **Maintain separate conversation contexts** for each project
- **Local-first processing** - your code never leaves your machine

## 🏗️ Architecture Overview

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │    │  Project Context │    │ Dynamic Model   │
│ Project Selector│◄──►│    Manager       │◄──►│    Loader       │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│ Project Registry│    │   Tree-sitter    │    │ Ollama + LoRA   │
│   & Metadata    │    │   Code Parser    │    │   Adapters      │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │                        │
                                ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Nomic Embed   │    │ Project-Specific │    │   LanceDB       │
│     Code        │◄──►│ Vector Stores    │◄──►│ Vector Storage  │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- **macOS** (optimized for Mac Mini M4)
- **Python 3.9+**
- **Ollama** installed and running locally
- **Git** for version control

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/seanc-codingtemple/codebase-gardener.git
   cd codebase-gardener
   ```

2. **Set up Python environment**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Install Ollama** (if not already installed)
   ```bash
   curl -fsSL https://ollama.ai/install.sh | sh
   ```

5. **Download base model**
   ```bash
   ollama pull codellama:7b  # or your preferred code model
   ```

6. **Initialize the application**
   ```bash
   python -m codebase_gardener.main init
   ```

### First Run

1. **Start the application**
   ```bash
   python -m codebase_gardener.main
   ```

2. **Open your browser** to `http://localhost:7860`

3. **Add your first project**
   - Click "Add Project"
   - Point to a local codebase directory
   - Wait for LoRA adapter training to complete

4. **Start analyzing**
   - Ask questions like "How does authentication work in this codebase?"
   - Switch between projects using the dropdown
   - Each project maintains its own conversation context

## 🛠️ Development Setup

### Development Dependencies

```bash
pip install -e ".[dev]"
```

This installs additional tools:
- `black` - Code formatting
- `pytest` - Testing framework
- `mypy` - Type checking
- `pre-commit` - Git hooks

### Project Structure

```
codebase-gardener/
├── src/codebase_gardener/          # Main application code
│   ├── config/                     # Configuration management
│   ├── core/                       # Core services (registry, context, loader)
│   ├── models/                     # AI model integrations
│   ├── data/                       # Data processing and storage
│   ├── ui/                         # Gradio interface
│   └── utils/                      # Utilities and helpers
├── tests/                          # Test suite
├── docs/                           # Documentation
├── .kiro/                          # Kiro IDE configuration
│   ├── specs/                      # Project specifications
│   └── steering/                   # Development principles
└── scripts/                        # Setup and utility scripts
```

### Development Workflow

1. **Create feature branch**
   ```bash
   git checkout -b feat/your-feature
   ```

2. **Follow the task structure** defined in `.kiro/specs/codebase-gardener-mvp/tasks.md`

3. **Create memory files** for each task to document decisions and learnings

4. **Run tests**
   ```bash
   pytest tests/
   ```

5. **Format code**
   ```bash
   black src/ tests/
   ```

6. **Type check**
   ```bash
   mypy src/
   ```

## 🎯 Key Features

### Specialized Analysis
- **Project-specific LoRA adapters** understand your codebase's unique patterns
- **Context-aware responses** that reference your actual code structure
- **Conversation memory** that builds understanding over time

### Local-First Privacy
- **All processing happens locally** - your code never leaves your machine
- **No external API calls** for core functionality
- **Complete offline operation** after initial setup

### Mac Mini M4 Optimized
- **Memory-efficient** dynamic model loading
- **Thermal-aware** processing to prevent throttling
- **Apple Silicon** optimizations where possible

### Multi-Project Management
- **Project registry** for managing multiple codebases
- **Instant switching** between specialized contexts
- **Isolated vector stores** for each project

## 📊 System Requirements

### Minimum Requirements
- **RAM**: 8GB (Mac Mini M4 base configuration)
- **Storage**: 10GB free space (for models and vector stores)
- **CPU**: Apple M4 or equivalent

### Recommended Requirements
- **RAM**: 16GB+ for better performance with multiple projects
- **Storage**: 50GB+ for extensive project libraries
- **SSD**: Fast storage for model loading performance

## 🔧 Configuration

### Environment Variables

```bash
# Application Configuration
export CODEBASE_GARDENER_DEBUG=false
export CODEBASE_GARDENER_LOG_LEVEL=INFO
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener

# Model Configuration
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code
export CODEBASE_GARDENER_MAX_CHUNK_SIZE=1000

# Performance Configuration
export CODEBASE_GARDENER_BATCH_SIZE=32
export CODEBASE_GARDENER_MAX_WORKERS=4
```

### Configuration File

Create `~/.codebase-gardener/config.yaml`:

```yaml
app:
  name: "Codebase Gardener"
  debug: false
  log_level: "INFO"

models:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 30
  embedding:
    model: "nomic-embed-code"
    batch_size: 32

storage:
  vector_db:
    path: "vector_store"
    index_type: "IVF_FLAT"
```

## 🧪 Testing

### Run All Tests
```bash
pytest
```

### Run Specific Test Categories
```bash
# Unit tests only
pytest tests/unit/

# Integration tests
pytest tests/integration/

# End-to-end tests
pytest tests/e2e/
```

### Performance Tests
```bash
pytest tests/performance/ --benchmark-only
```

## 📚 Documentation

- **[Development Principles](.kiro/steering/codebase-gardener-principles.md)** - Core project philosophy
- **[AI/ML Architecture](.kiro/steering/ai-ml-architecture-context.md)** - Technical architecture details
- **[Development Best Practices](.kiro/steering/development-best-practices.md)** - Development workflow
- **[Task Implementation Plan](.kiro/specs/codebase-gardener-mvp/tasks.md)** - Detailed implementation roadmap

## 🤝 Contributing

1. **Read the steering documents** in `.kiro/steering/` to understand project principles
2. **Follow the task-based development** approach outlined in the specs
3. **Create memory files** to document your implementation decisions
4. **Write comprehensive tests** for all new functionality
5. **Ensure Mac Mini M4 optimization** in all performance-critical code

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🙏 Acknowledgments

- **Ollama** for local LLM inference
- **HuggingFace** for PEFT and model ecosystem
- **LanceDB** for vector storage
- **Tree-sitter** for code parsing
- **Gradio** for the web interface
- **Nomic** for code-specific embeddings

---

**Built with ❤️ for developers who want AI that truly understands their code**