# Claude Execution Directives (READ FIRST)

## Always-Read Order (each task start)
Read these files in exact order before any task execution:

1. `.kiro/specs/enhanced-codebase-auditor/requirements.md`
2. `.kiro/specs/enhanced-codebase-auditor/design.md`
3. `.kiro/specs/enhanced-codebase-auditor/tasks.md`
4. `.kiro/steering/task-execution-framework.md`
5. `.kiro/steering/core-development-principles.md`

## Non-Interactive Policy
Never pause to ask for approval; choose safe defaults; keep logs concise. Use non-interactive flags: --yes, --quiet, --force-with-lease where applicable.

## MCP Tool Sequence (if available)
Sequential Thinking → Context7 → Bright Data → Basic Memory. If unavailable, use integrated reasoning, WebSearch/WebFetch, and file-based approaches.

## Task Lifecycle (MANDATORY per task)
1. **Pre-Task**: Previous memory check + read-first directives
2. **During-Task**: Implement + tests following "make it work first" principle
3. **Post-Task**: Gap closure, memory file creation, documentation updates
4. **Git/PR**: Conventional commits, push branch, maintain CI
5. **Validation**: All completion criteria met before marking complete

## Memory & Trace
- Write memory artifacts under `.kiro/memory/` per task (naming: `<task_slug>.md`)
- **CRITICAL**: Update `.kiro/specs/enhanced-codebase-auditor/tasks.md` FIRST - mark task completed with checkmarks and findings
- Update `.kiro/docs/task_completion_test_log.md` with completion status
- Memory files are authoritative handoff documents between tasks

## Git & CI
- Use conventional commit format: `feat(component): description`
- Push branches with proper naming: `feat/component-taskN`
- Keep CI green: run `ruff check --fix && ruff format && pytest -q`
- Use `--force-with-lease` for safe force pushes only when necessary

## Core Execution Principles
- **Make it work first** - fix broken functionality before optimizing
- **Read code first** - understand actual implementation before testing
- **Backwards compatibility** - existing CLI must continue working
- **Real validation** - test with actual data, real user interaction
- **Gap closure** - address quick wins, document deferred items
