"""
Embedding Manager

Orchestrates embedding generation, caching, and vector storage for code chunks.
Provides high-level interface for embedding-related operations with batch processing,
incremental updates, and quality validation.
"""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import structlog

from codebase_gardener.data.embeddings import (
    EmbeddingConfig,
    EmbeddingResult,
    NomicEmbeddings,
)
from codebase_gardener.data.preprocessor import CodeChunk
from codebase_gardener.data.vector_store import SearchResult, VectorStore
from codebase_gardener.utils.error_handling import EmbeddingError

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingManagerConfig:
    """Configuration for embedding manager."""

    # Embedding configuration
    embedding_config: EmbeddingConfig | None = None

    # Processing configuration
    batch_size: int = 16  # Conservative for Mac Mini M4
    max_concurrent_batches: int = 2

    # Quality validation
    min_similarity_threshold: float = 0.1
    validate_embeddings: bool = True

    # Incremental updates
    enable_incremental_updates: bool = True
    change_detection_method: str = "content_hash"  # "content_hash" or "file_mtime"

    # Storage paths
    vector_store_path: Path | None = None

    @classmethod
    def for_production(cls) -> "EmbeddingManagerConfig":
        """Create production-optimized configuration."""
        return cls(
            embedding_config=EmbeddingConfig.for_production(),
            batch_size=12,
            max_concurrent_batches=2,
            validate_embeddings=True,
            enable_incremental_updates=True,
        )

    @classmethod
    def for_development(cls) -> "EmbeddingManagerConfig":
        """Create development-optimized configuration."""
        return cls(
            embedding_config=EmbeddingConfig.for_development(),
            batch_size=4,
            max_concurrent_batches=1,
            validate_embeddings=False,
            enable_incremental_updates=False,
        )


@dataclass
class EmbeddingJobResult:
    """Result of an embedding generation job."""

    total_chunks: int
    processed_chunks: int
    successful_embeddings: int
    failed_embeddings: int
    cached_embeddings: int
    total_processing_time: float
    average_time_per_chunk: float
    errors: list[str]

    @property
    def success_rate(self) -> float:
        """Calculate success rate as percentage."""
        if self.processed_chunks == 0:
            return 0.0
        return (self.successful_embeddings / self.processed_chunks) * 100.0

    @property
    def cache_hit_rate(self) -> float:
        """Calculate cache hit rate as percentage."""
        if self.total_chunks == 0:
            return 0.0
        return (self.cached_embeddings / self.total_chunks) * 100.0


class EmbeddingManager:
    """
    High-level embedding management system.

    Coordinates embedding generation, caching, vector storage, and incremental updates
    for efficient semantic code representation.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        config: EmbeddingManagerConfig | None = None,
        settings=None,
    ):
        """
        Initialize embedding manager.

        Args:
            vector_store: Vector store for embedding storage
            config: Configuration for embedding manager
            settings: Optional settings (for component registry compatibility)
        """
        self.config = config or EmbeddingManagerConfig()
        self.vector_store = vector_store
        self.embeddings_generator = NomicEmbeddings(
            self.config.embedding_config, settings
        )

        # Content hashes for change detection
        self._content_hashes: dict[str, str] = {}

        logger.info(
            "Embedding manager initialized",
            batch_size=self.config.batch_size,
            validate_embeddings=self.config.validate_embeddings,
            incremental_updates=self.config.enable_incremental_updates,
        )

    def process_chunks(self, chunks: list[CodeChunk]) -> EmbeddingJobResult:
        """
        Process code chunks to generate and store embeddings.

        Args:
            chunks: List of code chunks to process

        Returns:
            EmbeddingJobResult with processing statistics
        """
        if not chunks:
            return EmbeddingJobResult(
                total_chunks=0,
                processed_chunks=0,
                successful_embeddings=0,
                failed_embeddings=0,
                cached_embeddings=0,
                total_processing_time=0.0,
                average_time_per_chunk=0.0,
                errors=[],
            )

        logger.info(
            "Starting embedding processing job",
            total_chunks=len(chunks),
            batch_size=self.config.batch_size,
        )

        start_time = time.time()
        errors = []

        # Filter chunks if incremental updates are enabled
        if self.config.enable_incremental_updates:
            chunks = self._filter_changed_chunks(chunks)
            logger.info(
                "Incremental update filtering",
                original_chunks=len(chunks),
                chunks_to_process=len(chunks),
            )

        if not chunks:
            return EmbeddingJobResult(
                total_chunks=0,
                processed_chunks=0,
                successful_embeddings=0,
                failed_embeddings=0,
                cached_embeddings=0,
                total_processing_time=time.time() - start_time,
                average_time_per_chunk=0.0,
                errors=[],
            )

        # Process chunks in batches
        all_results = []
        successful_embeddings = 0
        failed_embeddings = 0
        cached_embeddings = 0

        for i in range(0, len(chunks), self.config.batch_size):
            batch = chunks[i : i + self.config.batch_size]

            try:
                logger.info(
                    "Processing embedding batch",
                    batch_number=i // self.config.batch_size + 1,
                    batch_size=len(batch),
                    progress=f"{i + len(batch)}/{len(chunks)}",
                )

                # Generate embeddings for batch
                batch_results = self.embeddings_generator.embed_chunks_batch(batch)
                all_results.extend(batch_results)

                # Process results
                valid_results = []
                for result in batch_results:
                    if result.is_valid:
                        valid_results.append(result)
                        if hasattr(result, "cached") and result.cached:
                            cached_embeddings += 1
                        else:
                            successful_embeddings += 1
                    else:
                        failed_embeddings += 1
                        if result.error:
                            errors.append(result.error)

                # Store valid embeddings in vector store
                if valid_results:
                    self._store_embedding_results(batch, valid_results)

            except Exception as e:
                error_msg = f"Batch processing failed: {e}"
                logger.error(
                    error_msg, batch_start=i, batch_size=len(batch), error=str(e)
                )
                errors.append(error_msg)
                failed_embeddings += len(batch)

        # Update content hashes for processed chunks
        if self.config.enable_incremental_updates:
            self._update_content_hashes(chunks)

        total_processing_time = time.time() - start_time
        processed_chunks = len(chunks)

        result = EmbeddingJobResult(
            total_chunks=len(chunks),
            processed_chunks=processed_chunks,
            successful_embeddings=successful_embeddings,
            failed_embeddings=failed_embeddings,
            cached_embeddings=cached_embeddings,
            total_processing_time=total_processing_time,
            average_time_per_chunk=total_processing_time / processed_chunks
            if processed_chunks > 0
            else 0.0,
            errors=errors,
        )

        logger.info(
            "Embedding processing job completed",
            **{
                "total_chunks": result.total_chunks,
                "successful": result.successful_embeddings,
                "failed": result.failed_embeddings,
                "cached": result.cached_embeddings,
                "success_rate": f"{result.success_rate:.1f}%",
                "cache_hit_rate": f"{result.cache_hit_rate:.1f}%",
                "total_time": f"{result.total_processing_time:.2f}s",
                "avg_time_per_chunk": f"{result.average_time_per_chunk:.3f}s",
            },
        )

        return result

    def search_similar_chunks(
        self,
        query: str,
        limit: int = 10,
        language_filter: str | None = None,
        chunk_type_filter: str | None = None,
        min_similarity: float | None = None,
    ) -> list[SearchResult]:
        """
        Search for code chunks similar to a text query.

        Args:
            query: Text query to search for
            limit: Maximum number of results
            language_filter: Optional language filter
            chunk_type_filter: Optional chunk type filter
            min_similarity: Optional minimum similarity threshold

        Returns:
            List of similar chunks with similarity scores
        """
        try:
            # Generate query embedding
            query_embedding = self.embeddings_generator.embed_query(query)

            # Use configured minimum similarity if not specified
            if min_similarity is None:
                min_similarity = self.config.min_similarity_threshold

            # Search vector store
            results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                limit=limit,
                language_filter=language_filter,
                chunk_type_filter=chunk_type_filter,
                min_similarity=min_similarity,
            )

            logger.debug(
                "Similarity search completed",
                query_length=len(query),
                results_found=len(results),
                limit=limit,
                min_similarity=min_similarity,
            )

            return results

        except Exception as e:
            error_msg = f"Similarity search failed: {e}"
            logger.error(
                error_msg,
                query=query[:50] + "..." if len(query) > 50 else query,
                error=str(e),
            )
            raise EmbeddingError(error_msg) from e

    def update_chunk_embedding(self, chunk: CodeChunk) -> bool:
        """
        Update embedding for a single chunk.

        Args:
            chunk: Code chunk to update

        Returns:
            True if update successful, False otherwise
        """
        try:
            # Generate new embedding
            result = self.embeddings_generator.embed_chunk(chunk)

            if result.is_valid:
                # Update in vector store
                self.vector_store.update_chunk(chunk, result.embedding)

                # Update content hash
                if self.config.enable_incremental_updates:
                    self._update_content_hashes([chunk])

                logger.debug(
                    "Updated chunk embedding",
                    chunk_id=chunk.id,
                    processing_time=f"{result.processing_time:.3f}s",
                )
                return True
            else:
                logger.error(
                    "Failed to update chunk embedding",
                    chunk_id=chunk.id,
                    error=result.error,
                )
                return False

        except Exception as e:
            logger.error(
                "Error updating chunk embedding",
                chunk_id=chunk.id,
                error=str(e),
            )
            return False

    def delete_chunk_embeddings(self, chunk_ids: list[str]) -> int:
        """
        Delete embeddings for specified chunks.

        Args:
            chunk_ids: List of chunk IDs to delete

        Returns:
            Number of chunks successfully deleted
        """
        deleted_count = 0

        for chunk_id in chunk_ids:
            try:
                self.vector_store.delete_chunk(chunk_id)
                deleted_count += 1

                # Remove from content hash tracking
                self._content_hashes.pop(chunk_id, None)

            except Exception as e:
                logger.error(
                    "Failed to delete chunk embedding",
                    chunk_id=chunk_id,
                    error=str(e),
                )

        logger.info(
            "Deleted chunk embeddings",
            requested=len(chunk_ids),
            deleted=deleted_count,
        )

        return deleted_count

    def delete_file_embeddings(self, file_path: Path) -> int:
        """
        Delete all embeddings for a specific file.

        Args:
            file_path: Path of file whose embeddings should be deleted

        Returns:
            Number of chunks deleted
        """
        try:
            deleted_count = self.vector_store.delete_chunks_by_file(file_path)

            # Remove file chunks from content hash tracking
            file_path_str = str(file_path)
            keys_to_remove = [
                key
                for key in self._content_hashes.keys()
                if key.startswith(file_path_str)
            ]
            for key in keys_to_remove:
                del self._content_hashes[key]

            logger.info(
                "Deleted file embeddings",
                file_path=str(file_path),
                chunks_deleted=deleted_count,
            )

            return deleted_count

        except Exception as e:
            logger.error(
                "Failed to delete file embeddings",
                file_path=str(file_path),
                error=str(e),
            )
            return 0

    def validate_embeddings_quality(self, chunks: list[CodeChunk]) -> dict[str, Any]:
        """
        Validate the quality of stored embeddings.

        Args:
            chunks: Chunks to validate

        Returns:
            Validation results dictionary
        """
        if not self.config.validate_embeddings:
            return {"validation_enabled": False}

        logger.info(
            "Starting embedding quality validation",
            chunk_count=len(chunks),
        )

        validation_results = {
            "validation_enabled": True,
            "total_chunks": len(chunks),
            "valid_embeddings": 0,
            "invalid_embeddings": 0,
            "missing_embeddings": 0,
            "quality_issues": [],
        }

        for chunk in chunks[
            : min(100, len(chunks))
        ]:  # Limit validation for performance
            try:
                # Check if chunk exists in vector store
                stored_chunk = self.vector_store.get_chunk_by_id(chunk.id)

                if stored_chunk is None:
                    validation_results["missing_embeddings"] += 1
                    validation_results["quality_issues"].append(
                        f"Missing embedding for chunk {chunk.id}"
                    )
                    continue

                # Basic content consistency check
                if stored_chunk.content != chunk.content:
                    validation_results["invalid_embeddings"] += 1
                    validation_results["quality_issues"].append(
                        f"Content mismatch for chunk {chunk.id}"
                    )
                else:
                    validation_results["valid_embeddings"] += 1

            except Exception as e:
                validation_results["invalid_embeddings"] += 1
                validation_results["quality_issues"].append(
                    f"Validation error for chunk {chunk.id}: {e}"
                )

        logger.info(
            "Embedding quality validation completed",
            **{
                "valid": validation_results["valid_embeddings"],
                "invalid": validation_results["invalid_embeddings"],
                "missing": validation_results["missing_embeddings"],
                "issues": len(validation_results["quality_issues"]),
            },
        )

        return validation_results

    def get_stats(self) -> dict[str, Any]:
        """Get comprehensive embedding system statistics."""
        try:
            vector_stats = self.vector_store.get_stats()
            embedding_health = self.embeddings_generator.health_check()

            return {
                "vector_store": {
                    "total_chunks": vector_stats.total_chunks,
                    "languages": vector_stats.languages,
                    "chunk_types": vector_stats.chunk_types,
                    "avg_complexity": vector_stats.avg_complexity,
                    "storage_size_mb": vector_stats.storage_size_mb,
                    "last_updated": vector_stats.last_updated,
                },
                "embeddings_generator": embedding_health,
                "configuration": {
                    "batch_size": self.config.batch_size,
                    "validate_embeddings": self.config.validate_embeddings,
                    "incremental_updates": self.config.enable_incremental_updates,
                    "min_similarity_threshold": self.config.min_similarity_threshold,
                },
                "content_hashes_tracked": len(self._content_hashes),
            }
        except Exception as e:
            logger.error("Failed to get embedding system stats", error=str(e))
            return {"error": str(e)}

    def _filter_changed_chunks(self, chunks: list[CodeChunk]) -> list[CodeChunk]:
        """Filter chunks to only include those that have changed."""
        if not self.config.enable_incremental_updates:
            return chunks

        changed_chunks = []
        for chunk in chunks:
            current_hash = self._compute_content_hash(chunk)
            stored_hash = self._content_hashes.get(chunk.id)

            if stored_hash != current_hash:
                changed_chunks.append(chunk)

        return changed_chunks

    def _compute_content_hash(self, chunk: CodeChunk) -> str:
        """Compute hash for chunk content to detect changes."""
        # Include content and key metadata in hash
        hash_input = (
            f"{chunk.content}{chunk.file_path}{chunk.start_line}{chunk.end_line}"
        )
        return hashlib.md5(
            hash_input.encode("utf-8"), usedforsecurity=False
        ).hexdigest()

    def _update_content_hashes(self, chunks: list[CodeChunk]) -> None:
        """Update stored content hashes for processed chunks."""
        for chunk in chunks:
            content_hash = self._compute_content_hash(chunk)
            self._content_hashes[chunk.id] = content_hash

    def _store_embedding_results(
        self,
        chunks: list[CodeChunk],
        results: list[EmbeddingResult],
    ) -> None:
        """Store embedding results in vector store."""
        try:
            # Prepare chunks and embeddings for storage
            valid_chunks = []
            valid_embeddings = []

            for chunk, result in zip(chunks, results, strict=True):
                if result.is_valid and result.chunk_id == chunk.id:
                    valid_chunks.append(chunk)
                    valid_embeddings.append(result.embedding)

            if valid_chunks:
                self.vector_store.add_chunks(valid_chunks, valid_embeddings)

                logger.debug(
                    "Stored embedding results",
                    chunks_stored=len(valid_chunks),
                )

        except Exception as e:
            error_msg = f"Failed to store embedding results: {e}"
            logger.error(error_msg, chunks_count=len(chunks), error=str(e))
            raise EmbeddingError(error_msg) from e

    def health_check(self) -> dict[str, Any]:
        """Perform comprehensive health check."""
        health = {
            "status": "unknown",
            "components": {},
            "error": None,
        }

        try:
            # Check embeddings generator
            embeddings_health = self.embeddings_generator.health_check()
            health["components"]["embeddings_generator"] = embeddings_health

            # Check vector store
            vector_store_health = self.vector_store.health_check()
            health["components"]["vector_store"] = vector_store_health

            # Overall status
            all_healthy = (
                embeddings_health.get("status") == "healthy"
                and vector_store_health.get("status") == "healthy"
            )

            health["status"] = "healthy" if all_healthy else "degraded"

        except Exception as e:
            health.update(
                {
                    "status": "unhealthy",
                    "error": str(e),
                }
            )

        return health


def create_embedding_manager(
    vector_store: VectorStore,
    config: EmbeddingManagerConfig | None = None,
) -> EmbeddingManager:
    """
    Factory function to create embedding manager.

    Args:
        vector_store: Vector store instance
        config: Optional configuration

    Returns:
        Configured EmbeddingManager instance
    """
    return EmbeddingManager(vector_store, config)
