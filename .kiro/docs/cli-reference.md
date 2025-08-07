# CLI Reference

This document provides comprehensive reference for all Codebase Gardener command-line interface commands.

## Overview

The Codebase Gardener CLI provides commands for managing projects, analyzing code, and controlling the system. All commands are available through the `codebase-gardener` command.

```bash
codebase-gardener [OPTIONS] COMMAND [ARGS]...
```

### Global Options

- `--version`: Show the version and exit
- `--debug`: Enable debug mode with verbose logging
- `--help`: Show help message and exit

### Short Alias

You can also use the short alias `cgardener` for all commands:

```bash
cgardener [OPTIONS] COMMAND [ARGS]...
```

## Commands

### init

Initialize Codebase Gardener directory structure and configuration.

```bash
codebase-gardener init [OPTIONS]
```

**Description**: Creates the necessary directory structure and configuration files for Codebase Gardener. This should be run once after installation.

**Options**: None

**Example**:
```bash
codebase-gardener init
```

**Creates**:
- `~/.codebase-gardener/` - Main data directory
- `~/.codebase-gardener/projects/` - Project data storage
- `~/.codebase-gardener/contexts/` - Conversation contexts
- `~/.codebase-gardener/adapters/` - LoRA adapters
- `~/.codebase-gardener/logs/` - Application logs
- `~/.codebase-gardener/registry.json` - Project registry

### add

Add a new codebase project for analysis.

```bash
codebase-gardener add [OPTIONS] PROJECT_PATH
```

**Description**: Adds a new codebase project to the system. This will parse the code, generate embeddings, and train a project-specific LoRA adapter.

**Arguments**:
- `PROJECT_PATH`: Path to the codebase directory (required)

**Options**:
- `--name TEXT`: Custom name for the project (optional, defaults to directory name)
- `--description TEXT`: Description of the project (optional)
- `--languages TEXT`: Comma-separated list of programming languages to focus on (optional)

**Examples**:
```bash
# Add project with default name
codebase-gardener add /path/to/my-project

# Add project with custom name
codebase-gardener add /path/to/my-project --name "My Awesome Project"

# Add project with description
codebase-gardener add /path/to/my-project --name "Web API" --description "REST API for web application"

# Focus on specific languages
codebase-gardener add /path/to/my-project --languages "python,javascript"
```

**Process**:
1. Validates the project directory exists and contains code
2. Parses code files using Tree-sitter
3. Generates embeddings using Nomic Embed Code
4. Stores embeddings in project-specific LanceDB vector store
5. Trains LoRA adapter on project-specific patterns
6. Registers project in the system registry

### list

List all registered codebase projects.

```bash
codebase-gardener list [OPTIONS]
```

**Description**: Shows all projects registered in the system with their status and metadata.

**Options**:
- `--format TEXT`: Output format (table, json, yaml) [default: table]
- `--status TEXT`: Filter by status (active, training, error, ready) (optional)

**Examples**:
```bash
# List all projects in table format
codebase-gardener list

# List projects in JSON format
codebase-gardener list --format json

# List only ready projects
codebase-gardener list --status ready
```

**Output Fields**:
- **Name**: Project name
- **Path**: Original codebase path
- **Status**: Current status (ready, training, error)
- **Files**: Number of code files processed
- **Languages**: Detected programming languages
- **Created**: Date project was added
- **Last Updated**: Last modification date

### remove

Remove a codebase project and its associated data.

```bash
codebase-gardener remove [OPTIONS] PROJECT_NAME
```

**Description**: Removes a project from the system, including its LoRA adapter, vector store, and conversation history.

**Arguments**:
- `PROJECT_NAME`: Name of the project to remove (required)

**Options**:
- `--force`: Skip confirmation prompt
- `--keep-data`: Remove from registry but keep data files

**Examples**:
```bash
# Remove project with confirmation
codebase-gardener remove "My Project"

# Remove project without confirmation
codebase-gardener remove "My Project" --force

# Remove from registry but keep data
codebase-gardener remove "My Project" --keep-data
```

**Warning**: This operation is irreversible unless `--keep-data` is used.

### switch

Switch active project context across all components.

```bash
codebase-gardener switch [OPTIONS] PROJECT_NAME
```

**Description**: Changes the active project context, loading the appropriate LoRA adapter and conversation history.

**Arguments**:
- `PROJECT_NAME`: Name of the project to switch to (required)

**Options**: None

**Examples**:
```bash
# Switch to a specific project
codebase-gardener switch "My Web API"

# Switch to project with spaces in name
codebase-gardener switch "Machine Learning Project"
```

**Process**:
1. Saves current project context and conversation history
2. Unloads current LoRA adapter from memory
3. Loads target project's LoRA adapter
4. Restores target project's conversation history
5. Updates vector store context to target project

### analyze

Perform code analysis using project-specific models.

```bash
codebase-gardener analyze [OPTIONS] QUERY
```

**Description**: Analyzes code using the currently active project's specialized AI model. Provides project-specific insights and recommendations.

**Arguments**:
- `QUERY`: Analysis query or question (required)

**Options**:
- `--project TEXT`: Specify project name (uses active project if not specified)
- `--context-files TEXT`: Comma-separated list of specific files to include in context
- `--max-results INTEGER`: Maximum number of similar code examples to include [default: 5]
- `--output-format TEXT`: Output format (text, json, markdown) [default: text]

**Examples**:
```bash
# Analyze with current active project
codebase-gardener analyze "How does authentication work in this codebase?"

# Analyze specific project
codebase-gardener analyze "Find all database queries" --project "Web API"

# Include specific files in context
codebase-gardener analyze "Explain this function" --context-files "src/auth.py,src/models.py"

# Get JSON output
codebase-gardener analyze "List all API endpoints" --output-format json
```

**Output**:
- AI-generated analysis based on project-specific patterns
- Relevant code examples from the project
- Suggestions and recommendations
- Links to related files and functions

### train

Manually trigger LoRA training for a specific project.

```bash
codebase-gardener train [OPTIONS] PROJECT_NAME
```

**Description**: Manually triggers LoRA adapter training for a project. Useful for retraining after significant code changes.

**Arguments**:
- `PROJECT_NAME`: Name of the project to train (required)

**Options**:
- `--force`: Force retraining even if adapter exists
- `--epochs INTEGER`: Number of training epochs [default: 3]
- `--learning-rate FLOAT`: Learning rate for training [default: 0.0001]
- `--batch-size INTEGER`: Training batch size [default: 4]

**Examples**:
```bash
# Train project with default settings
codebase-gardener train "My Project"

# Force retraining with custom parameters
codebase-gardener train "My Project" --force --epochs 5 --learning-rate 0.0002
```

**Process**:
1. Validates project exists and has processed code
2. Prepares training data from parsed code
3. Trains LoRA adapter using PEFT
4. Validates trained adapter
5. Updates project status to ready

### serve

Start the Gradio web interface for project analysis.

```bash
codebase-gardener serve [OPTIONS]
```

**Description**: Starts the web-based user interface for interactive project analysis and management.

**Options**:
- `--host TEXT`: Host to bind to [default: 127.0.0.1]
- `--port INTEGER`: Port to bind to [default: 7860]
- `--share`: Create public shareable link
- `--auth TEXT`: Authentication in format "username:password"
- `--debug`: Enable debug mode for the web interface

**Examples**:
```bash
# Start with default settings
codebase-gardener serve

# Start on specific host and port
codebase-gardener serve --host 0.0.0.0 --port 8080

# Start with authentication
codebase-gardener serve --auth "admin:password123"

# Start with public sharing
codebase-gardener serve --share
```

**Web Interface Features**:
- Project selector dropdown
- Interactive chat interface
- Code analysis tools
- Project management
- System health monitoring

### status

Show system health and component status.

```bash
codebase-gardener status [OPTIONS]
```

**Description**: Displays comprehensive system health information and component status.

**Options**:
- `--format TEXT`: Output format (text, json, yaml) [default: text]
- `--verbose`: Show detailed component information
- `--check-models`: Verify all LoRA adapters are loadable

**Examples**:
```bash
# Show basic status
codebase-gardener status

# Show detailed status
codebase-gardener status --verbose

# Check model integrity
codebase-gardener status --check-models

# Get JSON status
codebase-gardener status --format json
```

**Status Information**:
- Overall system health
- Component status (registry, model loader, context manager, vector stores)
- Active project information
- Memory usage and performance metrics
- Ollama connection status
- Recent errors or warnings

## Configuration

### Environment Variables

All CLI commands respect environment variables with the `CODEBASE_GARDENER_` prefix:

```bash
# Application settings
export CODEBASE_GARDENER_DEBUG=true
export CODEBASE_GARDENER_LOG_LEVEL=DEBUG

# Model settings
export CODEBASE_GARDENER_OLLAMA_BASE_URL=http://localhost:11434
export CODEBASE_GARDENER_EMBEDDING_MODEL=nomic-embed-code

# Storage settings
export CODEBASE_GARDENER_DATA_DIR=~/.codebase-gardener

# Performance settings
export CODEBASE_GARDENER_MAX_WORKERS=4
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=4096
```

### Configuration File

You can also use a configuration file at `~/.codebase-gardener/config.yaml`:

```yaml
app:
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
  data_dir: "~/.codebase-gardener"
  max_cache_size: 3

performance:
  max_workers: 4
  memory_limit_mb: 4096
```

## Exit Codes

The CLI uses standard exit codes:

- `0`: Success
- `1`: General error
- `2`: Command line usage error
- `3`: Configuration error
- `4`: Project not found
- `5`: Model loading error
- `6`: Network/connection error

## Examples and Workflows

### Initial Setup Workflow

```bash
# 1. Initialize the system
codebase-gardener init

# 2. Add your first project
codebase-gardener add /path/to/my-project --name "My Project"

# 3. Check status
codebase-gardener status

# 4. Start web interface
codebase-gardener serve
```

### Multi-Project Workflow

```bash
# Add multiple projects
codebase-gardener add /path/to/web-api --name "Web API"
codebase-gardener add /path/to/mobile-app --name "Mobile App"
codebase-gardener add /path/to/data-pipeline --name "Data Pipeline"

# List all projects
codebase-gardener list

# Switch between projects for analysis
codebase-gardener switch "Web API"
codebase-gardener analyze "How does authentication work?"

codebase-gardener switch "Mobile App"
codebase-gardener analyze "Find all API calls"
```

### Maintenance Workflow

```bash
# Check system health
codebase-gardener status --verbose

# Retrain a project after major changes
codebase-gardener train "My Project" --force

# Clean up unused projects
codebase-gardener remove "Old Project" --force
```

## Troubleshooting

### Common Issues

**Command not found**:
```bash
# Ensure package is installed correctly
pip install -e .

# Check if command is in PATH
which codebase-gardener
```

**Permission errors**:
```bash
# Fix directory permissions
chmod -R 755 ~/.codebase-gardener
```

**Ollama connection errors**:
```bash
# Check if Ollama is running
curl http://localhost:11434/api/version

# Start Ollama if needed
ollama serve
```

**Memory issues**:
```bash
# Reduce memory usage
export CODEBASE_GARDENER_MEMORY_LIMIT_MB=2048
export CODEBASE_GARDENER_MAX_WORKERS=2
```

### Getting Help

- Use `--help` with any command for detailed usage information
- Check the [Troubleshooting Guide](troubleshooting.md) for common issues
- Enable debug mode with `--debug` for verbose output
- Check system status with `codebase-gardener status --verbose`

## See Also

- [Setup Guide](../../docs/setup-guide.md) - Installation and initial setup
- [API Reference](api-reference.md) - Python API documentation
- [Troubleshooting Guide](troubleshooting.md) - Common issues and solutions
- [Architecture Overview](architecture-overview.md) - System architecture details