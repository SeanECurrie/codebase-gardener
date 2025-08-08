# Requirements Document

## Introduction

The Codebase Gardener MVP is a Python-based AI-powered tool designed for project-specific codebase analysis through specialized model adaptation. The core concept is PROJECT SWITCHING between different codebases, where each codebase gets its own specialized LoRA (Low-Rank Adaptation) adapter trained on that specific project. Users can switch between different projects via a dropdown interface, and when switching, the system loads the appropriate LoRA adapter and project-specific vector store to provide specialized, project-specific code analysis rather than general code analysis. The system emphasizes local processing on Mac Mini M4 hardware, privacy, and efficient resource utilization while maintaining professional software development standards.

## Requirements

### Requirement 1

**User Story:** As a developer, I want to switch between different codebase projects with specialized AI models, so that I can get project-specific code analysis and insights tailored to each codebase.

#### Acceptance Criteria

1. WHEN I select a project from the dropdown THEN the system SHALL load the project-specific LoRA adapter and vector store
2. WHEN switching between projects THEN the system SHALL maintain separate conversation contexts for each project
3. WHEN analyzing code THEN the system SHALL use the specialized model trained on that specific codebase
4. WHEN I add a new project THEN the system SHALL train a new LoRA adapter specifically for that codebase
5. WHEN managing multiple projects THEN the system SHALL provide a clear interface showing available projects and their status

### Requirement 2

**User Story:** As a developer, I want a LoRA adapter training pipeline for each codebase, so that I can create specialized models that understand the specific patterns and context of each project.

#### Acceptance Criteria

1. WHEN adding a new project THEN the system SHALL automatically train a LoRA adapter on the codebase
2. WHEN training LoRA adapters THEN the system SHALL use HuggingFace PEFT for parameter-efficient fine-tuning
3. WHEN processing training data THEN the system SHALL extract meaningful code patterns and documentation
4. WHEN training completes THEN the system SHALL save the LoRA adapter in the project-specific directory
5. WHEN training fails THEN the system SHALL provide clear error messages and fallback to base model

### Requirement 3

**User Story:** As a user, I want dynamic model loading and unloading, so that I can efficiently switch between project-specific LoRA adapters without consuming excessive memory.

#### Acceptance Criteria

1. WHEN switching projects THEN the system SHALL unload the current LoRA adapter and load the new one
2. WHEN loading models THEN the system SHALL verify adapter compatibility with the base model
3. WHEN memory is constrained THEN the system SHALL efficiently manage model loading/unloading
4. WHEN adapters fail to load THEN the system SHALL fallback to the base model with appropriate warnings
5. WHEN multiple rapid switches occur THEN the system SHALL handle concurrent loading requests gracefully

### Requirement 4

**User Story:** As a user, I want a project registry system, so that I can manage multiple processed codebases and their associated specialized models efficiently.

#### Acceptance Criteria

1. WHEN adding projects THEN the system SHALL register each project with metadata and training status
2. WHEN viewing projects THEN the system SHALL display project name, path, training status, and last updated time
3. WHEN removing projects THEN the system SHALL clean up associated LoRA adapters and vector stores
4. WHEN projects are corrupted THEN the system SHALL detect and mark them for retraining
5. WHEN the registry is accessed THEN the system SHALL provide fast lookup and filtering capabilities

### Requirement 5

**User Story:** As a user, I want a project context manager, so that I can maintain separate conversation states and analysis contexts for each codebase project.

#### Acceptance Criteria

1. WHEN switching projects THEN the system SHALL maintain separate conversation history for each project
2. WHEN analyzing code THEN the system SHALL use project-specific context and previous interactions
3. WHEN storing context THEN the system SHALL persist conversation state between sessions
4. WHEN context becomes large THEN the system SHALL implement intelligent context pruning
5. WHEN multiple users access projects THEN the system SHALL handle concurrent context management

### Requirement 6

**User Story:** As a user, I want a Gradio project selector interface, so that I can easily switch between different codebase projects and see their specialized analysis capabilities.

#### Acceptance Criteria

1. WHEN using the interface THEN the system SHALL provide a dropdown to select from available projects
2. WHEN selecting a project THEN the system SHALL show loading status and switch to project-specific context
3. WHEN projects are training THEN the system SHALL display training progress and estimated completion time
4. WHEN no projects exist THEN the system SHALL provide clear instructions for adding the first project
5. WHEN projects have errors THEN the system SHALL display error status and provide remediation options

### Requirement 7

**User Story:** As a developer, I want proper Python project structure with modern tooling and dependencies, so that I can develop and maintain the multi-project codebase analysis system efficiently.

#### Acceptance Criteria

1. WHEN the project is initialized THEN the system SHALL create a pyproject.toml configuration file with all necessary dependencies
2. WHEN setting up AI dependencies THEN the system SHALL include Ollama, HuggingFace PEFT, LanceDB, Tree-sitter, Gradio, and Nomic Embed Code
3. WHEN managing the data directory THEN the system SHALL create ~/.codebase-gardener/ with base_models/, projects/, and active_project.json
4. WHEN setting up development tools THEN the system SHALL include black, pytest, mypy, and proper virtual environment management
5. WHEN organizing the codebase THEN the system SHALL follow Python ML/AI project best practices with comprehensive logging and error handling
