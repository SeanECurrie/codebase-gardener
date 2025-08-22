"""
Integration Tests for Embedding System

Tests the complete embedding generation pipeline including Nomic embeddings,
vector storage, and embedding management.
"""

import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pytest
from codebase_gardener.data.embedding_manager import (
    EmbeddingManager,
    EmbeddingManagerConfig,
)
from codebase_gardener.data.embeddings import (
    EmbeddingConfig,
    EmbeddingResult,
    NomicEmbeddings,
)
from codebase_gardener.data.preprocessor import ChunkType, CodeChunk
from codebase_gardener.data.vector_store import VectorStore


@pytest.fixture
def sample_chunk():
    """Create a sample code chunk for testing."""
    return CodeChunk(
        id="test_chunk_1",
        content="def hello_world():\n    return 'Hello, World!'",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        file_path=Path("test.py"),
        start_line=1,
        end_line=2,
        start_byte=0,
        end_byte=42,
        metadata={"element_name": "hello_world", "complexity": 1.0},
        dependencies=["print"],
        complexity_score=1.5,
    )


@pytest.fixture
def mock_embedding_config():
    """Create a mock embedding configuration."""
    return EmbeddingConfig(
        model_name="test-model",
        batch_size=4,
        device="cpu",
        cache_embeddings=False,  # Disable caching for tests
    )


@pytest.fixture
def temp_vector_store():
    """Create a temporary vector store for testing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        db_path = Path(temp_dir) / "test_db"
        vector_store = VectorStore(db_path, "test_chunks")
        yield vector_store


class TestNomicEmbeddings:
    """Test Nomic embeddings functionality."""

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_embeddings_initialization(
        self, mock_sentence_transformer, mock_embedding_config
    ):
        """Test embeddings generator initialization."""
        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_sentence_transformer.return_value = mock_model

        embeddings_gen = NomicEmbeddings(mock_embedding_config)
        embeddings_gen.ensure_loaded()

        assert embeddings_gen.is_loaded
        assert embeddings_gen.model is not None
        mock_sentence_transformer.assert_called_once()

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_single_chunk_embedding(
        self, mock_sentence_transformer, mock_embedding_config, sample_chunk
    ):
        """Test embedding generation for a single chunk."""
        # Mock the model
        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = np.random.rand(384)
        mock_model.encode.return_value = mock_embedding
        mock_sentence_transformer.return_value = mock_model

        embeddings_gen = NomicEmbeddings(mock_embedding_config)
        result = embeddings_gen.embed_chunk(sample_chunk)

        assert isinstance(result, EmbeddingResult)
        assert result.is_valid
        assert result.chunk_id == sample_chunk.id
        assert result.embedding.shape == (384,)
        assert result.processing_time > 0
        assert result.token_count > 0

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_batch_embedding(self, mock_sentence_transformer, mock_embedding_config):
        """Test batch embedding generation."""
        # Create multiple chunks
        chunks = []
        for i in range(3):
            chunk = CodeChunk(
                id=f"test_chunk_{i}",
                content=f"def function_{i}():\n    return {i}",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=Path("test.py"),
                start_line=i * 2 + 1,
                end_line=i * 2 + 2,
                start_byte=i * 50,
                end_byte=(i + 1) * 50,
                metadata={},
                dependencies=[],
                complexity_score=1.0,
            )
            chunks.append(chunk)

        # Mock the model
        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embeddings = np.random.rand(3, 384)
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model

        embeddings_gen = NomicEmbeddings(mock_embedding_config)
        results = embeddings_gen.embed_chunks_batch(chunks)

        assert len(results) == 3
        for i, result in enumerate(results):
            assert isinstance(result, EmbeddingResult)
            assert result.is_valid
            assert result.chunk_id == f"test_chunk_{i}"
            assert result.embedding.shape == (384,)

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_query_embedding(self, mock_sentence_transformer, mock_embedding_config):
        """Test query embedding generation."""
        # Mock the model
        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embedding = np.random.rand(384)
        mock_model.encode.return_value = mock_embedding
        mock_sentence_transformer.return_value = mock_model

        embeddings_gen = NomicEmbeddings(mock_embedding_config)
        query = "How to implement a function?"
        result = embeddings_gen.embed_query(query)

        assert isinstance(result, np.ndarray)
        assert result.shape == (384,)
        mock_model.encode.assert_called()

    def test_text_preparation(self, mock_embedding_config, sample_chunk):
        """Test chunk text preparation for embedding."""
        embeddings_gen = NomicEmbeddings(mock_embedding_config)
        prepared_text = embeddings_gen._prepare_chunk_text(sample_chunk)

        # Should include context information
        assert "Language: python" in prepared_text
        assert "Type: function" in prepared_text
        assert "File: test.py" in prepared_text
        assert sample_chunk.content in prepared_text


class TestVectorStore:
    """Test vector store functionality."""

    def test_vector_store_initialization(self, temp_vector_store):
        """Test vector store initialization."""
        assert temp_vector_store.db_path.exists()
        assert temp_vector_store.table_name == "test_chunks"
        assert not temp_vector_store._connected

    def test_connect_and_table_creation(self, temp_vector_store):
        """Test database connection and table creation."""
        # This test requires actual LanceDB, so we'll mock it
        with patch("lancedb.connect") as mock_connect:
            mock_db = Mock()
            mock_db.table_names.return_value = []
            mock_table = Mock()
            mock_db.create_table.return_value = mock_table
            mock_connect.return_value = mock_db

            temp_vector_store.connect()

            assert temp_vector_store._connected
            mock_connect.assert_called_once()
            mock_db.create_table.assert_called_once()

    def test_add_and_retrieve_chunks(self, temp_vector_store, sample_chunk):
        """Test adding and retrieving chunks from vector store."""
        # Mock LanceDB operations
        with patch("lancedb.connect") as mock_connect:
            mock_db = Mock()
            mock_db.table_names.return_value = ["test_chunks"]
            mock_table = Mock()
            mock_db.open_table.return_value = mock_table
            mock_connect.return_value = mock_db

            temp_vector_store.connect()

            # Test adding chunk
            embedding = np.random.rand(384)
            temp_vector_store.add_chunk(sample_chunk, embedding)

            mock_table.add.assert_called_once()

    def test_similarity_search(self, temp_vector_store):
        """Test vector similarity search."""
        # Mock LanceDB search operations
        with patch("lancedb.connect") as mock_connect:
            mock_db = Mock()
            mock_db.table_names.return_value = ["test_chunks"]
            mock_table = Mock()

            # Mock search results
            mock_search = Mock()
            mock_search.limit.return_value = mock_search
            mock_search.to_list.return_value = [
                {
                    "id": "test_chunk_1",
                    "content": "def hello():\n    return 'hello'",
                    "language": "python",
                    "chunk_type": "function",
                    "file_path": "test.py",
                    "start_line": 1,
                    "end_line": 2,
                    "start_byte": 0,
                    "end_byte": 25,
                    "metadata": "{}",
                    "dependencies": "[]",
                    "complexity_score": 1.0,
                    "_distance": 0.1,  # Low distance = high similarity
                }
            ]
            mock_table.search.return_value = mock_search
            mock_db.open_table.return_value = mock_table
            mock_connect.return_value = mock_db

            temp_vector_store.connect()

            query_embedding = np.random.rand(384)
            results = temp_vector_store.search_similar(query_embedding, limit=5)

            assert len(results) == 1
            result = results[0]
            assert result.chunk_id == "test_chunk_1"
            assert result.similarity_score > 0.8  # 1 - 0.1 = 0.9


class TestEmbeddingManager:
    """Test embedding manager functionality."""

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_embedding_manager_initialization(
        self, mock_sentence_transformer, temp_vector_store
    ):
        """Test embedding manager initialization."""
        config = EmbeddingManagerConfig.for_development()
        manager = EmbeddingManager(temp_vector_store, config)

        assert manager.config == config
        assert manager.vector_store == temp_vector_store
        assert isinstance(manager.embeddings_generator, NomicEmbeddings)

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    @patch("lancedb.connect")
    def test_process_chunks_workflow(
        self, mock_connect, mock_sentence_transformer, temp_vector_store, sample_chunk
    ):
        """Test the complete chunk processing workflow."""
        # Setup mocks
        mock_db = Mock()
        mock_db.table_names.return_value = []
        mock_table = Mock()
        mock_db.create_table.return_value = mock_table
        mock_connect.return_value = mock_db

        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embeddings = np.random.rand(1, 384)
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model

        # Create manager and process chunks
        config = EmbeddingManagerConfig.for_development()
        manager = EmbeddingManager(temp_vector_store, config)

        result = manager.process_chunks([sample_chunk])

        # Verify results
        assert result.total_chunks == 1
        assert result.processed_chunks == 1
        assert result.successful_embeddings == 1
        assert result.failed_embeddings == 0
        assert result.success_rate == 100.0

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    def test_search_similar_chunks(self, mock_sentence_transformer, temp_vector_store):
        """Test similarity search through embedding manager."""
        # Mock the embeddings generator
        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        query_embedding = np.random.rand(384)
        mock_model.encode.return_value = query_embedding
        mock_sentence_transformer.return_value = mock_model

        # Mock vector store search
        with patch.object(temp_vector_store, "search_similar") as mock_search:
            mock_search.return_value = []

            config = EmbeddingManagerConfig.for_development()
            manager = EmbeddingManager(temp_vector_store, config)

            results = manager.search_similar_chunks("test query", limit=5)

            assert isinstance(results, list)
            mock_search.assert_called_once()


class TestEmbeddingIntegration:
    """Test full integration of embedding system."""

    @patch("codebase_gardener.data.embeddings.SentenceTransformer")
    @patch("lancedb.connect")
    def test_full_pipeline_integration(
        self, mock_connect, mock_sentence_transformer, temp_vector_store
    ):
        """Test the complete embedding pipeline from chunks to search."""
        # Setup comprehensive mocks
        mock_db = Mock()
        mock_db.table_names.return_value = []
        mock_table = Mock()
        mock_db.create_table.return_value = mock_table

        # Mock search functionality
        mock_search = Mock()
        mock_search.limit.return_value = mock_search
        mock_search.to_list.return_value = []
        mock_table.search.return_value = mock_search

        mock_connect.return_value = mock_db

        mock_model = Mock()
        mock_model.max_seq_length = 2048
        mock_model.get_sentence_embedding_dimension.return_value = 384
        mock_embeddings = np.random.rand(2, 384)
        mock_model.encode.return_value = mock_embeddings
        mock_sentence_transformer.return_value = mock_model

        # Create test data
        chunks = []
        for i in range(2):
            chunk = CodeChunk(
                id=f"integration_chunk_{i}",
                content=f"def test_function_{i}():\n    return {i}",
                language="python",
                chunk_type=ChunkType.FUNCTION,
                file_path=Path("integration_test.py"),
                start_line=i * 3 + 1,
                end_line=i * 3 + 2,
                start_byte=i * 60,
                end_byte=(i + 1) * 60,
                metadata={"element_name": f"test_function_{i}"},
                dependencies=[],
                complexity_score=2.0,
            )
            chunks.append(chunk)

        # Run integration test
        config = EmbeddingManagerConfig.for_development()
        manager = EmbeddingManager(temp_vector_store, config)

        # Process chunks
        processing_result = manager.process_chunks(chunks)
        assert processing_result.success_rate == 100.0

        # Search for similar chunks
        search_results = manager.search_similar_chunks("test function", limit=10)
        assert isinstance(search_results, list)

        # Verify embedding generation was called
        mock_model.encode.assert_called()
        mock_table.add.assert_called()

    def test_embedding_system_health_check(self, temp_vector_store):
        """Test health check functionality."""
        with patch("codebase_gardener.data.embeddings.SentenceTransformer"):
            config = EmbeddingManagerConfig.for_development()
            manager = EmbeddingManager(temp_vector_store, config)

            health = manager.health_check()

            assert "status" in health
            assert "components" in health
            assert "embeddings_generator" in health["components"]
            assert "vector_store" in health["components"]


if __name__ == "__main__":
    pytest.main([__file__])
