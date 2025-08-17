---
inclusion: always
---

# Task Execution Framework - Comprehensive Template

## Overview

This framework ensures continuity between tasks, proper validation of previous work, and systematic Git/GitHub integration. Every task must follow this exact structure to maintain quality and traceability.

## Pre-Task Phase (MANDATORY)

### 1. Previous Task Validation
**BEFORE starting any task, ALWAYS check what was done in the previous task:**

```markdown
## Previous Task Validation (MANDATORY FIRST STEP)

### Check Previous Task Completion
- [ ] Read previous task's memory file: `.kiro/memory/[component]_task[N-1].md`
- [ ] Verify previous task's completion criteria were met
- [ ] Check `.kiro/docs/task_completion_test_log.md` for gaps or issues
- [ ] Review any steering document updates from previous task

### Validate Previous Task Outputs
- [ ] Test that previous task's code actually works
- [ ] Verify integration points are functional
- [ ] Check that documented interfaces match implementation
- [ ] Confirm no regressions were introduced

### Gap Analysis from Previous Task
- [ ] Review `.kiro/docs/gap-closure-criteria.md` for any gaps from previous task
- [ ] Apply Gap Validation Phase: identify gaps that align with current task scope
- [ ] Plan Gap Closure Phase: address quick wins (<30min, low risk, improves validation)

### Previous Task Integration Points
- [ ] Document how current task builds on previous work
- [ ] Identify any assumptions from previous task that need validation
- [ ] Plan how to leverage previous task's established patterns
```

### 2. Foundation Reading (MANDATORY)
**Read these in EXACT order before any implementation:**

1. **Core Principles**: Read `.kiro/steering/core-development-principles.md` completely
2. **Task Guidelines**: Read `.kiro/steering/Task Guidelines.md` completely
3. **Previous Task Memory**: Read `.kiro/memory/[component]_task[N-1].md` completely
4. **Gap Closure Framework**: Read `.kiro/docs/gap-closure-criteria.md` completely

### 3. MCP Tools Research (MANDATORY - Use in this order)

**ALWAYS use these MCP tools in this specific order:**

1. **Sequential Thinking FIRST** - Break down complex problems and architectural decisions
2. **Context7 SECOND** - Get precise library documentation and API references
3. **Bright Data THIRD** - Find real-world code examples and implementation patterns
4. **Basic Memory FOURTH** - Maintain context and patterns across tasks

**Document each tool usage:**
```markdown
### MCP Tools Used (MANDATORY - Use in this order)

- **Sequential Thinking**: [Problem breakdown and architectural decisions]
  - Thoughts: [Number of thoughts, key decision points analyzed]
  - Alternatives Evaluated: [List of approaches considered]
  - Applied: [Chosen approach and rationale]

- **Context7**: [Library documentation retrieved]
  - Library ID: [Context7-compatible library ID]
  - Topic: [Specific topic researched]
  - Key Findings: [Important documentation points]
  - Applied: [How findings were used in implementation]

- **Bright Data**: [Real-world examples found]
  - Repository/URL: [Source of examples]
  - Key Patterns: [Important patterns discovered]
  - Applied: [How patterns were adapted for project]

- **Basic Memory**: [Previous patterns referenced]
  - Previous Patterns: [Patterns from previous tasks]
  - Integration Points: [How current task connects to previous work]
  - Applied: [How established patterns were used]
```

## During Task Phase

### 4. Implementation Approach
```markdown
## Approach Decision

### Problem Statement
[Clear statement of what needs to be implemented and why]

### Gap Validation Phase Analysis
[From previous task completion test log, identify gaps that align with current scope]
- ⚠️ **[Gap Type]**: [Description] → **[Action]**: [How current task addresses this]

### Alternatives Considered
1. **[Approach 1]**:
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Decision: [Chosen/Rejected] - [Rationale]

2. **[Approach 2]**:
   - Pros: [Benefits]
   - Cons: [Drawbacks]
   - Decision: [Chosen/Rejected] - [Rationale]

### Chosen Approach
[Detailed description of chosen implementation approach]

### Key Architectural Decisions
- **[Decision 1]**: [Rationale]
- **[Decision 2]**: [Rationale]
```

### 5. Implementation Tracking
```markdown
## Implementation Notes

### Specific Challenges Encountered
1. **Challenge 1**: [Description]
   - **Solution**: [How it was resolved]
   - **Time Impact**: [Time spent]
   - **Learning**: [Key insight gained]

### Code Patterns Established
```python
# Pattern 1: [Description]
[Code example]
```

### Configuration Decisions
- **[Setting 1]**: [Value] - [Rationale]
- **[Setting 2]**: [Value] - [Rationale]

### Dependencies Added
- **[Dependency]**: [Version] - [Purpose]
```

### 6. Task Status Management
**Use taskStatus tool at key points:**
- Mark `in_progress` when starting implementation
- Mark `completed` only when ALL completion criteria are met

## Post-Task Phase (MANDATORY)

### 7. Gap Closure Phase
**BEFORE marking task complete, address gaps from current task:**

```markdown
## Gap Closure Phase (MANDATORY)

### Quick Wins Identified (<30min, low risk, improves validation)
- [ ] **[Gap 1]**: [Description] → [Action taken]
- [ ] **[Gap 2]**: [Description] → [Action taken]

### Next Task Gaps (aligns with scope, requires research)
- [ ] **[Gap 1]**: [Description] → [Documented for next task]

### Deferred Gaps (out of scope, major changes, low priority)
- [ ] **[Gap 1]**: [Description] → [Rationale for deferring]

### Gap Closure Rate
- Quick Wins Closed: [X]/[Y] ([Z]%)
- Target: >60% closure rate within 2 tasks of identification
```

### 8. Integration and Testing
```markdown
## Integration Points

### How This Component Connects to Others
- **[Component 1]**: [Integration description]
- **[Component 2]**: [Integration description]

### Dependencies and Interfaces
```python
# Input interfaces
[Code showing what this component expects]

# Output interfaces
[Code showing what this component provides]
```

### Data Flow Considerations
1. **Input Data**: [Description]
2. **Processing**: [Description]
3. **Output Data**: [Description]

## Testing Strategy

### Test Cases Implemented
[List of test cases with coverage]

### Edge Cases Discovered
[Edge cases found during implementation]

### Performance Benchmarks
[Performance metrics if applicable]
```

### 9. Memory File Creation (MANDATORY)
**Create comprehensive memory file:**

```markdown
# Task [N]: [Component Name] - [Date]

[Use complete template from ollama_client_task9.md as reference]

## References to Previous Tasks
- **Task [N-1] ([Component])**: [How previous task's work was used]
- **Task [N-2] ([Component])**: [Any patterns or decisions referenced]

## Next Task Considerations

### What the Next Task Should Know
- **[Key Point 1]**: [Information for next task]
- **[Key Point 2]**: [Information for next task]

### Potential Integration Challenges
- **[Challenge 1]**: [Description and suggested approach]
- **[Challenge 2]**: [Description and suggested approach]

### Recommended Approaches for Future Tasks
- **[Recommendation 1]**: [Rationale]
- **[Recommendation 2]**: [Rationale]
```

### 10. Git and GitHub Integration (MANDATORY)

**After successful task completion:**

```bash
# 1. Create feature branch
git checkout -b feat/[component-name]-task[N]

# 2. Add all changes
git add .

# 3. Commit with conventional format
git commit -m "feat([component]): implement [task description]

- [Key change 1]
- [Key change 2]
- [Key change 3]

Closes #[issue-number] if applicable
Refs: Task [N] - [Component Name]"

# 4. Push to GitHub
git push origin feat/[component-name]-task[N]

# 5. Create Pull Request (if applicable)
# Include:
# - Task completion summary
# - Key changes made
# - Testing performed
# - Integration points
# - Next task considerations
```

### 11. Documentation Updates (MANDATORY)

**Update these files after each task:**

```markdown
## Documentation Updates Required

### CRITICAL: Tasks.md Update (ALWAYS FIRST)
- [ ] **Mark task as completed in `.kiro/specs/enhanced-codebase-auditor/tasks.md`**:
  - Change `- [ ] N. Task Name` to `- [x] N. Task Name **COMPLETED YYYY-MM-DD**`
  - Add completion checkmarks to all Pre-Task, Implementation, Post-Task phases
  - Document key findings and validation results directly in task
  - List specific gaps and quick wins for next task
  - Update requirement completion status

### Task Completion Log
- [ ] Update `.kiro/docs/task_completion_test_log.md` with:
  - Task completion status
  - Key capabilities added
  - Integration test results
  - Gaps identified for next task

### API Documentation (if applicable)
- [ ] Update `.kiro/docs/api-reference.md`
- [ ] Update component documentation in `.kiro/docs/components/`

### Steering Documents (if needed)
- [ ] Update relevant steering documents with new patterns
- [ ] Add any new architectural decisions to steering files

### README Updates (if applicable)
- [ ] Update main README.md with new capabilities
- [ ] Update installation or usage instructions
```

## Task Completion Criteria (MANDATORY)

**A task is ONLY complete when ALL of these are met:**

### Functional Criteria
1. **Real Working Code**: Code works with actual systems/models
2. **Real Data**: Tested with actual data/codebases
3. **Real User Interaction**: Can be used through actual interface
4. **User Validation**: User can see and verify it works as intended
5. **Actionable Usage**: Clear explanation of how user uses the new functionality

### Process Criteria
6. **Previous Task Validated**: Previous task's outputs were verified and integrated
7. **MCP Tools Used**: All four MCP tools used in correct order with documentation (or documented why unavailable)
8. **Gap Closure Applied**: Gap Validation and Gap Closure phases completed
9. **Memory File Created**: Comprehensive memory file following template
10. **Git Integration**: Changes committed and pushed with proper messages
11. **Tasks.md Updated**: Task marked completed with checkmarks and findings in `.kiro/specs/enhanced-codebase-auditor/tasks.md`
12. **Documentation Updated**: All required documentation updated
13. **Next Task Prepared**: Clear handoff information for next task

### Quality Criteria
14. **Integration Tested**: Component works with existing system
15. **Error Handling**: Proper error handling and logging implemented
16. **Performance Acceptable**: Meets performance requirements for use case
17. **Code Quality**: Follows established patterns and conventions

## Failure Recovery

**If any completion criteria are not met:**

1. **Identify Missing Criteria**: Document which criteria failed
2. **Root Cause Analysis**: Understand why criteria weren't met
3. **Remediation Plan**: Create specific plan to address failures
4. **Re-execution**: Complete missing work before marking task complete
5. **Validation**: Verify all criteria are now met

## Template Usage

**For each new task:**

1. Copy this framework template
2. Fill in task-specific details
3. Follow each phase in order
4. Don't skip any mandatory steps
5. Verify all completion criteria before finishing

This framework ensures:
- ✅ Continuity between tasks
- ✅ Proper validation of previous work
- ✅ Systematic research and decision making
- ✅ Comprehensive documentation
- ✅ Git/GitHub integration
- ✅ Quality assurance
- ✅ Clear handoff to next task
