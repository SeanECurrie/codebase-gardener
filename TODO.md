# TODO.md - Project Task List

## Today's Priority (≤3 most important items)

1. **[HIGH PRIORITY]** Fix package configuration and test import issues (30 min)
   - Location: `pyproject.toml` - incorrect script entry point configuration
   - Current: `codebase-auditor = "codebase_auditor:main"` but no main() function exists
   - Impact: CLI installation and import issues affecting all tests

2. **[HIGH PRIORITY]** Add robust error handling to codebase_auditor.py (60 min)  
   - Location: `codebase_auditor.py` - Ollama connection and file processing
   - Current: Basic try-catch, no retries or graceful degradation
   - Impact: Better user experience when Ollama is unavailable or file access fails

3. **[MEDIUM PRIORITY]** Improve test coverage for the active CLI components (60 min)
   - Location: `tests/test_project_structure.py` - Fix module import issues
   - Current: Tests failing due to disabled modules being referenced
   - Impact: Enable reliable CI/CD pipeline for active components

## Code Quality & Architecture

### High Priority (≤30 min each)

- **Fix CLI script entry point**
  - `pyproject.toml:117` - Update script entry point to match actual file structure
  - Add proper main() function to `codebase_auditor.py` or fix entry point path

- **Resolve import path issues**  
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

Generated: 2025-08-09 from /todo-sweep command
Scope: Active CLI files only, prioritized by impact and effort