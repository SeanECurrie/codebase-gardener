# TODO.md - Project Task List

## Current Status (as of 2025-08-09)

✅ **Verified Working**
- Core import: `import codebase_auditor` succeeds
- Smoke test: `PYTHONPATH=. python scripts/smoke_cli.py` returns SMOKE_OK
- MVP tests: `pytest tests/test_single_file_auditor.py` passes 4/4
- CLI entry point: `codebase-auditor = "codebase_auditor:main"` correct (main() exists)
- Security audit and dependency audit completed
- Git alignment and branching strategy established (mvp/focus-cli branch)
- Pre-commit hooks configured and working

## Recent Completions ✅

✅ **Test Infrastructure Fixed** (commit 0fd4fd6)
- `tests/test_project_structure.py` replaced with MVP-focused tests
- All MVP tests now pass: pytest -q confirms 4/4 success

✅ **Ollama Retry Logic Added** (commit 1e2b184)
- Exponential backoff retry in codebase_auditor.py
- Friendly error messages with host/model info after retries
- Graceful degradation when AI service unavailable

✅ **Documentation Aligned** (commits 9e6d74f, 6b6a022)
- CLAUDE.md focuses on MVP scope with retry behavior noted
- CAPABILITY_REPORT.md created with current status

## 🚀 Next 3 Actions (≤45 min each)

### 1. Create HOW_TO_RUN.md Guide
**Gap**: Users need quickstart guide with concrete examples
**Output**: User-facing guide with install→smoke→CLI→troubleshooting flow
```bash
# Result: Clear onboarding path for new users
```

### 2. Verify All Test Coverage
**Task**: Run full test suite and smoke test to confirm stability
**Commands**: `pytest -q` + `PYTHONPATH=. python scripts/smoke_cli.py`
```bash
# Ensure CI pipeline stays green
```

### 3. Add Performance Benchmarks to Capability Report
**Enhancement**: Document scale limits (4k+ files behavior) and timing
**Research**: Test with large repo, document memory/time characteristics

## 🎯 Success Criteria (next 1–2 days)

- `pytest -v` returns 0 failures across all active tests
- GitHub Actions CI workflow runs clean without test failures
- Clear documentation scope: users understand MVP = single-file CLI tool
- Robust Ollama connection with retry logic and helpful error messages
- Pre-commit hooks pass consistently

**Notes**: Active CLI only; excludes *_DISABLED/ and .kiro/
