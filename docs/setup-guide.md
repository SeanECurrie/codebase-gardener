# Setup Guide - Codebase Gardener MVP

This guide provides detailed instructions for setting up the Codebase Gardener MVP on your system.

## Prerequisites

### System Requirements

- **Operating System**: macOS 12+ (optimized for Mac Mini M4)
- **Python**: 3.8 or higher
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 10GB free space for models and data
- **Network**: Internet connection for initial setup

### Required Software

#### 1. Ollama Installation

Ollama is required for local LLM inference:

```bash
# Install Ollama
curl -fsSL https://ollama.ai/install.sh | sh

# Start Ollama service
ollama serve

# Pull a base model (in another terminal)
ollama pull codellama:7b
# or
ollama pull llama2:7b
```

Verify Ollama is running:
```bash
curl http://localhost:11434/api/tags
```

#### 2. Python Environment

Ensure you have Python 3.8+ installed:

```bash
python3 --version
```

If you need to install Python:
- **macOS**: Use Homebrew: `brew install python@3.11`
- **Official installer**: Download from [python.org](https://www.python.org/downloads/)

## Installation

### 1. Clone the Repository

```bash
git clone https://github.com/your-org/codebase-gardener-mvp.git
cd codebase-gardener-mvp
```

### 2. Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate     # Windows
```

### 3. Install Dependencies

```bash
# Install the package in development mode
pip install -e .

# Or install with development dependencies
pip install -e ".[dev]"
```

### 4. Initialize the System

```bash
# Initialize directory structure and configuration
codebase-gardener init
```

This creates:
- `~/.codebase-gardener/` - Main data directory
- `~/.codebase-gardener/projects/` - Project data
- `~/.codebase-gardener/models/` - Model cache
- `~/.codebase-gardener/logs/` - Application logs
- `~/.codebase-gardener/config.yaml` - Configuration file

## Configuration

### Environment Variables

Set up environment variables for customization:

```bash
# Add to your ~/.zshrc or ~/.bashrc
export CODEBASE_GARDENER_DEBUG=false
export CODEBASE_GARDENER_LOG_LEVEL=INFO
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code
```

### Configuration File

Edit `~/.codebase-gardener/config.yaml`:

```yaml
app:
  name: "Codebase Gardener"
  debug: false
  log_level: "INFO"

models:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 30
    default_model: "codellama:7b"
  embedding:
    model: "nomic-embed-code"
    batch_size: 32
    max_length: 512

storage:
  data_dir: "~/.codebase-gardener"
  vector_db_path: "vector_stores"
  max_cache_size: 3

performance:
  max_workers: 4
  memory_limit_mb: 500
  context_limit: 50

ui:
  host: "127.0.0.1"
  port: 7860
  share: false
```

## Verification

### 1. Test Installation

```bash
# Check version
codebase-gardener --version

# Test help command
codebase-gardener --help

# Check system status
codebase-gardener status
```

### 2. Test Components

```bash
# Test Ollama connection
curl http://localhost:11434/api/tags

# Test Python imports
python -c "from src.codebase_gardener.main import ApplicationContext; print('Import successful')"
```

### 3. Add Test Project

```bash
# Create a simple test project
mkdir ~/test-project
echo "def hello(): return 'world'" > ~/test-project/main.py

# Add to Codebase Gardener
codebase-gardener add ~/test-project --name "Test Project"

# List projects
codebase-gardener list
```

### 4. Start Web Interface

```bash
# Start the web interface
codebase-gardener serve

# Open browser to http://localhost:7860
```

## Troubleshooting

### Common Issues

#### 1. Ollama Not Running

**Error**: `Connection refused to localhost:11434`

**Solution**:
```bash
# Start Ollama
ollama serve

# Check if running
ps aux | grep ollama
```

#### 2. Python Import Errors

**Error**: `ModuleNotFoundError: No module named 'src.codebase_gardener'`

**Solution**:
```bash
# Ensure you're in the project directory
cd /path/to/codebase-gardener-mvp

# Reinstall in development mode
pip install -e .
```

#### 3. Permission Errors

**Error**: `Permission denied: ~/.codebase-gardener`

**Solution**:
```bash
# Fix permissions
chmod -R 755 ~/.codebase-gardener

# Or remove and reinitialize
rm -rf ~/.codebase-gardener
codebase-gardener init
```

#### 4. Memory Issues

**Error**: System becomes slow or unresponsive

**Solution**:
```bash
# Reduce memory usage in config
export CODEBASE_GARDENER_MAX_CACHE_SIZE=1
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=200

# Or restart with lower settings
codebase-gardener serve --memory-limit 200
```

#### 5. Port Already in Use

**Error**: `Address already in use: 7860`

**Solution**:
```bash
# Use different port
codebase-gardener serve --port 8080

# Or kill existing process
lsof -ti:7860 | xargs kill -9
```

### Log Files

Check log files for detailed error information:

```bash
# Application logs
tail -f ~/.codebase-gardener/logs/app.log

# System logs (macOS)
log show --predicate 'process == "python"' --last 1h
```

### Performance Optimization

#### For Mac Mini M4

```bash
# Optimize for Apple Silicon
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false

# Reduce memory usage
export CODEBASE_GARDENER_MAX_WORKERS=2
export CODEBASE_GARDENER_BATCH_SIZE=16
```

#### Memory Management

```bash
# Monitor memory usage
top -pid $(pgrep -f codebase-gardener)

# Clear caches
rm -rf ~/.codebase-gardener/cache/
rm -rf ~/.codebase-gardener/models/cache/
```

## Advanced Setup

### Custom Model Configuration

```yaml
# ~/.codebase-gardener/config.yaml
models:
  ollama:
    models:
      - name: "codellama:7b"
        context_length: 4096
        temperature: 0.1
      - name: "llama2:13b"
        context_length: 2048
        temperature: 0.2
```

### Development Setup

```bash
# Install development dependencies
pip install -e ".[dev]"

# Install pre-commit hooks
pre-commit install

# Set up testing environment
export CODEBASE_GARDENER_TEST_MODE=true
export CODEBASE_GARDENER_DATA_DIR=/tmp/codebase-gardener-test
```

### Docker Setup (Optional)

```dockerfile
# Dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY . .

RUN pip install -e .
EXPOSE 7860

CMD ["codebase-gardener", "serve", "--host", "0.0.0.0"]
```

```bash
# Build and run
docker build -t codebase-gardener .
docker run -p 7860:7860 -v ~/.codebase-gardener:/root/.codebase-gardener codebase-gardener
```

## Next Steps

1. **Add Your First Project**: Use `codebase-gardener add /path/to/your/project` to add and analyze your first codebase
2. **Explore Features**: Try the web interface and CLI commands
3. **Customize Configuration**: Adjust settings for your specific needs
4. **Monitor Performance**: Use the system status commands to monitor resource usage

## Support

If you encounter issues not covered in this guide:

1. Check the [Troubleshooting Guide](../.kiro/docs/troubleshooting.md)
2. Search existing [GitHub Issues](https://github.com/your-org/codebase-gardener-mvp/issues)
3. Create a new issue with detailed information about your setup and the problem

## Security Considerations

- All processing happens locally - no data is sent to external servers
- Models and embeddings are stored locally in `~/.codebase-gardener/`
- Web interface binds to localhost by default for security
- Consider firewall settings if exposing the interface to other machines