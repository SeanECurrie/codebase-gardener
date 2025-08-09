# How to Run & Try It

## Quickstart (3 minutes)

```bash
# 1. Install Ollama and dependencies
pip install ollama

# 2. Start Ollama server
ollama serve &

# 3. Download model (one-time setup)
ollama pull llama3.2:3b

# 4. Smoke test (verify CLI loads without Ollama)
PYTHONPATH=. python scripts/smoke_cli.py
# Expected: "SMOKE_OK: project-analysis.md"

# 5. Run interactive CLI
python codebase_auditor.py
```

## Sample Run: Analyze This Repository

```bash
$ python codebase_auditor.py
🔍 Codebase Auditor - Interactive CLI

> analyze .
📊 Analyzing codebase at: /path/to/codebase-local-llm-advisor
📄 Found 15 files (12.3 KB total)
🤖 Generating analysis with llama3.2:3b...

💭 This is a Python CLI tool for codebase analysis...
[Analysis continues with architecture overview, patterns, suggestions]

> chat What's the main entry point?
💭 The main entry point is codebase_auditor.py. It provides an interactive CLI...

> export analysis-report.md
📄 Report exported to: analysis-report.md

> quit
👋 Goodbye!
```

**Output Location**: Analysis and chat exports save to current working directory.

## Troubleshooting

### Ollama Issues

**"Connection refused" or "Ollama not responding"**
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama if not running
ollama serve &

# Verify model is available
ollama list
# Should show llama3.2:3b (or your preferred model)
```

**"Model not found"**
```bash
# Install the default model
ollama pull llama3.2:3b

# Or use different model
export OLLAMA_MODEL=llama3.1:8b
ollama pull $OLLAMA_MODEL
```

**Custom Ollama host/port**
```bash
export OLLAMA_HOST=http://192.168.1.100:11434
python codebase_auditor.py
```

### Performance Tips

**Large repositories (1000+ files)**
- CLI automatically switches to high-level analysis mode
- For detailed analysis, target specific subdirectories:
```bash
> analyze ./src/core
> analyze ./tests
```

**Memory issues**
- Use smaller models: `export OLLAMA_MODEL=llama3.2:1b`
- Analyze subdirectories instead of entire large repos
- Close other resource-heavy applications

### Import/Python Issues

**"Module not found" errors**
```bash
# Ensure dependencies installed
pip install ollama

# For development setup
pip install -e .[dev]

# Check Python path
PYTHONPATH=. python -c "import codebase_auditor; print('OK')"
```

## CI Expectations

**GitHub Actions runs:**
- `ruff check` - Code linting
- `pytest -q` - All tests (should be 8/8 passing)

**Pre-commit hooks:**
- Code formatting (ruff-format)
- Basic file cleanup (trailing whitespace, etc.)

**Test failure diagnosis:**
```bash
# Run tests with verbose output
pytest -v

# Check specific test file
pytest -v tests/test_single_file_auditor.py

# Run smoke test
PYTHONPATH=. python scripts/smoke_cli.py
```

## What You Can Try Now

```bash
# Quick development workflow
ruff check --fix && ruff format && pytest -q

# Analyze this project
python codebase_auditor.py
# Then: > analyze .

# Test with a different project
cd /path/to/your/project && python /path/to/codebase_auditor.py
# Then: > analyze .
```
