#!/bin/bash

# Crotchety Code Auditor Startup Script
# This script ensures everything is ready and starts the auditor

echo "🔧 Starting Crotchety Code Auditor..."
echo "=================================="

# Debug info
echo "🔍 Debug Info:"
echo "Python: $(which python)"
echo "Python Version: $(python -V)"
echo "Current Directory: $(pwd)"

# Set PYTHONPATH to use local code
export PYTHONPATH="$(pwd):$PYTHONPATH"
echo "PYTHONPATH: $PYTHONPATH"

# Check if Ollama is running
if ! pgrep -x "ollama" > /dev/null; then
    echo "⚠️  Ollama not running. Starting Ollama..."
    ollama serve &
    sleep 3
fi

# Decide on model and ensure one is available
DEFAULT_MODEL="gpt-oss-20b"  # hyphen variant
ALT_MODEL="gpt-oss:20b"      # colon variant (older naming)
FALLBACK_MODEL="llama3.2:3b"

echo "🔍 Checking for available models..."
if ollama list | grep -q "$DEFAULT_MODEL"; then
  export OLLAMA_MODEL="$DEFAULT_MODEL"
elif ollama list | grep -q "$ALT_MODEL"; then
  export OLLAMA_MODEL="$ALT_MODEL"
else
  echo "📥 Pulling $DEFAULT_MODEL (if supported)..."
  if ollama pull "$DEFAULT_MODEL" 2>/dev/null; then
    export OLLAMA_MODEL="$DEFAULT_MODEL"
  else
    echo "⚠️  $DEFAULT_MODEL not available. Trying $ALT_MODEL..."
    if ollama pull "$ALT_MODEL" 2>/dev/null; then
      export OLLAMA_MODEL="$ALT_MODEL"
    else
      echo "⚠️  Neither $DEFAULT_MODEL nor $ALT_MODEL available. Falling back to $FALLBACK_MODEL"
      if ! ollama list | grep -q "$FALLBACK_MODEL"; then
        ollama pull "$FALLBACK_MODEL"
      fi
      export OLLAMA_MODEL="$FALLBACK_MODEL"
    fi
  fi
fi

echo "✅ Using model: $OLLAMA_MODEL"

echo "✅ Everything ready! Starting the Codebase Intelligence Auditor..."
echo ""
echo "💡 Tip: You can also run an interactive CLI via codebase_auditor.py"
echo ""

# Start the single-file auditor CLI
python codebase_auditor.py