# Implementation Plan

## Context Routing Guide

**Before starting any task, read these specific documents based on task type:**

- **WHEN** implementing AI/ML components (Tasks 5, 7-15) → READ `.kiro/steering/ai-ml-architecture-context.md`
- **WHEN** making architecture decisions → READ `.kiro/steering/codebase-gardener-principles.md`
- **WHEN** unsure about patterns or using MCP tools → READ `.kiro/steering/development-best-practices.md`
- **WHEN** starting any task → READ previous 2-3 memory files in `.kiro/memory/`
- **WHEN** creating memory files → USE template in `.kiro/docs/templates/memory-file-template.md`

---

- [x] 1. Set up project structure and configuration foundation
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/project-structure`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR understanding core project vision
    - `.kiro/steering/development-best-practices.md` - FOR MCP tool usage patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools to research Python project structure best practices
  - **Memory File Creation**: Create `project_setup_task1.md` in `.kiro/memory/` using template

  **Implementation:**

  - Create pyproject.toml with all dependencies and development tools configuration
  - Set up src/codebase_gardener package structure with proper **init**.py files
  - Create .gitignore, .python-version, and README.md files
  - Generate requirements.txt from pyproject.toml for compatibility

  **Post-Task Review:**

  - **Quality Validation**: Review implementation against principles in `codebase-gardener-principles.md`
  - **Memory Update**: Complete memory file with lessons learned and patterns established
  - **Integration Check**: Test project structure setup (virtual environment, dependencies)
  - **Documentation**: UPDATE `.kiro/docs/development-setup.md` with setup procedures
  - Commit: `git add . && git commit -m "feat: initial project structure and configuration"`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 4.1, 4.3, 4.4_

- [x] 2. Implement core configuration and logging system
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/core-config-logging`
  - **Context Review** (read these specific files):
    - `.kiro/steering/development-best-practices.md` - FOR configuration management patterns
    - `.kiro/memory/project_setup_task1.md` - FOR established project patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for Pydantic and structlog best practices
  - **Memory File Creation**: Create `config_logging_task2.md` in `.kiro/memory/`

  **Implementation:**

  - Create settings.py with Pydantic BaseSettings for configuration management
  - Implement logging_config.py with structured logging using structlog
  - Add environment variable support with CODEBASE*GARDENER* prefix
  - Write unit tests for configuration loading and validation

  **Post-Task Review:**

  - **Quality Validation**: Test configuration loading with different environment setups
  - **Memory Update**: Document configuration patterns and testing approaches
  - **Integration Check**: Validate logging output formats and integration with project structure
  - Commit: `git add . && git commit -m "feat: core configuration and structured logging system"`
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 3. Create directory setup and initialization utilities
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/directory-setup`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR local-first processing principles
    - `.kiro/memory/config_logging_task2.md` - FOR established error handling patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for file system and directory management best practices
  - **Memory File Creation**: Create `directory_setup_task3.md` in `.kiro/memory/`

  **Implementation:**

  - Implement directory_setup.py to create ~/.codebase-gardener/ structure
  - Create base_models/, projects/, and active_project.json management
  - Add proper permissions and error handling for directory creation
  - Write tests for directory initialization and permission handling

  **Post-Task Review:**

  - **Quality Validation**: Test directory creation across different OS and permissions
  - **Memory Update**: Document directory patterns and permission strategies
  - **Integration Check**: Validate integration with logging and configuration systems
  - Commit: `git add . && git commit -m "feat: directory setup and initialization utilities"`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [x] 4. Implement error handling framework
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/error-handling`
  - **Context Review** (read these specific files):
    - `.kiro/steering/development-best-practices.md` - FOR error handling patterns
    - `.kiro/memory/config_logging_task2.md` AND `.kiro/memory/directory_setup_task3.md` - FOR error patterns encountered
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for retry mechanisms and exponential backoff patterns
  - **Memory File Creation**: Create `error_handling_task4.md` in `.kiro/memory/`

  **Implementation:**

  - Create custom exception hierarchy in error_handling.py
  - Implement retry decorators with exponential backoff
  - Add graceful error handling patterns and user-friendly error messages
  - Write comprehensive tests for error scenarios and recovery mechanisms

  **Post-Task Review:**

  - **Quality Validation**: Test error handling with various failure scenarios
  - **Memory Update**: Document error handling patterns and testing strategies
  - **Integration Check**: Validate integration with existing logging system
  - Commit: `git add . && git commit -m "feat: comprehensive error handling framework"`
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [x] 5. Build Tree-sitter code parser integration
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/treesitter-parser`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR multi-modal understanding stack
    - `.kiro/steering/development-best-practices.md` - FOR code quality standards
    - `.kiro/memory/error_handling_task4.md` - FOR established error handling patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for Tree-sitter documentation and language support
  - **Memory File Creation**: Create `treesitter_parser_task5.md` in `.kiro/memory/`

  **Implementation:**

  - Implement parser.py with Tree-sitter Python bindings
  - Add support for multiple programming languages (Python, JavaScript, etc.)
  - Create AST traversal and code structure extraction functionality
  - Write tests for parsing various code structures and handling malformed code

  **Post-Task Review:**

  - **Quality Validation**: Test parser with various programming languages and edge cases
  - **Memory Update**: Document parsing strategies and language-specific considerations
  - **Integration Check**: Validate integration with error handling framework
  - Commit: `git add . && git commit -m "feat: Tree-sitter code parser integration"`
  - _Requirements: 2.4, 7.1, 7.2_

- [x] 6. Create code preprocessing and chunking system
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/code-preprocessing`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR chunking strategy and embedding preparation
    - `.kiro/memory/treesitter_parser_task5.md` - FOR parsing patterns and AST structures
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for code analysis and intelligent chunking strategies
  - **Memory File Creation**: Create `preprocessing_task6.md` in `.kiro/memory/`

  **Implementation:**

  - Implement preprocessor.py for code normalization and cleaning
  - Add intelligent code chunking based on AST structure (functions, classes, modules)
  - Create metadata extraction for code chunks (language, type, complexity)
  - Write tests for preprocessing different code patterns and edge cases

  **Post-Task Review:**

  - **Quality Validation**: Test preprocessing with various code styles and structures
  - **Memory Update**: Document preprocessing patterns and chunking strategies
  - **Integration Check**: Review performance benchmarks and optimization opportunities
  - Commit: `git add . && git commit -m "feat: code preprocessing and intelligent chunking system"`
  - _Requirements: 7.1, 7.2, 7.3_

- [x] 7. Implement Nomic Embed Code integration
     **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/nomic-embeddings`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR semantic understanding layer and embedding strategy
    - `.kiro/steering/codebase-gardener-principles.md` - FOR Mac Mini M4 optimization priorities
    - `.kiro/memory/preprocessing_task6.md` - FOR chunk structures and preprocessing patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for Nomic Embed Code optimization and caching techniques
  - **Memory File Creation**: Create `nomic_embeddings_task7.md` in `.kiro/memory/`

  **Implementation:**

  - Create nomic_embedder.py for code-specific embedding generation
  - Add batch processing capabilities for efficient embedding generation
  - Implement caching mechanism for generated embeddings
  - Write tests for embedding generation and batch processing performance

  **Post-Task Review:**

  - **Quality Validation**: Test embedding generation with various code chunk types and sizes
  - **Memory Update**: Document embedding patterns and performance optimizations
  - **Integration Check**: Validate integration with preprocessing system and caching effectiveness
  - Commit: `git add . && git commit -m "feat: Nomic Embed Code integration with caching"`
  - _Requirements: 2.5, 7.3, 7.4_

- [ ] 8. Build LanceDB vector storage system

  - [x] 8.1 **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`
  - [x] 8.2 **IMPLEMENTATION**: Build LanceDB vector storage system

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/lancedb-storage`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR contextual storage layer and vector store architecture
    - `.kiro/memory/nomic_embeddings_task7.md` - FOR embedding patterns and data structures
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for LanceDB optimization and indexing strategies
  - **Memory File Creation**: Create `lancedb_storage_task8.md` in `.kiro/memory/`

  **Implementation:**

  - Implement vector_store.py with LanceDB integration
  - Add efficient similarity search and metadata filtering capabilities
  - Create index management and optimization functionality
  - Write tests for vector storage, retrieval, and performance benchmarks

  **Post-Task Review:**

  - **Quality Validation**: Test vector storage with various embedding sizes and metadata structures
  - **Memory Update**: Document storage patterns and optimization strategies
  - **Integration Check**: Validate similarity search accuracy and performance benchmarks
  - Commit: `git add . && git commit -m "feat: LanceDB vector storage with similarity search"`
  - _Requirements: 2.3, 7.1, 7.2_

- [x] 9. Create Ollama client integration

  - [x] 9.1 **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`
  - [x] 9.2 **IMPLEMENTATION**: Create Ollama client integration

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/ollama-client`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR Ollama integration patterns and base model management
    - `.kiro/steering/codebase-gardener-principles.md` - FOR local-first processing principles
    - `.kiro/memory/error_handling_task4.md` - FOR retry logic and error handling patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for Ollama API best practices and connection management
  - **Memory File Creation**: Create `ollama_client_task9.md` in `.kiro/memory/`

  **Implementation:**

  - Implement ollama_client.py for local LLM communication
  - Add connection management, model loading, and inference capabilities
  - Implement retry logic and error handling for API calls
  - Write tests for Ollama integration including connection failures and timeouts

  **Post-Task Review:**

  - **Quality Validation**: Test Ollama client with various model configurations and failure scenarios
  - **Memory Update**: Document client patterns and API management strategies
  - **Integration Check**: Validate retry logic and connection management robustness
  - Commit: `git add . && git commit -m "feat: Ollama client with robust error handling"`
  - _Requirements: 2.1, 6.1, 6.2, 6.4_

- [ ] 10. Implement HuggingFace PEFT manager

  - [x] 10.1 **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`
  - [-] 10.2 **IMPLEMENTATION**: Implement HuggingFace PEFT manager

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/peft-manager`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR LoRA rationale and PEFT integration patterns
    - `.kiro/steering/codebase-gardener-principles.md` - FOR Mac Mini M4 memory efficiency requirements
    - `.kiro/memory/ollama_client_task9.md` - FOR model management patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for HuggingFace PEFT documentation and optimization
  - **Memory File Creation**: Create `peft_manager_task10.md` in `.kiro/memory/`

  **Implementation:**

  - Create peft_manager.py for Parameter Efficient Fine-Tuning workflows
  - Add model adaptation capabilities for codebase-specific fine-tuning
  - Implement training and inference interfaces with proper resource management
  - Write tests for PEFT operations and model management

  **Post-Task Review:**

  - **Quality Validation**: Test PEFT manager with various model configurations and training scenarios
  - **Memory Update**: Document PEFT patterns and training strategies
  - **Integration Check**: Validate resource management and memory optimization
  - Commit: `git add . && git commit -m "feat: HuggingFace PEFT manager for model adaptation"`
  - _Requirements: 2.2, 7.3, 7.4_

- [ ] 11. Build project registry system

  - [ ] 11.1 **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`
  - [ ] 11.2 **IMPLEMENTATION**: Build project registry system

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/project-registry`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR project switching paradigm and core concept
    - `.kiro/steering/development-best-practices.md` - FOR project lifecycle patterns
    - ALL previous memory files - FOR understanding foundational patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for metadata management and project lifecycle patterns
  - **Memory File Creation**: Create `project_registry_task11.md` in `.kiro/memory/`

  **Implementation:**

  - Implement project_registry.py for managing multiple processed codebases and their metadata
  - Add project registration, status tracking, and fast lookup capabilities
  - Create project lifecycle management (add, remove, update, retrain)
  - Write tests for project registry operations and metadata persistence

  **Post-Task Review:**

  - **Quality Validation**: Test project registry with multiple projects and concurrent operations
  - **Memory Update**: Document registry patterns and project lifecycle strategies
  - **Integration Check**: Validate metadata persistence and lookup performance
  - Commit: `git add . && git commit -m "feat: project registry with lifecycle management"`
  - _Requirements: 4.1, 4.2, 4.3, 4.4, 4.5_

- [ ] 12. Implement LoRA training pipeline

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/lora-training-pipeline`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR LoRA training rationale and pipeline architecture
    - `.kiro/steering/codebase-gardener-principles.md` - FOR specialized adapter concepts
    - `.kiro/memory/peft_manager_task10.md` AND `.kiro/memory/project_registry_task11.md` - FOR integration patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for training pipeline optimization and monitoring
  - **Memory File Creation**: Create `lora_training_task12.md` in `.kiro/memory/`

  **Implementation:**

  - Create lora_training_pipeline.py for training project-specific LoRA adapters
  - Add automatic training workflow when new projects are added
  - Implement training progress tracking and resource management
  - Write tests for training pipeline including failure scenarios and data processing

  **Post-Task Review:**

  - **Quality Validation**: Test training pipeline with various codebase sizes and complexities
  - **Memory Update**: Document training patterns and optimization strategies
  - **Integration Check**: Validate progress tracking and resource management effectiveness
  - Commit: `git add . && git commit -m "feat: LoRA training pipeline with progress tracking"`
  - _Requirements: 2.1, 2.2, 2.3, 2.4, 2.5_

- [ ] 13. Create dynamic model loader system

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/dynamic-model-loader`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR dynamic loading strategy and memory management
    - `.kiro/steering/codebase-gardener-principles.md` - FOR Mac Mini M4 optimization priorities
    - `.kiro/memory/lora_training_task12.md` - FOR LoRA adapter patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for memory management and model optimization
  - **Memory File Creation**: Create `dynamic_loader_task13.md` in `.kiro/memory/`

  **Implementation:**

  - Implement dynamic_model_loader.py for efficient LoRA adapter loading/unloading
  - Add memory management and model caching capabilities
  - Create adapter compatibility verification and fallback mechanisms
  - Write tests for concurrent model loading and memory optimization

  **Post-Task Review:**

  - **Quality Validation**: Test dynamic loader with multiple LoRA adapters and memory constraints
  - **Memory Update**: Document loading patterns and memory optimization strategies
  - **Integration Check**: Validate adapter compatibility checks and fallback mechanisms
  - Commit: `git add . && git commit -m "feat: dynamic model loader with memory management"`
  - _Requirements: 3.1, 3.2, 3.3, 3.4, 3.5_

- [ ] 14. Build project context manager

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/project-context-manager`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR project switching paradigm and conversation context
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR context switching mechanics
    - `.kiro/memory/project_registry_task11.md` AND `.kiro/memory/dynamic_loader_task13.md` - FOR integration patterns
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for context management and session handling
  - **Memory File Creation**: Create `context_manager_task14.md` in `.kiro/memory/`

  **Implementation:**

  - Implement project_context_manager.py for maintaining separate conversation states
  - Add context switching logic and project-specific analysis history
  - Create intelligent context pruning and session persistence
  - Write tests for context management and concurrent access scenarios

  **Post-Task Review:**

  - **Quality Validation**: Test context manager with multiple concurrent project sessions
  - **Memory Update**: Document context patterns and session management strategies
  - **Integration Check**: Validate context switching performance and memory efficiency
  - Commit: `git add . && git commit -m "feat: project context manager with session persistence"`
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 15. Create project-specific vector store management

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat-project-vector-stores`
  - **Context Review** (read these specific files):
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR multi-tenant vector store architecture
    - `.kiro/memory/lancedb_storage_task8.md` - FOR vector storage patterns
    - `.kiro/memory/context_manager_task14.md` - FOR project isolation requirements
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for multi-tenant database management
  - **Memory File Creation**: Create `project_vector_stores_task15.md` in `.kiro/memory/`

  **Implementation:**

  - Implement project_vector_store.py for managing separate vector stores per project
  - Add project-specific similarity search and metadata filtering
  - Create vector store initialization and cleanup for project lifecycle
  - Write tests for vector store isolation and performance across projects

  **Post-Task Review:**

  - **Quality Validation**: Test project-specific vector stores with multiple codebases
  - **Memory Update**: Document multi-tenant storage patterns and optimization strategies
  - **Integration Check**: Validate data isolation and cross-project performance
  - Commit: `git add . && git commit -m "feat: project-specific vector store management"`
  - _Requirements: 1.1, 1.2, 1.3, 7.2, 7.3_

- [ ] 16. Implement Gradio project selector interface

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`th real UI interactions and project switching workflows
  - [ ] **Integration Validation Plan**: Define how project selector will integrate with all backend management systems
  - [ ] **Forward Compatibility Check**: Ensure project selector interfaces support future web interface integration and user workflows

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/gradio-project-selector`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR user experience philosophy
    - `.kiro/steering/development-best-practices.md` - FOR UI/UX patterns
    - `.kiro/memory/project_registry_task11.md` AND `.kiro/memory/context_manager_task14.md` - FOR project management integration
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for Gradio documentation and UI/UX best practices
  - **Memory File Creation**: Create `gradio_selector_task16.md` in `.kiro/memory/`

  **Implementation:**

  - Create project_selector.py with dropdown for project switching
  - Add project status display, training progress, and error handling
  - Implement real-time updates for project state changes
  - Write tests for UI interactions and project switching workflows

  **Post-Task Review:**

  - **Quality Validation**: Test project selector with various project states and user interactions
  - **Memory Update**: Document UI patterns and user experience strategies
  - **Integration Check**: Validate real-time updates and error handling in UI
  - Commit: `git add . && git commit -m "feat: Gradio project selector with real-time updates"`
  - _Requirements: 6.1, 6.2, 6.3, 6.4, 6.5_

- [ ] 17. Create Gradio web interface integration

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/gradio-web-interface`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR magical user experience goals
    - `.kiro/memory/gradio_selector_task16.md` - FOR UI patterns and integration points
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for web interface optimization and accessibility
  - **Memory File Creation**: Create `gradio_interface_task17.md` in `.kiro/memory/`

  **Implementation:**

  - Implement gradio_app.py integrating project selector with analysis interface
  - Add components.py with reusable UI elements for project-specific analysis
  - Create real-time feedback for model loading and analysis progress
  - Write tests for complete UI workflow including project switching

  **Post-Task Review:**

  - **Quality Validation**: Test complete web interface with end-to-end project switching workflows
  - **Memory Update**: Document integration patterns and UX optimization strategies
  - **Integration Check**: Validate user experience and performance under various load conditions
  - **Documentation**: UPDATE `.kiro/docs/architecture-overview.md` with UI architecture
  - Commit: `git add . && git commit -m "feat: integrated Gradio web interface with analysis"`
  - _Requirements: 1.4, 6.2, 6.3, 7.2_

- [ ] 18. Build file utilities and helper functions

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/file-utilities`
  - **Context Review** (read these specific files):
    - `.kiro/steering/development-best-practices.md` - FOR utility patterns and security considerations
    - ALL memory files - FOR understanding common file operation needs across components
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for file system optimization and security
  - **Memory File Creation**: Create `file_utilities_task18.md` in `.kiro/memory/`

  **Implementation:**

  - Implement file_utils.py with file system operations and path handling
  - Add file type detection, size calculation, and directory traversal utilities
  - Create safe file operations with proper error handling
  - Write tests for file utilities covering edge cases and permissions

  **Post-Task Review:**

  - **Quality Validation**: Test file utilities with various file systems and permission scenarios
  - **Memory Update**: Document utility patterns and security considerations
  - **Integration Check**: Validate security and performance of file operations
  - Commit: `git add . && git commit -m "feat: comprehensive file utilities with security"`
  - _Requirements: 7.3, 7.4, 7.5_

- [ ] 19. Create main application entry point

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/main-application`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR overall system integration goals
    - `.kiro/steering/ai-ml-architecture-context.md` - FOR system startup/shutdown procedures
    - ALL previous memory files - FOR understanding complete system integration
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for application architecture and CLI design
  - **Memory File Creation**: Create `main_application_task19.md` in `.kiro/memory/`

  **Implementation:**

  - Implement main.py as the primary application launcher with project switching support
  - Add command-line interface with project management commands
  - Integrate all components and provide startup/shutdown procedures
  - Write tests for application startup, project initialization, and graceful shutdown

  **Post-Task Review:**

  - **Quality Validation**: Test complete application integration with all components
  - **Memory Update**: Document integration patterns and deployment strategies
  - **Integration Check**: Validate startup/shutdown procedures and error recovery
  - **Documentation**: UPDATE `.kiro/docs/architecture-overview.md` with complete system overview
  - Commit: `git add . && git commit -m "feat: main application with integrated project switching"`
  - _Requirements: 1.5, 7.1, 7.4, 7.5_

- [ ] 20. Add comprehensive integration tests and documentation

  - [ ] **PRE-TASK REVIEW**: Complete comprehensive review using `.kiro/docs/templates/pre-task-review-template.md`

    **Pre-Task Setup:**

  - Create git feature branch: `git checkout -b feat/integration-tests-docs`
  - **Context Review** (read these specific files):
    - `.kiro/steering/codebase-gardener-principles.md` - FOR success metrics and validation criteria
    - `.kiro/steering/development-best-practices.md` - FOR testing strategies
    - ALL memory files - FOR comprehensive system understanding and lessons learned
    - `.kiro/docs/templates/memory-file-template.md` - FOR creating memory file
  - **MCP Research**: Use MCP server tools for testing frameworks and documentation generation
  - **Memory File Creation**: Create `integration_testing_task20.md` in `.kiro/memory/`

  **Implementation:**

  - Create end-to-end tests for complete project switching and analysis workflow
  - Test integration between LoRA training, model loading, and project context management
  - Add performance tests for model switching and memory usage optimization
  - Write comprehensive documentation including setup, usage, and troubleshooting guides

  **Post-Task Review:**

  - **Quality Validation**: Validate all integration tests pass with comprehensive coverage
  - **Memory Update**: Document testing patterns and documentation standards
  - **Integration Check**: Create final system overview and architectural decision records
  - **Documentation**: COMPLETE all documentation in `.kiro/docs/` with final system guides
  - **Steering Evolution**: UPDATE all steering files with final patterns and lessons learned
  - **Final Memory Summary**: Update all memory files with project summary and outcomes
  - Commit: `git add . && git commit -m "feat: comprehensive integration tests and documentation"`
  - _Requirements: 1.1, 1.2, 1.3, 1.4, 1.5, 7.1, 7.2, 7.3, 7.4, 7.5_
