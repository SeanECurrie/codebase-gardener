# Task [N]: [Component Name] - [Date]

## Task Overview
- **Task Number**: [N]
- **Component**: [Component Name]
- **Date Started**: [YYYY-MM-DD]
- **Date Completed**: [YYYY-MM-DD]
- **Developer**: [Name]
- **Branch**: [feat/branch-name]

## Approach Decision

### Problem Statement
[Describe the specific problem this task addresses]

### Alternatives Considered
1. **Option 1**: [Description]
   - Pros: [List advantages]
   - Cons: [List disadvantages]
   - Decision: [Chosen/Rejected and why]

2. **Option 2**: [Description]
   - Pros: [List advantages]
   - Cons: [List disadvantages]
   - Decision: [Chosen/Rejected and why]

### Chosen Approach
[Detailed description of the selected approach and rationale]

### Key Architectural Decisions
- **Decision 1**: [Description and rationale]
- **Decision 2**: [Description and rationale]
- **Decision 3**: [Description and rationale]

## Research Findings

### MCP Tools Used (MANDATORY - Use in this order)

- **Sequential Thinking**: [Problem breakdown and architectural decisions]
  - Thoughts: [Key decision points analyzed]
  - Alternatives Evaluated: [Options considered systematically]
  - Applied: [How structured thinking influenced implementation]

- **Context7**: [Specific library documentation retrieved]
  - Library ID: [Context7 library identifier used]
  - Topic: [Specific documentation topic]
  - Key Findings: [Important API details, configuration options, best practices]
  - Applied: [How documentation guided implementation]

- **Bright Data**: [Real-world code examples found]
  - Repository/URL: [Source of examples]
  - Key Patterns: [Implementation patterns discovered]
  - Applied: [How real-world examples influenced design]

- **Basic Memory**: [Context maintained from previous tasks]
  - Previous Patterns: [Patterns referenced from earlier tasks]
  - Integration Points: [How previous work influenced current task]
  - Applied: [How memory context guided decisions]

### Documentation Sources
- [Source 1]: [URL/Reference] - [Key insights]
- [Source 2]: [URL/Reference] - [Key insights]
- [Source 3]: [URL/Reference] - [Key insights]

### Best Practices Discovered
- [Practice 1]: [Description and source]
- [Practice 2]: [Description and source]
- [Practice 3]: [Description and source]

## Implementation Notes

### Specific Challenges Encountered
1. **Challenge 1**: [Description]
   - **Solution**: [How it was resolved]
   - **Time Impact**: [How much time it took]
   - **Learning**: [What was learned]

2. **Challenge 2**: [Description]
   - **Solution**: [How it was resolved]
   - **Time Impact**: [How much time it took]
   - **Learning**: [What was learned]

### Code Patterns Established
```python
# Pattern 1: [Description]
class ExamplePattern:
    def __init__(self, param: Type):
        self.param = param

    def method(self) -> ReturnType:
        # Implementation pattern
        pass
```

```python
# Pattern 2: [Description]
def example_function(input_param: Type) -> ReturnType:
    """
    Example of established pattern
    """
    # Implementation pattern
    pass
```

### Configuration Decisions
- **Setting 1**: `VALUE` - [Rationale]
- **Setting 2**: `VALUE` - [Rationale]
- **Setting 3**: `VALUE` - [Rationale]

### Dependencies Added
- **Package 1**: `version` - [Purpose and rationale]
- **Package 2**: `version` - [Purpose and rationale]

## Integration Points

### How This Component Connects to Others
- **Component A**: [Description of relationship and data flow]
- **Component B**: [Description of relationship and data flow]
- **Component C**: [Description of relationship and data flow]

### Dependencies and Interfaces
```python
# Input interfaces
class InputInterface:
    def method(self, param: Type) -> Type:
        pass

# Output interfaces
class OutputInterface:
    def method(self, param: Type) -> Type:
        pass
```

### Data Flow Considerations
1. **Input Data**: [Format, source, validation]
2. **Processing**: [Transformation steps]
3. **Output Data**: [Format, destination, validation]

### Error Handling Integration
- **Error Types**: [List of custom exceptions]
- **Propagation**: [How errors are passed to other components]
- **Recovery**: [Fallback mechanisms]

## Testing Strategy

### Test Cases Implemented
1. **Unit Tests**:
   - `test_[function_name]_success`: [Description]
   - `test_[function_name]_error_handling`: [Description]
   - `test_[function_name]_edge_cases`: [Description]

2. **Integration Tests**:
   - `test_[component]_integration`: [Description]
   - `test_[component]_error_scenarios`: [Description]

3. **Performance Tests**:
   - `test_[component]_performance`: [Description]
   - `test_[component]_memory_usage`: [Description]

### Edge Cases Discovered
- **Edge Case 1**: [Description and handling]
- **Edge Case 2**: [Description and handling]
- **Edge Case 3**: [Description and handling]

### Performance Benchmarks
- **Metric 1**: [Value] - [Context and target]
- **Metric 2**: [Value] - [Context and target]
- **Metric 3**: [Value] - [Context and target]

### Mock Strategies Used
```python
# Mock example
@pytest.fixture
def mock_dependency():
    with patch('module.Dependency') as mock:
        mock.return_value.method.return_value = expected_value
        yield mock
```

## Lessons Learned

### What Worked Well
- **Approach 1**: [Description and why it was effective]
- **Tool 1**: [Description and benefits]
- **Pattern 1**: [Description and advantages]

### What Would Be Done Differently
- **Issue 1**: [Description and better approach]
- **Issue 2**: [Description and better approach]
- **Issue 3**: [Description and better approach]

### Patterns to Reuse in Future Tasks
- **Pattern 1**: [Description and when to use]
- **Pattern 2**: [Description and when to use]
- **Pattern 3**: [Description and when to use]

### Anti-Patterns to Avoid
- **Anti-Pattern 1**: [Description and why to avoid]
- **Anti-Pattern 2**: [Description and why to avoid]

## Performance Considerations

### Mac Mini M4 Specific Optimizations
- **Memory Usage**: [Current usage and optimizations]
- **CPU Utilization**: [Performance characteristics]
- **Thermal Management**: [Heat generation and mitigation]

### Resource Usage Metrics
- **Memory**: [Peak usage during operation]
- **CPU**: [Average and peak CPU usage]
- **Disk I/O**: [Read/write patterns and optimization]
- **Network**: [If applicable, network usage patterns]

## Next Task Considerations

### What the Next Task Should Know
- **Key Interfaces**: [Important interfaces to use]
- **Established Patterns**: [Patterns that should be followed]
- **Configuration**: [Settings that affect next task]
- **Dependencies**: [New dependencies available]

### Potential Integration Challenges
- **Challenge 1**: [Description and suggested approach]
- **Challenge 2**: [Description and suggested approach]
- **Challenge 3**: [Description and suggested approach]

### Recommended Approaches for Future Tasks
- **Recommendation 1**: [Description and rationale]
- **Recommendation 2**: [Description and rationale]
- **Recommendation 3**: [Description and rationale]

### Technical Debt Created
- **Debt 1**: [Description and plan to address]
- **Debt 2**: [Description and plan to address]

## References to Previous Tasks
- **Task [N-1] ([Component])**: [How it was used/referenced]
- **Task [N-2] ([Component])**: [How it was used/referenced]
- **Task [N-3] ([Component])**: [How it was used/referenced]

## Gap Closure Analysis
- **Gaps from Previous Task**: [List gaps from previous task that were relevant to current task]
- **Gap Validation Phase**: [How previous gaps were addressed in current task scope]
- **Gap Closure Phase**: [Quick wins implemented before task completion]
- **Remaining Gaps**: [Gaps identified in current task for future closure]
- **Gap Closure Rate**: [Percentage of previous gaps closed in this task]

## Task Completion Test Reference
- **Test Log Entry**: See `.kiro/docs/task_completion_test_log.md` Task [N] entry
- **Capabilities Proven**: [Summary of what the completion test validated]
- **Integration Validated**: [Which component integrations were tested]
- **Gaps Identified**: [New gaps discovered during completion testing]
- **Gap Closure Recommendations**: [Specific gaps that could be quick wins for next task]
- **Gaps for Next Task**: [What the next task should address based on test results]

**Reference `.kiro/docs/gap-closure-criteria.md` for gap management framework and decision criteria.**

## Steering Document Updates
- **Updated**: [List of steering documents modified]
- **New Patterns**: [New patterns added to steering documents]
- **Deprecated**: [Old patterns that are no longer recommended]

## Commit Information
- **Branch**: [feat/branch-name]
- **Commits**: [List of commit hashes and messages]
- **Files Modified**: [List of files created/modified]
- **Tests Added**: [List of test files created]

---

**Template Version**: 1.0
**Last Updated**: [Date]
