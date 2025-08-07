# Troubleshooting Guide

## Common Issues and Solutions

### Installation and Setup Issues

#### Python Environment Problems

**Issue**: `ModuleNotFoundError` when importing codebase_gardener
```bash
ModuleNotFoundError: No module named 'codebase_gardener'
```

**Solutions**:
```bash
# Verify virtual environment is activated
which python  # Should point to venv/bin/python

# Reinstall in development mode
pip install -e ".[dev]"

# Check PYTHONPATH
echo $PYTHONPATH

# Verify installation
python -c "import codebase_gardener; print('OK')"
```

**Issue**: Package installation fails on Mac Mini M4
```bash
ERROR: Failed building wheel for some-package
```

**Solutions**:
```bash
# Update pip and setuptools
pip install --upgrade pip setuptools wheel

# Install with specific architecture
pip install --no-cache-dir package-name

# Use conda for problematic packages
conda install package-name

# Check for Apple Silicon compatibility
arch -arm64 pip install package-name
```

#### Ollama Connection Issues

**Issue**: Cannot connect to Ollama service
```
ConnectionError: HTTPConnectionPool(host='localhost', port=11434)
```

**Solutions**:
```bash
# Check if Ollama is running
ps aux | grep ollama

# Start Ollama service
ollama serve

# Test connection
curl http://localhost:11434/api/version

# Check port availability
lsof -i :11434

# Restart Ollama if needed
pkill ollama
ollama serve
```

**Issue**: Ollama model not found
```bash
Error: model 'codellama:7b' not found
```

**Solutions**:
```bash
# List available models
ollama list

# Download required model
ollama pull codellama:7b

# Verify model is available
ollama show codellama:7b

# Check disk space
df -h
```

### Runtime Issues

#### Memory and Performance Problems

**Issue**: Application crashes with out of memory error
```bash
MemoryError: Unable to allocate array
```

**Solutions**:
```bash
# Check available memory
vm_stat | grep "Pages free"

# Monitor memory usage
top -pid $(pgrep -f "python.*codebase_gardener")

# Reduce batch size in configuration
export CODEBASE_GARDENER_BATCH_SIZE=8

# Clear Python cache
find . -name "__pycache__" -exec rm -rf {} +

# Restart application
pkill -f "python.*codebase_gardener"
```

**Issue**: Slow performance on Mac Mini M4
```bash
# Application feels sluggish, high CPU usage
```

**Solutions**:
```bash
# Check thermal throttling
sudo powermetrics --samplers smc -n 1 | grep -i temp

# Monitor CPU usage
top -o cpu

# Reduce worker count
export CODEBASE_GARDENER_MAX_WORKERS=2

# Check for background processes
ps aux | grep -E "(python|ollama)" | grep -v grep

# Enable performance monitoring
export CODEBASE_GARDENER_DEBUG=true
```

#### Model Loading Issues

**Issue**: LoRA adapter fails to load
```bash
AdapterLoadError: Failed to load adapter from path
```

**Solutions**:
```bash
# Check adapter file exists and is readable
ls -la ~/.codebase-gardener/projects/*/lora_adapter.bin

# Verify file permissions
chmod 644 ~/.codebase-gardener/projects/*/lora_adapter.bin

# Check adapter compatibility
python -c "
from codebase_gardener.models.peft_manager import PEFTManager
pm = PEFTManager()
pm.validate_adapter('path/to/adapter.bin')
"

# Regenerate adapter if corrupted
rm ~/.codebase-gardener/projects/project_name/lora_adapter.bin
# Re-add project to trigger retraining
```

**Issue**: Base model incompatible with adapter
```bash
IncompatibleModelError: Adapter trained for different base model
```

**Solutions**:
```bash
# Check base model version
ollama show codellama:7b

# Update base model
ollama pull codellama:7b

# Retrain adapters for new base model
python -m codebase_gardener.main retrain-all

# Check adapter metadata
python -c "
import json
with open('~/.codebase-gardener/projects/project/metadata.json') as f:
    print(json.load(f)['base_model'])
"
```

### Data Processing Issues

#### Code Parsing Problems

**Issue**: Tree-sitter fails to parse code
```bash
ParsingError: Failed to parse file with Tree-sitter
```

**Solutions**:
```bash
# Check file encoding
file -I problematic_file.py

# Convert to UTF-8 if needed
iconv -f ISO-8859-1 -t UTF-8 problematic_file.py > fixed_file.py

# Check for binary files in codebase
find /path/to/codebase -type f -exec file {} \; | grep -v text

# Skip problematic files
echo "*.bin" >> .codebase-gardener-ignore
echo "*.so" >> .codebase-gardener-ignore

# Validate Tree-sitter installation
python -c "import tree_sitter; print('Tree-sitter OK')"
```

**Issue**: Unsupported programming language
```bash
UnsupportedLanguageError: Language 'kotlin' not supported
```

**Solutions**:
```bash
# Check supported languages
python -c "
from codebase_gardener.data.parser import TreeSitterParser
parser = TreeSitterParser()
print(parser.supported_languages)
"

# Add language support (if available)
# Edit src/codebase_gardener/data/parser.py

# Skip unsupported files
echo "*.kt" >> .codebase-gardener-ignore
echo "*.swift" >> .codebase-gardener-ignore
```

#### Vector Store Issues

**Issue**: LanceDB vector store corruption
```bash
VectorStoreError: Failed to read vector store
```

**Solutions**:
```bash
# Check vector store files
ls -la ~/.codebase-gardener/projects/*/vector_store/

# Verify LanceDB installation
python -c "import lancedb; print('LanceDB OK')"

# Rebuild vector store
rm -rf ~/.codebase-gardener/projects/project_name/vector_store/
python -m codebase_gardener.main rebuild-vectors project_name

# Check disk space
df -h ~/.codebase-gardener/
```

**Issue**: Embedding generation fails
```bash
EmbeddingError: Failed to generate embeddings
```

**Solutions**:
```bash
# Test Nomic Embed Code
python -c "
from codebase_gardener.models.nomic_embedder import NomicEmbedder
embedder = NomicEmbedder()
result = embedder.embed('def test(): pass')
print(f'Embedding shape: {len(result)}')
"

# Check network connectivity (for model download)
ping -c 3 huggingface.co

# Clear embedding cache
rm -rf ~/.cache/huggingface/

# Reduce batch size
export CODEBASE_GARDENER_BATCH_SIZE=4
```

### UI and Interface Issues

#### Gradio Interface Problems

**Issue**: Gradio interface won't start
```bash
OSError: [Errno 48] Address already in use
```

**Solutions**:
```bash
# Check what's using port 7860
lsof -i :7860

# Kill process using the port
kill -9 $(lsof -t -i:7860)

# Use different port
export CODEBASE_GARDENER_PORT=7861

# Start with specific port
python -m codebase_gardener.main --port 7861
```

**Issue**: Interface loads but shows errors
```bash
# Browser shows "Internal Server Error"
```

**Solutions**:
```bash
# Check application logs
tail -f ~/.codebase-gardener/logs/app.log

# Enable debug mode
export CODEBASE_GARDENER_DEBUG=true

# Check browser console for JavaScript errors
# Open browser dev tools (F12)

# Clear browser cache
# Hard refresh (Cmd+Shift+R on Mac)
```

#### Project Switching Issues

**Issue**: Project switching hangs or fails
```bash
# UI shows "Loading..." indefinitely
```

**Solutions**:
```bash
# Check project status
python -c "
from codebase_gardener.core.project_registry import ProjectRegistry
registry = ProjectRegistry()
for project in registry.list_projects():
    print(f'{project.name}: {project.status}')
"

# Check for stuck training processes
ps aux | grep -E "(python.*train|peft)"

# Reset project state
python -m codebase_gardener.main reset-project project_name

# Check memory usage during switching
top -o mem
```

### Configuration Issues

#### Environment Variable Problems

**Issue**: Configuration not loading correctly
```bash
ConfigurationError: Invalid configuration value
```

**Solutions**:
```bash
# Check environment variables
env | grep CODEBASE_GARDENER

# Validate configuration
python -c "
from codebase_gardener.config.settings import Settings
settings = Settings()
print(settings.dict())
"

# Reset to defaults
unset $(env | grep CODEBASE_GARDENER | cut -d= -f1)

# Load from config file
cp config.example.yaml ~/.codebase-gardener/config.yaml
```

**Issue**: File permissions on Mac Mini M4
```bash
PermissionError: [Errno 13] Permission denied
```

**Solutions**:
```bash
# Check directory permissions
ls -la ~/.codebase-gardener/

# Fix permissions
chmod -R 755 ~/.codebase-gardener/
chmod -R 644 ~/.codebase-gardener/projects/*/

# Check ownership
chown -R $(whoami) ~/.codebase-gardener/

# Verify write access
touch ~/.codebase-gardener/test_write && rm ~/.codebase-gardener/test_write
```

## Diagnostic Commands

### System Health Check
```bash
#!/bin/bash
# health_check.sh - Comprehensive system health check

echo "=== Codebase Gardener Health Check ==="

# Python environment
echo "Python version: $(python --version)"
echo "Virtual environment: $(which python)"

# Dependencies
echo "Checking dependencies..."
python -c "
import sys
required = ['codebase_gardener', 'ollama', 'lancedb', 'tree_sitter', 'gradio']
for pkg in required:
    try:
        __import__(pkg)
        print(f'✓ {pkg}')
    except ImportError:
        print(f'✗ {pkg} - MISSING')
"

# Ollama status
echo "Ollama status:"
if curl -s http://localhost:11434/api/version > /dev/null; then
    echo "✓ Ollama service running"
    echo "Available models:"
    ollama list
else
    echo "✗ Ollama service not accessible"
fi

# Directory structure
echo "Directory structure:"
if [ -d ~/.codebase-gardener ]; then
    echo "✓ ~/.codebase-gardener exists"
    ls -la ~/.codebase-gardener/
else
    echo "✗ ~/.codebase-gardener missing"
fi

# Memory and disk
echo "System resources:"
echo "Memory: $(vm_stat | grep 'Pages free' | awk '{print $3}' | sed 's/\.//')KB free"
echo "Disk space: $(df -h ~/.codebase-gardener | tail -1 | awk '{print $4}') available"

# Process check
echo "Running processes:"
ps aux | grep -E "(python.*codebase|ollama)" | grep -v grep
```

### Log Analysis
```bash
#!/bin/bash
# analyze_logs.sh - Analyze application logs for issues

LOG_FILE=~/.codebase-gardener/logs/app.log

if [ ! -f "$LOG_FILE" ]; then
    echo "Log file not found: $LOG_FILE"
    exit 1
fi

echo "=== Recent Errors ==="
tail -100 "$LOG_FILE" | grep -i error

echo "=== Memory Warnings ==="
tail -100 "$LOG_FILE" | grep -i "memory\|oom"

echo "=== Performance Issues ==="
tail -100 "$LOG_FILE" | grep -E "(slow|timeout|performance)"

echo "=== Model Loading Issues ==="
tail -100 "$LOG_FILE" | grep -E "(adapter|model.*load|peft)"

echo "=== Recent Activity ==="
tail -20 "$LOG_FILE"
```

### Performance Monitoring
```bash
#!/bin/bash
# monitor_performance.sh - Monitor system performance

echo "=== Performance Monitoring ==="

# CPU and Memory
echo "CPU and Memory usage:"
top -l 1 -n 0 | grep -E "(CPU usage|PhysMem)"

# Process-specific monitoring
if pgrep -f "python.*codebase_gardener" > /dev/null; then
    PID=$(pgrep -f "python.*codebase_gardener")
    echo "Codebase Gardener process (PID: $PID):"
    ps -p $PID -o pid,ppid,pcpu,pmem,time,command
fi

# Thermal status
echo "Thermal status:"
sudo powermetrics --samplers smc -n 1 2>/dev/null | grep -i temp | head -5

# Disk I/O
echo "Disk usage:"
df -h ~/.codebase-gardener/

# Network (for Ollama)
echo "Network connections:"
lsof -i :11434
```

## Recovery Procedures

### Complete Reset
```bash
#!/bin/bash
# reset_system.sh - Complete system reset

echo "WARNING: This will delete all projects and data!"
read -p "Are you sure? (yes/no): " confirm

if [ "$confirm" = "yes" ]; then
    echo "Stopping services..."
    pkill -f "python.*codebase_gardener"
    pkill ollama
    
    echo "Removing data directory..."
    rm -rf ~/.codebase-gardener/
    
    echo "Clearing Python cache..."
    find . -name "__pycache__" -exec rm -rf {} + 2>/dev/null
    find . -name "*.pyc" -delete 2>/dev/null
    
    echo "Reinstalling application..."
    pip uninstall -y codebase-gardener
    pip install -e ".[dev]"
    
    echo "Restarting Ollama..."
    ollama serve &
    sleep 5
    ollama pull codellama:7b
    
    echo "System reset complete!"
else
    echo "Reset cancelled."
fi
```

### Project Recovery
```bash
#!/bin/bash
# recover_project.sh - Recover a corrupted project

PROJECT_NAME=$1
if [ -z "$PROJECT_NAME" ]; then
    echo "Usage: $0 <project_name>"
    exit 1
fi

PROJECT_DIR=~/.codebase-gardener/projects/$PROJECT_NAME

echo "Recovering project: $PROJECT_NAME"

# Backup existing data
if [ -d "$PROJECT_DIR" ]; then
    echo "Backing up existing project data..."
    cp -r "$PROJECT_DIR" "${PROJECT_DIR}.backup.$(date +%Y%m%d_%H%M%S)"
fi

# Remove corrupted files
echo "Removing corrupted files..."
rm -f "$PROJECT_DIR/lora_adapter.bin"
rm -rf "$PROJECT_DIR/vector_store/"

# Trigger reprocessing
echo "Triggering reprocessing..."
python -m codebase_gardener.main reprocess-project "$PROJECT_NAME"

echo "Project recovery initiated. Check logs for progress."
```

## Getting Help

### Debug Information Collection
```bash
#!/bin/bash
# collect_debug_info.sh - Collect debug information for support

DEBUG_FILE="debug_info_$(date +%Y%m%d_%H%M%S).txt"

echo "Collecting debug information..."

{
    echo "=== System Information ==="
    uname -a
    sw_vers
    
    echo "=== Python Environment ==="
    python --version
    which python
    pip list | grep -E "(codebase|ollama|lance|tree|gradio)"
    
    echo "=== Configuration ==="
    env | grep CODEBASE_GARDENER
    
    echo "=== Directory Structure ==="
    ls -la ~/.codebase-gardener/ 2>/dev/null || echo "Directory not found"
    
    echo "=== Recent Logs ==="
    tail -50 ~/.codebase-gardener/logs/app.log 2>/dev/null || echo "No logs found"
    
    echo "=== Process Information ==="
    ps aux | grep -E "(python.*codebase|ollama)" | grep -v grep
    
    echo "=== System Resources ==="
    top -l 1 -n 0 | head -10
    df -h
    
} > "$DEBUG_FILE"

echo "Debug information saved to: $DEBUG_FILE"
echo "Please include this file when reporting issues."
```

### Support Channels
- **GitHub Issues**: https://github.com/seanc-codingtemple/codebase-gardener/issues
- **Documentation**: Check `.kiro/docs/` for detailed guides
- **Steering Documents**: Review `.kiro/steering/` for architectural context
- **Memory Files**: Check `.kiro/memory/` for implementation decisions

### Before Reporting Issues
1. **Run health check**: Execute the health check script
2. **Check logs**: Review recent application logs
3. **Collect debug info**: Use the debug information collection script
4. **Try recovery**: Attempt relevant recovery procedures
5. **Search existing issues**: Check if the issue is already reported
6. **Provide context**: Include system info, steps to reproduce, and expected behavior