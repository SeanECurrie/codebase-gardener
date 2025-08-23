"""
RAG Engine Implementation

This module provides a Retrieval-Augmented Generation (RAG) engine that combines
semantic similarity search with context-aware prompt enhancement for code analysis.
Optimized for Mac Mini M4 constraints with efficient caching and batching.

Key Features:
- Context retrieval using semantic similarity search within 200ms for <1000 tokens
- Query embedding and context ranking algorithms
- Context formatting and prompt enhancement for language models
- Relevance scoring and context quality assessment
- Context caching and optimization for repeated queries
- Project-specific isolation and multi-tenant support
"""

import hashlib
import time
from dataclasses import dataclass, field
from typing import Any
from uuid import uuid4

import numpy as np
import structlog

from codebase_gardener.data.embedding_manager import EmbeddingManager
from codebase_gardener.data.embeddings import EmbeddingConfig, NomicEmbeddings
from codebase_gardener.data.preprocessor import CodeChunk
from codebase_gardener.data.vector_store import SearchResult, VectorStore
from codebase_gardener.utils.error_handling import (
    RAGEngineError,
    retry_with_backoff,
)

logger = structlog.get_logger(__name__)


@dataclass
class RAGConfig:
    """Configuration for RAG engine operations."""

    # Retrieval configuration
    max_context_chunks: int = 5  # Maximum chunks to retrieve
    min_similarity_threshold: float = 0.3  # Minimum similarity for relevance
    context_window_size: int = 4000  # Maximum total context size in chars
    retrieval_timeout_ms: int = 200  # Target retrieval time under 200ms

    # Ranking configuration
    relevance_score_weight: float = 0.6  # Weight for similarity score
    recency_weight: float = 0.2  # Weight for chunk recency
    quality_weight: float = 0.2  # Weight for chunk quality

    # Context formatting
    include_metadata: bool = True  # Include chunk metadata in context
    include_file_paths: bool = True  # Include file paths for context
    max_context_per_chunk: int = 1200  # Max chars per chunk in context

    # Caching configuration
    enable_query_cache: bool = True
    cache_ttl_seconds: int = 300  # Cache entries expire after 5 minutes
    max_cache_size: int = 100  # Maximum cached queries

    # Quality assessment
    enable_quality_filtering: bool = True
    min_chunk_quality: float = 0.3  # Minimum quality score for chunks
    boost_high_quality: bool = True  # Boost scores for high quality chunks

    @classmethod
    def for_production(cls) -> "RAGConfig":
        """Create production-optimized configuration."""
        return cls(
            max_context_chunks=3,  # Conservative for response time
            min_similarity_threshold=0.4,  # Higher threshold for quality
            context_window_size=3000,  # Reasonable context size
            retrieval_timeout_ms=150,  # Strict timeout for production
            enable_query_cache=True,
            cache_ttl_seconds=600,  # 10 minute cache
        )

    @classmethod
    def for_development(cls) -> "RAGConfig":
        """Create development-friendly configuration."""
        return cls(
            max_context_chunks=5,  # More context for development
            min_similarity_threshold=0.2,  # Lower threshold for exploration
            context_window_size=4500,  # Larger context window
            retrieval_timeout_ms=300,  # More relaxed timeout
            enable_query_cache=False,  # Disable cache for testing
        )


@dataclass
class RetrievalResult:
    """Result from context retrieval operation."""

    query: str
    query_embedding: np.ndarray
    chunks: list[SearchResult]
    total_chunks_searched: int
    retrieval_time_ms: float
    cache_hit: bool = False
    relevance_scores: list[float] = field(default_factory=list)

    @property
    def is_within_timeout(self) -> bool:
        """Check if retrieval completed within timeout."""
        return self.retrieval_time_ms <= 200.0

    @property
    def average_relevance(self) -> float:
        """Calculate average relevance score."""
        if not self.relevance_scores:
            return 0.0
        return sum(self.relevance_scores) / len(self.relevance_scores)

    @property
    def top_relevance(self) -> float:
        """Get highest relevance score."""
        return max(self.relevance_scores) if self.relevance_scores else 0.0


@dataclass
class EnhancedContext:
    """Enhanced context for prompt generation."""

    context_id: str
    formatted_context: str
    source_chunks: list[SearchResult]
    total_chars: int
    chunk_count: int
    relevance_summary: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    @property
    def is_high_quality(self) -> bool:
        """Check if context meets high quality standards."""
        return (
            self.chunk_count >= 2
            and self.relevance_summary.get("average_score", 0) >= 0.6
            and self.total_chars >= 500
        )


class QueryCache:
    """LRU cache for query results with TTL."""

    def __init__(self, max_size: int = 100, ttl_seconds: int = 300):
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self._cache: dict[str, tuple[Any, float]] = {}
        self._access_order: list[str] = []

    def _generate_key(self, query: str, **kwargs) -> str:
        """Generate cache key from query and parameters."""
        key_data = f"{query}:{sorted(kwargs.items())}"
        return hashlib.md5(key_data.encode()).hexdigest()

    def get(self, query: str, **kwargs) -> Any | None:
        """Get cached result if available and not expired."""
        key = self._generate_key(query, **kwargs)

        if key not in self._cache:
            return None

        result, timestamp = self._cache[key]

        # Check if expired
        if time.time() - timestamp > self.ttl_seconds:
            del self._cache[key]
            if key in self._access_order:
                self._access_order.remove(key)
            return None

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

        return result

    def put(self, query: str, result: Any, **kwargs) -> None:
        """Cache query result with TTL."""
        key = self._generate_key(query, **kwargs)

        # Evict oldest if at capacity
        if len(self._cache) >= self.max_size and key not in self._cache:
            oldest_key = self._access_order.pop(0)
            del self._cache[oldest_key]

        self._cache[key] = (result, time.time())

        # Update access order
        if key in self._access_order:
            self._access_order.remove(key)
        self._access_order.append(key)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._access_order.clear()

    def get_stats(self) -> dict[str, Any]:
        """Get cache statistics."""
        current_time = time.time()
        valid_entries = sum(
            1
            for _, timestamp in self._cache.values()
            if current_time - timestamp <= self.ttl_seconds
        )

        return {
            "total_entries": len(self._cache),
            "valid_entries": valid_entries,
            "max_size": self.max_size,
            "ttl_seconds": self.ttl_seconds,
        }


class RAGEngine:
    """
    Retrieval-Augmented Generation engine for code analysis.

    Provides context retrieval, relevance scoring, and prompt enhancement
    for improved code analysis with LLMs.
    """

    def __init__(
        self,
        vector_store: VectorStore,
        embedding_manager: EmbeddingManager | None = None,
        config: RAGConfig | None = None,
    ):
        """
        Initialize RAG engine.

        Args:
            vector_store: Vector store for similarity search
            embedding_manager: Optional embedding manager (creates if None)
            config: Optional configuration (uses default if None)
        """
        self.vector_store = vector_store
        self.config = config or RAGConfig.for_production()

        # Initialize embedding manager if not provided
        if embedding_manager is None:
            embedding_config = EmbeddingConfig.for_production()
            self.embedding_manager = EmbeddingManager(vector_store, embedding_config)
        else:
            self.embedding_manager = embedding_manager

        # Initialize embeddings generator for queries
        self.embeddings_generator = NomicEmbeddings(
            self.embedding_manager.config.embedding_config
            or EmbeddingConfig.for_production()
        )

        # Initialize query cache
        self.query_cache = (
            QueryCache(
                max_size=self.config.max_cache_size,
                ttl_seconds=self.config.cache_ttl_seconds,
            )
            if self.config.enable_query_cache
            else None
        )

        # Performance tracking
        self._retrieval_times: list[float] = []
        self._cache_hits: int = 0
        self._cache_misses: int = 0

        logger.info(
            "RAG engine initialized",
            max_context_chunks=self.config.max_context_chunks,
            cache_enabled=self.config.enable_query_cache,
            min_similarity=self.config.min_similarity_threshold,
        )

    @retry_with_backoff(max_attempts=2)
    def retrieve_context(
        self,
        query: str,
        language_filter: str | None = None,
        chunk_type_filter: str | None = None,
        project_context: dict[str, Any] | None = None,
    ) -> RetrievalResult:
        """
        Retrieve relevant context for a query using semantic similarity.

        Args:
            query: User query to find context for
            language_filter: Optional language filter for chunks
            chunk_type_filter: Optional chunk type filter
            project_context: Optional project-specific context

        Returns:
            RetrievalResult with retrieved chunks and metadata

        Raises:
            RAGEngineError: If retrieval fails
        """
        start_time = time.time()

        # Check cache first
        cache_key_params = {
            "language": language_filter,
            "chunk_type": chunk_type_filter,
            "max_chunks": self.config.max_context_chunks,
        }

        if self.query_cache:
            cached_result = self.query_cache.get(query, **cache_key_params)
            if cached_result:
                self._cache_hits += 1
                cached_result.cache_hit = True
                logger.debug(
                    "RAG cache hit",
                    query_hash=hashlib.md5(query.encode()).hexdigest()[:8],
                )
                return cached_result
            self._cache_misses += 1

        try:
            # Generate query embedding
            query_embedding = self.embeddings_generator.embed_query(query)

            # Perform similarity search
            search_results = self.vector_store.search_similar(
                query_embedding=query_embedding,
                limit=self.config.max_context_chunks * 2,  # Get extra for filtering
                language_filter=language_filter,
                chunk_type_filter=chunk_type_filter,
                min_similarity=self.config.min_similarity_threshold,
            )

            # Apply quality filtering if enabled
            if self.config.enable_quality_filtering and search_results:
                search_results = self._filter_by_quality(search_results)

            # Rank and select top results
            ranked_results = self._rank_results(search_results, query)
            final_results = ranked_results[: self.config.max_context_chunks]

            # Calculate relevance scores
            relevance_scores = [
                self._calculate_relevance_score(result, query)
                for result in final_results
            ]

            # Create retrieval result
            retrieval_time_ms = (time.time() - start_time) * 1000
            result = RetrievalResult(
                query=query,
                query_embedding=query_embedding,
                chunks=final_results,
                total_chunks_searched=len(search_results),
                retrieval_time_ms=retrieval_time_ms,
                relevance_scores=relevance_scores,
            )

            # Cache result if caching enabled
            if self.query_cache:
                self.query_cache.put(query, result, **cache_key_params)

            # Track performance
            self._retrieval_times.append(retrieval_time_ms)

            logger.debug(
                "Context retrieval completed",
                query_hash=hashlib.md5(query.encode()).hexdigest()[:8],
                chunks_found=len(final_results),
                retrieval_time_ms=retrieval_time_ms,
                cache_hit=False,
                average_relevance=result.average_relevance,
            )

            return result

        except Exception as e:
            error_msg = f"Context retrieval failed: {e}"
            logger.error(
                error_msg,
                query_hash=hashlib.md5(query.encode()).hexdigest()[:8],
                error=str(e),
            )
            raise RAGEngineError(error_msg) from e

    def _filter_by_quality(
        self, search_results: list[SearchResult]
    ) -> list[SearchResult]:
        """Filter search results by chunk quality."""
        filtered = []

        for result in search_results:
            chunk = result.chunk

            # Check minimum quality if available
            quality_score = chunk.metadata.get("quality_score", 1.0)
            if quality_score < self.config.min_chunk_quality:
                continue

            # Check content quality indicators
            if len(chunk.content.strip()) < 50:  # Too short
                continue

            # Check for trivial content patterns
            if self._is_trivial_content(chunk.content):
                continue

            filtered.append(result)

        return filtered

    def _is_trivial_content(self, content: str) -> bool:
        """Check if content is trivial and should be filtered out."""
        content = content.strip().lower()

        # Common trivial patterns
        trivial_patterns = [
            "pass",
            "return none",
            "return true",
            "return false",
            "# todo",
            "# fixme",
            "...",
        ]

        for pattern in trivial_patterns:
            if pattern in content:
                return True

        # Check for very short or mostly whitespace content
        if len(content.replace(" ", "").replace("\n", "")) < 20:
            return True

        return False

    def _rank_results(
        self, search_results: list[SearchResult], query: str
    ) -> list[SearchResult]:
        """Rank search results using multiple relevance factors."""
        scored_results = []

        for result in search_results:
            # Base similarity score
            similarity_score = (
                result.similarity_score * self.config.relevance_score_weight
            )

            # Quality boost
            quality_score = result.chunk.metadata.get("quality_score", 0.5)
            quality_boost = quality_score * self.config.quality_weight

            # Recency boost (newer chunks preferred)
            recency_boost = (
                self._calculate_recency_score(result.chunk) * self.config.recency_weight
            )

            # Contextual relevance boost
            contextual_boost = self._calculate_contextual_relevance(result.chunk, query)

            # Calculate final score
            final_score = (
                similarity_score + quality_boost + recency_boost + contextual_boost
            )

            scored_results.append((final_score, result))

        # Sort by score descending
        scored_results.sort(key=lambda x: x[0], reverse=True)

        return [result for _, result in scored_results]

    def _calculate_recency_score(self, chunk: CodeChunk) -> float:
        """Calculate recency score for a chunk (0.0 to 1.0)."""
        # For now, return base score since we don't have timestamps
        # This can be enhanced when chunk creation/modification times are available
        return 0.5

    def _calculate_contextual_relevance(self, chunk: CodeChunk, query: str) -> float:
        """Calculate contextual relevance boost based on content analysis."""
        query_lower = query.lower()
        content_lower = chunk.content.lower()

        boost = 0.0

        # Boost for exact keyword matches
        query_words = set(query_lower.split())
        content_words = set(content_lower.split())
        match_ratio = (
            len(query_words & content_words) / len(query_words) if query_words else 0
        )
        boost += match_ratio * 0.1

        # Boost for function/class name matches
        if chunk.chunk_type.value in ["function", "class", "method"]:
            element_name = chunk.metadata.get("element_name", "").lower()
            if any(word in element_name for word in query_words):
                boost += 0.15

        # Boost for documentation presence
        if "docstring" in chunk.content.lower() or '"""' in chunk.content:
            boost += 0.05

        return min(boost, 0.3)  # Cap boost at 0.3

    def _calculate_relevance_score(self, result: SearchResult, query: str) -> float:
        """Calculate final relevance score for a search result."""
        # Combine similarity with contextual factors
        base_score = result.similarity_score
        contextual_score = self._calculate_contextual_relevance(result.chunk, query)
        quality_score = result.chunk.metadata.get("quality_score", 0.5)

        # Weighted combination
        final_score = base_score * 0.6 + contextual_score * 0.25 + quality_score * 0.15

        return min(final_score, 1.0)

    def format_context(self, retrieval_result: RetrievalResult) -> EnhancedContext:
        """
        Format retrieved chunks into enhanced context for prompt generation.

        Args:
            retrieval_result: Result from context retrieval

        Returns:
            EnhancedContext with formatted context string and metadata
        """
        if not retrieval_result.chunks:
            return EnhancedContext(
                context_id=str(uuid4()),
                formatted_context="No relevant context found.",
                source_chunks=[],
                total_chars=0,
                chunk_count=0,
                relevance_summary={"average_score": 0.0, "top_score": 0.0},
            )

        context_parts = []
        total_chars = 0

        for i, result in enumerate(retrieval_result.chunks):
            chunk = result.chunk

            # Prepare chunk content
            chunk_content = chunk.content
            if len(chunk_content) > self.config.max_context_per_chunk:
                chunk_content = (
                    chunk_content[: self.config.max_context_per_chunk] + "..."
                )

            # Build context entry
            context_entry_parts = []

            # Add metadata if enabled
            if self.config.include_metadata:
                metadata_parts = []

                if self.config.include_file_paths and chunk.file_path:
                    metadata_parts.append(f"File: {chunk.file_path}")

                if chunk.chunk_type:
                    metadata_parts.append(f"Type: {chunk.chunk_type.value}")

                if chunk.language:
                    metadata_parts.append(f"Language: {chunk.language}")

                element_name = chunk.metadata.get("element_name")
                if element_name:
                    metadata_parts.append(f"Name: {element_name}")

                # Add relevance score
                if i < len(retrieval_result.relevance_scores):
                    score = retrieval_result.relevance_scores[i]
                    metadata_parts.append(f"Relevance: {score:.2f}")

                if metadata_parts:
                    context_entry_parts.append(f"[{' | '.join(metadata_parts)}]")

            # Add content
            context_entry_parts.append(chunk_content)

            # Combine entry parts
            context_entry = "\n".join(context_entry_parts)
            context_parts.append(context_entry)
            total_chars += len(context_entry)

            # Check if we're approaching context window limit
            if total_chars >= self.config.context_window_size:
                break

        # Combine all context parts
        formatted_context = "\n\n---\n\n".join(context_parts)

        # Create relevance summary
        relevance_summary = {
            "average_score": retrieval_result.average_relevance,
            "top_score": retrieval_result.top_relevance,
            "total_chunks": len(retrieval_result.chunks),
            "retrieval_time_ms": retrieval_result.retrieval_time_ms,
        }

        context_id = str(uuid4())

        logger.debug(
            "Context formatted",
            context_id=context_id,
            chunk_count=len(retrieval_result.chunks),
            total_chars=total_chars,
            avg_relevance=relevance_summary["average_score"],
        )

        return EnhancedContext(
            context_id=context_id,
            formatted_context=formatted_context,
            source_chunks=retrieval_result.chunks,
            total_chars=total_chars,
            chunk_count=len(retrieval_result.chunks),
            relevance_summary=relevance_summary,
            metadata={
                "query": retrieval_result.query,
                "cache_hit": retrieval_result.cache_hit,
                "retrieval_time_ms": retrieval_result.retrieval_time_ms,
            },
        )

    def enhance_prompt(self, user_query: str, context: EnhancedContext) -> str:
        """
        Enhance user prompt with retrieved context for better LLM responses.

        Args:
            user_query: Original user query
            context: Enhanced context from retrieval

        Returns:
            Enhanced prompt string with context
        """
        if not context.source_chunks:
            return user_query

        prompt_parts = [
            "Based on the following relevant code from this project:",
            "",
            context.formatted_context,
            "",
            "---",
            "",
            f"User Question: {user_query}",
            "",
            "Please provide a detailed, project-specific answer based on the code context above. "
            "Reference specific functions, classes, or patterns from the provided code when relevant.",
        ]

        enhanced_prompt = "\n".join(prompt_parts)

        logger.debug(
            "Prompt enhanced",
            context_id=context.context_id,
            original_length=len(user_query),
            enhanced_length=len(enhanced_prompt),
            context_chunks=context.chunk_count,
        )

        return enhanced_prompt

    def get_performance_stats(self) -> dict[str, Any]:
        """Get performance statistics for the RAG engine."""
        stats = {
            "retrieval_times": {
                "count": len(self._retrieval_times),
                "average_ms": sum(self._retrieval_times) / len(self._retrieval_times)
                if self._retrieval_times
                else 0,
                "max_ms": max(self._retrieval_times) if self._retrieval_times else 0,
                "min_ms": min(self._retrieval_times) if self._retrieval_times else 0,
                "within_timeout_pct": sum(1 for t in self._retrieval_times if t <= 200)
                / len(self._retrieval_times)
                * 100
                if self._retrieval_times
                else 0,
            },
            "cache_performance": {
                "hits": self._cache_hits,
                "misses": self._cache_misses,
                "hit_rate_pct": self._cache_hits
                / (self._cache_hits + self._cache_misses)
                * 100
                if (self._cache_hits + self._cache_misses) > 0
                else 0,
            },
        }

        if self.query_cache:
            stats["cache_status"] = self.query_cache.get_stats()

        return stats

    def health_check(self) -> dict[str, Any]:
        """Perform health check on RAG engine components."""
        health = {
            "status": "unknown",
            "components": {},
            "performance": {},
            "error": None,
        }

        try:
            # Check vector store health
            vector_health = self.vector_store.health_check()
            health["components"]["vector_store"] = vector_health

            # Check embedding manager health
            embedding_health = self.embedding_manager.health_check()
            health["components"]["embedding_manager"] = embedding_health

            # Check embeddings generator
            embeddings_health = {
                "status": "healthy",
                "loaded": self.embeddings_generator.is_loaded,
            }
            if self.embeddings_generator.is_loaded:
                embeddings_health[
                    "model_info"
                ] = self.embeddings_generator.get_model_info()
            health["components"]["embeddings_generator"] = embeddings_health

            # Check cache if enabled
            if self.query_cache:
                health["components"]["query_cache"] = {
                    "status": "healthy",
                    "stats": self.query_cache.get_stats(),
                }

            # Overall performance stats
            health["performance"] = self.get_performance_stats()

            # Determine overall status
            component_statuses = [
                comp.get("status") for comp in health["components"].values()
            ]
            if all(status == "healthy" for status in component_statuses):
                health["status"] = "healthy"
            elif any(status == "unhealthy" for status in component_statuses):
                health["status"] = "unhealthy"
            else:
                health["status"] = "degraded"

        except Exception as e:
            health.update(
                {
                    "status": "unhealthy",
                    "error": str(e),
                }
            )

        return health


def create_rag_engine(
    vector_store: VectorStore,
    embedding_manager: EmbeddingManager | None = None,
    config: RAGConfig | None = None,
) -> RAGEngine:
    """
    Factory function to create a RAG engine.

    Args:
        vector_store: Vector store for similarity search
        embedding_manager: Optional embedding manager
        config: Optional configuration

    Returns:
        Configured RAGEngine instance
    """
    return RAGEngine(vector_store, embedding_manager, config)
