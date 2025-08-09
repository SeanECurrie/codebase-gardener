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

## What's Broken / Gaps

❌ **Legacy Test Infrastructure**
- `tests/test_project_structure.py` fails 4/4 tests (ModuleNotFoundError: codebase_gardener)
- Tests reference disabled `src/codebase_gardener/` system components
- CI/CD pipeline affected by failing tests

❌ **Single Point of Failure**
- Ollama connection has no retry logic or graceful degradation
- Generic error messages when AI service unavailable

❌ **Documentation Confusion**
- CLAUDE.md references disabled "Full Gardener System" components
- Mixed messaging about what's actually available in MVP

## 🚀 Immediate Next Actions (ranked 1–3)

### 1. Fix Test Infrastructure
**Problem**: 4/4 project structure tests failing due to disabled module imports
**Solution**: Replace tests/test_project_structure.py with MVP-focused tests for codebase_auditor and simple_file_utils modules
```bash
python -m pytest tests/test_project_structure.py -v  # should pass after fix
```

### 2. Add Ollama Retry Logic
**Problem**: Single-attempt connection to Ollama causes poor UX when service starting
**Solution**: Add exponential backoff retry in codebase_auditor.py analyze_codebase() method, lines ~250-280
```bash
# Test with: python codebase_auditor.py (when Ollama not running)
```

### 3. Clean Up Documentation
**Problem**: CLAUDE.md references disabled "Full Gardener System" confusing users/tests
**Solution**: Update CLAUDE.md to focus only on working MVP components (codebase_auditor.py, simple_file_utils.py)

## 🎯 Success Criteria (next 1–2 days)

- `pytest -v` returns 0 failures across all active tests
- GitHub Actions CI workflow runs clean without test failures
- Clear documentation scope: users understand MVP = single-file CLI tool
- Robust Ollama connection with retry logic and helpful error messages
- Pre-commit hooks pass consistently

**Notes**: Active CLI only; excludes *_DISABLED/ and .kiro/
