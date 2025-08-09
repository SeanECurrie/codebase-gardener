# Codebase Auditor

AI-powered interactive CLI for instant codebase analysis and Q&A.

## Quickstart

```bash
pip install ollama
ollama serve &
ollama pull llama3.2:3b
python codebase_auditor.py
```

## Scripts

```bash
# Start interactive CLI (main tool)
python codebase_auditor.py

# Quick development workflow
ruff check --fix && pytest -q

# Code quality checks
black . && isort . && mypy src/ && ruff .

# Run all tests
pytest

# Run specific test categories
pytest -m unit          # Unit tests only
pytest -m integration   # Integration tests only

# Smoke test CLI functionality
python scripts/smoke_cli.py

# Setup development environment
pip install -e ".[dev]"
pre-commit install
```

## Environment Variables

- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: llama3.2:3b)

## Example Usage

```bash
$ python codebase_auditor.py
🔍 Codebase Auditor - Interactive CLI

> analyze ./my-project
📊 Analysis Summary: 28/28 files, 156,789 bytes processed

> chat What are the main architectural patterns?
💭 This React application follows component-based architecture...

> export project-analysis.md
📄 Report exported to: project-analysis.md

> help
Available commands: analyze, chat, export, status, help, quit
```

**Key Features:**
- 🎯 Context-aware analysis (adapts to project size)
- 🔍 Smart file filtering (excludes node_modules, .git, etc.)
- 💬 Interactive chat with your codebase
- 📄 Markdown report export
- ⚡ Local-first (works offline with Ollama)

## Troubleshooting

**Ollama not running:** Start with `ollama serve`  
**Model missing:** Install with `ollama pull llama3.2:3b`  
**Import errors:** Ensure dependencies with `pip install ollama`  
**Permission errors:** Check file/directory access permissions

## Development Status

✅ **Working:** Interactive CLI analysis tool  
🚧 **In Progress:** Enhanced file processing and analysis depth  
📋 **Planned:** VS Code extension, multi-project comparison

## Architecture Notes

**Current Focus:** Single-file CLI tool (`codebase_auditor.py`)  
**Deferred:** Complex multi-project system with LoRA training, vector stores, and web UI  
**Rationale:** Prioritizing working CLI functionality over advanced features