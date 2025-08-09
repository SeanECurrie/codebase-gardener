"""
Project-Specific Vector Store Management

This module provides project-specific vector store management for the Codebase Gardener MVP.
It extends the existing LanceDB vector store implementation to support multiple projects
with data isolation, efficient project switching, and health monitoring.
"""

import logging
import threading
from collections import OrderedDict
from dataclasses import dataclass
from datetime import datetime
from typing import Any

import lancedb
import numpy as np

from codebase_gardener.config.settings import get_settings
from codebase_gardener.core.project_registry import (
    get_project_registry,
)
from codebase_gardener.data.preprocessor import CodeChunk
from codebase_gardener.data.vector_store import (
    SearchResult,
    VectorStore,
)
from codebase_gardener.utils.error_handling import (
    VectorStoreError,
    retry_with_exponential_backoff,
)

logger = logging.getLogger(__name__)


@dataclass
class ProjectVectorStoreInfo:
    """Information about a project-specific vector store."""
    project_id: str
    table_name: str
    vector_store: VectorStore
    last_accessed: datetime
    chunk_count: int
    health_status: str = "healthy"

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "project_id": self.project_id,
            "table_name": self.table_name,
            "last_accessed": self.last_accessed.isoformat(),
            "chunk_count": self.chunk_count,
            "health_status": self.health_status
        }


class ProjectVectorStoreManager:
    """
    Manages project-specific vector stores with data isolation and efficient switching.

    This class provides:
    - Separate LanceDB tables per project for data isolation
    - Efficient project switching with caching
    - Health monitoring and automatic recovery
    - Integration with project registry and context manager
    """

    def __init__(self, max_cache_size: int = 3):
        """
        Initialize the project vector store manager.

        Args:
            max_cache_size: Maximum number of vector stores to keep in memory
        """
        self.settings = get_settings()
        self.project_registry = get_project_registry()

        # Vector store cache with LRU eviction
        self._vector_store_cache: OrderedDict[str, ProjectVectorStoreInfo] = OrderedDict()
        self._max_cache_size = max_cache_size
        self._lock = threading.RLock()

        # Current active project
        self._active_project_id: str | None = None
        self._active_vector_store: VectorStore | None = None

        # Database connection
        self.db_path = self.settings.data_dir / "vector_stores"
        self.db_path.mkdir(parents=True, exist_ok=True)
        self.db = None

        logger.info(f"ProjectVectorStoreManager initialized with cache_size={max_cache_size}")

    def _ensure_db_connected(self) -> None:
        """Ensure database connection is established."""
        if self.db is None:
            try:
                self.db = lancedb.connect(str(self.db_path))
                logger.info(f"Connected to LanceDB at {self.db_path}")
            except Exception as e:
                raise VectorStoreError(f"Failed to connect to LanceDB: {e}") from e

    def _get_table_name(self, project_id: str) -> str:
        """Generate table name for a project."""
        # Use project ID as table name, sanitized for LanceDB
        sanitized_id = project_id.replace("-", "_").replace(" ", "_")
        return f"project_{sanitized_id}"

    def _manage_cache(self) -> None:
        """Manage vector store cache with LRU eviction."""
        while len(self._vector_store_cache) > self._max_cache_size:
            # Remove oldest entry
            oldest_project_id, oldest_info = self._vector_store_cache.popitem(last=False)

            # Close the vector store connection
            try:
                oldest_info.vector_store.close()
                logger.info(f"Evicted vector store for project {oldest_project_id} from cache")
            except Exception as e:
                logger.warning(f"Error closing vector store for {oldest_project_id}: {e}")

    @retry_with_exponential_backoff(max_retries=3)
    def get_project_vector_store(self, project_id: str) -> VectorStore:
        """
        Get or create a vector store for the specified project.

        Args:
            project_id: Unique identifier of the project

        Returns:
            VectorStore instance for the project

        Raises:
            VectorStoreError: If project doesn't exist or vector store creation fails
        """
        with self._lock:
            # Validate project exists
            project = self.project_registry.get_project(project_id)
            if not project:
                raise VectorStoreError(f"Project {project_id} not found in registry")

            # Check cache first
            if project_id in self._vector_store_cache:
                # Move to end (most recently used)
                info = self._vector_store_cache.pop(project_id)
                info.last_accessed = datetime.now()
                self._vector_store_cache[project_id] = info

                logger.debug(f"Retrieved cached vector store for project {project_id}")
                return info.vector_store

            # Create new vector store
            try:
                self._ensure_db_connected()
                table_name = self._get_table_name(project_id)

                # Create vector store instance
                vector_store = VectorStore(self.db_path, table_name)
                vector_store.connect()

                # Create cache entry
                info = ProjectVectorStoreInfo(
                    project_id=project_id,
                    table_name=table_name,
                    vector_store=vector_store,
                    last_accessed=datetime.now(),
                    chunk_count=0,
                    health_status="healthy"
                )

                # Add to cache and manage size
                self._vector_store_cache[project_id] = info
                self._manage_cache()

                logger.info(f"Created new vector store for project {project_id}")
                return vector_store

            except Exception as e:
                raise VectorStoreError(f"Failed to create vector store for project {project_id}: {e}") from e

    def switch_project(self, project_id: str) -> bool:
        """
        Switch to a different project's vector store.

        Args:
            project_id: ID of the project to switch to

        Returns:
            True if switch was successful, False otherwise
        """
        with self._lock:
            try:
                # Get the vector store for the new project
                vector_store = self.get_project_vector_store(project_id)

                # Update active project
                self._active_project_id = project_id
                self._active_vector_store = vector_store

                logger.info(f"Switched to project {project_id} vector store")
                return True

            except Exception as e:
                logger.error(f"Failed to switch to project {project_id}: {e}")
                return False

    def get_active_vector_store(self) -> VectorStore | None:
        """Get the currently active vector store."""
        return self._active_vector_store

    def get_active_project_id(self) -> str | None:
        """Get the currently active project ID."""
        return self._active_project_id

    def search_similar_in_project(
        self,
        project_id: str,
        query_embedding: np.ndarray,
        limit: int = 10,
        filters: dict[str, Any] | None = None
    ) -> list[SearchResult]:
        """
        Search for similar chunks within a specific project.

        Args:
            project_id: ID of the project to search in
            query_embedding: Query vector for similarity search
            limit: Maximum number of results to return
            filters: Optional metadata filters

        Returns:
            List of SearchResult objects ordered by similarity
        """
        try:
            vector_store = self.get_project_vector_store(project_id)
            return vector_store.search_similar(query_embedding, limit, filters)
        except Exception as e:
            logger.error(f"Failed to search in project {project_id}: {e}")
            return []

    def add_chunks_to_project(
        self,
        project_id: str,
        chunks: list[CodeChunk],
        embeddings: list[np.ndarray]
    ) -> bool:
        """
        Add code chunks to a specific project's vector store.

        Args:
            project_id: ID of the project to add chunks to
            chunks: List of CodeChunk objects to store
            embeddings: List of corresponding embedding vectors

        Returns:
            True if successful, False otherwise
        """
        try:
            vector_store = self.get_project_vector_store(project_id)
            vector_store.add_chunks(chunks, embeddings)

            # Update chunk count in cache
            with self._lock:
                if project_id in self._vector_store_cache:
                    self._vector_store_cache[project_id].chunk_count += len(chunks)

            logger.info(f"Added {len(chunks)} chunks to project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to add chunks to project {project_id}: {e}")
            return False

    def remove_project_vector_store(self, project_id: str) -> bool:
        """
        Remove a project's vector store and clean up resources.

        Args:
            project_id: ID of the project to remove

        Returns:
            True if successful, False otherwise
        """
        with self._lock:
            try:
                # Remove from cache if present
                if project_id in self._vector_store_cache:
                    info = self._vector_store_cache.pop(project_id)
                    info.vector_store.close()

                # Clear active project if it's the one being removed
                if self._active_project_id == project_id:
                    self._active_project_id = None
                    self._active_vector_store = None

                # Drop table from database
                self._ensure_db_connected()
                table_name = self._get_table_name(project_id)

                if table_name in self.db.table_names():
                    self.db.drop_table(table_name)
                    logger.info(f"Dropped table {table_name} for project {project_id}")

                return True

            except Exception as e:
                logger.error(f"Failed to remove vector store for project {project_id}: {e}")
                return False

    def health_check(self, project_id: str | None = None) -> dict[str, Any]:
        """
        Perform health check on vector stores.

        Args:
            project_id: Optional specific project to check, or None for all

        Returns:
            Dictionary with health check results
        """
        health_results = {
            "timestamp": datetime.now().isoformat(),
            "overall_status": "healthy",
            "projects": {}
        }

        try:
            self._ensure_db_connected()

            # Check specific project or all cached projects
            projects_to_check = [project_id] if project_id else list(self._vector_store_cache.keys())

            for pid in projects_to_check:
                if pid in self._vector_store_cache:
                    info = self._vector_store_cache[pid]

                    try:
                        # Test basic operations
                        stats = info.vector_store.get_stats()

                        health_results["projects"][pid] = {
                            "status": "healthy",
                            "table_name": info.table_name,
                            "chunk_count": stats.get("total_chunks", 0),
                            "last_accessed": info.last_accessed.isoformat()
                        }

                    except Exception as e:
                        health_results["projects"][pid] = {
                            "status": "unhealthy",
                            "error": str(e),
                            "last_accessed": info.last_accessed.isoformat()
                        }
                        health_results["overall_status"] = "degraded"

            # Check database connection
            table_names = self.db.table_names()
            health_results["database"] = {
                "status": "connected",
                "table_count": len(table_names),
                "tables": table_names
            }

        except Exception as e:
            health_results["overall_status"] = "unhealthy"
            health_results["database"] = {
                "status": "disconnected",
                "error": str(e)
            }

        return health_results

    def get_project_stats(self, project_id: str) -> dict[str, Any]:
        """
        Get statistics for a specific project's vector store.

        Args:
            project_id: ID of the project

        Returns:
            Dictionary with project statistics
        """
        try:
            vector_store = self.get_project_vector_store(project_id)
            stats = vector_store.get_stats()

            # Add project-specific information
            stats["project_id"] = project_id
            stats["table_name"] = self._get_table_name(project_id)

            if project_id in self._vector_store_cache:
                info = self._vector_store_cache[project_id]
                stats["last_accessed"] = info.last_accessed.isoformat()
                stats["health_status"] = info.health_status

            return stats

        except Exception as e:
            logger.error(f"Failed to get stats for project {project_id}: {e}")
            return {"error": str(e)}

    def list_project_vector_stores(self) -> list[dict[str, Any]]:
        """
        List all project vector stores.

        Returns:
            List of dictionaries with project vector store information
        """
        result = []

        try:
            self._ensure_db_connected()
            table_names = self.db.table_names()

            # Get information for all project tables
            for table_name in table_names:
                if table_name.startswith("project_"):
                    # Extract project ID from table name
                    project_id = table_name.replace("project_", "").replace("_", "-")

                    # Get project metadata
                    project = self.project_registry.get_project(project_id)
                    if project:
                        info = {
                            "project_id": project_id,
                            "project_name": project.name,
                            "table_name": table_name,
                            "cached": project_id in self._vector_store_cache
                        }

                        # Add cache information if available
                        if project_id in self._vector_store_cache:
                            cache_info = self._vector_store_cache[project_id]
                            info.update({
                                "last_accessed": cache_info.last_accessed.isoformat(),
                                "chunk_count": cache_info.chunk_count,
                                "health_status": cache_info.health_status
                            })

                        result.append(info)

        except Exception as e:
            logger.error(f"Failed to list project vector stores: {e}")

        return result

    def optimize_project_index(self, project_id: str) -> bool:
        """
        Optimize the vector index for a specific project.

        Args:
            project_id: ID of the project to optimize

        Returns:
            True if successful, False otherwise
        """
        try:
            vector_store = self.get_project_vector_store(project_id)
            vector_store.optimize_index()
            logger.info(f"Optimized index for project {project_id}")
            return True

        except Exception as e:
            logger.error(f"Failed to optimize index for project {project_id}: {e}")
            return False

    def close_all(self) -> None:
        """Close all vector store connections and cleanup resources."""
        with self._lock:
            # Close all cached vector stores
            for project_id, info in self._vector_store_cache.items():
                try:
                    info.vector_store.close()
                    logger.debug(f"Closed vector store for project {project_id}")
                except Exception as e:
                    logger.warning(f"Error closing vector store for {project_id}: {e}")

            # Clear cache and active project
            self._vector_store_cache.clear()
            self._active_project_id = None
            self._active_vector_store = None

            # Close database connection
            self.db = None

            logger.info("Closed all project vector stores")

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close_all()


# Global instance management
_project_vector_store_manager: ProjectVectorStoreManager | None = None
_manager_lock = threading.Lock()


def get_project_vector_store_manager() -> ProjectVectorStoreManager:
    """
    Get the global project vector store manager instance.

    Returns:
        ProjectVectorStoreManager singleton instance
    """
    global _project_vector_store_manager

    if _project_vector_store_manager is None:
        with _manager_lock:
            if _project_vector_store_manager is None:
                _project_vector_store_manager = ProjectVectorStoreManager()
                logger.info("Created global ProjectVectorStoreManager instance")

    return _project_vector_store_manager


def reset_project_vector_store_manager() -> None:
    """Reset the global project vector store manager (for testing)."""
    global _project_vector_store_manager

    with _manager_lock:
        if _project_vector_store_manager is not None:
            _project_vector_store_manager.close_all()
            _project_vector_store_manager = None
            logger.info("Reset global ProjectVectorStoreManager instance")
