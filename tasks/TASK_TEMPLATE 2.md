# Task N: [Component Name]

## Overview
[Brief description of the task and its goals]

## Requirements
- [Requirement 1]
- [Requirement 2]
- [Requirement 3]
- _Requirements: [Reference numbers from specs]_

## Implementation Steps
- [Step 1]: [Description]
- [Step 2]: [Description]
- [Step 3]: [Description]

## Acceptance Criteria
- [ ] [Criteria 1]
- [ ] [Criteria 2]
- [ ] [Criteria 3]

## Execution Block (Agent MUST follow)
Read CLAUDE.md:
- Branching: Branching & PR Policy (Authoritative)
- Steps: Task Loop (Start → Finish)
- Edits: Edit Rules (Diff-Only, No Rewrites)

Start
- From development:
```bash
git checkout development && git pull
git checkout -b feat/component-taskN development
```
- Summarize context (branch, task #) before edits.

Finish
- Tests/docs updated.
- Open PR → base=development; merge after validation.
- Post a 5-bullet report per Reporting Format.
