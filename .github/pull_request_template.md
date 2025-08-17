# Pull Request Checklist

## Checks
- [ ] Branch from development (feat/task-\*)
- [ ] PR base=development
- [ ] Tests/docs updated
- [ ] Followed CLAUDE.md → Task Loop (Start → Finish)

## Task Information
- **Task Number**: [N]
- **Component**: [component-name]
- **Requirements Addressed**: [list requirement numbers]

## Changes Made
- [Change 1]: [Description]
- [Change 2]: [Description]
- [Change 3]: [Description]

## Testing
- [ ] Core tests pass: `pytest -q tests/test_single_file_auditor.py tests/test_project_structure.py`
- [ ] Code quality: `ruff check --fix && ruff format`
- [ ] Integration testing completed
- [ ] No regressions in existing functionality

## Documentation
- [ ] Memory file created: `.kiro/memory/[component]_task[N].md`
- [ ] Tasks.md updated with completion status
- [ ] Task completion test log updated

## Integration Points
[Describe how this change integrates with existing system]

## Next Task Considerations
[Any notes for the next task or future work]
