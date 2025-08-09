# TODO.md - Project Task List

## Current Status Assessment (Updated 2025-08-09)

✅ **COMPLETED**: Core MVP functionality is working
- Single-file auditor imports and runs successfully
- Script entry point `codebase-auditor = "codebase_auditor:main"` is correct (main() exists at line 483)
- Basic tests passing (4/4 in test_single_file_auditor.py)
- Smoke test functioning (PYTHONPATH=. python scripts/smoke_cli.py works)
- Security review and dependency audit completed
- Git alignment and branching strategy established

❌ **FAILING**: Legacy test infrastructure
- `tests/test_project_structure.py` fails due to disabled `codebase_gardener` module references
- Tests expect complex system components that are intentionally disabled for MVP

## Today's Priority (≤3 most important items)

1. **[HIGH PRIORITY]** Fix failing project structure tests (20 min) ✳️ NEXT ACTION
   - Location: `tests/test_project_structure.py` - Remove references to disabled modules
   - Current: 4/4 tests failing due to `codebase_gardener` import errors
   - Impact: Clean CI/CD pipeline and accurate test reporting

2. **[HIGH PRIORITY]** Add connection retry logic to CLI (45 min)
   - Location: `codebase_auditor.py` lines 250-280 - Ollama client connection
   - Current: Single attempt connection, generic error on failure
   - Impact: Better user experience when Ollama is starting up or temporarily unavailable

3. **[MEDIUM PRIORITY]** Clean up disabled component references (30 min)
   - Location: Documentation and configuration files
   - Current: CLAUDE.md and other docs reference disabled features
   - Impact: Reduce confusion about what's actually available in MVP

## Code Quality & Architecture

### High Priority (≤30 min each)

- ✅ **COMPLETED: CLI script entry point**
  - `pyproject.toml:117` entry point is correct, main() function exists at line 483
  - CLI installation and imports work properly

- **Resolve import path issues**  ✳️ IMMEDIATE NEXT
  - `tests/test_project_structure.py` - Update imports to only test active components
  - Remove references to disabled `codebase_gardener` module imports

### Medium Priority (≤60 min each)

- **Enhanced error handling in CLI tools**
  - `codebase_auditor.py` - Add connection retry logic for Ollama
  - `simple_file_utils.py` - Add better error messages for file access issues
  - Implement graceful degradation when AI services are unavailable

- **Configuration validation**
  - Add environment variable validation for `OLLAMA_HOST` and `OLLAMA_MODEL`
  - Provide clear error messages when required dependencies are missing
  - Validate model availability before starting analysis

- **Test reliability improvements**
  - `test_simple_auditor.py:84` - Make connection tests work with/without Ollama
  - Add mock-based testing for AI integration components
  - Create test fixtures that don't require external dependencies

### Low Priority (≤120 min each)

- **Code documentation improvements**
  - Add comprehensive docstrings to main classes in active CLI files
  - Document configuration options and environment variables in README
  - Add inline comments for complex file filtering logic in `simple_file_utils.py`

- **AST-based code splitting** (Future Enhancement)
  - Location: `src/codebase_gardener_DISABLED/data/preprocessor.py:640`
  - Current: `# TODO: Implement more sophisticated AST-based splitting`
  - Note: This is in disabled components, defer until post-MVP

## Testing & Quality Assurance

### High Priority (≤30 min each)

- **Fix active test suite**
  - Remove/update tests that reference disabled modules
  - Ensure `pytest tests/test_single_file_auditor.py` runs cleanly
  - Update test configurations to match active component structure

### Medium Priority (≤60 min each)

- **Integration testing for CLI workflow**
  - Test end-to-end analysis workflow with small test codebase
  - Verify markdown export functionality works correctly
  - Test chat functionality with mock responses

### Low Priority (≤120 min each)

- **Performance testing on large codebases**
  - Test memory usage and processing time with 100+ file projects
  - Validate file filtering performance with deep directory structures
  - Benchmark analysis quality across different programming languages

## Infrastructure & DevOps

### Medium Priority (≤60 min each)

- **Package management cleanup**
  - Review and remove unused dependencies from `pyproject.toml`
  - Create minimal requirements.txt for CLI-only usage
  - Update package metadata to reflect actual MVP scope

- **CI/CD pipeline improvements**
  - Fix GitHub Actions workflow to only test active components
  - Add proper test matrix for supported Python versions
  - Configure pre-commit hooks to run only on active files

### Low Priority (≤120 min each)

- **Development tooling enhancements**
  - Improve `setup.sh` script with better error handling
  - Add development Docker container for consistent testing environment
  - Create VS Code workspace configuration for active components only

## Future Enhancements (Post-MVP)

- **Multi-model support**: Add support for different LLM backends beyond Ollama
- **Output format options**: JSON export alongside markdown reports
- **Real-time analysis**: Streaming analysis for very large projects
- **Custom analysis templates**: User-defined analysis prompts and report formats

---

## Notes

- **Focus Area**: Active CLI components only (`codebase_auditor.py`, `simple_file_utils.py`, active tests)
- **Disabled Components**: All `*_DISABLED/` directories and files are intentionally parked for post-MVP
- **Current Status**: MVP-ready with basic functionality, needs polish and reliability improvements
- **Next Milestone**: Production-ready CLI with robust error handling and comprehensive testing

## 🚀 IMMEDIATE NEXT ACTIONS (Recommended Order)

### 1. Fix Test Infrastructure (20 min) - **START HERE**
```bash
# Problem: Legacy tests failing due to disabled module references
# Solution: Update tests/test_project_structure.py to test only MVP components
# Command: python -m pytest tests/test_project_structure.py -v
```

### 2. Improve CLI Reliability (45 min)
```bash
# Problem: Single-point-of-failure Ollama connection
# Solution: Add retry logic and better error messages in codebase_auditor.py
# Location: Lines 250-280 in analyze_codebase() method
```

### 3. Documentation Cleanup (30 min)
```bash
# Problem: Docs reference disabled features, confusing for users
# Solution: Update CLAUDE.md to focus on working MVP components only
# Files: CLAUDE.md, README.md (ensure consistency)
```

### 🎯 **Success Criteria**
- All tests passing: `pytest -v` returns 0 failures
- Clean CI/CD: GitHub Actions workflow runs without errors
- Clear documentation: Users understand exactly what's available

---

Generated: 2025-08-09 from /todo-sweep command + manual status assessment
Updated: 2025-08-09 with current progress and immediate priorities
Scope: Active CLI files only, prioritized by impact and effort
