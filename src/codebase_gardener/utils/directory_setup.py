"""
Directory setup and initialization utilities.

This module provides utilities for creating and managing the ~/.codebase-gardener/
directory structure with proper permissions and error handling.
"""

import json
import stat
from pathlib import Path
from typing import Dict, Any, Optional, List
import structlog

from ..config import settings

logger = structlog.get_logger(__name__)


class DirectorySetupError(Exception):
    """Base exception for directory setup operations."""
    pass


class PermissionError(DirectorySetupError):
    """Raised when directory permissions cannot be set."""
    pass


class DirectoryValidationError(DirectorySetupError):
    """Raised when directory structure validation fails."""
    pass


class DirectoryManager:
    """
    Manages the creation and maintenance of the application directory structure.
    
    This class handles:
    - Creating the main ~/.codebase-gardener/ directory
    - Setting up subdirectories (base_models/, projects/, logs/)
    - Managing active_project.json state file
    - Setting appropriate permissions
    - Validating directory structure integrity
    """
    
    def __init__(self):
        """Initialize the directory manager with current settings."""
        self.data_dir = settings.data_dir
        self.projects_dir = settings.projects_dir
        self.base_models_dir = settings.base_models_dir
        self.logs_dir = self.data_dir / "logs"
        self.active_project_file = self.data_dir / "active_project.json"
        
        logger.debug(
            "DirectoryManager initialized",
            data_dir=str(self.data_dir),
            projects_dir=str(self.projects_dir),
            base_models_dir=str(self.base_models_dir)
        )
    
    def initialize_directories(self) -> None:
        """
        Initialize the complete directory structure.
        
        Creates all necessary directories with proper permissions and
        initializes the active project state file.
        
        Raises:
            DirectorySetupError: If directory creation fails
            PermissionError: If permissions cannot be set
        """
        logger.info("Initializing directory structure", data_dir=str(self.data_dir))
        
        try:
            # Create main directories
            self._create_directory_structure()
            
            # Set appropriate permissions
            self._set_directory_permissions()
            
            # Initialize active project state
            self._initialize_active_project_state()
            
            # Validate the created structure
            self._validate_directory_structure()
            
            logger.info(
                "Directory structure initialized successfully",
                data_dir=str(self.data_dir),
                directories_created=self._get_directory_list()
            )
            
        except Exception as e:
            logger.error(
                "Failed to initialize directory structure",
                error=str(e),
                error_type=type(e).__name__,
                data_dir=str(self.data_dir)
            )
            raise DirectorySetupError(f"Directory initialization failed: {e}") from e
    
    def _create_directory_structure(self) -> None:
        """Create the main directory structure."""
        directories = [
            self.data_dir,
            self.projects_dir,
            self.base_models_dir,
            self.logs_dir,
        ]
        
        for directory in directories:
            if directory:
                try:
                    directory.mkdir(parents=True, exist_ok=True)
                    logger.debug("Created directory", path=str(directory))
                except OSError as e:
                    logger.error(
                        "Failed to create directory",
                        path=str(directory),
                        error=str(e)
                    )
                    raise DirectorySetupError(f"Cannot create directory {directory}: {e}") from e
    
    def _set_directory_permissions(self) -> None:
        """Set appropriate permissions for directories."""
        directories = [
            self.data_dir,
            self.projects_dir,
            self.base_models_dir,
            self.logs_dir,
        ]
        
        # Standard directory permissions (owner: rwx, group: r-x, other: r-x)
        dir_permissions = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
        
        for directory in directories:
            if directory and directory.exists():
                try:
                    directory.chmod(dir_permissions)
                    logger.debug(
                        "Set directory permissions",
                        path=str(directory),
                        permissions=oct(dir_permissions)
                    )
                except OSError as e:
                    # Log warning but don't fail - permissions might not be settable on all systems
                    logger.warning(
                        "Could not set directory permissions",
                        path=str(directory),
                        error=str(e),
                        permissions=oct(dir_permissions)
                    )
    
    def _initialize_active_project_state(self) -> None:
        """Initialize the active project state file."""
        if not self.active_project_file.exists():
            initial_state = {
                "active_project": None,
                "last_updated": None,
                "projects": {},
                "version": "1.0"
            }
            
            try:
                with self.active_project_file.open('w', encoding='utf-8') as f:
                    json.dump(initial_state, f, indent=2, ensure_ascii=False)
                
                logger.debug(
                    "Created active project state file",
                    path=str(self.active_project_file)
                )
                
            except (OSError, json.JSONEncodeError) as e:
                logger.error(
                    "Failed to create active project state file",
                    path=str(self.active_project_file),
                    error=str(e)
                )
                raise DirectorySetupError(f"Cannot create active project state: {e}") from e
    
    def _validate_directory_structure(self) -> None:
        """Validate that the directory structure is correct."""
        required_directories = [
            self.data_dir,
            self.projects_dir,
            self.base_models_dir,
            self.logs_dir,
        ]
        
        missing_directories = []
        for directory in required_directories:
            if directory and not directory.exists():
                missing_directories.append(str(directory))
        
        if missing_directories:
            raise DirectoryValidationError(
                f"Missing required directories: {', '.join(missing_directories)}"
            )
        
        # Validate active project file
        if not self.active_project_file.exists():
            raise DirectoryValidationError(
                f"Active project state file missing: {self.active_project_file}"
            )
        
        # Validate active project file format
        try:
            with self.active_project_file.open('r', encoding='utf-8') as f:
                state = json.load(f)
                required_keys = ["active_project", "projects", "version"]
                missing_keys = [key for key in required_keys if key not in state]
                if missing_keys:
                    raise DirectoryValidationError(
                        f"Active project state missing keys: {', '.join(missing_keys)}"
                    )
        except (OSError, json.JSONDecodeError) as e:
            raise DirectoryValidationError(
                f"Invalid active project state file: {e}"
            ) from e
        
        logger.debug("Directory structure validation passed")
    
    def _get_directory_list(self) -> List[str]:
        """Get a list of created directories for logging."""
        directories = [
            self.data_dir,
            self.projects_dir,
            self.base_models_dir,
            self.logs_dir,
        ]
        return [str(d) for d in directories if d and d.exists()]
    
    def create_project_directory(self, project_name: str) -> Path:
        """
        Create a directory structure for a specific project.
        
        Args:
            project_name: Name of the project
            
        Returns:
            Path to the created project directory
            
        Raises:
            DirectorySetupError: If project directory creation fails
        """
        if not project_name or not project_name.strip():
            raise ValueError("Project name cannot be empty")
        
        # Sanitize project name for filesystem
        safe_project_name = self._sanitize_project_name(project_name)
        project_dir = self.projects_dir / safe_project_name
        
        try:
            # Create main project directory
            project_dir.mkdir(parents=True, exist_ok=True)
            
            # Create project subdirectories
            subdirs = [
                project_dir / "vector_store",
                project_dir / "models",
                project_dir / "cache",
            ]
            
            for subdir in subdirs:
                subdir.mkdir(parents=True, exist_ok=True)
            
            # Set permissions
            dir_permissions = stat.S_IRWXU | stat.S_IRGRP | stat.S_IXGRP | stat.S_IROTH | stat.S_IXOTH
            try:
                project_dir.chmod(dir_permissions)
                for subdir in subdirs:
                    subdir.chmod(dir_permissions)
            except OSError as e:
                logger.warning(
                    "Could not set project directory permissions",
                    project_dir=str(project_dir),
                    error=str(e)
                )
            
            logger.info(
                "Created project directory",
                project_name=project_name,
                project_dir=str(project_dir),
                subdirectories=[str(d) for d in subdirs]
            )
            
            return project_dir
            
        except OSError as e:
            logger.error(
                "Failed to create project directory",
                project_name=project_name,
                project_dir=str(project_dir),
                error=str(e)
            )
            raise DirectorySetupError(f"Cannot create project directory: {e}") from e
    
    def _sanitize_project_name(self, project_name: str) -> str:
        """
        Sanitize project name for filesystem use.
        
        Args:
            project_name: Original project name
            
        Returns:
            Sanitized project name safe for filesystem
        """
        # Replace problematic characters with underscores
        import re
        sanitized = re.sub(r'[<>:"/\\|?*]', '_', project_name)
        sanitized = sanitized.strip('. ')  # Remove leading/trailing dots and spaces
        
        # Ensure it's not empty after sanitization
        if not sanitized:
            sanitized = "unnamed_project"
        
        return sanitized
    
    def get_active_project_state(self) -> Dict[str, Any]:
        """
        Get the current active project state.
        
        Returns:
            Dictionary containing active project state
            
        Raises:
            DirectorySetupError: If state file cannot be read
        """
        try:
            with self.active_project_file.open('r', encoding='utf-8') as f:
                return json.load(f)
        except (OSError, json.JSONDecodeError) as e:
            logger.error(
                "Failed to read active project state",
                path=str(self.active_project_file),
                error=str(e)
            )
            raise DirectorySetupError(f"Cannot read active project state: {e}") from e
    
    def update_active_project_state(self, state: Dict[str, Any]) -> None:
        """
        Update the active project state.
        
        Args:
            state: New state dictionary
            
        Raises:
            DirectorySetupError: If state file cannot be written
        """
        try:
            # Backup current state
            backup_path = self.active_project_file.with_suffix('.json.backup')
            if self.active_project_file.exists():
                backup_path.write_text(self.active_project_file.read_text(encoding='utf-8'))
            
            # Write new state
            with self.active_project_file.open('w', encoding='utf-8') as f:
                json.dump(state, f, indent=2, ensure_ascii=False)
            
            logger.debug(
                "Updated active project state",
                path=str(self.active_project_file)
            )
            
        except (OSError, json.JSONDecodeError) as e:
            logger.error(
                "Failed to update active project state",
                path=str(self.active_project_file),
                error=str(e)
            )
            raise DirectorySetupError(f"Cannot update active project state: {e}") from e
    
    def cleanup_project_directory(self, project_name: str) -> None:
        """
        Clean up a project directory and all its contents.
        
        Args:
            project_name: Name of the project to clean up
            
        Raises:
            DirectorySetupError: If cleanup fails
        """
        safe_project_name = self._sanitize_project_name(project_name)
        project_dir = self.projects_dir / safe_project_name
        
        if not project_dir.exists():
            logger.warning(
                "Project directory does not exist for cleanup",
                project_name=project_name,
                project_dir=str(project_dir)
            )
            return
        
        try:
            import shutil
            shutil.rmtree(project_dir)
            
            logger.info(
                "Cleaned up project directory",
                project_name=project_name,
                project_dir=str(project_dir)
            )
            
        except OSError as e:
            logger.error(
                "Failed to cleanup project directory",
                project_name=project_name,
                project_dir=str(project_dir),
                error=str(e)
            )
            raise DirectorySetupError(f"Cannot cleanup project directory: {e}") from e


# Global directory manager instance
directory_manager = DirectoryManager()


def initialize_directories() -> None:
    """Initialize the application directory structure."""
    directory_manager.initialize_directories()


def create_project_directory(project_name: str) -> Path:
    """Create a directory structure for a specific project."""
    return directory_manager.create_project_directory(project_name)


def get_active_project_state() -> Dict[str, Any]:
    """Get the current active project state."""
    return directory_manager.get_active_project_state()


def update_active_project_state(state: Dict[str, Any]) -> None:
    """Update the active project state."""
    directory_manager.update_active_project_state(state)


def cleanup_project_directory(project_name: str) -> None:
    """Clean up a project directory and all its contents."""
    directory_manager.cleanup_project_directory(project_name)