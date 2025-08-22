"""
LanceDB Vector Storage System

This module provides a vector storage system using LanceDB for efficient similarity search
and metadata filtering of code chunks. It integrates with the Nomic embeddings system
and supports project-specific vector stores for multi-tenant architecture.
"""

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any

import lancedb
import numpy as np
import structlog

from codebase_gardener.data.preprocessor import ChunkType, CodeChunk
from codebase_gardener.utils.error_handling import (
    VectorStoreError,
    retry_with_backoff,
)

logger = structlog.get_logger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""

    chunk_id: str
    chunk: CodeChunk
    similarity_score: float
    metadata: dict[str, Any]


@dataclass
class VectorStoreStats:
    """Statistics about the vector store."""

    total_chunks: int
    languages: dict[str, int]
    chunk_types: dict[str, int]
    avg_complexity: float
    storage_size_mb: float
    last_updated: str


class VectorStore:
    """
    LanceDB-based vector storage system for code chunks.

    Provides efficient similarity search, metadata filtering, and batch operations
    optimized for Mac Mini M4 constraints.
    """

    def __init__(self, db_path: Path, table_name: str = "code_chunks", settings=None):
        """
        Initialize the vector store.

        Args:
            db_path: Path to the LanceDB database directory
            table_name: Name of the table to store code chunks
            settings: Optional settings (for component registry compatibility)
        """
        self.db_path = db_path
        self.table_name = table_name
        self.db = None
        self.table = None
        self._connected = False

        # Ensure database directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Vector store initialized",
            db_path=str(db_path),
            table_name=table_name,
        )

    def connect(self) -> None:
        """Connect to LanceDB and initialize table if needed."""
        try:
            self.db = lancedb.connect(str(self.db_path))
            self._connected = True

            # Check if table exists, create if not
            if self.table_name not in self.db.table_names():
                logger.info(
                    "Creating new vector store table", table_name=self.table_name
                )
                self._create_table()
            else:
                logger.info(
                    "Opening existing vector store table", table_name=self.table_name
                )
                self.table = self.db.open_table(self.table_name)

        except Exception as e:
            error_msg = f"Failed to connect to LanceDB: {e}"
            logger.error(error_msg, db_path=str(self.db_path), error=str(e))
            raise VectorStoreError(error_msg) from e

    def _create_table(self) -> None:
        """Create a new table with the CodeChunk schema."""
        try:
            # Define schema for LanceDB
            import pyarrow as pa

            schema = pa.schema(
                [
                    ("id", pa.string()),
                    ("file_path", pa.string()),
                    ("content", pa.string()),
                    ("language", pa.string()),
                    ("chunk_type", pa.string()),
                    ("start_line", pa.int32()),
                    ("end_line", pa.int32()),
                    ("start_byte", pa.int64()),
                    ("end_byte", pa.int64()),
                    (
                        "embedding",
                        pa.list_(pa.float32(), 384),
                    ),  # Nomic embedding dimension
                    ("metadata", pa.string()),
                    ("dependencies", pa.string()),
                    ("complexity_score", pa.float32()),
                    ("created_at", pa.string()),
                    ("updated_at", pa.string()),
                ]
            )

            # Create empty table with schema
            self.table = self.db.create_table(self.table_name, schema=schema)

            logger.info(
                "Created vector store table",
                table_name=self.table_name,
                schema_fields=len(schema),
            )

        except Exception as e:
            error_msg = f"Failed to create table {self.table_name}: {e}"
            logger.error(error_msg, table_name=self.table_name, error=str(e))
            raise VectorStoreError(error_msg) from e

    def _ensure_connected(self) -> None:
        """Ensure database connection is established."""
        if not self._connected or self.db is None:
            self.connect()

    def _chunk_to_record(
        self, chunk: CodeChunk, embedding: np.ndarray
    ) -> dict[str, Any]:
        """Convert CodeChunk to record format for LanceDB."""
        now = datetime.now().isoformat()

        return {
            "id": chunk.id,
            "file_path": str(chunk.file_path) if chunk.file_path else "",
            "content": chunk.content,
            "language": chunk.language,
            "chunk_type": chunk.chunk_type.value
            if hasattr(chunk.chunk_type, "value")
            else str(chunk.chunk_type),
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "start_byte": chunk.start_byte,
            "end_byte": chunk.end_byte,
            "embedding": embedding.tolist(),
            "metadata": json.dumps(chunk.metadata),
            "dependencies": json.dumps(chunk.dependencies),
            "complexity_score": float(chunk.complexity_score),
            "created_at": now,
            "updated_at": now,
        }

    def _record_to_chunk(self, record: dict[str, Any]) -> CodeChunk:
        """Convert LanceDB record back to CodeChunk object."""
        # Parse chunk type
        chunk_type_str = record["chunk_type"]
        try:
            chunk_type = ChunkType(chunk_type_str)
        except ValueError:
            # Fallback for unknown chunk types
            chunk_type = ChunkType.BLOCK

        # Parse file path
        file_path = Path(record["file_path"]) if record["file_path"] else None

        return CodeChunk(
            id=record["id"],
            content=record["content"],
            language=record["language"],
            chunk_type=chunk_type,
            file_path=file_path,
            start_line=record["start_line"],
            end_line=record["end_line"],
            start_byte=record["start_byte"],
            end_byte=record["end_byte"],
            metadata=json.loads(record["metadata"]),
            dependencies=json.loads(record["dependencies"]),
            complexity_score=record["complexity_score"],
        )

    @retry_with_backoff(max_attempts=3)
    def add_chunks(self, chunks: list[CodeChunk], embeddings: list[np.ndarray]) -> None:
        """
        Add code chunks with their embeddings to the vector store.

        Args:
            chunks: List of CodeChunk objects to store
            embeddings: List of corresponding embedding vectors

        Raises:
            VectorStoreError: If chunks and embeddings don't match or storage fails
        """
        if len(chunks) != len(embeddings):
            raise VectorStoreError(
                f"Chunks and embeddings count mismatch: {len(chunks)} vs {len(embeddings)}"
            )

        if not chunks:
            logger.warning("No chunks to add to vector store")
            return

        self._ensure_connected()

        try:
            # Convert chunks to record format
            records = []
            for chunk, embedding in zip(chunks, embeddings, strict=True):
                record = self._chunk_to_record(chunk, embedding)
                records.append(record)

            # Add to table
            self.table.add(records)

            logger.info(
                "Added chunks to vector store",
                chunk_count=len(chunks),
                table_name=self.table_name,
            )

        except Exception as e:
            error_msg = f"Failed to add chunks to vector store: {e}"
            logger.error(error_msg, chunk_count=len(chunks), error=str(e))
            raise VectorStoreError(error_msg) from e

    def add_chunk(self, chunk: CodeChunk, embedding: np.ndarray) -> None:
        """
        Add a single code chunk with its embedding to the vector store.

        Args:
            chunk: CodeChunk object to store
            embedding: Corresponding embedding vector
        """
        self.add_chunks([chunk], [embedding])

    @retry_with_backoff(max_attempts=3)
    def search_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        language_filter: str | None = None,
        chunk_type_filter: str | None = None,
        min_similarity: float = 0.0,
    ) -> list[SearchResult]:
        """
        Search for similar code chunks using vector similarity.

        Args:
            query_embedding: Query vector for similarity search
            limit: Maximum number of results to return
            language_filter: Optional language filter
            chunk_type_filter: Optional chunk type filter
            min_similarity: Minimum similarity score threshold

        Returns:
            List of SearchResult objects sorted by similarity

        Raises:
            VectorStoreError: If search fails
        """
        self._ensure_connected()

        try:
            # Build query
            query = self.table.search(query_embedding.tolist()).limit(
                limit * 2
            )  # Get extra for filtering

            # Apply filters if specified
            filter_conditions = []
            if language_filter:
                filter_conditions.append(f"language = '{language_filter}'")
            if chunk_type_filter:
                filter_conditions.append(f"chunk_type = '{chunk_type_filter}'")

            if filter_conditions:
                filter_expr = " AND ".join(filter_conditions)
                query = query.where(filter_expr)

            # Execute search
            results = query.to_list()

            # Convert to SearchResult objects and apply similarity filter
            search_results = []
            for result in results:
                similarity_score = float(
                    result.get("_distance", 0.0)
                )  # LanceDB uses distance
                # Convert distance to similarity (assuming cosine distance)
                similarity_score = 1.0 - similarity_score

                if similarity_score >= min_similarity:
                    chunk = self._record_to_chunk(result)
                    search_result = SearchResult(
                        chunk_id=chunk.id,
                        chunk=chunk,
                        similarity_score=similarity_score,
                        metadata=chunk.metadata,
                    )
                    search_results.append(search_result)

            # Sort by similarity (highest first) and limit
            search_results.sort(key=lambda x: x.similarity_score, reverse=True)
            search_results = search_results[:limit]

            logger.debug(
                "Vector similarity search completed",
                results_found=len(search_results),
                limit=limit,
                language_filter=language_filter,
                chunk_type_filter=chunk_type_filter,
                min_similarity=min_similarity,
            )

            return search_results

        except Exception as e:
            error_msg = f"Vector similarity search failed: {e}"
            logger.error(error_msg, limit=limit, error=str(e))
            raise VectorStoreError(error_msg) from e

    def get_chunk_by_id(self, chunk_id: str) -> CodeChunk | None:
        """
        Retrieve a specific chunk by its ID.

        Args:
            chunk_id: ID of the chunk to retrieve

        Returns:
            CodeChunk object if found, None otherwise
        """
        self._ensure_connected()

        try:
            results = self.table.search().where(f"id = '{chunk_id}'").limit(1).to_list()

            if results:
                return self._record_to_chunk(results[0])
            return None

        except Exception as e:
            logger.error(
                "Failed to retrieve chunk by ID",
                chunk_id=chunk_id,
                error=str(e),
            )
            return None

    def update_chunk(self, chunk: CodeChunk, embedding: np.ndarray) -> None:
        """
        Update an existing chunk and its embedding.

        Args:
            chunk: Updated CodeChunk object
            embedding: Updated embedding vector
        """
        self._ensure_connected()

        try:
            # Delete existing record
            self.table.delete(f"id = '{chunk.id}'")

            # Add updated record
            self.add_chunk(chunk, embedding)

            logger.debug(
                "Updated chunk in vector store",
                chunk_id=chunk.id,
            )

        except Exception as e:
            error_msg = f"Failed to update chunk {chunk.id}: {e}"
            logger.error(error_msg, chunk_id=chunk.id, error=str(e))
            raise VectorStoreError(error_msg) from e

    def delete_chunk(self, chunk_id: str) -> None:
        """
        Delete a chunk from the vector store.

        Args:
            chunk_id: ID of the chunk to delete
        """
        self._ensure_connected()

        try:
            self.table.delete(f"id = '{chunk_id}'")

            logger.debug(
                "Deleted chunk from vector store",
                chunk_id=chunk_id,
            )

        except Exception as e:
            error_msg = f"Failed to delete chunk {chunk_id}: {e}"
            logger.error(error_msg, chunk_id=chunk_id, error=str(e))
            raise VectorStoreError(error_msg) from e

    def delete_chunks_by_file(self, file_path: Path) -> int:
        """
        Delete all chunks from a specific file.

        Args:
            file_path: Path of the file whose chunks should be deleted

        Returns:
            Number of chunks deleted
        """
        self._ensure_connected()

        try:
            # Get count before deletion for reporting
            file_path_str = str(file_path)
            results = (
                self.table.search().where(f"file_path = '{file_path_str}'").to_list()
            )
            chunk_count = len(results)

            # Delete chunks
            self.table.delete(f"file_path = '{file_path_str}'")

            logger.info(
                "Deleted chunks by file",
                file_path=file_path_str,
                chunks_deleted=chunk_count,
            )

            return chunk_count

        except Exception as e:
            error_msg = f"Failed to delete chunks for file {file_path}: {e}"
            logger.error(error_msg, file_path=str(file_path), error=str(e))
            raise VectorStoreError(error_msg) from e

    def get_stats(self) -> VectorStoreStats:
        """
        Get statistics about the vector store.

        Returns:
            VectorStoreStats with comprehensive statistics
        """
        self._ensure_connected()

        try:
            # Get all records for analysis
            results = (
                self.table.search().limit(100000).to_list()
            )  # Large limit for stats

            total_chunks = len(results)
            if total_chunks == 0:
                return VectorStoreStats(
                    total_chunks=0,
                    languages={},
                    chunk_types={},
                    avg_complexity=0.0,
                    storage_size_mb=0.0,
                    last_updated="",
                )

            # Analyze languages
            languages: dict[str, int] = {}
            chunk_types: dict[str, int] = {}
            complexity_scores = []
            last_updated_times = []

            for result in results:
                # Count languages
                language = result.get("language", "unknown")
                languages[language] = languages.get(language, 0) + 1

                # Count chunk types
                chunk_type = result.get("chunk_type", "unknown")
                chunk_types[chunk_type] = chunk_types.get(chunk_type, 0) + 1

                # Collect complexity scores
                complexity = result.get("complexity_score", 0.0)
                complexity_scores.append(complexity)

                # Track last updated times
                updated_at = result.get("updated_at", "")
                if updated_at:
                    last_updated_times.append(updated_at)

            # Calculate average complexity
            avg_complexity = (
                sum(complexity_scores) / len(complexity_scores)
                if complexity_scores
                else 0.0
            )

            # Estimate storage size (rough approximation)
            # LanceDB uses columnar storage, so this is a rough estimate
            avg_content_size = (
                sum(len(r.get("content", "")) for r in results) / total_chunks
                if total_chunks > 0
                else 0
            )
            estimated_size_mb = (total_chunks * (avg_content_size + 384 * 4 + 500)) / (
                1024 * 1024
            )  # Content + embedding + metadata

            # Get most recent update time
            last_updated = max(last_updated_times) if last_updated_times else ""

            return VectorStoreStats(
                total_chunks=total_chunks,
                languages=languages,
                chunk_types=chunk_types,
                avg_complexity=round(avg_complexity, 2),
                storage_size_mb=round(estimated_size_mb, 2),
                last_updated=last_updated,
            )

        except Exception as e:
            logger.error("Failed to get vector store stats", error=str(e))
            # Return empty stats on error
            return VectorStoreStats(
                total_chunks=0,
                languages={},
                chunk_types={},
                avg_complexity=0.0,
                storage_size_mb=0.0,
                last_updated="",
            )

    def clear(self) -> None:
        """Clear all data from the vector store."""
        self._ensure_connected()

        try:
            # Drop and recreate table
            self.db.drop_table(self.table_name)
            self._create_table()

            logger.info(
                "Vector store cleared",
                table_name=self.table_name,
            )

        except Exception as e:
            error_msg = f"Failed to clear vector store: {e}"
            logger.error(error_msg, table_name=self.table_name, error=str(e))
            raise VectorStoreError(error_msg) from e

    def health_check(self) -> dict[str, Any]:
        """
        Perform health check on the vector store.

        Returns:
            Health status dictionary
        """
        health = {
            "status": "unknown",
            "connected": self._connected,
            "db_path": str(self.db_path),
            "table_name": self.table_name,
            "table_exists": False,
            "total_chunks": 0,
            "error": None,
        }

        try:
            self._ensure_connected()

            # Check if table exists and get basic info
            if self.table_name in self.db.table_names():
                health["table_exists"] = True

                # Get count
                try:
                    self.table.search().limit(1).to_list()  # Test table access
                    stats = self.get_stats()
                    health["total_chunks"] = stats.total_chunks
                    health["storage_size_mb"] = stats.storage_size_mb
                except Exception:
                    # Table might be empty, which is fine
                    health["total_chunks"] = 0

            health["status"] = "healthy"

        except Exception as e:
            health.update(
                {
                    "status": "unhealthy",
                    "error": str(e),
                }
            )

        return health


def create_vector_store(db_path: Path, table_name: str = "code_chunks") -> VectorStore:
    """
    Factory function to create a vector store.

    Args:
        db_path: Path to the LanceDB database directory
        table_name: Name of the table to store code chunks

    Returns:
        Configured VectorStore instance
    """
    return VectorStore(db_path, table_name)
