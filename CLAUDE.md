# CLAUDE.md

Policy-Version: 2025-08-17

## READ FIRST (Auto-Run)
- Always read (in order) the directives and spec before any action:
  `.kiro/specs/enhanced-codebase-auditor/claude-directives.md`
  `.kiro/specs/enhanced-codebase-auditor/requirements.md`
  `.kiro/specs/enhanced-codebase-auditor/design.md`
  `.kiro/specs/enhanced-codebase-auditor/tasks.md`
  `.kiro/steering/task-execution-framework.md`
- Non-interactive mode: never ask to proceed; use safe defaults.

## CRITICAL TASK COMPLETION REQUIREMENT
**ALWAYS UPDATE TASKS.MD FIRST** when completing any task:
- Change `- [ ] N. Task Name` to `- [x] N. Task Name **COMPLETED YYYY-MM-DD**`
- Add completion checkmarks to all Pre-Task, Implementation, Post-Task phases
- Document key findings and gaps directly in the task
- This is completion criteria #11 - the task is NOT complete without this update

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## MVP Scope

**Current Focus**: Single-file CLI tool only (`codebase_auditor.py` + `simple_file_utils.py`)

The project is scoped to MVP - a working interactive CLI for immediate codebase analysis. Complex system components in `*_DISABLED/` directories are parked for post-MVP development.

**Core Components:**
1. **Single-file Auditor** (`codebase_auditor.py`) - Main interactive CLI with retry logic
2. **File Utilities** (`simple_file_utils.py`) - Source file discovery and filtering

## Quick Development Commands

## How to Run

### Lint/Format
```bash
ruff check --fix && ruff format
```

### Tests
```bash
pytest -q tests/test_single_file_auditor.py
python -m pytest -q tests/test_project_structure.py
```

### Smoke (no Ollama needed)
```bash
PYTHONPATH=. python scripts/smoke_cli.py
```

### Run CLI (requires Ollama running & model present)
```bash
python codebase_auditor.py
```

**Note:** CLI now includes retry behavior for Ollama connections with exponential backoff and clearer error messages.

### Code Quality
```bash
# Format code
black src/ tests/
isort src/ tests/

# Type checking
mypy src/

# Lint with Ruff
ruff src/ tests/

# Run all quality checks
black . && isort . && mypy src/ && ruff .
```

### Running the Applications

#### Single-file Auditor (Recommended for immediate use)
```bash
# Interactive CLI mode
python codebase_auditor.py

# With specific Ollama settings
export OLLAMA_HOST=http://localhost:11434
export OLLAMA_MODEL=llama3.2:3b
python codebase_auditor.py

# CLI commands available:
# analyze <directory>              - Basic codebase analysis
# analyze --advanced <directory>   - Enhanced analysis with advanced features (if available)
# features                         - Show advanced feature status
# chat <question>                  - Ask questions about analysis
# export [filename]                - Export markdown report
# status                           - Show current analysis status
# projects                         - List all registered projects
# project create <dir>             - Create/register new project
# project info [id]                - Show project information
# project switch <id>              - Switch between project contexts
# project cleanup                  - Analyze old project data
# project health                   - Check project system health
```

#### Full System (Development/Advanced)
```bash
# Setup development environment
./setup.sh

# Run main application
python -m codebase_gardener.main analyze /path/to/project
```

### Environment Setup
```bash
# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # macOS/Linux

# Install dependencies
pip install -e ".[dev,performance]"
# OR minimal: pip install ollama

# Install requirements
pip install -r requirements.txt
```

## Architecture Overview

### Key Components

**Working Components:**
- `codebase_auditor.py` - Single-file interactive auditor (fully functional)
- `simple_file_utils.py` - File discovery and processing utilities
- `src/codebase_gardener/utils/file_utils.py` - Enhanced file utilities
- `src/codebase_gardener/config/` - Configuration management

**Complex System Components (varying completion states):**
- `src/codebase_gardener/core/` - Project registry, context management, training pipeline
- `src/codebase_gardener/models/` - AI model interfaces (some disabled)
- `src/codebase_gardener/data/` - Vector stores and preprocessing
- `src/codebase_gardener/ui/` - Gradio web interface
- `src/codebase_gardener/monitoring/` - Operational monitoring
- `src/codebase_gardener/performance/` - Load testing and benchmarking

### File Processing Architecture

The codebase uses a multi-stage file filtering approach:
1. **Discovery**: Find all files in target directory
2. **Filtering**: Exclude dependencies, build files, binaries using patterns in `EXCLUDE_PATTERNS`
3. **Size-based Analysis**: Different analysis depth based on project size:
   - Small (≤5 files): Brief analysis
   - Medium (6-100 files): Comprehensive analysis
   - Large (>100 files): High-level overview

### AI Integration

- **Primary Interface**: Direct `ollama` package usage
- **Model Support**: Ollama-compatible models (llama3.2:3b recommended for development)
- **Context Management**: Project-specific conversation states
- **Disabled Components**: Complex OllamaClient wrapper (use ollama package directly)

## Development Patterns

### File Utilities Usage
```python
# Use SimpleFileUtilities for basic operations
from simple_file_utils import SimpleFileUtilities
utils = SimpleFileUtilities()
files = utils.discover_files(directory_path)

# Use enhanced FileUtilities for advanced operations
from codebase_gardener.utils.file_utils import FileUtilities
utils = FileUtilities()
```

### Testing Strategy
- Unit tests for individual components
- Integration tests for end-to-end workflows
- Performance tests for load scenarios
- Separate test configurations for different components

### Configuration Management
- Environment variables with `CODEBASE_GARDENER_` prefix
- Pydantic-based settings validation
- Development vs production configurations

## Dependencies

### Core Runtime
- `ollama` - LLM inference
- `pydantic` - Configuration validation
- `structlog` - Logging
- `click` - CLI interface
- `rich` - Console output

### Development
- `pytest` - Testing framework
- `black` - Code formatting
- `isort` - Import sorting
- `mypy` - Type checking
- `ruff` - Linting

### Full System (when using advanced features)
- `transformers` + `peft` - Model loading and LoRA
- `lancedb` - Vector database
- `gradio` - Web interface
- `tree-sitter` - Code parsing

## Common Development Tasks

### Adding New File Types
1. Update `EXCLUDE_PATTERNS` in file utilities
2. Add parsing logic if needed
3. Update tests to include new file types

### Modifying Analysis Depth
- Edit size thresholds in `codebase_auditor.py`
- Update corresponding prompts for different analysis levels

### Extending CLI Commands
- Add commands to `src/codebase_gardener/main.py`
- Follow Click command patterns
- Include rich console output for user feedback

## Troubleshooting

### Ollama Connection Issues
- Ensure Ollama is running: `ollama serve`
- Check model availability: `ollama list`
- Set correct `OLLAMA_HOST` environment variable

### Import Errors
- Some components are intentionally disabled (e.g., `OllamaClient`)
- Use direct ollama package imports instead of wrapper classes
- Check PYTHONPATH includes `src/` directory

### Performance Issues
- Large projects (>100 files) automatically get high-level analysis
- Use specific subdirectories for detailed analysis
- Monitor memory usage with performance utilities

# important-instruction-reminders
Do what has been asked; nothing more, nothing less.
NEVER create files unless they're absolutely necessary for achieving your goal.
ALWAYS prefer editing an existing file to creating a new one.
NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User.

## Branching & PR Policy (Authoritative)

### Branching Strategy
- **main**: Production-ready code, protected branch
- **development**: Integration branch for feature work
- **feat/component-taskN**: Feature branches for individual tasks

### Branch Workflow
```bash
# Always start from development
git checkout development && git pull origin development

# Create feature branch
git checkout -b feat/component-taskN development

# Work on task with conventional commits
git commit -m "feat(component): implement feature X"

# Push and create PR to development (NOT main)
git push -u origin feat/component-taskN
gh pr create --base development --title "feat(component): Task N - Feature Description"
```

### Conventional Commit Format
```
<type>(scope): <description>

[optional body]

[optional footer]
```

**Types**: feat, fix, docs, style, refactor, test, chore
**Scope**: Component name (core, data, models, ui, etc.)

### PR Requirements
- PR base=development (never directly to main)
- All tests pass (pytest -q core tests)
- Code quality checks pass (ruff check --fix && ruff format)
- Tasks.md updated with completion status
- Memory file created/updated

## Task Loop (Start → Finish)

### Pre-Task Phase (MANDATORY)
1. **Previous Task Validation**
   - Read `.kiro/memory/[component]_task[N-1].md`
   - Verify previous task completion criteria met
   - Test previous task outputs work
   - Review gaps from `.kiro/docs/task_completion_test_log.md`

2. **Foundation Reading**
   - `.kiro/steering/core-development-principles.md` (Make it work first)
   - `.kiro/steering/task-execution-framework.md` (Complete framework)
   - Previous memory file for context
   - `.kiro/docs/gap-closure-criteria.md` (Gap management)

3. **Research Phase**
   - Use integrated reasoning for system planning
   - Search existing codebase for patterns
   - Check component integration points
   - Plan implementation approach

### During Task Phase
4. **Implementation**
   - Apply "Make it work first" principle
   - Fix broken functionality before optimizing
   - Read code first, test second
   - Focus on core goal, not peripheral symptoms

5. **Gap Closure Integration**
   - **Gap Validation**: Review previous task gaps that align with current scope
   - **Quick Wins**: Address gaps <30min, low risk, improve validation
   - **Documentation**: Track gaps for next task consideration

### Post-Task Phase (MANDATORY)
6. **Testing & Integration**
   - Run `pytest -q tests/test_single_file_auditor.py tests/test_project_structure.py`
   - Run `ruff check --fix && ruff format`
   - Test component integration with existing system
   - Verify no regressions introduced

7. **Documentation & Handoff**
   - **CRITICAL**: Update `.kiro/specs/enhanced-codebase-auditor/tasks.md` FIRST
   - Create comprehensive memory file following template
   - Update `.kiro/docs/task_completion_test_log.md`
   - Document integration points and next task considerations

8. **Git Integration**
   - Create feature branch: `git checkout -b feat/component-taskN development`
   - Conventional commits with proper scope
   - Push branch and create PR to development
   - Ensure CI passes before merge

### Task Completion Criteria
- **Functional**: Real working code, real data, user validation, actionable usage
- **Process**: Previous task validated, gap closure applied, memory file created, git integration
- **Quality**: Integration tested, error handling, performance acceptable, code quality

## Edit Rules (Diff-Only, No Rewrites)

### File Editing Guidelines
- **ALWAYS read files before editing** using Read tool
- **Use diff-only edits** - never rewrite entire files
- **Preserve exact indentation** from Read tool output (after line number prefix)
- **Make surgical changes** - edit only what needs to change
- **Use MultiEdit for multiple changes** to same file

### Code Quality Requirements
- Follow established patterns from existing codebase
- Maintain backwards compatibility (MVP CLI must keep working)
- No emojis unless explicitly requested
- Use descriptive variable names and clear comments

### When to Create vs Edit
- **ALWAYS prefer editing existing files** over creating new ones
- **Only create files when absolutely necessary** for functionality
- **Never create documentation proactively** - only when requested
- **Use existing configuration patterns** rather than new config files

## Reasoning Protocol (Read → Act → Verify)

### Read First Principle
- **Examine actual code implementation** before making changes
- **Understand existing patterns** and architectural decisions
- **Check integration points** with other components
- **Review previous memory files** for established patterns

### Act on Real Problems
- **Fix broken functionality first** before optimizing
- **Address root causes** not symptoms
- **Use simplest solution that works** (pragmatic POC approach)
- **Focus on user's core workflow** completion

### Verify Everything
- **Test with actual data** not theoretical scenarios
- **Verify integration points** work correctly
- **Check backwards compatibility** maintained
- **Validate task completion criteria** met

### Decision Framework
When making implementation choices:
1. Does this fix broken functionality?
2. What's the simplest approach that works?
3. Does this maintain backwards compatibility?
4. Will this help complete the user's workflow?
5. Is this aligned with project-specific intelligence goals?

## Test & Docs Expectations

### Testing Requirements
- **MVP Tests Must Pass**: `pytest -q tests/test_single_file_auditor.py tests/test_project_structure.py`
- **Code Quality Checks**: `ruff check --fix && ruff format`
- **Smoke Tests**: `PYTHONPATH=. python scripts/smoke_cli.py`
- **Real Data Testing**: Test with actual codebases, not mock data
- **Integration Testing**: Verify component works with existing system

### Testing Strategy by Component Type
- **Core Components**: Unit tests + integration with existing CLI
- **Data Components**: Real parsing tests with actual code files
- **AI Components**: Mock-friendly tests + real model integration tests
- **UI Components**: User interaction tests + error handling

### Documentation Standards
- **Memory Files**: Comprehensive handoff documentation in `.kiro/memory/`
- **Task Updates**: Mark completion in `.kiro/specs/enhanced-codebase-auditor/tasks.md`
- **Integration Docs**: Document component interfaces and data flow
- **No Proactive Docs**: Never create README/docs unless explicitly requested

### Quality Gates
- All existing functionality preserved
- New functionality tested with real scenarios
- Error handling implemented for failure cases
- Performance acceptable for Mac Mini M4 constraints
- Code follows established patterns and conventions

## Reporting Format

### Task Completion Report Template
```markdown
## Task N Completion Summary

### Functional Achievements
- [Achievement 1]: Description with verification method
- [Achievement 2]: Description with verification method
- [Requirements Met]: List specific requirements addressed

### Integration Points
- [Component 1]: How this task integrates with existing system
- [Component 2]: New interfaces or data flow changes
- [Backwards Compatibility]: Confirmation existing functionality preserved

### Quality Validation
- **Tests**: [Test results and coverage]
- **Performance**: [Performance metrics within constraints]
- **Error Handling**: [Failure scenarios addressed]
- **Code Quality**: [Linting/formatting results]

### Gap Closure Results
- **Quick Wins Closed**: [X]/[Y] ([Z]%) from previous task gaps
- **New Gaps Identified**: [List gaps for next task consideration]
- **Deferred Items**: [Items outside scope with rationale]

### Next Task Preparation
- **Handoff Information**: [Key points for next implementer]
- **Integration Challenges**: [Potential issues to watch for]
- **Recommended Approach**: [Suggested next steps]
```

### Memory File Handoff Requirements
- **Problem Analysis**: What was the core issue and why this approach
- **Implementation Details**: Key code patterns and architectural decisions
- **Integration Notes**: How component connects to existing system
- **Lessons Learned**: What worked well, what would be done differently
- **Next Task Gaps**: Specific items for future consideration

### Git Commit Message Format
```
feat(component): implement core functionality

- Add [specific capability 1]
- Integrate with [existing component]
- Handle [error scenarios]

Refs: Task N - [Component Name]
Tests: pytest -q [relevant tests]
```

---

**Cross-Reference Links**:
- Background specs: `.kiro/specs/enhanced-codebase-auditor/`
- Gap closure framework: `.kiro/docs/gap-closure-criteria.md`
- Task execution details: `.kiro/steering/task-execution-framework.md`
- Core principles: `.kiro/steering/core-development-principles.md`
