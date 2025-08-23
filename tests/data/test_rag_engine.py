"""
Test suite for RAG Engine Implementation

Comprehensive tests covering context retrieval, relevance scoring, prompt enhancement,
and performance optimization.
"""

import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import numpy as np
import pytest
from codebase_gardener.data.embedding_manager import (
    EmbeddingManager,
    EmbeddingManagerConfig,
)
from codebase_gardener.data.preprocessor import ChunkType, CodeChunk
from codebase_gardener.data.rag_engine import (
    EnhancedContext,
    QueryCache,
    RAGConfig,
    RAGEngine,
    RetrievalResult,
    create_rag_engine,
)
from codebase_gardener.data.vector_store import SearchResult, VectorStore
from codebase_gardener.utils.error_handling import RAGEngineError


class TestRAGConfig:
    """Test RAG configuration classes."""

    def test_default_config(self):
        """Test default configuration values."""
        config = RAGConfig()

        assert config.max_context_chunks == 5
        assert config.min_similarity_threshold == 0.3
        assert config.context_window_size == 4000
        assert config.retrieval_timeout_ms == 200
        assert config.enable_query_cache is True
        assert config.cache_ttl_seconds == 300

    def test_production_config(self):
        """Test production-optimized configuration."""
        config = RAGConfig.for_production()

        assert config.max_context_chunks == 3
        assert config.min_similarity_threshold == 0.4
        assert config.context_window_size == 3000
        assert config.retrieval_timeout_ms == 150
        assert config.enable_query_cache is True
        assert config.cache_ttl_seconds == 600

    def test_development_config(self):
        """Test development-friendly configuration."""
        config = RAGConfig.for_development()

        assert config.max_context_chunks == 5
        assert config.min_similarity_threshold == 0.2
        assert config.context_window_size == 4500
        assert config.retrieval_timeout_ms == 300
        assert config.enable_query_cache is False


class TestQueryCache:
    """Test query caching functionality."""

    def test_cache_basic_operations(self):
        """Test basic cache operations."""
        cache = QueryCache(max_size=3, ttl_seconds=1)

        # Test put and get
        cache.put("query1", "result1")
        assert cache.get("query1") == "result1"

        # Test cache miss
        assert cache.get("nonexistent") is None

    def test_cache_lru_eviction(self):
        """Test LRU eviction policy."""
        cache = QueryCache(max_size=2, ttl_seconds=60)

        cache.put("query1", "result1")
        cache.put("query2", "result2")
        cache.put("query3", "result3")  # Should evict query1

        assert cache.get("query1") is None
        assert cache.get("query2") == "result2"
        assert cache.get("query3") == "result3"

    def test_cache_ttl_expiration(self):
        """Test TTL expiration."""
        cache = QueryCache(max_size=10, ttl_seconds=0.1)

        cache.put("query1", "result1")
        assert cache.get("query1") == "result1"

        time.sleep(0.2)  # Wait for expiration
        assert cache.get("query1") is None

    def test_cache_with_parameters(self):
        """Test cache with query parameters."""
        cache = QueryCache(max_size=10, ttl_seconds=60)

        cache.put("query1", "result1", language="python")
        cache.put("query1", "result2", language="javascript")

        assert cache.get("query1", language="python") == "result1"
        assert cache.get("query1", language="javascript") == "result2"
        assert cache.get("query1", language="go") is None

    def test_cache_stats(self):
        """Test cache statistics."""
        cache = QueryCache(max_size=5, ttl_seconds=60)

        cache.put("query1", "result1")
        cache.put("query2", "result2")

        stats = cache.get_stats()
        assert stats["total_entries"] == 2
        assert stats["valid_entries"] == 2
        assert stats["max_size"] == 5
        assert stats["ttl_seconds"] == 60


class TestRetrievalResult:
    """Test retrieval result functionality."""

    def test_retrieval_result_properties(self):
        """Test retrieval result property calculations."""
        query_embedding = np.random.randn(384).astype(np.float32)

        result = RetrievalResult(
            query="test query",
            query_embedding=query_embedding,
            chunks=[],
            total_chunks_searched=100,
            retrieval_time_ms=150.0,
            relevance_scores=[0.8, 0.6, 0.4],
        )

        assert result.is_within_timeout is True  # 150ms < 200ms
        assert result.average_relevance == 0.6  # (0.8 + 0.6 + 0.4) / 3
        assert result.top_relevance == 0.8

    def test_retrieval_result_timeout_check(self):
        """Test timeout checking."""
        query_embedding = np.random.randn(384).astype(np.float32)

        slow_result = RetrievalResult(
            query="slow query",
            query_embedding=query_embedding,
            chunks=[],
            total_chunks_searched=100,
            retrieval_time_ms=300.0,
            relevance_scores=[],
        )

        assert slow_result.is_within_timeout is False
        assert slow_result.average_relevance == 0.0
        assert slow_result.top_relevance == 0.0


class TestEnhancedContext:
    """Test enhanced context functionality."""

    def test_enhanced_context_quality_check(self):
        """Test context quality assessment."""
        # High quality context
        high_quality = EnhancedContext(
            context_id="test-id",
            formatted_context="def function(): pass",
            source_chunks=[],
            total_chars=1000,
            chunk_count=3,
            relevance_summary={"average_score": 0.7, "top_score": 0.9},
        )

        assert high_quality.is_high_quality is True

        # Low quality context
        low_quality = EnhancedContext(
            context_id="test-id",
            formatted_context="pass",
            source_chunks=[],
            total_chars=100,
            chunk_count=1,
            relevance_summary={"average_score": 0.3, "top_score": 0.4},
        )

        assert low_quality.is_high_quality is False


@pytest.fixture
def sample_code_chunks():
    """Create sample code chunks for testing."""
    chunks = []

    # Python function chunk
    chunks.append(
        CodeChunk(
            id="chunk-1",
            content="def calculate_total(items): return sum(item.price for item in items)",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=Path("src/utils.py"),
            start_line=10,
            end_line=15,
            start_byte=200,
            end_byte=300,
            metadata={"element_name": "calculate_total", "quality_score": 0.8},
            dependencies=[],
            complexity_score=0.3,
        )
    )

    # JavaScript class chunk
    chunks.append(
        CodeChunk(
            id="chunk-2",
            content="class ShoppingCart { constructor() { this.items = []; } }",
            language="javascript",
            chunk_type=ChunkType.CLASS,
            file_path=Path("src/cart.js"),
            start_line=1,
            end_line=5,
            start_byte=0,
            end_byte=100,
            metadata={"element_name": "ShoppingCart", "quality_score": 0.9},
            dependencies=[],
            complexity_score=0.4,
        )
    )

    # Python method chunk
    chunks.append(
        CodeChunk(
            id="chunk-3",
            content="def add_item(self, item): self.items.append(item)",
            language="python",
            chunk_type=ChunkType.METHOD,
            file_path=Path("src/cart.py"),
            start_line=20,
            end_line=25,
            start_byte=400,
            end_byte=500,
            metadata={"element_name": "add_item", "quality_score": 0.7},
            dependencies=["chunk-1"],
            complexity_score=0.2,
        )
    )

    return chunks


@pytest.fixture
def mock_vector_store():
    """Create a mock vector store."""
    mock_store = MagicMock(spec=VectorStore)

    # Mock search results
    def mock_search_similar(**kwargs):
        # Return mock search results
        chunk = CodeChunk(
            id="test-chunk",
            content="def test_function(): pass",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=Path("test.py"),
            start_line=1,
            end_line=5,
            start_byte=0,
            end_byte=100,
            metadata={"element_name": "test_function", "quality_score": 0.8},
            dependencies=[],
            complexity_score=0.1,
        )

        return [
            SearchResult(
                chunk_id="test-chunk",
                chunk=chunk,
                similarity_score=0.85,
                metadata={"element_name": "test_function"},
            )
        ]

    mock_store.search_similar.side_effect = mock_search_similar
    mock_store.health_check.return_value = {"status": "healthy"}

    return mock_store


@pytest.fixture
def mock_embedding_manager():
    """Create a mock embedding manager."""
    mock_manager = MagicMock(spec=EmbeddingManager)
    mock_manager.config = EmbeddingManagerConfig()
    mock_manager.health_check.return_value = {"status": "healthy"}

    return mock_manager


@pytest.fixture
def rag_engine(mock_vector_store, mock_embedding_manager):
    """Create RAG engine for testing."""
    config = RAGConfig.for_development()
    config.enable_query_cache = True  # Enable caching for tests

    with patch("codebase_gardener.data.rag_engine.NomicEmbeddings") as mock_embeddings:
        # Mock embeddings generator
        mock_embeddings_instance = MagicMock()
        mock_embeddings_instance.embed_query.return_value = np.random.randn(384).astype(
            np.float32
        )
        mock_embeddings_instance.is_loaded = True
        mock_embeddings_instance.get_model_info.return_value = {
            "model": "nomic-embed-text",
            "dimension": 384,
        }
        mock_embeddings_instance.health_check.return_value = {
            "status": "healthy",
            "loaded": True,
        }
        mock_embeddings.return_value = mock_embeddings_instance

        engine = RAGEngine(mock_vector_store, mock_embedding_manager, config)
        engine.embeddings_generator = mock_embeddings_instance

        return engine


class TestRAGEngine:
    """Test RAG engine core functionality."""

    def test_rag_engine_initialization(self, mock_vector_store, mock_embedding_manager):
        """Test RAG engine initialization."""
        config = RAGConfig()

        with patch("codebase_gardener.data.rag_engine.NomicEmbeddings"):
            engine = RAGEngine(mock_vector_store, mock_embedding_manager, config)

            assert engine.vector_store == mock_vector_store
            assert engine.config == config
            assert engine.embedding_manager == mock_embedding_manager
            assert engine.query_cache is not None

    def test_retrieve_context_basic(self, rag_engine):
        """Test basic context retrieval."""
        query = "how to calculate total price"

        # Disable quality filtering for this test to avoid issues
        rag_engine.config.enable_quality_filtering = False

        result = rag_engine.retrieve_context(query)

        assert isinstance(result, RetrievalResult)
        assert result.query == query
        assert len(result.chunks) > 0
        assert result.retrieval_time_ms > 0
        assert result.cache_hit is False

        # Verify the vector store was called properly
        rag_engine.vector_store.search_similar.assert_called_once()

    def test_retrieve_context_with_filters(self, rag_engine):
        """Test context retrieval with language and type filters."""
        query = "python function"

        result = rag_engine.retrieve_context(
            query, language_filter="python", chunk_type_filter="function"
        )

        assert isinstance(result, RetrievalResult)
        assert result.query == query

        # Verify filters were applied
        rag_engine.vector_store.search_similar.assert_called_with(
            query_embedding=result.query_embedding,
            limit=10,  # max_context_chunks * 2
            language_filter="python",
            chunk_type_filter="function",
            min_similarity=0.2,  # from development config
        )

    def test_retrieve_context_caching(self, rag_engine):
        """Test query result caching."""
        query = "test caching"

        # First retrieval
        result1 = rag_engine.retrieve_context(query)
        assert result1.cache_hit is False

        # Second retrieval should hit cache
        result2 = rag_engine.retrieve_context(query)
        assert result2.cache_hit is True

    def test_format_context_basic(self, rag_engine, sample_code_chunks):
        """Test basic context formatting."""
        # Create mock retrieval result
        query_embedding = np.random.randn(384).astype(np.float32)
        search_results = [
            SearchResult(
                chunk_id=chunk.id,
                chunk=chunk,
                similarity_score=0.8 - i * 0.1,
                metadata=chunk.metadata,
            )
            for i, chunk in enumerate(sample_code_chunks[:2])
        ]

        retrieval_result = RetrievalResult(
            query="test query",
            query_embedding=query_embedding,
            chunks=search_results,
            total_chunks_searched=3,
            retrieval_time_ms=100.0,
            relevance_scores=[0.8, 0.7],
        )

        context = rag_engine.format_context(retrieval_result)

        assert isinstance(context, EnhancedContext)
        assert len(context.formatted_context) > 0
        assert context.chunk_count == 2
        assert context.total_chars > 0
        assert len(context.source_chunks) == 2

    def test_format_context_empty_results(self, rag_engine):
        """Test context formatting with no results."""
        query_embedding = np.random.randn(384).astype(np.float32)

        empty_result = RetrievalResult(
            query="no results query",
            query_embedding=query_embedding,
            chunks=[],
            total_chunks_searched=0,
            retrieval_time_ms=50.0,
            relevance_scores=[],
        )

        context = rag_engine.format_context(empty_result)

        assert context.formatted_context == "No relevant context found."
        assert context.chunk_count == 0
        assert context.total_chars == 0
        assert len(context.source_chunks) == 0

    def test_enhance_prompt_basic(self, rag_engine, sample_code_chunks):
        """Test basic prompt enhancement."""
        # Create enhanced context
        search_results = [
            SearchResult(
                chunk_id=sample_code_chunks[0].id,
                chunk=sample_code_chunks[0],
                similarity_score=0.8,
                metadata=sample_code_chunks[0].metadata,
            )
        ]

        context = EnhancedContext(
            context_id="test-context",
            formatted_context="def calculate_total(): pass",
            source_chunks=search_results,
            total_chars=100,
            chunk_count=1,
            relevance_summary={"average_score": 0.8, "top_score": 0.8},
        )

        user_query = "How do I calculate totals?"
        enhanced_prompt = rag_engine.enhance_prompt(user_query, context)

        assert "Based on the following relevant code" in enhanced_prompt
        assert user_query in enhanced_prompt
        assert "calculate_total" in enhanced_prompt
        assert len(enhanced_prompt) > len(user_query)

    def test_enhance_prompt_no_context(self, rag_engine):
        """Test prompt enhancement with no context."""
        empty_context = EnhancedContext(
            context_id="empty",
            formatted_context="",
            source_chunks=[],
            total_chars=0,
            chunk_count=0,
            relevance_summary={"average_score": 0.0, "top_score": 0.0},
        )

        user_query = "Test query"
        enhanced_prompt = rag_engine.enhance_prompt(user_query, empty_context)

        assert enhanced_prompt == user_query  # No enhancement when no context

    def test_quality_filtering(self, rag_engine, sample_code_chunks):
        """Test content quality filtering."""
        # Test trivial content detection
        assert rag_engine._is_trivial_content("pass") is True
        assert rag_engine._is_trivial_content("return None") is True
        assert rag_engine._is_trivial_content("# TODO: implement") is True
        assert rag_engine._is_trivial_content("...") is True

        # Test non-trivial content
        assert (
            rag_engine._is_trivial_content("def complex_function(): return calculate()")
            is False
        )

    def test_contextual_relevance_calculation(self, rag_engine, sample_code_chunks):
        """Test contextual relevance scoring."""
        chunk = sample_code_chunks[0]  # calculate_total function
        query = "calculate total price"

        relevance = rag_engine._calculate_contextual_relevance(chunk, query)

        assert 0.0 <= relevance <= 0.3  # Capped at 0.3
        assert relevance > 0  # Should have some relevance due to "calculate" match

    def test_ranking_algorithm(self, rag_engine, sample_code_chunks):
        """Test result ranking algorithm."""
        # Create mock search results
        search_results = []
        for i, chunk in enumerate(sample_code_chunks):
            search_results.append(
                SearchResult(
                    chunk_id=chunk.id,
                    chunk=chunk,
                    similarity_score=0.8 - i * 0.1,  # Decreasing similarity
                    metadata=chunk.metadata,
                )
            )

        query = "calculate function"
        ranked_results = rag_engine._rank_results(search_results, query)

        assert len(ranked_results) == len(search_results)

        # Verify results are in descending order of relevance
        for i in range(len(ranked_results) - 1):
            current_score = rag_engine._calculate_relevance_score(
                ranked_results[i], query
            )
            next_score = rag_engine._calculate_relevance_score(
                ranked_results[i + 1], query
            )
            assert current_score >= next_score

    def test_performance_stats(self, rag_engine):
        """Test performance statistics collection."""
        # Perform some retrievals
        for i in range(3):
            rag_engine.retrieve_context(f"test query {i}")

        stats = rag_engine.get_performance_stats()

        assert "retrieval_times" in stats
        assert "cache_performance" in stats
        assert stats["retrieval_times"]["count"] >= 3
        # Cache is enabled in test config, so we should have misses
        assert stats["cache_performance"]["misses"] >= 3

    def test_health_check(self, rag_engine):
        """Test RAG engine health check."""
        health = rag_engine.health_check()

        assert "status" in health
        assert "components" in health
        assert "performance" in health

        assert "vector_store" in health["components"]
        assert "embedding_manager" in health["components"]
        assert "embeddings_generator" in health["components"]

        # Should be healthy with mocked components
        assert health["status"] in ["healthy", "degraded"]


class TestRAGEngineEdgeCases:
    """Test RAG engine edge cases and error conditions."""

    def test_retrieve_context_failure(self, mock_vector_store, mock_embedding_manager):
        """Test context retrieval failure handling."""
        config = RAGConfig()

        # Make vector store search fail
        mock_vector_store.search_similar.side_effect = Exception("Vector store error")

        with patch(
            "codebase_gardener.data.rag_engine.NomicEmbeddings"
        ) as mock_embeddings:
            mock_embeddings_instance = MagicMock()
            mock_embeddings_instance.embed_query.return_value = np.random.randn(
                384
            ).astype(np.float32)
            mock_embeddings.return_value = mock_embeddings_instance

            engine = RAGEngine(mock_vector_store, mock_embedding_manager, config)
            engine.embeddings_generator = mock_embeddings_instance

            with pytest.raises(RAGEngineError):
                engine.retrieve_context("test query")

    def test_large_context_truncation(self, rag_engine):
        """Test handling of large context that exceeds window size."""
        rag_engine.config.context_window_size = 50  # Very small window
        rag_engine.config.max_context_per_chunk = 30
        rag_engine.config.include_metadata = False  # Disable metadata to simplify

        # Create large chunks
        large_chunk = CodeChunk(
            id="large-chunk",
            content="x" * 1000,  # Very large content
            language="python",
            chunk_type=ChunkType.FUNCTION,
            file_path=Path("large.py"),
            start_line=1,
            end_line=100,
            start_byte=0,
            end_byte=1000,
            metadata={},
            dependencies=[],
            complexity_score=0.5,
        )

        search_results = [
            SearchResult(
                chunk_id=large_chunk.id,
                chunk=large_chunk,
                similarity_score=0.9,
                metadata={},
            )
        ]

        query_embedding = np.random.randn(384).astype(np.float32)
        retrieval_result = RetrievalResult(
            query="test",
            query_embedding=query_embedding,
            chunks=search_results,
            total_chunks_searched=1,
            retrieval_time_ms=100.0,
            relevance_scores=[0.9],
        )

        context = rag_engine.format_context(retrieval_result)

        # Content should be truncated
        assert "..." in context.formatted_context
        assert context.total_chars <= rag_engine.config.context_window_size


class TestRAGEngineIntegration:
    """Integration tests for RAG engine with real components."""

    @pytest.mark.skip(reason="Requires real model dependencies")
    def test_end_to_end_retrieval(self):
        """Test end-to-end retrieval with real components."""
        # This test would require actual LanceDB and sentence-transformers
        # Skip in CI/CD but useful for local testing
        pass


class TestRAGEngineFactory:
    """Test RAG engine factory function."""

    def test_create_rag_engine(self, mock_vector_store):
        """Test RAG engine factory function."""
        config = RAGConfig.for_production()

        with patch(
            "codebase_gardener.data.rag_engine.EmbeddingManager"
        ) as mock_em_class:
            mock_em_class.return_value = MagicMock()

            engine = create_rag_engine(mock_vector_store, config=config)

            assert isinstance(engine, RAGEngine)
            assert engine.vector_store == mock_vector_store
            assert engine.config == config


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
