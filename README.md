# Codebase Auditor

AI-powered interactive CLI for instant codebase analysis and Q&A.

## Quickstart

```bash
pip install ollama
ollama serve &
ollama pull llama3.2:3b
python codebase_auditor.py
```

## Agent Workflow

Agents must follow CLAUDE.md → Branching & PR Policy (Authoritative) and Task Loop (Start → Finish).

## Scripts

```bash
# Start interactive CLI (main tool)
python codebase_auditor.py

# Quick development workflow
ruff check --fix && pytest -q

# Testing
pytest -q tests/test_single_file_auditor.py
python -m pytest -q tests/test_project_structure.py

# Smoke test (no Ollama needed)
PYTHONPATH=. python scripts/smoke_cli.py

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

> analyze --advanced ./my-project
🚀 Starting advanced analysis of: ./my-project
⚠️  Advanced features requested but not available - falling back to standard analysis

> features
🔧 Advanced Features Status:
⚠️  Advanced features are not currently available
   Available features: 0/6

> project create ./my-project
✅ Created new project: my-project
   ID: 41df9e52-468f-458c-a2d2-6fc280dc966d
🔄 Project is now active for analysis

> projects
📂 Registered Projects (1):
📝 my-project (ID: 41df9e52... ← CURRENT)

> chat What are the main architectural patterns?
💭 This React application follows component-based architecture...

> export project-analysis.md
📄 Report exported to: project-analysis.md

> help
Available commands: analyze, chat, export, status, features, projects, project create/info/switch/cleanup/health, help, quit
```

**Key Features:**
- 🎯 Context-aware analysis (adapts to project size)
- 🔍 Smart file filtering (excludes node_modules, .git, etc.)
- 💬 Interactive chat with your codebase
- 📄 Markdown report export
- ⚡ Local-first (works offline with Ollama)
- 🚀 Advanced mode support (with graceful fallback during MVP)
- 📊 Feature status reporting and mode detection
- 📂 Project management with persistent conversation state
- 🔄 Multi-project workflow support with automatic project creation

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
