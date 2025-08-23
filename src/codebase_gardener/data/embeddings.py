"""
Nomic Embeddings Integration for Semantic Code Representation

This module provides integration with Nomic embeddings for generating semantic
vector representations of code chunks. Optimized for batch processing and
efficient memory usage on Mac Mini M4 constraints.
"""

import hashlib
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

import numpy as np
import structlog
from sentence_transformers import SentenceTransformer

from codebase_gardener.data.preprocessor import CodeChunk
from codebase_gardener.utils.error_handling import (
    EmbeddingError,
    retry_with_backoff,
)

logger = structlog.get_logger(__name__)


@dataclass
class EmbeddingConfig:
    """Configuration for embedding generation."""

    model_name: str = "nomic-ai/nomic-embed-text-v1.5"
    batch_size: int = 32  # Optimized for Mac Mini M4 memory constraints
    max_sequence_length: int = 2048  # Nomic model max length
    trust_remote_code: bool = True
    device: str = "mps"  # Use Metal Performance Shaders on Mac
    normalize_embeddings: bool = True
    cache_embeddings: bool = True
    cache_directory: Path | None = None

    @classmethod
    def for_production(cls) -> "EmbeddingConfig":
        """Create production-optimized configuration."""
        return cls(
            batch_size=16,  # Conservative batch size for stability
            device="mps",
            normalize_embeddings=True,
            cache_embeddings=True,
        )

    @classmethod
    def for_development(cls) -> "EmbeddingConfig":
        """Create development-optimized configuration."""
        return cls(
            batch_size=8,  # Small batch size for development
            device="cpu",  # Fallback to CPU for compatibility
            cache_embeddings=False,  # Skip caching in development
        )


@dataclass
class EmbeddingResult:
    """Result of embedding generation for a code chunk."""

    chunk_id: str
    embedding: np.ndarray
    processing_time: float
    token_count: int
    truncated: bool = False
    error: str | None = None

    @property
    def dimension(self) -> int:
        """Get embedding dimension."""
        return self.embedding.shape[0] if self.embedding is not None else 0

    @property
    def is_valid(self) -> bool:
        """Check if embedding result is valid."""
        return self.embedding is not None and self.error is None


class NomicEmbeddings:
    """
    Nomic embeddings generator for semantic code representation.

    Provides batch processing, caching, and error recovery for efficient
    embedding generation optimized for local development workflows.
    """

    def __init__(self, config: EmbeddingConfig | None = None, settings=None):
        """
        Initialize Nomic embeddings generator.

        Args:
            config: Embedding configuration, uses defaults if None
            settings: Optional settings (for component registry compatibility)
        """
        self.config = config or EmbeddingConfig()
        self.model = None
        self.is_loaded = False
        self._embedding_cache: dict[str, np.ndarray] = {}

        # Set up cache directory
        if self.config.cache_embeddings and self.config.cache_directory is None:
            self.config.cache_directory = Path.cwd() / ".embedding_cache"

        if self.config.cache_directory:
            self.config.cache_directory.mkdir(parents=True, exist_ok=True)

        logger.info(
            "Nomic embeddings initialized",
            model_name=self.config.model_name,
            batch_size=self.config.batch_size,
            device=self.config.device,
            cache_enabled=self.config.cache_embeddings,
        )

    def ensure_loaded(self) -> None:
        """Ensure the embedding model is loaded and ready."""
        if self.is_loaded and self.model is not None:
            return

        try:
            logger.info(
                "Loading Nomic embedding model",
                model_name=self.config.model_name,
                device=self.config.device,
            )

            start_time = time.time()

            # Initialize the model with configuration
            self.model = SentenceTransformer(
                self.config.model_name,
                trust_remote_code=self.config.trust_remote_code,
                device=self.config.device,
            )

            # Set max sequence length
            self.model.max_seq_length = self.config.max_sequence_length

            load_time = time.time() - start_time
            self.is_loaded = True

            logger.info(
                "Nomic embedding model loaded successfully",
                load_time=f"{load_time:.2f}s",
                max_seq_length=self.model.max_seq_length,
                embedding_dimension=self.model.get_sentence_embedding_dimension(),
            )

        except Exception as e:
            error_msg = f"Failed to load Nomic embedding model: {e}"
            logger.error(error_msg, model_name=self.config.model_name, error=str(e))
            raise EmbeddingError(
                error_msg,
                details={"model_name": self.config.model_name, "error": str(e)},
            ) from e

    @retry_with_backoff(max_attempts=3)
    def embed_chunk(self, chunk: CodeChunk) -> EmbeddingResult:
        """
        Generate embedding for a single code chunk.

        Args:
            chunk: Code chunk to embed

        Returns:
            EmbeddingResult with embedding and metadata
        """
        start_time = time.time()

        try:
            self.ensure_loaded()

            # Check cache first
            if self.config.cache_embeddings:
                cached_embedding = self._get_cached_embedding(chunk)
                if cached_embedding is not None:
                    logger.debug(
                        "Using cached embedding",
                        chunk_id=chunk.id,
                        cache_hit=True,
                    )
                    return EmbeddingResult(
                        chunk_id=chunk.id,
                        embedding=cached_embedding,
                        processing_time=time.time() - start_time,
                        token_count=len(chunk.content.split()),
                        truncated=len(chunk.content) > self.config.max_sequence_length,
                    )

            # Prepare text for embedding
            embedding_text = self._prepare_chunk_text(chunk)

            # Generate embedding
            embedding = self.model.encode(
                embedding_text,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False,
            )

            # Ensure numpy array
            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)

            # Cache the embedding
            if self.config.cache_embeddings:
                self._cache_embedding(chunk, embedding)

            processing_time = time.time() - start_time

            result = EmbeddingResult(
                chunk_id=chunk.id,
                embedding=embedding,
                processing_time=processing_time,
                token_count=len(embedding_text.split()),
                truncated=len(embedding_text) > self.config.max_sequence_length,
            )

            logger.debug(
                "Generated embedding for chunk",
                chunk_id=chunk.id,
                embedding_dimension=result.dimension,
                processing_time=f"{processing_time:.3f}s",
                truncated=result.truncated,
            )

            return result

        except Exception as e:
            error_msg = f"Failed to generate embedding for chunk {chunk.id}: {e}"
            logger.error(error_msg, chunk_id=chunk.id, error=str(e))

            return EmbeddingResult(
                chunk_id=chunk.id,
                embedding=np.zeros(384),  # Nomic embedding dimension
                processing_time=time.time() - start_time,
                token_count=0,
                error=error_msg,
            )

    def embed_chunks_batch(self, chunks: list[CodeChunk]) -> list[EmbeddingResult]:
        """
        Generate embeddings for multiple chunks in batches.

        Args:
            chunks: List of code chunks to embed

        Returns:
            List of EmbeddingResult objects
        """
        if not chunks:
            return []

        logger.info(
            "Starting batch embedding generation",
            chunk_count=len(chunks),
            batch_size=self.config.batch_size,
        )

        start_time = time.time()
        results = []

        try:
            self.ensure_loaded()

            # Process in batches
            for i in range(0, len(chunks), self.config.batch_size):
                batch = chunks[i : i + self.config.batch_size]
                batch_results = self._process_batch(batch)
                results.extend(batch_results)

                # Progress logging
                processed = min(i + self.config.batch_size, len(chunks))
                logger.info(
                    "Batch processing progress",
                    processed=processed,
                    total=len(chunks),
                    progress_pct=f"{(processed / len(chunks) * 100):.1f}%",
                )

            total_time = time.time() - start_time
            successful_results = [r for r in results if r.is_valid]

            logger.info(
                "Batch embedding generation completed",
                total_chunks=len(chunks),
                successful=len(successful_results),
                failed=len(results) - len(successful_results),
                total_time=f"{total_time:.2f}s",
                avg_time_per_chunk=f"{total_time / len(chunks):.3f}s",
            )

            return results

        except Exception as e:
            error_msg = f"Batch embedding generation failed: {e}"
            logger.error(error_msg, chunk_count=len(chunks), error=str(e))

            # Return error results for all chunks
            return [
                EmbeddingResult(
                    chunk_id=chunk.id,
                    embedding=np.zeros(384),
                    processing_time=0.0,
                    token_count=0,
                    error=error_msg,
                )
                for chunk in chunks
            ]

    def _process_batch(self, batch: list[CodeChunk]) -> list[EmbeddingResult]:
        """Process a single batch of chunks."""
        batch_start_time = time.time()

        # Separate chunks that need processing from cached ones
        to_process = []
        results = []

        for chunk in batch:
            if self.config.cache_embeddings:
                cached_embedding = self._get_cached_embedding(chunk)
                if cached_embedding is not None:
                    results.append(
                        EmbeddingResult(
                            chunk_id=chunk.id,
                            embedding=cached_embedding,
                            processing_time=0.0,
                            token_count=len(chunk.content.split()),
                            truncated=len(chunk.content)
                            > self.config.max_sequence_length,
                        )
                    )
                    continue

            to_process.append(chunk)

        # Process remaining chunks
        if to_process:
            try:
                # Prepare texts
                texts = [self._prepare_chunk_text(chunk) for chunk in to_process]

                # Generate embeddings in batch
                embeddings = self.model.encode(
                    texts,
                    batch_size=len(texts),  # Process entire batch at once
                    normalize_embeddings=self.config.normalize_embeddings,
                    show_progress_bar=False,
                )

                # Ensure numpy array format
                if not isinstance(embeddings, np.ndarray):
                    embeddings = np.array(embeddings)

                # Create results
                for i, chunk in enumerate(to_process):
                    embedding = embeddings[i]

                    # Cache the embedding
                    if self.config.cache_embeddings:
                        self._cache_embedding(chunk, embedding)

                    results.append(
                        EmbeddingResult(
                            chunk_id=chunk.id,
                            embedding=embedding,
                            processing_time=(time.time() - batch_start_time)
                            / len(to_process),
                            token_count=len(texts[i].split()),
                            truncated=len(texts[i]) > self.config.max_sequence_length,
                        )
                    )

            except Exception as e:
                # Handle batch processing error
                error_msg = f"Batch processing failed: {e}"
                for chunk in to_process:
                    results.append(
                        EmbeddingResult(
                            chunk_id=chunk.id,
                            embedding=np.zeros(384),
                            processing_time=0.0,
                            token_count=0,
                            error=error_msg,
                        )
                    )

        # Sort results to match original batch order
        chunk_id_to_result = {r.chunk_id: r for r in results}
        return [chunk_id_to_result[chunk.id] for chunk in batch]

    def _prepare_chunk_text(self, chunk: CodeChunk) -> str:
        """
        Prepare chunk text for embedding generation.

        Combines code content with relevant metadata for better semantic representation.
        """
        # Base content
        text_parts = [chunk.content.strip()]

        # Add semantic context for better embeddings
        context_parts = []

        # Add chunk type and language context
        context_parts.append(f"Language: {chunk.language}")
        context_parts.append(f"Type: {chunk.chunk_type.value}")

        # Add file context if available
        if chunk.file_path:
            context_parts.append(f"File: {chunk.file_path.name}")

        # Add function/class name if available
        metadata = chunk.metadata
        if metadata.get("element_name"):
            context_parts.append(f"Name: {metadata['element_name']}")

        # Add dependencies context (top 3 for relevance)
        if chunk.dependencies:
            deps = chunk.dependencies[:3]  # Limit to avoid token explosion
            context_parts.append(f"Dependencies: {', '.join(deps)}")

        # Add complexity context for function/method types
        if (
            chunk.chunk_type.value in ["function", "method", "class"]
            and chunk.complexity_score > 0
        ):
            complexity_level = (
                "low"
                if chunk.complexity_score < 3
                else "medium"
                if chunk.complexity_score < 8
                else "high"
            )
            context_parts.append(f"Complexity: {complexity_level}")

        # Combine context
        if context_parts:
            context_text = " | ".join(context_parts)
            # Prepend context to help with semantic understanding
            text_parts.insert(0, f"[{context_text}]")

        full_text = "\n".join(text_parts)

        # Truncate if necessary (leave room for context)
        if len(full_text) > self.config.max_sequence_length:
            # Try to keep context and truncate content
            context_length = len(context_parts[0]) if context_parts else 0
            max_content_length = self.config.max_sequence_length - context_length - 100

            if max_content_length > 100:  # Ensure minimum content
                truncated_content = chunk.content[:max_content_length] + "..."
                text_parts[1] = truncated_content  # Update content part
                full_text = "\n".join(text_parts)

        return full_text

    def _generate_cache_key(self, chunk: CodeChunk) -> str:
        """Generate cache key for a chunk."""
        # Include content, metadata, and config in cache key
        key_data = f"{chunk.content}{chunk.metadata}{self.config.model_name}{self.config.normalize_embeddings}"
        return hashlib.md5(key_data.encode("utf-8"), usedforsecurity=False).hexdigest()

    def _get_cached_embedding(self, chunk: CodeChunk) -> np.ndarray | None:
        """Get cached embedding for a chunk."""
        if not self.config.cache_embeddings:
            return None

        cache_key = self._generate_cache_key(chunk)

        # Check in-memory cache first
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]

        # Check file cache
        if self.config.cache_directory:
            cache_file = self.config.cache_directory / f"{cache_key}.npy"
            if cache_file.exists():
                try:
                    embedding = np.load(cache_file)
                    self._embedding_cache[
                        cache_key
                    ] = embedding  # Update in-memory cache
                    return embedding
                except Exception as e:
                    logger.warning(
                        "Failed to load cached embedding",
                        cache_file=str(cache_file),
                        error=str(e),
                    )

        return None

    def _cache_embedding(self, chunk: CodeChunk, embedding: np.ndarray) -> None:
        """Cache embedding for a chunk."""
        if not self.config.cache_embeddings:
            return

        cache_key = self._generate_cache_key(chunk)

        # Update in-memory cache
        self._embedding_cache[cache_key] = embedding

        # Update file cache
        if self.config.cache_directory:
            cache_file = self.config.cache_directory / f"{cache_key}.npy"
            try:
                np.save(cache_file, embedding)
            except Exception as e:
                logger.warning(
                    "Failed to cache embedding to file",
                    cache_file=str(cache_file),
                    error=str(e),
                )

    def embed_query(self, query: str) -> np.ndarray:
        """
        Generate embedding for a search query.

        Args:
            query: Search query text

        Returns:
            Query embedding as numpy array
        """
        try:
            self.ensure_loaded()

            embedding = self.model.encode(
                query,
                normalize_embeddings=self.config.normalize_embeddings,
                show_progress_bar=False,
            )

            if not isinstance(embedding, np.ndarray):
                embedding = np.array(embedding)

            logger.debug(
                "Generated query embedding",
                query_length=len(query),
                embedding_dimension=embedding.shape[0],
            )

            return embedding

        except Exception as e:
            error_msg = f"Failed to generate query embedding: {e}"
            logger.error(
                error_msg,
                query=query[:50] + "..." if len(query) > 50 else query,
                error=str(e),
            )
            raise EmbeddingError(error_msg) from e

    def get_embedding_dimension(self) -> int:
        """Get the dimension of embeddings produced by this model."""
        try:
            self.ensure_loaded()
            return self.model.get_sentence_embedding_dimension()
        except Exception:
            # Fallback to known Nomic dimension
            return 384

    def clear_cache(self) -> None:
        """Clear embedding cache."""
        self._embedding_cache.clear()

        if self.config.cache_directory and self.config.cache_directory.exists():
            # Remove cache files
            try:
                cache_files = list(self.config.cache_directory.glob("*.npy"))
                for cache_file in cache_files:
                    cache_file.unlink()

                logger.info(
                    "Embedding cache cleared",
                    cache_files_removed=len(cache_files),
                    cache_directory=str(self.config.cache_directory),
                )
            except Exception as e:
                logger.warning(
                    "Failed to clear file cache",
                    cache_directory=str(self.config.cache_directory),
                    error=str(e),
                )

    def health_check(self) -> dict[str, Any]:
        """Perform health check on the embeddings system."""
        health = {
            "status": "unknown",
            "model_loaded": self.is_loaded,
            "model_name": self.config.model_name,
            "cache_enabled": self.config.cache_embeddings,
            "cache_size": len(self._embedding_cache),
            "error": None,
        }

        try:
            # Test embedding generation
            test_embedding = self.embed_query("test health check query")

            health.update(
                {
                    "status": "healthy",
                    "embedding_dimension": test_embedding.shape[0],
                    "test_embedding_generated": True,
                }
            )

        except Exception as e:
            health.update(
                {
                    "status": "unhealthy",
                    "error": str(e),
                    "test_embedding_generated": False,
                }
            )

        return health


def create_embeddings_generator(
    config: EmbeddingConfig | None = None,
) -> NomicEmbeddings:
    """
    Factory function to create Nomic embeddings generator.

    Args:
        config: Optional embedding configuration

    Returns:
        Configured NomicEmbeddings instance
    """
    return NomicEmbeddings(config)
