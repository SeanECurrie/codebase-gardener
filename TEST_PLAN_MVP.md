# MVP Test Plan: Codebase Intelligence Auditor

**Date:** 2025-08-09  
**Scope:** Active CLI components only (MVP functionality)  
**Focus:** Single-file auditor and file utilities

## Executive Summary

This test plan covers the MVP components that are currently active and functional:
- `codebase_auditor.py` - Primary CLI tool
- `simple_file_utils.py` - File discovery utilities
- Supporting test files

**Note:** The full `codebase_gardener` package is disabled (`*_DISABLED` suffix), so this plan focuses exclusively on the standalone MVP components.

## MVP Component Analysis

### Active Components
- ✅ `codebase_auditor.py` - Main CLI auditor (615 lines)
- ✅ `simple_file_utils.py` - File utilities (319 lines) 
- ✅ `tests/test_single_file_auditor.py` - Basic tests (104 lines)

### Disabled Components
- ❌ `src/codebase_gardener_DISABLED/` - Full package system
- ❌ `tests/test_project_structure.py` - Tests complex package (failing)
- ❌ All `*_DISABLED` files and directories

## Test Categories

### 1. Core Functionality Tests

#### 1.1 File Discovery & Processing
- [x] **EXISTING**: Basic file discovery (`test_basic_file_discovery`)
- [ ] **MISSING**: Large project handling (>100 files)
- [ ] **MISSING**: Binary file exclusion validation
- [ ] **MISSING**: Directory permission handling
- [ ] **MISSING**: Symbolic link handling
- [ ] **MISSING**: File encoding error handling

#### 1.2 Content Analysis
- [x] **EXISTING**: Analysis prompt generation (`test_analysis_prompt_generation`)
- [ ] **MISSING**: Content size limiting (max_file_bytes, max_total_bytes)
- [ ] **MISSING**: File truncation behavior
- [ ] **MISSING**: Multi-language project analysis
- [ ] **MISSING**: Empty/invalid file handling

#### 1.3 AI Model Integration
- [x] **EXISTING**: Basic chat functionality (`test_chat_functionality`)
- [ ] **MISSING**: Model availability checks (`_preflight_model_check`)
- [ ] **MISSING**: Ollama connection error handling
- [ ] **MISSING**: Large prompt handling
- [ ] **MISSING**: Model response validation

### 2. CLI Interface Tests

#### 2.1 Command Processing
- [ ] **MISSING**: `analyze <directory>` command validation
- [ ] **MISSING**: `chat <question>` command validation
- [ ] **MISSING**: `export [filename]` command validation
- [ ] **MISSING**: `status` command validation
- [ ] **MISSING**: `help` command validation
- [ ] **MISSING**: Invalid command handling

#### 2.2 Input Validation
- [ ] **MISSING**: Directory path sanitization
- [ ] **MISSING**: Question length limits
- [ ] **MISSING**: Filename validation
- [ ] **MISSING**: Special character handling

#### 2.3 Output Validation
- [x] **EXISTING**: Markdown export (`test_single_file_auditor_basic`)
- [ ] **MISSING**: Progress feedback validation
- [ ] **MISSING**: Error message formatting
- [ ] **MISSING**: Status display accuracy

### 3. Security & Robustness Tests

#### 3.1 Path Security
- [ ] **MISSING**: System directory access prevention
- [ ] **MISSING**: Path traversal protection
- [ ] **MISSING**: Symlink security validation

#### 3.2 Resource Management
- [ ] **MISSING**: Memory usage limits
- [ ] **MISSING**: File handle management
- [ ] **MISSING**: Large file processing limits

#### 3.3 Error Handling
- [ ] **MISSING**: Network connectivity issues
- [ ] **MISSING**: Disk space limitations
- [ ] **MISSING**: Corrupted file handling

### 4. Integration Tests

#### 4.1 End-to-End Workflows
- [x] **EXISTING**: Complete analysis workflow (`test_single_file_auditor_basic`)
- [ ] **MISSING**: Multi-step CLI session simulation
- [ ] **MISSING**: Real project analysis validation
- [ ] **MISSING**: Export-to-file workflow

#### 4.2 Environment Configuration
- [ ] **MISSING**: OLLAMA_HOST configuration testing
- [ ] **MISSING**: OLLAMA_MODEL configuration testing
- [ ] **MISSING**: Environment variable precedence

### 5. Performance Tests

#### 5.1 Scalability
- [ ] **MISSING**: Small project performance (≤5 files)
- [ ] **MISSING**: Medium project performance (6-100 files)  
- [ ] **MISSING**: Large project performance (>100 files)
- [ ] **MISSING**: Memory usage profiling

#### 5.2 Response Times
- [ ] **MISSING**: File discovery timing
- [ ] **MISSING**: AI model response timing
- [ ] **MISSING**: Export generation timing

## Test Implementation Priority

### High Priority (Critical MVP functionality)
1. **CLI Command Validation Suite** - Validate all CLI commands work correctly
2. **File Discovery Edge Cases** - Handle permissions, encoding, large projects
3. **Security Input Validation** - Prevent path traversal and system access
4. **Error Handling Robustness** - Graceful handling of common failures

### Medium Priority (Stability & User Experience)
1. **Integration Workflows** - End-to-end user scenarios
2. **Performance Benchmarks** - Validate acceptable performance
3. **Configuration Testing** - Environment variable handling

### Low Priority (Future Improvements)
1. **Advanced Edge Cases** - Rare scenarios and complex setups
2. **Optimization Testing** - Performance tuning validation

## Test Execution Strategy

### Phase 1: Core Functionality Validation
- Execute existing tests: `pytest tests/test_single_file_auditor.py`
- Implement missing file discovery tests
- Add content processing validation tests
- Validate security input handling

### Phase 2: CLI Interface Testing  
- Create comprehensive CLI command test suite
- Test interactive session scenarios
- Validate error message clarity and helpfulness

### Phase 3: Integration & Performance
- End-to-end workflow testing
- Performance benchmarking on different project sizes
- Environment configuration validation

### Phase 4: Edge Cases & Robustness
- Error condition testing
- Resource limit validation
- Security boundary testing

## Success Criteria

### Minimum Viable Testing (Must Pass)
- [ ] All existing tests continue to pass
- [ ] Basic CLI commands work correctly
- [ ] File discovery handles common project structures
- [ ] Security input validation prevents system access
- [ ] Analysis completes successfully on test projects

### Full MVP Testing (Should Pass)
- [ ] All CLI workflows function end-to-end
- [ ] Error handling provides helpful feedback
- [ ] Performance acceptable for typical projects
- [ ] Configuration options work correctly

### Comprehensive Testing (Nice to Have)
- [ ] Edge cases handled gracefully
- [ ] Performance optimized for large projects
- [ ] Advanced security scenarios validated

## Testing Environment Requirements

### Prerequisites
- Python 3.11+
- Ollama installed and available (for integration tests)
- Test model pulled (e.g., `ollama pull llama3.2:3b`)
- pytest and mocking libraries

### Test Data Requirements
- Sample small project (≤5 files)
- Sample medium project (6-100 files)
- Sample large project (>100 files)
- Projects with various file types and encodings
- Edge case directories (empty, permission-restricted, etc.)

## Expected Deliverables

1. **Enhanced Test Suite** - Comprehensive test coverage for MVP components
2. **Test Results Report** - Detailed results of all test executions
3. **Performance Benchmarks** - Performance baselines for different project sizes
4. **Security Validation Report** - Confirmation of security boundaries
5. **Recommendations** - Improvements needed for production readiness

## Risk Assessment

### High Risk
- **Ollama Dependency**: Tests requiring AI model may fail if Ollama unavailable
- **File System Permissions**: Tests may behave differently across environments

### Medium Risk
- **Large Project Testing**: May require significant test data preparation
- **Performance Variability**: Results may vary across different hardware

### Low Risk
- **Input Validation**: Well-defined test cases with predictable outcomes
- **Unit Testing**: Isolated components with minimal dependencies

This test plan provides comprehensive coverage of the MVP functionality while acknowledging the current project scope and limitations.