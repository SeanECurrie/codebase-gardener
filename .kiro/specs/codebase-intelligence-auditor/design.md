# Codebase Intelligence Auditor - Design Document

## Overview

**Simple Goal:** Point at a directory, get comprehensive codebase analysis from gpt-oss-20b, chat about it, export markdown.

**Core Principle:** Make it work first. Single file, hardcoded prompts, direct implementation.

## Architecture

### Pragmatic Approach - Single File Solution

```
User → codebase_auditor.py → Ollama (gpt-oss-20b) → Chat + Markdown Export
```

**That's it.** No complex engines, no abstractions, no enterprise patterns.

## Core Implementation

### Single Main Class

```python
class CodebaseAuditor:
    def __init__(self):
        self.ollama_client = OllamaClient()  # Use existing
        self.analysis_results = None
        
    def analyze_codebase(self, directory_path: str) -> str:
        """Main method - does everything"""
        # 1. Find files (use existing FileUtilities)
        # 2. Read files in chunks
        # 3. Send to gpt-oss-20b with analysis prompt
        # 4. Store results
        # 5. Return summary
        
    def chat(self, question: str) -> str:
        """Answer questions about the analysis"""
        
    def export_markdown(self) -> str:
        """Generate markdown report"""
```

**Three methods. That's the entire design.**

## Implementation Details

### File Discovery (Use Existing)

```python
def _find_files(self, directory_path: str) -> List[str]:
    """Use existing FileUtilities.find_source_files()"""
    # Leverage what already works
    # Add simple filtering for .py, .js, .ts, .md files
    # Exclude node_modules, .git, __pycache__
```

### Analysis Prompts (Hardcoded)

```python
ANALYSIS_PROMPT = """
You are a senior code reviewer. Analyze this codebase and provide:

1. **Architecture Overview**: Main components and how they connect
2. **Tech Debt Issues**: Code quality problems, inconsistencies, duplications
3. **Documentation Gaps**: Missing or outdated documentation
4. **Key Insights**: Most important things a developer should know

Be specific with file names and line numbers when possible.

Codebase files:
{file_contents}
"""

CHAT_PROMPT = """
Based on your previous analysis of this codebase:
{previous_analysis}

User question: {user_question}

Provide a helpful, specific answer.
"""
```

### Simple Data Storage

```python
# Just store as strings - no complex data models
self.analysis_results = {
    'full_analysis': str,  # Complete analysis from gpt-oss-20b
    'file_list': List[str],  # Files that were analyzed
    'timestamp': str  # When analysis was done
}
```

## Error Handling (Keep It Simple)

```python
def analyze_codebase(self, directory_path: str) -> str:
    try:
        # Basic validation
        if not os.path.exists(directory_path):
            return "Directory not found"
            
        # Find files
        files = self._find_files(directory_path)
        if not files:
            return "No source files found"
            
        # Analyze with gpt-oss-20b
        analysis = self._analyze_with_ollama(files)
        self.analysis_results = analysis
        
        return "Analysis complete. Ask me questions or export markdown."
        
    except Exception as e:
        return f"Analysis failed: {str(e)}"
```

**That's it.** No complex error hierarchies, no retry logic, no elaborate handling.

## Usage (Dead Simple)

```python
# Create auditor
auditor = CodebaseAuditor()

# Analyze codebase
result = auditor.analyze_codebase("/path/to/codebase")
print(result)  # "Analysis complete. Ask me questions or export markdown."

# Chat about findings
response = auditor.chat("What are the main architecture issues?")
print(response)

# Export markdown
report = auditor.export_markdown()
with open("codebase_analysis.md", "w") as f:
    f.write(report)
```

## Integration with Existing Code

**Use What Works:**
- `FileUtilities.find_source_files()` for file discovery
- Existing `OllamaClient` for gpt-oss-20b communication
- Existing error handling and logging patterns

**Add Minimal New Code:**
- Single `codebase_auditor.py` file
- Hardcoded analysis prompts
- Simple string-based storage

## Testing (Pragmatic)

**Test on THIS codebase first:**
1. Point it at current codebase-gardener project
2. See if analysis makes sense
3. Compare with what we know about the code
4. Fix obvious issues

**That's the entire testing strategy for MVP.**

## Future Enhancements (When It Works)

- Better file chunking for large codebases
- More sophisticated prompts
- Gradio web interface
- MLX optimization for faster analysis

**But first: Make it work with the simplest possible implementation.**