---
inclusion: always
---

# Development Philosophy: Pragmatic POC Approach

## Project Context
- Solo developer working on personal/small projects
- NOT enterprise-level - prioritize shipping over perfect architecture
- Default assumption: everything is a Proof of Concept unless explicitly stated otherwise

## Core Principles

### Simplicity First
- Choose the most obvious solution that works
- Prefer direct implementations over abstractions
- Single files over multiple files when reasonable
- Hardcode sensible defaults instead of building configuration systems

### Shipping Over Perfection
- Start with working code, refine only when necessary
- Don't overthink solutions - implement and iterate
- Avoid frameworks unless absolutely required
- Focus on functionality over architectural purity

## Implementation Guidelines

### What TO Do
- **Start simple**: Begin with the most straightforward approach
- **Hardcode defaults**: Use reasonable hardcoded values instead of complex config
- **Consolidate files**: Keep related functionality together when it makes sense
- **Ship early**: Get working versions deployed quickly for feedback

### What NOT To Do
- **No premature abstraction**: Don't add layers until you actually need them
- **No future-proofing**: Don't build for imaginary requirements
- **No over-engineering**: Avoid complex error handling for unlikely edge cases
- **No pattern obsession**: Don't force design patterns where simple code suffices
- **No premature optimization**: Don't optimize until you have actual performance problems
- **No configuration overkill**: Don't make everything configurable

## Code Style Preferences
- Favor readability over cleverness
- Use descriptive variable names even if they're longer
- Keep functions small and focused
- Comment the "why" not the "what"
- Prefer explicit over implicit when it aids understanding

## Decision Framework
When facing implementation choices, ask:
1. What's the simplest thing that could work?
2. Can I ship this today?
3. Will this actually be used or am I building for "someday"?
4. Is this abstraction solving a real problem I have right now?

Choose the path that gets you to working software fastest.

## Gap Closure Integration with Pragmatic Approach

**IMPORTANT**: Our dynamic gap closure framework (see `.kiro/docs/gap-closure-criteria.md`) aligns perfectly with the pragmatic POC approach:

### Gap Closure Decision Framework
- **Quick Win Criteria** aligns with "ship early" - close gaps that can be done in <30 minutes
- **Next Task Criteria** aligns with "don't build for someday" - only address gaps that fit next task's actual scope
- **Defer Criteria** aligns with "avoid over-engineering" - don't fix gaps that require major architectural changes

### Pragmatic Gap Management
- **Focus on functionality**: Close gaps that improve actual functionality, not theoretical completeness
- **Ship working versions**: Use Gap Closure Phase to ship more complete versions without scope creep
- **Iterate based on real needs**: Use Gap Validation Phase to address gaps when they become relevant

**See `.kiro/docs/task_completion_test_log.md` for current system capabilities and `.kiro/docs/gap-closure-criteria.md` for detailed framework.**
