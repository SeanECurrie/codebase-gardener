#!/bin/bash
# MVP Scope Command - Add this to your shell profile or run directly
# Usage: ./mvp_scope_command.sh [project_directory]

# Set default project directory to current directory if not provided
PROJECT_DIR="${1:-.}"

echo "🔍 Executing MVP Scope for project: $PROJECT_DIR"

# Change to project directory
cd "$PROJECT_DIR" || {
    echo "❌ Error: Could not access directory $PROJECT_DIR"
    exit 1
}

# Check if mvp_scope.py exists
if [ ! -f "mvp_scope.py" ]; then
    echo "❌ Error: mvp_scope.py not found in $PROJECT_DIR"
    echo "This command should be run from the codebase-local-llm-advisor directory"
    exit 1
fi

# Run the MVP scope process
python mvp_scope.py "$PROJECT_DIR"

# Check if successful
if [ $? -eq 0 ]; then
    echo ""
    echo "✅ MVP scoping complete!"
    echo "📋 View the report: cat mvp_scope_report.md"
    echo "🏃 Run MVP CLI: python codebase_auditor.py"
    echo "🧪 Test MVP: python scripts/smoke_cli.py"
else
    echo "❌ MVP scoping failed"
    exit 1
fi
