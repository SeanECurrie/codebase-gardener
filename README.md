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
# Lint and fix issues
ruff check --fix

# Run tests quickly
pytest -q

# Start interactive CLI
python codebase_auditor.py

# Smoke test (note: requires PYTHONPATH or sys.path fix)
python scripts/smoke_cli.py
```

## Environment Variables

- `OLLAMA_HOST` - Ollama server URL (default: http://localhost:11434)
- `OLLAMA_MODEL` - Model name (default: llama3.2:3b)

## Example Usage

```bash
🔍 > analyze ./my-project
📊 Analysis Summary: 28/28 files, 156,789 bytes processed

🔍 > chat What are the main architectural patterns?
💭 Response: This React application follows component-based architecture...

🔍 > export project-analysis.md
📄 Report exported to: project-analysis.md
```

**Features:**
- Context-aware analysis (adapts to project size)
- Smart file filtering (excludes node_modules, .git, etc.)
- Interactive chat with your codebase
- Markdown report export

## Troubleshooting

**Ollama not running:** Start with `ollama serve`
**Model missing:** Install with `ollama pull llama3.2:3b`

## Roadmap

**Now:** Interactive CLI analysis  
**Next:** VS Code extension  
**Later:** Multi-project comparison

## Deferred Components

The following components are parked for post-MVP development:

- `deployment_DISABLED/` - Docker & production deployment configs
- `scripts_DISABLED/` - Advanced automation scripts  
- `src/codebase_gardener_DISABLED/` - Complex multi-project system with LoRA training, vector stores, and web UI

These were excluded to focus on the working CLI tool.