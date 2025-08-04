#!/usr/bin/env bash
set -euo pipefail

# Codebase Gardener Setup Script
# This script sets up the development environment for the Codebase Gardener project

echo "Setting up Codebase Gardener development environment..."

# Check Python version
python_version=$(python3 --version 2>&1 | cut -d' ' -f2 | cut -d'.' -f1,2)
required_version="3.11"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo "Error: Python $required_version or higher is required. Found: $python_version"
    exit 1
fi

# Install dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip setuptools wheel

# Install the package in development mode with dev dependencies
pip install -e ".[dev,performance]"

# Install additional requirements if they exist
if [ -f "requirements.txt" ]; then
    echo "Installing additional requirements..."
    pip install -r requirements.txt
fi

# Set up pre-commit hooks if available
if command -v pre-commit &> /dev/null; then
    echo "Setting up pre-commit hooks..."
    pre-commit install
fi

# Create necessary directories
echo "Creating project directories..."
mkdir -p logs
mkdir -p data/models
mkdir -p data/vector_stores

# Set environment variables for development
export PYTHONPATH="${PYTHONPATH:-}:$(pwd)/src"
export CODEBASE_GARDENER_ENV="development"
export CODEBASE_GARDENER_LOG_LEVEL="INFO"

# Verify installation by running basic tests
echo "Verifying installation..."
python -c "import codebase_gardener; print('✓ Package imported successfully')"

# Run a quick test to ensure everything is working
python -m pytest tests/test_project_structure.py -v

echo "✓ Setup completed successfully!"
echo "You can now run the application with: python -m codebase_gardener.main"