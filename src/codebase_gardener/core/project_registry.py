"""
Project Registry System

This module provides a centralized registry for managing multiple processed codebases
and their metadata. It supports project registration, status tracking, fast lookup
capabilities, and project lifecycle management.

The registry uses a JSON-based storage format with in-memory caching for performance.
All operations are thread-safe using atomic file operations.
"""

import json
import uuid
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
from threading import Lock

import structlog
from pydantic import BaseModel, Field, field_validator, ConfigDict

from codebase_gardener.config import settings
from codebase_gardener.utils.error_handling import (
    CodebaseGardenerError,
    StorageError,
    retry_with_backoff
)

logger = structlog.get_logger(__name__)


class TrainingStatus(str, Enum):
    """Enumeration of possible training states for LoRA adapters."""
    NOT_STARTED = "not_started"
    TRAINING = "training"
    COMPLETED = "completed"
    FAILED = "failed"


class ProjectMetadata(BaseModel):
    """
    Metadata for a registered project.
    
    This model contains all the information needed to track a project's
    state, training status, and file locations.
    """
    project_id: str = Field(..., description="Unique identifier for the project")
    name: str = Field(..., description="Human-readable project name")
    source_path: Path = Field(..., description="Path to the original codebase")
    created_at: datetime = Field(default_factory=datetime.now, description="Project creation timestamp")
    last_updated: datetime = Field(default_factory=datetime.now, description="Last modification timestamp")
    training_status: TrainingStatus = Field(default=TrainingStatus.NOT_STARTED, description="Current training status")
    language: str = Field(default="python", description="Primary programming language")
    file_count: int = Field(default=0, description="Number of files processed")
    lora_adapter_path: Optional[Path] = Field(None, description="Path to the trained LoRA adapter")
    vector_store_path: Optional[Path] = Field(None, description="Path to the project's vector store")
    context_path: Optional[Path] = Field(None, description="Path to conversation context file")

    @field_validator('source_path', 'lora_adapter_path', 'vector_store_path', 'context_path', mode='before')
    @classmethod
    def convert_path_strings(cls, v):
        """Convert string paths to Path objects."""
        if v is None:
            return v
        return Path(v) if isinstance(v, str) else v

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Ensure project name is not empty and contains valid characters."""
        if not v or not v.strip():
            raise ValueError("Project name cannot be empty")
        # Remove potentially problematic characters for filesystem
        invalid_chars = '<>:"/\\|?*'
        if any(char in v for char in invalid_chars):
            raise ValueError(f"Project name contains invalid characters: {invalid_chars}")
        return v.strip()

    def update_timestamp(self) -> None:
        """Update the last_updated timestamp to current time."""
        self.last_updated = datetime.now()

    model_config = ConfigDict(
        # Allow Path objects to be serialized
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }
    )


class RegistryData(BaseModel):
    """
    Container for the entire registry data structure.
    
    This includes versioning information and the projects dictionary.
    """
    version: str = Field(default="1.0", description="Registry format version")
    projects: Dict[str, ProjectMetadata] = Field(default_factory=dict, description="Map of project_id to metadata")
    active_project: Optional[str] = Field(None, description="Currently active project ID")

    model_config = ConfigDict(
        json_encoders = {
            Path: str,
            datetime: lambda v: v.isoformat()
        }
    )


class ProjectRegistryError(CodebaseGardenerError):
    """Specific error for project registry operations."""
    pass


class ProjectRegistry:
    """
    Centralized registry for managing multiple processed codebases.
    
    This class provides a thread-safe interface for registering projects,
    tracking their status, and managing project lifecycle operations.
    
    The registry uses JSON-based persistence with in-memory caching for
    fast lookup operations.
    """

    def __init__(self, registry_path: Optional[Path] = None):
        """
        Initialize the project registry.
        
        Args:
            registry_path: Optional custom path for the registry file.
                          Defaults to ~/.codebase-gardener/registry.json
        """
        self.registry_file = registry_path or (settings.data_dir / "registry.json")
        self._data: RegistryData = RegistryData()
        self._lock = Lock()
        
        # Ensure the data directory exists
        self.registry_file.parent.mkdir(parents=True, exist_ok=True)
        
        # Load existing registry if it exists
        self._load_registry()
        
        logger.info(
            "Project registry initialized",
            registry_file=str(self.registry_file),
            project_count=len(self._data.projects)
        )

    def _load_registry(self) -> None:
        """Load the registry from disk if it exists."""
        if not self.registry_file.exists():
            logger.debug("Registry file does not exist, starting with empty registry")
            return

        try:
            with self.registry_file.open('r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Convert datetime strings back to datetime objects
            if 'projects' in data:
                for project_data in data['projects'].values():
                    if 'created_at' in project_data:
                        project_data['created_at'] = datetime.fromisoformat(project_data['created_at'])
                    if 'last_updated' in project_data:
                        project_data['last_updated'] = datetime.fromisoformat(project_data['last_updated'])
            
            self._data = RegistryData(**data)
            logger.info(
                "Registry loaded successfully",
                project_count=len(self._data.projects),
                version=self._data.version
            )
        except (json.JSONDecodeError, ValueError) as e:
            logger.error(
                "Failed to load registry file, starting with empty registry",
                error=str(e),
                registry_file=str(self.registry_file)
            )
            # Backup corrupted file
            backup_file = self.registry_file.with_suffix('.backup')
            if self.registry_file.exists():
                self.registry_file.rename(backup_file)
                logger.warning("Corrupted registry backed up", backup_file=str(backup_file))
            self._data = RegistryData()

    @retry_with_backoff(max_attempts=3)
    def _save_registry(self) -> None:
        """Save the registry to disk atomically."""
        temp_file = self.registry_file.with_suffix('.tmp')
        
        try:
            # Convert to dict for JSON serialization
            registry_dict = self._data.model_dump()
            
            # Write to temporary file first
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(registry_dict, f, indent=2, default=str, ensure_ascii=False)
            
            # Atomic move to final location
            temp_file.replace(self.registry_file)
            
            logger.debug("Registry saved successfully", registry_file=str(self.registry_file))
            
        except Exception as e:
            # Clean up temporary file on error
            if temp_file.exists():
                temp_file.unlink()
            logger.error("Failed to save registry", error=str(e))
            raise StorageError(f"Cannot save registry: {e}") from e

    def register_project(
        self,
        name: str,
        source_path: Path,
        language: str = "python"
    ) -> str:
        """
        Register a new project in the registry.
        
        Args:
            name: Human-readable project name
            source_path: Path to the original codebase
            language: Primary programming language
            
        Returns:
            str: The generated project ID
            
        Raises:
            ProjectRegistryError: If project registration fails
        """
        with self._lock:
            # Validate inputs
            if not name or not name.strip():
                raise ProjectRegistryError("Project name cannot be empty")
            
            if not source_path.exists():
                raise ProjectRegistryError(f"Source path does not exist: {source_path}")
            
            # Check for duplicate names
            for project in self._data.projects.values():
                if project.name.lower() == name.lower():
                    raise ProjectRegistryError(f"Project with name '{name}' already exists")
            
            # Generate unique project ID
            project_id = str(uuid.uuid4())
            
            # Create project directories
            project_dir = settings.data_dir / "projects" / project_id
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project metadata
            metadata = ProjectMetadata(
                project_id=project_id,
                name=name.strip(),
                source_path=source_path,
                language=language,
                lora_adapter_path=project_dir / "lora_adapter.bin",
                vector_store_path=project_dir / "vector_store",
                context_path=project_dir / "context.json"
            )
            
            # Save to disk first (this can fail)
            # Temporarily add to registry for saving
            self._data.projects[project_id] = metadata
            
            # Set as active project if it's the first one
            if len(self._data.projects) == 1:
                self._data.active_project = project_id
            
            try:
                self._save_registry()
            except Exception:
                # Roll back changes on save failure
                del self._data.projects[project_id]
                if self._data.active_project == project_id:
                    self._data.active_project = None
                # Clean up project directory
                if project_dir.exists():
                    import shutil
                    shutil.rmtree(project_dir, ignore_errors=True)
                raise
            
            logger.info(
                "Project registered successfully",
                project_id=project_id,
                name=name,
                source_path=str(source_path),
                language=language
            )
            
            return project_id

    def get_project(self, project_id: str) -> Optional[ProjectMetadata]:
        """
        Get project metadata by ID.
        
        Args:
            project_id: The project identifier
            
        Returns:
            ProjectMetadata or None if not found
        """
        return self._data.projects.get(project_id)

    def list_projects(self) -> List[ProjectMetadata]:
        """
        Get a list of all registered projects.
        
        Returns:
            List of ProjectMetadata objects
        """
        return list(self._data.projects.values())

    def update_project_status(self, project_id: str, status: TrainingStatus) -> None:
        """
        Update the training status of a project.
        
        Args:
            project_id: The project identifier
            status: New training status
            
        Raises:
            ProjectRegistryError: If project not found
        """
        with self._lock:
            if project_id not in self._data.projects:
                raise ProjectRegistryError(f"Project not found: {project_id}")
            
            project = self._data.projects[project_id]
            old_status = project.training_status
            project.training_status = status
            project.update_timestamp()
            
            self._save_registry()
            
            logger.info(
                "Project status updated",
                project_id=project_id,
                name=project.name,
                old_status=old_status,
                new_status=status
            )

    def update_project_metadata(self, project_id: str, **kwargs) -> None:
        """
        Update project metadata fields.
        
        Args:
            project_id: The project identifier
            **kwargs: Fields to update
            
        Raises:
            ProjectRegistryError: If project not found
        """
        with self._lock:
            if project_id not in self._data.projects:
                raise ProjectRegistryError(f"Project not found: {project_id}")
            
            project = self._data.projects[project_id]
            
            # Update allowed fields
            allowed_fields = {'file_count', 'language'}
            for field, value in kwargs.items():
                if field in allowed_fields:
                    setattr(project, field, value)
            
            project.update_timestamp()
            self._save_registry()
            
            logger.info(
                "Project metadata updated",
                project_id=project_id,
                name=project.name,
                updated_fields=list(kwargs.keys())
            )

    def remove_project(self, project_id: str) -> None:
        """
        Remove a project from the registry and clean up its files.
        
        Args:
            project_id: The project identifier
            
        Raises:
            ProjectRegistryError: If project not found
        """
        with self._lock:
            if project_id not in self._data.projects:
                raise ProjectRegistryError(f"Project not found: {project_id}")
            
            project = self._data.projects[project_id]
            project_name = project.name
            
            # Clean up project directory
            project_dir = settings.data_dir / "projects" / project_id
            if project_dir.exists():
                import shutil
                try:
                    shutil.rmtree(project_dir)
                    logger.debug("Project directory removed", project_dir=str(project_dir))
                except OSError as e:
                    logger.warning("Failed to remove project directory", error=str(e))
            
            # Remove from registry
            del self._data.projects[project_id]
            
            # Update active project if necessary
            if self._data.active_project == project_id:
                # Set to another project or None
                remaining_projects = list(self._data.projects.keys())
                self._data.active_project = remaining_projects[0] if remaining_projects else None
            
            self._save_registry()
            
            logger.info(
                "Project removed successfully",
                project_id=project_id,
                name=project_name
            )

    def get_active_project(self) -> Optional[str]:
        """
        Get the currently active project ID.
        
        Returns:
            Active project ID or None
        """
        return self._data.active_project

    def set_active_project(self, project_id: str) -> None:
        """
        Set the active project.
        
        Args:
            project_id: The project identifier to set as active
            
        Raises:
            ProjectRegistryError: If project not found
        """
        with self._lock:
            if project_id not in self._data.projects:
                raise ProjectRegistryError(f"Project not found: {project_id}")
            
            old_active = self._data.active_project
            self._data.active_project = project_id
            
            self._save_registry()
            
            logger.info(
                "Active project changed",
                old_active=old_active,
                new_active=project_id,
                project_name=self._data.projects[project_id].name
            )

    def get_projects_by_status(self, status: TrainingStatus) -> List[ProjectMetadata]:
        """
        Get all projects with a specific training status.
        
        Args:
            status: Training status to filter by
            
        Returns:
            List of matching projects
        """
        return [
            project for project in self._data.projects.values()
            if project.training_status == status
        ]

    def get_project_count(self) -> int:
        """Get the total number of registered projects."""
        return len(self._data.projects)

    def validate_registry(self) -> List[str]:
        """
        Validate the registry and return any issues found.
        
        Returns:
            List of validation issues (empty if valid)
        """
        issues = []
        
        for project_id, project in self._data.projects.items():
            # Check if source path still exists
            if not project.source_path.exists():
                issues.append(f"Project {project.name}: source path no longer exists")
            
            # Check if project directory exists
            project_dir = settings.data_dir / "projects" / project_id
            if not project_dir.exists():
                issues.append(f"Project {project.name}: project directory missing")
        
        # Check if active project exists
        if self._data.active_project and self._data.active_project not in self._data.projects:
            issues.append("Active project ID does not exist in registry")
        
        return issues


# Global registry instance
_registry_instance: Optional[ProjectRegistry] = None
_registry_lock = Lock()


def get_project_registry() -> ProjectRegistry:
    """
    Get the global project registry instance.
    
    This function implements a thread-safe singleton pattern for the registry.
    
    Returns:
        ProjectRegistry: The global registry instance
    """
    global _registry_instance
    
    if _registry_instance is None:
        with _registry_lock:
            if _registry_instance is None:
                _registry_instance = ProjectRegistry()
    
    return _registry_instance