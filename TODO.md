# TODO.md - Project Task List

## Today's Priority (≤3 most important items)

1. **[HIGH PRIORITY]** Implement more sophisticated AST-based code splitting in preprocessor
   - Location: `src/codebase_gardener_DISABLED/data/preprocessor.py:640`
   - Current: Basic text splitting, needs proper AST parsing
   - Impact: Better code analysis accuracy for large files

2. **[HIGH PRIORITY]** Add proper error handling and retry logic to CLI tools
   - Location: `codebase_auditor.py` - Ollama connection failures
   - Current: Basic try-catch, no retries or graceful degradation
   - Impact: Better user experience when Ollama is unavailable

3. **[MEDIUM PRIORITY]** Improve test coverage for edge cases in file discovery
   - Location: `test_simple_auditor.py:84` - Connection test requires running Ollama
   - Current: Tests skip actual Ollama integration
   - Impact: More reliable CI/CD pipeline

## Code Quality & Architecture

### High Priority

- **Fix AST-based code splitting**: `src/codebase_gardener_DISABLED/data/preprocessor.py:640`
  - TODO: Implement more sophisticated AST-based splitting
  - Current approach may not handle complex code structures properly

- **Enhance error handling in CLI tools**
  - `codebase_auditor.py` - Add retry logic for Ollama connections
  - `simple_file_utils.py` - Add better error messages for file access issues
  - Add graceful degradation when AI services are unavailable

### Medium Priority

- **Improve test reliability**
  - `test_simple_auditor.py:84` - Make connection tests work without running Ollama
  - Add mock-based testing for AI integration
  - Fix test dependency on working directory in `test_settings.py:233`

- **Configuration management improvements**
  - Consolidate environment variable handling
  - Add validation for Ollama host/model settings
  - Better default model selection logic

### Low Priority

- **Code documentation**
  - Add more detailed docstrings to main classes
  - Document configuration options and environment variables
  - Add inline comments for complex file filtering logic

## Testing & CI/CD

### High Priority
- **Integration test improvements**
  - `tests/test_core/test_project_registry.py:382` - Fix fixture cleanup interference
  - Add tests that don't require external dependencies
  - Mock Ollama responses for consistent testing

### Medium Priority
- **Performance testing**
  - Add benchmarks for file discovery on large codebases
  - Test memory usage with different project sizes
  - Validate analysis quality across different code types

### Low Priority
- **Test coverage gaps**
  - `tests/test_data/test_parser.py:418` - Tree-sitter incremental parsing edge cases
  - `tests/test_utils/test_directory_setup.py:306` - Permission handling edge cases

## Infrastructure & DevOps

### Medium Priority
- **Package management**
  - Update pyproject.toml script entry point to match actual file structure
  - Clean up unused dependencies in complex system components
  - Add minimal requirements file for CLI-only usage

### Low Priority
- **Development tooling**
  - Add pre-commit hooks configuration
  - Improve setup.sh script error handling
  - Add development Docker container for consistent testing

## Feature Enhancements

### Future Considerations
- **AI model flexibility**
  - Support for different model backends beyond Ollama
  - Model selection based on codebase characteristics
  - Custom prompt templates for different analysis types

- **Output formats**
  - JSON export option alongside markdown
  - Integration with popular code analysis tools
  - Real-time streaming analysis for large projects

---

## Notes

- **Completed Recently**: Basic CLI functionality, file discovery, Ollama integration
- **In Progress**: Test suite stabilization, error handling improvements
- **Blocked**: Advanced features pending MVP completion

Generated: 2025-08-09 from /todo-sweep command
Focus: Active CLI files only (excluding *_DISABLED directories)