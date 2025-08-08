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

# Check if gpt-oss:20b is available
echo "🔍 Checking for gpt-oss:20b model..."
if ! ollama list | grep -q "gpt-oss:20b"; then
    echo "📥 Trying to install gpt-oss:20b model..."
    if ! ollama pull gpt-oss:20b 2>/dev/null; then
        echo "⚠️  gpt-oss:20b requires newer Ollama version. Will use fallback model."
        echo "💡 To use gpt-oss:20b, update Ollama from: https://ollama.com/download"
        
        # Try to ensure we have at least one working model
        if ! ollama list | grep -q "llama3.2:3b"; then
            echo "📥 Installing fallback model llama3.2:3b..."
            ollama pull llama3.2:3b
        fi
    fi
fi

echo "✅ Everything ready! Starting the Crotchety Code Auditor..."
echo ""
echo "🌐 Web interface will open at: http://localhost:7860"
echo "👴 Ready to provide brutally honest code reviews!"
echo ""

# Start the auditor
python crotchety_code_auditor.py