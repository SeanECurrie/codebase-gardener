# Configuration Guide

This guide covers all configuration options for the Codebase Gardener system, including environment variables, configuration files, and runtime settings.

## Configuration Methods

Codebase Gardener supports multiple configuration methods, listed in order of precedence:

1. **Command-line arguments** (highest precedence)
2. **Environment variables**
3. **Configuration file**
4. **Default values** (lowest precedence)

## Environment Variables

All environment variables use the `CODEBASE_GARDENER_` prefix.

### Application Settings

```bash
# Enable debug mode with verbose logging
export CODEBASE_GARDENER_DEBUG=true

# Set logging level (DEBUG, INFO, WARNING, ERROR)
export CODEBASE_GARDENER_LOG_LEVEL=INFO

# Custom data directory location
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener

# Application name (for logging and UI)
export CODEBASE_GARDENER_APP_NAME="Codebase Gardener"
```

### Model Configuration

```bash
# Ollama service URL
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434

# Ollama connection timeout (seconds)
export CODEBASE_GARDENER_OLLAMA_TIMEOUT=30

# Default base model for LoRA training
export CODEBASE_GARDENER_BASE_MODEL=codellama:7b

# Embedding model name
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code

# Embedding batch size for processing
export CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE=32

# Maximum context length for models
export CODEBASE_GARDENER_MAX_CONTEXT_LENGTH=4096
```

### Performance Settings

```bash
# Maximum number of worker threads
export CODEBASE_GARDENER_MAX_WORKERS=4

# Memory limit in MB for the application
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=4096

# Maximum number of cached LoRA adapters
export CODEBASE_GARDENER_MAX_CACHE_SIZE=3

# Maximum number of cached conversation contexts
export CODEBASE_GARDENER_MAX_CONTEXT_CACHE=3

# Vector store cache size in MB
export CODEBASE_GARDENER_VECTOR_CACHE_SIZE=500
```

### Training Configuration

```bash
# Default number of training epochs
export CODEBASE_GARDENER_TRAINING_EPOCHS=3

# Default learning rate for LoRA training
export CODEBASE_GARDENER_LEARNING_RATE=0.0001

# Training batch size
export CODEBASE_GARDENER_TRAINING_BATCH_SIZE=4

# LoRA rank parameter
export CODEBASE_GARDENER_LORA_RANK=16

# LoRA alpha parameter
export CODEBASE_GARDENER_LORA_ALPHA=32

# LoRA dropout rate
export CODEBASE_GARDENER_LORA_DROPOUT=0.1
```

### Web Interface Settings

```bash
# Default host for web interface
export CODEBASE_GARDENER_HOST=127.0.0.1

# Default port for web interface
export CODEBASE_GARDENER_PORT=7860

# Enable public sharing (Gradio)
export CODEBASE_GARDENER_SHARE=false

# Web interface authentication (username:password)
export CODEBASE_GARDENER_AUTH=""

# Enable web interface debug mode
export CODEBASE_GARDENER_WEB_DEBUG=false
```

### File Processing Settings

```bash
# Maximum file size to process (MB)
export CODEBASE_GARDENER_MAX_FILE_SIZE=10

# File extensions to include (comma-separated)
export CODEBASE_GARDENER_INCLUDE_EXTENSIONS=".py,.js,.ts,.java,.go,.rs,.cpp,.c,.h"

# File patterns to exclude (comma-separated)
export CODEBASE_GARDENER_EXCLUDE_PATTERNS="*.pyc,__pycache__,node_modules,.git"

# Maximum directory depth to scan
export CODEBASE_GARDENER_MAX_DEPTH=10

# Enable hidden file processing
export CODEBASE_GARDENER_INCLUDE_HIDDEN=false
```

## Configuration File

You can create a YAML configuration file at `~/.codebase-gardener/config.yaml`:

### Complete Configuration Example

```yaml
# Application configuration
app:
  name: "Codebase Gardener"
  debug: false
  log_level: "INFO"
  data_dir: "~/.codebase-gardener"

# Model configuration
models:
  ollama:
    base_url: "http://localhost:11434"
    timeout: 30
    default_model: "codellama:7b"
    models:
      - name: "codellama:7b"
        context_length: 4096
        temperature: 0.1
      - name: "llama2:13b"
        context_length: 2048
        temperature: 0.2

  embedding:
    model: "nomic-embed-code"
    batch_size: 32
    max_length: 512
    cache_embeddings: true

  training:
    epochs: 3
    learning_rate: 0.0001
    batch_size: 4
    lora_rank: 16
    lora_alpha: 32
    lora_dropout: 0.1
    save_steps: 100
    eval_steps: 50

# Storage configuration
storage:
  data_dir: "~/.codebase-gardener"
  vector_db_path: "vector_stores"
  adapters_path: "adapters"
  contexts_path: "contexts"
  logs_path: "logs"
  max_cache_size: 3
  backup_enabled: true
  backup_retention_days: 30

# Performance configuration
performance:
  max_workers: 4
  memory_limit_mb: 4096
  max_context_cache: 3
  vector_cache_size_mb: 500
  enable_gpu: true
  gpu_memory_fraction: 0.8

# File processing configuration
files:
  max_file_size_mb: 10
  include_extensions:
    - ".py"
    - ".js"
    - ".ts"
    - ".java"
    - ".go"
    - ".rs"
    - ".cpp"
    - ".c"
    - ".h"
  exclude_patterns:
    - "*.pyc"
    - "__pycache__"
    - "node_modules"
    - ".git"
    - "*.log"
  max_depth: 10
  include_hidden: false
  encoding_detection: true

# Web interface configuration
ui:
  host: "127.0.0.1"
  port: 7860
  share: false
  auth: null
  debug: false
  theme: "default"
  title: "Codebase Gardener"
  description: "AI-powered project-specific codebase analysis"

# Logging configuration
logging:
  level: "INFO"
  format: "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
  file_enabled: true
  file_path: "logs/app.log"
  file_max_size_mb: 10
  file_backup_count: 5
  console_enabled: true
  structured_logging: true
```

### Minimal Configuration Example

```yaml
# Minimal configuration for basic usage
app:
  debug: false
  data_dir: "~/.codebase-gardener"

models:
  ollama:
    base_url: "http://localhost:11434"
  embedding:
    model: "nomic-embed-code"

ui:
  port: 7860
```

## Runtime Configuration

Some settings can be configured at runtime through the CLI or web interface.

### CLI Configuration

```bash
# Override host and port for web interface
codebase-gardener serve --host 0.0.0.0 --port 8080

# Enable debug mode for any command
codebase-gardener --debug status

# Override training parameters
codebase-gardener train "My Project" --epochs 5 --learning-rate 0.0002
```

### Web Interface Configuration

The web interface allows runtime configuration of:
- Active project selection
- Analysis parameters
- Display preferences
- Real-time system monitoring

## Configuration Validation

Codebase Gardener validates configuration on startup and provides helpful error messages:

### Validation Examples

```bash
# Check configuration validity
codebase-gardener status --verbose

# Test Ollama connection
curl http://localhost:11434/api/version

# Validate data directory permissions
ls -la ~/.codebase-gardener/
```

### Common Configuration Errors

**Invalid Ollama URL**:
```
ERROR: Cannot connect to Ollama at http://localhost:11434
Solution: Check if Ollama is running with 'ollama serve'
```

**Permission Errors**:
```
ERROR: Cannot write to data directory ~/.codebase-gardener
Solution: Fix permissions with 'chmod -R 755 ~/.codebase-gardener'
```

**Memory Limit Exceeded**:
```
WARNING: Memory usage exceeds configured limit
Solution: Increase CODEBASE_GARDENER_MEMORY_LIMIT_MB or reduce cache sizes
```

## Platform-Specific Configuration

### macOS (Mac Mini M4)

Optimized settings for Mac Mini M4:

```bash
# Optimize for Apple Silicon
export PYTORCH_ENABLE_MPS_FALLBACK=1
export TOKENIZERS_PARALLELISM=false

# Mac Mini M4 specific settings
export CODEBASE_GARDENER_MAX_WORKERS=2
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=3072
export CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE=16
export CODEBASE_GARDENER_TRAINING_BATCH_SIZE=2
```

### Linux

```bash
# Linux specific optimizations
export CODEBASE_GARDENER_MAX_WORKERS=4
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=4096
export CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE=32
```

### Docker

```yaml
# Docker environment configuration
version: '3.8'
services:
  codebase-gardener:
    image: codebase-gardener:latest
    environment:
      - CODEBASE_GARDENER_HOST=0.0.0.0
      - CODEBASE_GARDENER_PORT=7860
      - CODEBASE_GARDENER_DATA_DIR=/app/data
      - CODEBASE_GARDENER_OLLAMA_BASE_URL=http://ollama:11434
    volumes:
      - ./data:/app/data
      - ./projects:/app/projects
    ports:
      - "7860:7860"
```

## Security Configuration

### Authentication

```bash
# Enable basic authentication
export CODEBASE_GARDENER_AUTH="username:password"

# Or in config file
ui:
  auth: "admin:secure_password_123"
```

### Network Security

```bash
# Bind to localhost only (default)
export CODEBASE_GARDENER_HOST=127.0.0.1

# Disable public sharing
export CODEBASE_GARDENER_SHARE=false
```

### Data Security

```yaml
storage:
  backup_enabled: true
  encryption_enabled: false  # Future feature
  access_logging: true
```

## Performance Tuning

### Memory Optimization

```bash
# Reduce memory usage for constrained environments
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=2048
export CODEBASE_GARDENER_MAX_CACHE_SIZE=1
export CODEBASE_GARDENER_VECTOR_CACHE_SIZE=256
export CODEBASE_GARDENER_EMBEDDING_BATCH_SIZE=8
```

### CPU Optimization

```bash
# Optimize for multi-core systems
export CODEBASE_GARDENER_MAX_WORKERS=8

# Optimize for single-core systems
export CODEBASE_GARDENER_MAX_WORKERS=1
```

### Storage Optimization

```yaml
storage:
  vector_db_path: "/fast/ssd/vector_stores"  # Use SSD for vector stores
  adapters_path: "/fast/ssd/adapters"        # Use SSD for adapters
  logs_path: "/slower/hdd/logs"              # Use HDD for logs
```

## Troubleshooting Configuration

### Debug Configuration Issues

```bash
# Enable debug mode
export CODEBASE_GARDENER_DEBUG=true
export CODEBASE_GARDENER_LOG_LEVEL=DEBUG

# Check configuration loading
codebase-gardener status --verbose

# Validate specific settings
python -c "
from codebase_gardener.config.settings import Settings
settings = Settings()
print(settings.dict())
"
```

### Configuration Reset

```bash
# Reset to defaults by removing config file
rm ~/.codebase-gardener/config.yaml

# Clear environment variables
unset $(env | grep CODEBASE_GARDENER | cut -d= -f1)

# Reinitialize
codebase-gardener init
```

## Best Practices

### Development Configuration

```yaml
app:
  debug: true
  log_level: "DEBUG"

performance:
  max_workers: 2
  memory_limit_mb: 2048

files:
  include_hidden: true
  max_file_size_mb: 50
```

### Production Configuration

```yaml
app:
  debug: false
  log_level: "INFO"

performance:
  max_workers: 4
  memory_limit_mb: 4096

storage:
  backup_enabled: true
  backup_retention_days: 30

logging:
  file_enabled: true
  file_max_size_mb: 100
  file_backup_count: 10
```

### Testing Configuration

```bash
# Use temporary directory for testing
export CODEBASE_GARDENER_DATA_DIR=/tmp/codebase-gardener-test
export CODEBASE_GARDENER_DEBUG=true
export CODEBASE_GARDENER_LOG_LEVEL=DEBUG
```

## See Also

- [CLI Reference](cli-reference.md) - Command-line interface documentation
- [Setup Guide](../../docs/setup-guide.md) - Installation and initial setup
- [Troubleshooting Guide](troubleshooting.md) - Common configuration issues
- [Architecture Overview](architecture-overview.md) - System architecture and performance considerations
