"""
Tests for the NomicEmbedder class and EmbeddingCache.

This module tests the embedding generation functionality including:
- Embedding generation for code chunks
- Batch processing capabilities
- Caching mechanisms and performance
- Error handling and fallback behavior
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest

from codebase_gardener.config.settings import Settings
from codebase_gardener.data.preprocessor import ChunkType, CodeChunk
from codebase_gardener.models.nomic_embedder import EmbeddingCache, NomicEmbedder
from codebase_gardener.utils.error_handling import EmbeddingError


class TestEmbeddingCache:
    """Test cases for the EmbeddingCache class."""

    @pytest.fixture
    def temp_cache_dir(self):
        """Create a temporary directory for cache testing."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create an EmbeddingCache instance for testing."""
        return EmbeddingCache(temp_cache_dir, max_size=3)

    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initialization with directory creation."""
        cache = EmbeddingCache(temp_cache_dir, max_size=5)

        assert cache.cache_dir == temp_cache_dir
        assert cache.max_size == 5
        assert len(cache._memory_cache) == 0
        assert len(cache._access_order) == 0
        assert temp_cache_dir.exists()

    def test_cache_key_generation(self, cache):
        """Test cache key generation is consistent and unique."""
        content1 = "def hello(): return 'world'"
        content2 = "def goodbye(): return 'farewell'"
        model_name = "test-model"

        key1a = cache._generate_cache_key(content1, model_name)
        key1b = cache._generate_cache_key(content1, model_name)
        key2 = cache._generate_cache_key(content2, model_name)

        # Same content should generate same key
        assert key1a == key1b
        # Different content should generate different keys
        assert key1a != key2
        # Keys should be reasonable length
        assert len(key1a) > 10
        assert len(key1a) < 50

    def test_cache_miss(self, cache):
        """Test cache miss returns None."""
        result = cache.get("nonexistent content", "test-model")
        assert result is None

    def test_cache_put_and_get(self, cache):
        """Test basic cache put and get operations."""
        content = "def test(): pass"
        model_name = "test-model"
        embedding = np.array([1.0, 2.0, 3.0])

        # Put embedding in cache
        cache.put(content, model_name, embedding)

        # Get embedding from cache
        retrieved = cache.get(content, model_name)

        assert retrieved is not None
        np.testing.assert_array_equal(retrieved, embedding)

    def test_cache_lru_eviction(self, cache):
        """Test LRU eviction when cache exceeds max size."""
        embeddings = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
            np.array([7.0, 8.0, 9.0]),
            np.array([10.0, 11.0, 12.0])
        ]

        # Fill cache to max capacity
        for i in range(3):
            cache.put(f"content_{i}", "test-model", embeddings[i])

        # Verify all are cached
        for i in range(3):
            result = cache.get(f"content_{i}", "test-model")
            assert result is not None

        # Add one more to trigger eviction
        cache.put("content_3", "test-model", embeddings[3])

        # First item should be evicted
        assert cache.get("content_0", "test-model") is None
        # Others should still be there
        for i in range(1, 4):
            result = cache.get(f"content_{i}", "test-model")
            assert result is not None

    def test_cache_access_order_update(self, cache):
        """Test that accessing items updates LRU order."""
        embeddings = [
            np.array([1.0, 2.0, 3.0]),
            np.array([4.0, 5.0, 6.0]),
            np.array([7.0, 8.0, 9.0]),
            np.array([10.0, 11.0, 12.0])
        ]

        # Fill cache
        for i in range(3):
            cache.put(f"content_{i}", "test-model", embeddings[i])

        # Access first item to make it most recent
        cache.get("content_0", "test-model")

        # Add new item to trigger eviction
        cache.put("content_3", "test-model", embeddings[3])

        # content_1 should be evicted (was least recently used)
        assert cache.get("content_1", "test-model") is None
        # content_0 should still be there (was accessed recently)
        assert cache.get("content_0", "test-model") is not None

    def test_cache_disk_persistence(self, cache):
        """Test that cache persists to disk and can be retrieved."""
        content = "def persistent(): return True"
        model_name = "test-model"
        embedding = np.array([1.0, 2.0, 3.0])

        # Put in cache
        cache.put(content, model_name, embedding)

        # Clear memory cache
        cache._memory_cache.clear()
        cache._access_order.clear()

        # Should still be retrievable from disk
        retrieved = cache.get(content, model_name)
        assert retrieved is not None
        np.testing.assert_array_equal(retrieved, embedding)

    def test_cache_clear(self, cache):
        """Test cache clearing removes all entries."""
        # Add some entries
        for i in range(3):
            embedding = np.array([float(i), float(i+1), float(i+2)])
            cache.put(f"content_{i}", "test-model", embedding)

        # Verify entries exist
        assert len(cache._memory_cache) == 3
        assert len(list(cache.cache_dir.glob("*.npz"))) == 3

        # Clear cache
        cache.clear()

        # Verify everything is cleared
        assert len(cache._memory_cache) == 0
        assert len(cache._access_order) == 0
        assert len(list(cache.cache_dir.glob("*.npz"))) == 0

    def test_cache_stats(self, cache):
        """Test cache statistics reporting."""
        # Add some entries
        for i in range(2):
            embedding = np.array([float(i), float(i+1), float(i+2)])
            cache.put(f"content_{i}", "test-model", embedding)

        stats = cache.get_stats()

        assert stats["memory_entries"] == 2
        assert stats["disk_entries"] == 2
        assert stats["max_size"] == 3
        assert "cache_dir" in stats

    def test_cache_corrupted_file_handling(self, cache, temp_cache_dir):
        """Test handling of corrupted cache files."""
        # Create a cache entry first, then corrupt its file
        content = "some content"
        model_name = "test-model"
        embedding = np.array([1.0, 2.0, 3.0])

        # Put in cache to create the proper file
        cache.put(content, model_name, embedding)

        # Get the cache key and file path
        cache_key = cache._generate_cache_key(content, model_name)
        cache_file = cache._get_cache_file_path(cache_key)

        # Clear memory cache to force disk read
        cache._memory_cache.clear()
        cache._access_order.clear()

        # Corrupt the file
        cache_file.write_text("not a valid npz file")

        # Should handle gracefully and return None
        result = cache.get(content, model_name)
        assert result is None

        # Corrupted file should be removed
        assert not cache_file.exists()


class TestNomicEmbedder:
    """Test cases for the NomicEmbedder class."""

    @pytest.fixture
    def mock_settings(self):
        """Create mock settings for testing."""
        settings = Mock(spec=Settings)
        settings.data_dir = Path("/tmp/test_codebase_gardener")
        settings.embedding_model = "test-model"
        settings.embedding_batch_size = 2
        settings.embedding_device = None
        settings.embedding_cache_size = 100
        return settings

    @pytest.fixture
    def sample_chunks(self):
        """Create sample CodeChunk objects for testing."""
        return [
            CodeChunk(
                id="chunk_1",
                content="def hello(): return 'world'",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=Path("test.py"),
                start_line=1,
                end_line=1,
                start_byte=0,
                end_byte=28,
                metadata={},
                dependencies=[],
                complexity_score=1.0
            ),
            CodeChunk(
                id="chunk_2",
                content="def goodbye(): return 'farewell'",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=Path("test.py"),
                start_line=3,
                end_line=3,
                start_byte=30,
                end_byte=62,
                metadata={},
                dependencies=[],
                complexity_score=1.5
            ),
            CodeChunk(
                id="chunk_3",
                content="class TestClass: pass",
                language="python",
                chunk_type=ChunkType.CLASS,
                file_path=Path("test.py"),
                start_line=5,
                end_line=5,
                start_byte=64,
                end_byte=85,
                metadata={},
                dependencies=[],
                complexity_score=2.0
            )
        ]

    @pytest.fixture
    def mock_sentence_transformer(self):
        """Create a mock SentenceTransformer."""
        mock_model = Mock()
        mock_model.encode.return_value = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0]
        ])
        mock_model.get_sentence_embedding_dimension.return_value = 3
        mock_model.device = "cpu"
        return mock_model

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_embedder_initialization(self, mock_st_class, mock_settings):
        """Test NomicEmbedder initialization."""
        embedder = NomicEmbedder(mock_settings)

        assert embedder.settings == mock_settings
        assert embedder.model_name == "test-model"
        assert embedder.batch_size == 2
        assert embedder.device is None
        assert embedder._model is None
        assert not embedder._model_loaded
        assert isinstance(embedder.cache, EmbeddingCache)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_lazy_model_loading(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test that model is loaded lazily on first access."""
        mock_st_class.return_value = mock_sentence_transformer
        embedder = NomicEmbedder(mock_settings)

        # Model should not be loaded initially
        assert not embedder._model_loaded

        # Accessing model property should trigger loading
        model = embedder.model

        assert embedder._model_loaded
        assert model == mock_sentence_transformer
        mock_st_class.assert_called_once_with("test-model", device=None)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_model_loading_error(self, mock_st_class, mock_settings):
        """Test error handling during model loading."""
        mock_st_class.side_effect = Exception("Model loading failed")
        embedder = NomicEmbedder(mock_settings)

        with pytest.raises(EmbeddingError) as exc_info:
            _ = embedder.model

        assert "Could not load embedding model" in str(exc_info.value)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_embed_single_chunk(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test embedding a single code chunk."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.return_value = np.array([[1.0, 2.0, 3.0]])

        embedder = NomicEmbedder(mock_settings)
        chunk = sample_chunks[0]

        embedding = embedder.embed_single(chunk)

        assert isinstance(embedding, np.ndarray)
        assert embedding.shape == (3,)
        np.testing.assert_array_equal(embedding, [1.0, 2.0, 3.0])

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_embed_multiple_chunks(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test embedding multiple code chunks."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.return_value = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])

        embedder = NomicEmbedder(mock_settings)

        embeddings = embedder.embed_chunks(sample_chunks)

        assert len(embeddings) == 3
        assert all(isinstance(emb, np.ndarray) for emb in embeddings)
        assert all(emb.shape == (3,) for emb in embeddings)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_batch_processing(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test that chunks are processed in batches."""
        mock_st_class.return_value = mock_sentence_transformer
        # Mock encode to return different results for different calls
        mock_sentence_transformer.encode.side_effect = [
            np.array([[1.0, 2.0, 3.0], [4.0, 5.0, 6.0]]),  # First batch
            np.array([[7.0, 8.0, 9.0]])  # Second batch
        ]

        embedder = NomicEmbedder(mock_settings)
        embedder.batch_size = 2  # Force batching
        embedder.clear_cache()  # Clear cache to ensure fresh processing

        embeddings = embedder.embed_chunks(sample_chunks)

        # Should have made 2 calls to encode (batch size 2, 3 chunks)
        assert mock_sentence_transformer.encode.call_count == 2
        assert len(embeddings) == 3

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_caching_behavior(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test that embeddings are cached and reused."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.return_value = np.array([[1.0, 2.0, 3.0]])

        embedder = NomicEmbedder(mock_settings)
        embedder.clear_cache()  # Clear cache to ensure fresh start
        chunk = sample_chunks[0]

        # First call should generate embedding
        embedding1 = embedder.embed_single(chunk)
        assert mock_sentence_transformer.encode.call_count == 1

        # Second call should use cache
        embedding2 = embedder.embed_single(chunk)
        assert mock_sentence_transformer.encode.call_count == 1  # No additional calls

        # Embeddings should be identical
        np.testing.assert_array_equal(embedding1, embedding2)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_empty_chunks_list(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test handling of empty chunks list."""
        mock_st_class.return_value = mock_sentence_transformer
        embedder = NomicEmbedder(mock_settings)

        embeddings = embedder.embed_chunks([])

        assert embeddings == []
        assert mock_sentence_transformer.encode.call_count == 0

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_embedding_generation_error(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test error handling during embedding generation."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.side_effect = Exception("Encoding failed")

        embedder = NomicEmbedder(mock_settings)
        embedder.clear_cache()  # Clear cache to ensure fresh processing

        with pytest.raises(EmbeddingError) as exc_info:
            embedder.embed_chunks(sample_chunks)

        assert "Batch embedding generation failed" in str(exc_info.value)

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_get_embedding_dimension(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test getting embedding dimension."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 768

        embedder = NomicEmbedder(mock_settings)

        dimension = embedder.get_embedding_dimension()
        assert dimension == 768

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_get_embedding_dimension_error(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test fallback when getting embedding dimension fails."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.get_sentence_embedding_dimension.side_effect = Exception("Failed")

        embedder = NomicEmbedder(mock_settings)

        dimension = embedder.get_embedding_dimension()
        assert dimension == 768  # Fallback value

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_calculate_similarity(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test cosine similarity calculation."""
        mock_st_class.return_value = mock_sentence_transformer
        embedder = NomicEmbedder(mock_settings)

        # Test identical vectors
        vec1 = np.array([1.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])
        similarity = embedder.calculate_similarity(vec1, vec2)
        assert abs(similarity - 1.0) < 1e-6

        # Test orthogonal vectors
        vec3 = np.array([1.0, 0.0, 0.0])
        vec4 = np.array([0.0, 1.0, 0.0])
        similarity = embedder.calculate_similarity(vec3, vec4)
        assert abs(similarity - 0.0) < 1e-6

        # Test opposite vectors
        vec5 = np.array([1.0, 0.0, 0.0])
        vec6 = np.array([-1.0, 0.0, 0.0])
        similarity = embedder.calculate_similarity(vec5, vec6)
        assert abs(similarity - (-1.0)) < 1e-6

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_calculate_similarity_zero_vectors(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test similarity calculation with zero vectors."""
        mock_st_class.return_value = mock_sentence_transformer
        embedder = NomicEmbedder(mock_settings)

        vec1 = np.array([0.0, 0.0, 0.0])
        vec2 = np.array([1.0, 0.0, 0.0])

        similarity = embedder.calculate_similarity(vec1, vec2)
        assert similarity == 0.0

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_get_model_info(self, mock_st_class, mock_settings, mock_sentence_transformer):
        """Test getting model information."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.device = "cpu"

        embedder = NomicEmbedder(mock_settings)

        info = embedder.get_model_info()

        assert info["model_name"] == "test-model"
        assert info["embedding_dimension"] == 384
        assert info["batch_size"] == 2
        assert "device" in info
        assert "cache_stats" in info

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_clear_cache(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test clearing the embedding cache."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.return_value = np.array([[1.0, 2.0, 3.0]])

        embedder = NomicEmbedder(mock_settings)

        # Generate and cache an embedding
        embedder.embed_single(sample_chunks[0])

        # Verify it's cached
        cached = embedder.cache.get(sample_chunks[0].content, embedder.model_name)
        assert cached is not None

        # Clear cache
        embedder.clear_cache()

        # Verify it's no longer cached
        cached = embedder.cache.get(sample_chunks[0].content, embedder.model_name)
        assert cached is None

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_retry_on_model_loading_failure(self, mock_st_class, mock_settings):
        """Test retry behavior on model loading failure."""
        # First two calls fail, third succeeds
        mock_st_class.side_effect = [
            Exception("First failure"),
            Exception("Second failure"),
            Mock()  # Success on third try
        ]

        embedder = NomicEmbedder(mock_settings)

        # Should eventually succeed after retries
        model = embedder.model
        assert model is not None
        assert mock_st_class.call_count == 3

    @patch('codebase_gardener.models.nomic_embedder.SentenceTransformer')
    def test_performance_logging(self, mock_st_class, mock_settings, mock_sentence_transformer, sample_chunks):
        """Test that performance metrics are logged."""
        mock_st_class.return_value = mock_sentence_transformer
        mock_sentence_transformer.encode.return_value = np.array([
            [1.0, 2.0, 3.0],
            [4.0, 5.0, 6.0],
            [7.0, 8.0, 9.0]
        ])

        embedder = NomicEmbedder(mock_settings)

        with patch('codebase_gardener.models.nomic_embedder.logger') as mock_logger:
            embeddings = embedder.embed_chunks(sample_chunks)

            # Should log performance information
            mock_logger.info.assert_called()
            log_calls = [call.args[0] for call in mock_logger.info.call_args_list]

            # Check for performance-related log messages
            assert any("Generating embeddings" in msg for msg in log_calls)
            assert any("Generated" in msg and "embeddings in" in msg for msg in log_calls)
