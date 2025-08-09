# Pre-Task Comprehensive Review Template

## MANDATORY: Complete this review BEFORE starting any task implementation

### 1. Previous Tasks Integration Review
**Read and understand ALL completed tasks:**
- [ ] Read ALL memory files in `.kiro/memory/` to understand what has been built
- [ ] Identify interfaces, data structures, and patterns established by previous tasks
- [ ] Note any integration points that this task must respect
- [ ] Check for any assumptions or dependencies from previous implementations

**Key Questions:**
- What interfaces do previous tasks expect this task to provide?
- What data structures/formats must this task consume or produce?
- Are there established patterns this task should follow?
- What integration points were mentioned in previous memory files?

### 2. Project Goals and Architecture Review
**Read and understand the project vision:**
- [ ] Read `.kiro/specs/codebase-gardener-mvp/requirements.md` - understand user stories and acceptance criteria
- [ ] Read `.kiro/specs/codebase-gardener-mvp/design.md` - understand system architecture and data flow
- [ ] Read `.kiro/steering/codebase-gardener-principles.md` - understand core principles and success metrics
- [ ] Read `.kiro/steering/ai-ml-architecture-context.md` - understand technical architecture decisions

**Key Questions:**
- How does this task contribute to the overall project vision?
- What are the specific requirements this task must fulfill?
- How does this task fit into the larger system architecture?
- What are the performance/quality constraints for this task?

### 3. Forward Compatibility Review
**Check upcoming tasks for expected interfaces:**
- [ ] Read the next 3-5 tasks in `tasks.md` to understand what they expect from this task
- [ ] Identify any interfaces, data formats, or patterns that future tasks will need
- [ ] Note any dependencies that future tasks have on this task's output
- [ ] Check if this task needs to prepare for future integrations

**Key Questions:**
- What will the next tasks expect this task to provide?
- Are there any interfaces this task should expose for future use?
- What data formats or structures should this task output for downstream tasks?
- Are there any extensibility requirements for future features?

### 4. Development Standards Review
**Ensure consistency with established patterns:**
- [ ] Read `.kiro/steering/development-best-practices.md` - understand coding standards and MCP tool usage
- [ ] Review established error handling patterns from previous tasks
- [ ] Check configuration management patterns from previous tasks
- [ ] Understand testing strategies and quality standards

**Key Questions:**
- What coding patterns and standards should this task follow?
- How should this task integrate with the error handling framework?
- What configuration management approach should this task use?
- What testing approach and quality standards should this task meet?

### 5. Integration Validation Plan
**Plan how to validate this task works with the existing system:**
- [ ] Identify what components this task will integrate with
- [ ] Plan integration tests that validate end-to-end functionality
- [ ] Define success criteria for integration validation
- [ ] Plan performance benchmarks and quality metrics

**Key Questions:**
- How will I validate this task works with existing components?
- What integration tests should I create?
- What are the performance and quality requirements?
- How will I know this task is truly complete and integrated?

## Pre-Task Review Completion Checklist
- [ ] All previous memory files read and understood
- [ ] Requirements and design documents reviewed
- [ ] Steering documents and principles understood
- [ ] Forward compatibility with future tasks considered
- [ ] Development standards and patterns identified
- [ ] Integration validation plan created
- [ ] Ready to implement with full context and understanding

**ONLY PROCEED TO IMPLEMENTATION AFTER COMPLETING THIS ENTIRE REVIEW**
