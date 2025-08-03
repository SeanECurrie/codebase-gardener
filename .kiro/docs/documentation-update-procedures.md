# Documentation Update Procedures

## Overview

This document establishes the procedures for maintaining and updating documentation throughout the Codebase Gardener development process. These procedures ensure that documentation remains current, accurate, and useful as the system evolves.

## Documentation Types and Update Responsibilities

### 1. Memory Files (`.kiro/memory/`)
**Purpose**: Document implementation decisions, lessons learned, and patterns established during task execution.

**Update Responsibility**: Task implementer
**Update Frequency**: During task execution
**Review Required**: No (but encouraged for complex tasks)

**Procedure**:
1. Create memory file at task start using template
2. Update throughout implementation with decisions and challenges
3. Complete final update with lessons learned before task completion
4. Commit memory file with implementation code

### 2. API Documentation (Component APIs)
**Purpose**: Document public interfaces, classes, and functions for component users.

**Update Responsibility**: Component implementer
**Update Frequency**: When public APIs change
**Review Required**: Yes, during code review

**Procedure**:
1. Use API documentation template for new components
2. Update docstrings in code (primary source of truth)
3. Generate/update API documentation from docstrings
4. Include examples and usage patterns
5. Update integration examples when interfaces change

### 3. Component Documentation (`.kiro/docs/components/`)
**Purpose**: High-level component design, architecture, and integration information.

**Update Responsibility**: Component implementer
**Update Frequency**: When component design changes significantly
**Review Required**: Yes, for architectural changes

**Procedure**:
1. Create component documentation using template
2. Update when architectural decisions change
3. Include performance characteristics and benchmarks
4. Document integration points and dependencies
5. Update troubleshooting section based on common issues

### 4. Steering Documents (`.kiro/steering/`)
**Purpose**: Establish and maintain development principles, patterns, and architectural context.

**Update Responsibility**: Any developer when patterns change
**Update Frequency**: When new patterns are established or existing ones change
**Review Required**: Yes, team consensus required

**Procedure**:
1. Propose changes through pull request
2. Discuss architectural implications
3. Update affected steering documents
4. Notify team of pattern changes
5. Update related documentation to reflect new patterns

### 5. System Documentation (`.kiro/docs/`)
**Purpose**: Overall system architecture, setup guides, and operational procedures.

**Update Responsibility**: System architect or designated maintainer
**Update Frequency**: When system architecture changes
**Review Required**: Yes, for significant changes

**Procedure**:
1. Update architecture diagrams when system structure changes
2. Revise setup procedures when dependencies change
3. Update troubleshooting guides based on user feedback
4. Maintain testing guidelines as testing practices evolve

## Task-Integrated Documentation Workflow

### Pre-Task Documentation Setup
```bash
# 1. Create memory file from template
cp .kiro/docs/templates/memory-file-template.md .kiro/memory/[component]_task[N].md

# 2. Fill in task overview section
# Edit .kiro/memory/[component]_task[N].md with task details

# 3. Review relevant existing documentation
# Read related memory files, component docs, and steering documents
```

### During-Task Documentation Updates
```bash
# 1. Update memory file with decisions and challenges
# Document approach decisions, research findings, implementation notes

# 2. Update API documentation as interfaces are created
# Add docstrings to new classes and functions
# Update existing docstrings when interfaces change

# 3. Note patterns for potential steering document updates
# Document new patterns that might be reusable
# Note deviations from existing patterns
```

### Post-Task Documentation Completion
```bash
# 1. Complete memory file with lessons learned
# Document what worked well, what would be done differently
# Include recommendations for future tasks

# 2. Update component documentation if significant changes
# Update architecture diagrams if component structure changed
# Update integration examples if interfaces changed

# 3. Propose steering document updates if new patterns established
# Create pull request for steering document changes
# Include rationale for pattern changes

# 4. Commit all documentation updates
git add .kiro/memory/[component]_task[N].md
git add docs/components/[component].md  # if updated
git commit -m "docs: update documentation for task [N] implementation"
```

## Documentation Quality Standards

### Memory Files
- **Completeness**: All template sections filled with relevant information
- **Clarity**: Decisions and rationale clearly explained
- **Actionability**: Future developers can understand and build upon the work
- **Accuracy**: Information reflects actual implementation decisions

**Quality Checklist**:
- [ ] Task overview complete with dates and developer info
- [ ] Approach decision documented with alternatives considered
- [ ] Research findings include MCP tool usage and sources
- [ ] Implementation challenges and solutions documented
- [ ] Integration points clearly described
- [ ] Testing strategy and results included
- [ ] Lessons learned section provides actionable insights
- [ ] Next task considerations help future implementers

### API Documentation
- **Completeness**: All public APIs documented with examples
- **Accuracy**: Documentation matches actual implementation
- **Usability**: Examples are practical and runnable
- **Consistency**: Follows established documentation patterns

**Quality Checklist**:
- [ ] All public classes and functions have docstrings
- [ ] Parameter types and return types specified
- [ ] Exceptions that can be raised are documented
- [ ] Usage examples are provided and tested
- [ ] Performance characteristics noted where relevant
- [ ] Integration examples show real-world usage

### Component Documentation
- **Architecture**: Component's role and relationships clearly explained
- **Design Rationale**: Architectural decisions and trade-offs documented
- **Integration**: How component fits into overall system
- **Operations**: Configuration, monitoring, and troubleshooting information

**Quality Checklist**:
- [ ] Component purpose and scope clearly defined
- [ ] Architectural decisions and trade-offs explained
- [ ] Integration points and dependencies documented
- [ ] Configuration options and examples provided
- [ ] Performance characteristics and benchmarks included
- [ ] Troubleshooting section addresses common issues

## Documentation Review Process

### Memory File Reviews
**When**: Optional, but recommended for complex tasks
**Who**: Peer developer or team lead
**Focus**: Completeness, clarity, and lessons learned quality

**Review Checklist**:
- Are the architectural decisions well-reasoned?
- Are the lessons learned actionable for future tasks?
- Is the integration information sufficient for dependent tasks?
- Are performance considerations documented?

### API Documentation Reviews
**When**: Required for all public API changes
**Who**: Component users or team lead
**Focus**: Accuracy, completeness, and usability

**Review Process**:
1. Verify documentation matches implementation
2. Test provided examples
3. Check for missing edge cases or error conditions
4. Validate integration examples work correctly

### Steering Document Reviews
**When**: Required for all steering document changes
**Who**: Full development team
**Focus**: Architectural consistency and team consensus

**Review Process**:
1. Discuss architectural implications
2. Ensure consistency with existing patterns
3. Validate against project principles
4. Achieve team consensus before merging

## Documentation Maintenance

### Regular Maintenance Tasks

#### Weekly
- Review memory files from completed tasks
- Identify patterns that should be added to steering documents
- Update troubleshooting guides with new issues encountered

#### Monthly
- Review API documentation for accuracy
- Update performance benchmarks in component documentation
- Consolidate lessons learned into best practices

#### Per Release
- Update system architecture documentation
- Review and update setup procedures
- Validate all examples and code snippets
- Update version information in templates

### Documentation Debt Management

#### Identifying Documentation Debt
- APIs without documentation
- Outdated examples that no longer work
- Missing integration documentation
- Incomplete troubleshooting guides

#### Addressing Documentation Debt
```bash
# 1. Create documentation debt tracking issue
# Document what needs to be updated and why

# 2. Prioritize based on user impact
# Focus on frequently used components first

# 3. Assign ownership
# Each component should have a documentation owner

# 4. Set deadlines
# Include documentation updates in sprint planning
```

## Automation and Tools

### Documentation Generation
```bash
# Generate API documentation from docstrings
python scripts/generate_api_docs.py

# Validate documentation links and examples
python scripts/validate_docs.py

# Check for outdated documentation
python scripts/check_doc_freshness.py
```

### Documentation Testing
```python
# Test code examples in documentation
def test_documentation_examples():
    """Ensure all code examples in docs actually work."""
    for doc_file in find_documentation_files():
        examples = extract_code_examples(doc_file)
        for example in examples:
            try:
                exec(example)
            except Exception as e:
                pytest.fail(f"Example in {doc_file} failed: {e}")
```

### Documentation Metrics
- **Coverage**: Percentage of public APIs with documentation
- **Freshness**: Age of documentation relative to code changes
- **Quality**: Number of broken examples or outdated information
- **Usage**: Which documentation is accessed most frequently

## Integration with Development Tools

### IDE Integration
```json
// VS Code settings for documentation
{
    "python.linting.enabled": true,
    "python.linting.pydocstyleEnabled": true,
    "autoDocstring.docstringFormat": "google",
    "autoDocstring.generateDocstringOnEnter": true
}
```

### Git Hooks
```bash
# Pre-commit hook to check documentation
#!/bin/bash
# Check that new public APIs have documentation
python scripts/check_api_documentation.py

# Validate memory file completeness for completed tasks
python scripts/validate_memory_files.py
```

### CI/CD Integration
```yaml
# GitHub Actions workflow for documentation
name: Documentation Check
on: [push, pull_request]

jobs:
  docs:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Check API Documentation
      run: python scripts/check_api_docs.py
    - name: Validate Examples
      run: python scripts/test_doc_examples.py
    - name: Check Documentation Freshness
      run: python scripts/check_doc_freshness.py
```

## Documentation Templates Usage

### When to Use Each Template

#### Memory File Template
- **Use for**: Every task in the implementation plan
- **Customize**: Add task-specific sections as needed
- **Skip sections**: Only if genuinely not applicable

#### API Documentation Template
- **Use for**: New components with public APIs
- **Customize**: Add component-specific sections
- **Update**: When APIs change significantly

#### Component Documentation Template
- **Use for**: Major components with complex architecture
- **Customize**: Focus on component-specific concerns
- **Update**: When architectural decisions change

### Template Customization Guidelines
1. **Add sections** that are specific to your component
2. **Remove sections** only if they're truly not applicable
3. **Modify examples** to be relevant to your use case
4. **Update version info** and dates appropriately
5. **Maintain consistency** with established patterns

## Documentation Best Practices

### Writing Guidelines
- **Be specific**: Avoid vague descriptions
- **Include examples**: Show don't just tell
- **Consider the audience**: Write for the intended users
- **Keep it current**: Update when code changes
- **Link related information**: Connect related concepts

### Code Examples
- **Make them runnable**: Examples should work as-is
- **Keep them simple**: Focus on the key concept
- **Include error handling**: Show proper error handling patterns
- **Use realistic data**: Avoid foo/bar examples when possible
- **Test them regularly**: Ensure examples don't break

### Maintenance
- **Review regularly**: Schedule periodic documentation reviews
- **Update proactively**: Don't wait for user complaints
- **Track metrics**: Monitor documentation usage and quality
- **Gather feedback**: Ask users what documentation they need
- **Iterate**: Continuously improve based on feedback

---

**Last Updated**: [Date]
**Version**: 1.0
**Owner**: Development Team