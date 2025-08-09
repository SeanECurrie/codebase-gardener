# Pre-Task Comprehensive Review for Task 11.1: Project Registry System

## MANDATORY: Complete this review BEFORE starting any task implementation

### 1. Previous Tasks Integration Review
**Read and understand ALL completed tasks:**
- [x] Read ALL memory files in `.kiro/memory/` to understand what has been built
- [x] Identify interfaces, data structures, and patterns established by previous tasks
- [x] Note any integration points that this task must respect
- [x] Check for any assumptions or dependencies from previous implementations

**Key Questions:**
- What interfaces do previous tasks expect this task to provide?
- What data structures/formats must this task consume or produce?
- Are there established patterns this task should follow?
- What integration points were mentioned in previous memory files?

#### Analysis of Previous Tasks:

**Task 1 (Project Structure)**: Established src/codebase_gardener package structure with proper __init__.py files and pyproject.toml configuration. The project registry should follow this modular structure and be placed in the core/ module.

**Task 2 (Configuration/Logging)**: Established Settings class with Pydantic BaseSettings and structured logging with structlog. The project registry must:
- Use `from codebase_gardener.config import settings` for configuration access
- Use `logger = structlog.get_logger(__name__)` for structured logging
- Support CODEBASE_GARDENER_ environment variable prefix

**Task 3 (Directory Setup)**: Established ~/.codebase-gardener/ directory structure with projects/ subdirectory and active_project.json management. The project registry must:
- Use the established projects/ directory for project storage
- Integrate with DirectoryManager for project directory creation
- Follow the established project directory naming patterns (sanitized names)
- Use active_project.json for tracking current project state

**Task 4 (Error Handling)**: Established custom exception hierarchy and retry decorators. The project registry must:
- Use CodebaseGardenerError base class and create specific exceptions (e.g., ProjectRegistryError)
- Apply retry_with_backoff decorators for potentially failing operations
- Provide user-friendly error messages with actionable suggestions

**Task 5 (Tree-sitter Parser)**: Established multi-language code parsing with AST extraction. The project registry should:
- Support language detection for project metadata
- Store language information in project metadata
- Potentially use parser for project analysis during registration

**Task 6 (Preprocessing)**: Established CodeChunk structure and intelligent chunking. The project registry should:
- Track preprocessing status for projects
- Store chunk count and processing statistics
- Support reprocessing when codebases change

**Task 7 (Nomic Embeddings)**: Established embedding generation with caching. The project registry should:
- Track embedding generation status
- Store embedding model version information
- Support re-embedding when models change

**Task 8 (LanceDB Storage)**: Established vector storage with project-specific capabilities. The project registry must:
- Coordinate with VectorStore for project-specific vector stores
- Track vector store status and statistics
- Support vector store cleanup during project removal

**Task 9 (Ollama Client)**: Established local LLM communication. The project registry should:
- Track base model information for projects
- Support model compatibility checking
- Coordinate with Ollama client for model availability

**Task 10 (PEFT Manager)**: Established LoRA adapter management. The project registry must:
- Track LoRA adapter training status and metadata
- Coordinate with PeftManager for adapter lifecycle
- Store adapter performance metrics and training history

### 2. Project Goals and Architecture Review
**Read and understand the project vision:**
- [x] Read `.kiro/specs/codebase-gardener-mvp/requirements.md` - understand user stories and acceptance criteria
- [x] Read `.kiro/specs/codebase-gardener-mvp/design.md` - understand system architecture and data flow
- [x] Read `.kiro/steering/codebase-gardener-principles.md` - understand core principles and success metrics
- [x] Read `.kiro/steering/ai-ml-architecture-context.md` - understand technical architecture decisions

**Key Questions:**
- How does this task contribute to the overall project vision?
- What are the specific requirements this task must fulfill?
- How does this task fit into the larger system architecture?
- What are the performance/quality constraints for this task?

#### Analysis of Project Goals:

**Core Vision**: The project registry is CENTRAL to the project switching paradigm. It enables users to switch between different codebase projects with specialized AI models. Each project gets its own "brain" (LoRA adapter) and context.

**Specific Requirements from requirements.md**:
- **Requirement 4**: Project registry system for managing multiple processed codebases
- **Acceptance Criteria 4.1**: Register each project with metadata and training status
- **Acceptance Criteria 4.2**: Display project name, path, training status, and last updated time
- **Acceptance Criteria 4.3**: Clean up associated LoRA adapters and vector stores when removing projects
- **Acceptance Criteria 4.4**: Detect and mark corrupted projects for retraining
- **Acceptance Criteria 4.5**: Provide fast lookup and filtering capabilities

**Architecture Role from design.md**: The project registry sits at the center of the system architecture, coordinating between:
- Dynamic Model Loader (for LoRA adapter management)
- Project Context Manager (for conversation state)
- Vector Store Management (for project-specific embeddings)
- Training Pipeline (for LoRA adapter creation)

**Core Principles Alignment**:
- **Project-Specific Intelligence**: Registry enables specialized AI assistants per codebase
- **Project Switching Paradigm**: Registry is the foundation for switching between specialized contexts
- **Local-First Processing**: All project metadata stored locally
- **Mac Mini M4 Optimization**: Fast lookup and efficient metadata management

### 3. Forward Compatibility Review
**Check upcoming tasks for expected interfaces:**
- [x] Read the next 3-5 tasks in `tasks.md` to understand what they expect from this task
- [x] Identify any interfaces, data formats, or patterns that future tasks will need
- [x] Note any dependencies that future tasks have on this task's output
- [x] Check if this task needs to prepare for future integrations

**Key Questions:**
- What will the next tasks expect this task to provide?
- Are there any interfaces this task should expose for future use?
- What data formats or structures should this task output for downstream tasks?
- Are there any extensibility requirements for future features?

#### Analysis of Future Task Dependencies:

**Task 12 (LoRA Training Pipeline)**: Expects project registry to:
- Provide project metadata for training data preparation
- Track training status and progress
- Support automatic training workflow when new projects are added
- Store training history and performance metrics

**Task 13 (Dynamic Model Loader)**: Expects project registry to:
- Provide project-to-adapter mapping information
- Track adapter availability and compatibility
- Support adapter loading/unloading coordination
- Store adapter metadata and performance data

**Task 14 (Project Context Manager)**: Expects project registry to:
- Provide project metadata for context initialization
- Support project switching events and notifications
- Track conversation history and analysis state
- Coordinate context cleanup during project removal

**Task 15 (Project-Specific Vector Stores)**: Expects project registry to:
- Coordinate vector store lifecycle with project lifecycle
- Track vector store status and statistics
- Support vector store cleanup during project removal
- Provide project isolation metadata

**Task 16 (Gradio Project Selector)**: Expects project registry to:
- Provide project list for dropdown interface
- Support real-time project status updates
- Track project state changes for UI updates
- Provide project metadata for display

### 4. Development Standards Review
**Ensure consistency with established patterns:**
- [x] Read `.kiro/steering/development-best-practices.md` - understand coding standards and MCP tool usage
- [x] Review established error handling patterns from previous tasks
- [x] Check configuration management patterns from previous tasks
- [x] Understand testing strategies and quality standards

**Key Questions:**
- What coding patterns and standards should this task follow?
- How should this task integrate with the error handling framework?
- What configuration management approach should this task use?
- What testing approach and quality standards should this task meet?

#### Analysis of Development Standards:

**MCP Tool Usage Order (MANDATORY)**:
1. **Sequential Thinking FIRST** - Break down project registry architecture decisions
2. **Context7 FOURTH** - Get precise documentation for metadata management libraries
3. **Bright Data SECOND** - Find real-world project registry implementations
4. **Basic Memory THIRD** - Reference patterns from previous tasks

**Error Handling Patterns**:
- Use CodebaseGardenerError hierarchy with ProjectRegistryError subclass
- Apply retry_with_backoff decorators for file operations and database access
- Provide user-friendly error messages with actionable suggestions
- Implement graceful degradation when registry operations fail

**Configuration Management**:
- Use Settings class for registry-specific configuration
- Support CODEBASE_GARDENER_ environment variable prefix
- Store configuration in pyproject.toml where appropriate
- Use structured logging for all registry operations

**Testing Standards**:
- Comprehensive unit tests with mocking for external dependencies
- Integration tests for registry operations with real file system
- Performance tests for lookup and filtering operations
- Edge case testing for corrupted projects and concurrent access

### 5. Integration Validation Plan
**Plan how to validate this task works with the existing system:**
- [x] Identify what components this task will integrate with
- [x] Plan integration tests that validate end-to-end functionality
- [x] Define success criteria for integration validation
- [x] Plan performance benchmarks and quality metrics

**Key Questions:**
- How will I validate this task works with existing components?
- What integration tests should I create?
- What are the performance and quality requirements?
- How will I know this task is truly complete and integrated?

#### Integration Validation Plan:

**Component Integration Points**:
1. **Directory Setup (Task 3)**: Validate project directory creation and management
2. **PEFT Manager (Task 10)**: Validate LoRA adapter lifecycle coordination
3. **Vector Store (Task 8)**: Validate project-specific vector store management
4. **Configuration System (Task 2)**: Validate settings integration and logging
5. **Error Handling (Task 4)**: Validate exception handling and retry logic

**Integration Tests to Create**:
1. **Full Project Lifecycle Test**: Add project → process → train → remove
2. **Concurrent Access Test**: Multiple projects being managed simultaneously
3. **Error Recovery Test**: Handle corrupted project metadata and recovery
4. **Performance Test**: Fast lookup with 10+ projects
5. **Cleanup Test**: Verify complete cleanup of project resources

**Success Criteria**:
- Project registration completes in <1 second
- Project lookup operations complete in <100ms
- Registry handles 50+ projects without performance degradation
- All project resources are properly cleaned up on removal
- Registry survives system restarts and maintains consistency

**Performance Benchmarks**:
- Project registration: <1 second for typical codebase
- Project lookup: <100ms for registry with 50 projects
- Status updates: <50ms for project status changes
- Memory usage: <50MB for registry with 50 projects
- Disk usage: <10MB for registry metadata storage

## Pre-Task Review Completion Checklist
- [x] All previous memory files read and understood
- [x] Requirements and design documents reviewed
- [x] Steering documents and principles understood
- [x] Forward compatibility with future tasks considered
- [x] Development standards and patterns identified
- [x] Integration validation plan created
- [x] Ready to implement with full context and understanding

**ONLY PROCEED TO IMPLEMENTATION AFTER COMPLETING THIS ENTIRE REVIEW**

## Key Implementation Insights

### Critical Integration Points Identified:
1. **Directory Management**: Must integrate with DirectoryManager from Task 3 for project directory lifecycle
2. **PEFT Coordination**: Must coordinate with PeftManager from Task 10 for adapter lifecycle
3. **Vector Store Coordination**: Must coordinate with VectorStore from Task 8 for project-specific storage
4. **Configuration Integration**: Must use Settings from Task 2 and follow established patterns
5. **Error Handling**: Must use established exception hierarchy and retry patterns from Task 4

### Required Interfaces for Future Tasks:
1. **Project Metadata Interface**: Structured project information for all downstream tasks
2. **Status Tracking Interface**: Real-time project status for UI and coordination
3. **Lifecycle Events Interface**: Notifications for project add/remove/update events
4. **Fast Lookup Interface**: Efficient project filtering and search capabilities
5. **Resource Coordination Interface**: Cleanup coordination with all project resources

### Performance and Quality Constraints:
1. **Fast Lookup**: <100ms for project operations to support real-time UI
2. **Memory Efficiency**: <50MB for registry with 50 projects (Mac Mini M4 constraint)
3. **Reliability**: Survive system restarts and maintain consistency
4. **Concurrent Access**: Handle multiple simultaneous project operations
5. **Resource Cleanup**: Complete cleanup of all project resources on removal

This comprehensive review confirms that the project registry is a critical central component that coordinates the entire project switching paradigm. It must be implemented with careful attention to integration points, performance constraints, and forward compatibility with all future tasks.
