"""
Tests for the LanceDB vector storage system.

This module tests the VectorStore class functionality including:
- Connection management and table creation
- Adding and retrieving code chunks with embeddings
- Similarity search with metadata filtering
- Batch operations and error handling
- Index optimization and performance
"""

import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

import numpy as np
import pandas as pd
import pytest
from codebase_gardener.data.preprocessor import ChunkType, CodeChunk
from codebase_gardener.data.vector_store import (
    CodeChunkSchema,
    SearchResult,
    VectorStore,
)
from codebase_gardener.utils.error_handling import VectorStoreError


@pytest.fixture
def temp_db_path():
    """Create a temporary directory for test database."""
    with tempfile.TemporaryDirectory() as temp_dir:
        yield Path(temp_dir) / "test_db"


@pytest.fixture
def sample_chunks():
    """Create sample CodeChunk objects for testing."""
    return [
        CodeChunk(
            id="chunk_1",
            file_path=Path("test.py"),
            content="def hello(): return 'world'",
            language="python",
            chunk_type=ChunkType.FUNCTION,
            start_line=1,
            end_line=1,
            start_byte=0,
            end_byte=28,
            metadata={"author": "test"},
            dependencies=[],
            complexity_score=1.0
        ),
        CodeChunk(
            id="chunk_2",
            file_path=Path("test.js"),
            content="function greet() { return 'hello'; }",
            language="javascript",
            chunk_type=ChunkType.FUNCTION,
            start_line=1,
            end_line=1,
            start_byte=0,
            end_byte=36,
            metadata={"author": "test"},
            dependencies=[],
            complexity_score=1.5
        )
    ]


@pytest.fixture
def sample_embeddings():
    """Create sample embedding vectors."""
    return [
        np.array([1.0, 2.0, 3.0] + [0.0] * 381),  # 384 dimensions
        np.array([4.0, 5.0, 6.0] + [0.0] * 381)   # 384 dimensions
    ]


@pytest.fixture
def mock_lancedb():
    """Mock LanceDB for testing."""
    with patch('codebase_gardener.data.vector_store.lancedb') as mock_lancedb:
        mock_db = Mock()
        mock_table = Mock()

        # Setup mock database
        mock_lancedb.connect.return_value = mock_db
        mock_db.table_names.return_value = []
        mock_db.create_table.return_value = mock_table
        mock_db.open_table.return_value = mock_table

        # Setup mock table
        mock_table.add = Mock()
        mock_table.search.return_value = Mock()
        mock_table.delete = Mock()
        mock_table.create_index = Mock()
        mock_table.__len__ = Mock(return_value=0)
        mock_table.to_pandas.return_value = pd.DataFrame()
        mock_table.schema = "mock_schema"

        yield mock_lancedb, mock_db, mock_table


class TestVectorStore:
    """Test cases for VectorStore class."""

    def test_initialization(self, temp_db_path):
        """Test VectorStore initialization."""
        vector_store = VectorStore(temp_db_path, "test_table")

        assert vector_store.db_path == temp_db_path
        assert vector_store.table_name == "test_table"
        assert vector_store.db is None
        assert vector_store.table is None
        assert not vector_store._connected
        assert temp_db_path.exists()  # Directory should be created

    def test_connect_new_table(self, temp_db_path, mock_lancedb):
        """Test connecting and creating a new table."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path, "test_table")
        vector_store.connect()

        # Verify connection was established
        mock_lancedb_module.connect.assert_called_once_with(str(temp_db_path))
        assert vector_store._connected
        assert vector_store.db == mock_db

        # Verify table was created
        mock_db.table_names.assert_called_once()
        mock_db.create_table.assert_called_once()

    def test_connect_existing_table(self, temp_db_path, mock_lancedb):
        """Test connecting to an existing table."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_db.table_names.return_value = ["test_table"]

        vector_store = VectorStore(temp_db_path, "test_table")
        vector_store.connect()

        # Verify existing table was opened
        mock_db.open_table.assert_called_once_with("test_table")
        assert vector_store.table == mock_table

    def test_connect_failure(self, temp_db_path, mock_lancedb):
        """Test connection failure handling."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_lancedb_module.connect.side_effect = Exception("Connection failed")

        vector_store = VectorStore(temp_db_path, "test_table")

        with pytest.raises(VectorStoreError, match="Failed to connect to LanceDB"):
            vector_store.connect()

    def test_chunk_to_schema_conversion(self, temp_db_path, sample_chunks, sample_embeddings):
        """Test conversion from CodeChunk to schema format."""
        vector_store = VectorStore(temp_db_path)
        chunk = sample_chunks[0]
        embedding = sample_embeddings[0]

        schema_data = vector_store._chunk_to_schema(chunk, embedding)

        assert schema_data["id"] == chunk.id
        assert schema_data["file_path"] == str(chunk.file_path)
        assert schema_data["content"] == chunk.content
        assert schema_data["language"] == chunk.language
        assert schema_data["chunk_type"] == chunk.chunk_type.value
        assert schema_data["embedding"] == embedding.tolist()
        assert json.loads(schema_data["metadata"]) == chunk.metadata
        assert "created_at" in schema_data
        assert "updated_at" in schema_data

    def test_schema_to_chunk_conversion(self, temp_db_path):
        """Test conversion from schema format back to CodeChunk."""
        vector_store = VectorStore(temp_db_path)

        schema_row = {
            "id": "test_chunk",
            "file_path": "test.py",
            "content": "def test(): pass",
            "language": "python",
            "chunk_type": "function",
            "start_line": 1,
            "end_line": 1,
            "start_byte": 0,
            "end_byte": 16,
            "metadata": '{"author": "test"}',
            "dependencies": '[]',
            "complexity_score": 1.0
        }

        chunk = vector_store._schema_to_chunk(schema_row)

        assert chunk.id == "test_chunk"
        assert chunk.file_path == Path("test.py")
        assert chunk.content == "def test(): pass"
        assert chunk.language == "python"
        assert chunk.chunk_type == ChunkType.FUNCTION
        assert chunk.metadata == {"author": "test"}
        assert chunk.dependencies == []

    def test_add_chunks_success(self, temp_db_path, mock_lancedb, sample_chunks, sample_embeddings):
        """Test successfully adding chunks to vector store."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()
        vector_store.add_chunks(sample_chunks, sample_embeddings)

        # Verify table.add was called with correct data
        mock_table.add.assert_called_once()
        call_args = mock_table.add.call_args[0][0]
        assert len(call_args) == 2  # Two chunks
        assert call_args[0]["id"] == "chunk_1"
        assert call_args[1]["id"] == "chunk_2"

    def test_add_chunks_mismatch_error(self, temp_db_path, sample_chunks, sample_embeddings):
        """Test error when chunks and embeddings count don't match."""
        vector_store = VectorStore(temp_db_path)

        with pytest.raises(VectorStoreError, match="Chunks and embeddings count mismatch"):
            vector_store.add_chunks(sample_chunks, sample_embeddings[:1])  # One less embedding

    def test_add_chunks_storage_error(self, temp_db_path, mock_lancedb, sample_chunks, sample_embeddings):
        """Test handling of storage errors during add operation."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_table.add.side_effect = Exception("Storage error")

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        with pytest.raises(VectorStoreError, match="Failed to add chunks to vector store"):
            vector_store.add_chunks(sample_chunks, sample_embeddings)

    def test_search_similar_basic(self, temp_db_path, mock_lancedb, sample_chunks):
        """Test basic similarity search."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        # Mock search results
        mock_search_query = Mock()
        mock_table.search.return_value = mock_search_query
        mock_search_query.limit.return_value = mock_search_query

        # Create mock pandas DataFrame with search results
        result_data = {
            "id": ["chunk_1"],
            "file_path": ["test.py"],
            "content": ["def hello(): return 'world'"],
            "language": ["python"],
            "chunk_type": ["function"],
            "start_line": [1],
            "end_line": [1],
            "start_byte": [0],
            "end_byte": [28],
            "metadata": ['{"author": "test"}'],
            "dependencies": ['[]'],
            "complexity_score": [1.0],
            "_distance": [0.1]  # LanceDB distance score
        }
        mock_df = pd.DataFrame(result_data)
        mock_search_query.to_pandas.return_value = mock_df

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        query_embedding = np.array([1.0, 2.0, 3.0] + [0.0] * 381)
        results = vector_store.search_similar(query_embedding, limit=5)

        # Verify search was called correctly
        mock_table.search.assert_called_once_with(query_embedding.tolist())
        mock_search_query.limit.assert_called_once_with(5)

        # Verify results
        assert len(results) == 1
        assert isinstance(results[0], SearchResult)
        assert results[0].chunk_id == "chunk_1"
        assert results[0].similarity_score == 0.9  # 1.0 - 0.1 distance

    def test_search_similar_with_filters(self, temp_db_path, mock_lancedb):
        """Test similarity search with metadata filters."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        mock_search_query = Mock()
        mock_table.search.return_value = mock_search_query
        mock_search_query.limit.return_value = mock_search_query
        mock_search_query.where.return_value = mock_search_query
        mock_search_query.to_pandas.return_value = pd.DataFrame()

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        query_embedding = np.array([1.0, 2.0, 3.0] + [0.0] * 381)
        filters = {"language": "python", "complexity_score": 1.0}

        vector_store.search_similar(query_embedding, limit=5, filters=filters)

        # Verify filters were applied
        mock_search_query.where.assert_called_once()
        where_clause = mock_search_query.where.call_args[0][0]
        assert "language = 'python'" in where_clause
        assert "complexity_score = 1.0" in where_clause

    def test_search_similar_error(self, temp_db_path, mock_lancedb):
        """Test error handling during similarity search."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_table.search.side_effect = Exception("Search error")

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        query_embedding = np.array([1.0, 2.0, 3.0] + [0.0] * 381)

        with pytest.raises(VectorStoreError, match="Failed to search similar chunks"):
            vector_store.search_similar(query_embedding)

    def test_get_by_id_found(self, temp_db_path, mock_lancedb):
        """Test retrieving chunk by ID when it exists."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        # Mock search results
        mock_search_query = Mock()
        mock_table.search.return_value = mock_search_query
        mock_search_query.where.return_value = mock_search_query
        mock_search_query.limit.return_value = mock_search_query

        result_data = {
            "id": ["chunk_1"],
            "file_path": ["test.py"],
            "content": ["def hello(): return 'world'"],
            "language": ["python"],
            "chunk_type": ["function"],
            "start_line": [1],
            "end_line": [1],
            "start_byte": [0],
            "end_byte": [28],
            "metadata": ['{"author": "test"}'],
            "dependencies": ['[]'],
            "complexity_score": [1.0]
        }
        mock_df = pd.DataFrame(result_data)
        mock_search_query.to_pandas.return_value = mock_df

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        chunk = vector_store.get_by_id("chunk_1")

        assert chunk is not None
        assert chunk.id == "chunk_1"
        assert chunk.content == "def hello(): return 'world'"

    def test_get_by_id_not_found(self, temp_db_path, mock_lancedb):
        """Test retrieving chunk by ID when it doesn't exist."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        mock_search_query = Mock()
        mock_table.search.return_value = mock_search_query
        mock_search_query.where.return_value = mock_search_query
        mock_search_query.limit.return_value = mock_search_query
        mock_search_query.to_pandas.return_value = pd.DataFrame()  # Empty results

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        chunk = vector_store.get_by_id("nonexistent")

        assert chunk is None

    def test_update_chunk(self, temp_db_path, mock_lancedb, sample_chunks, sample_embeddings):
        """Test updating an existing chunk."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        chunk = sample_chunks[0]
        embedding = sample_embeddings[0]

        vector_store.update_chunk(chunk, embedding)

        # Verify delete and add were called
        mock_table.delete.assert_called_once_with(f"id = '{chunk.id}'")
        mock_table.add.assert_called_once()

    def test_delete_chunks_single(self, temp_db_path, mock_lancedb):
        """Test deleting a single chunk."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        vector_store.delete_chunks(["chunk_1"])

        mock_table.delete.assert_called_once_with("id = 'chunk_1'")

    def test_delete_chunks_multiple(self, temp_db_path, mock_lancedb):
        """Test deleting multiple chunks."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        vector_store.delete_chunks(["chunk_1", "chunk_2"])

        mock_table.delete.assert_called_once_with("id IN ('chunk_1', 'chunk_2')")

    def test_optimize_index(self, temp_db_path, mock_lancedb):
        """Test index optimization."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        vector_store.optimize_index()

        mock_table.create_index.assert_called_once_with(
            column="embedding",
            index_type="IVF_FLAT",
            num_partitions=256,
            num_sub_vectors=96
        )

    def test_optimize_index_already_exists(self, temp_db_path, mock_lancedb):
        """Test index optimization when index already exists."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_table.create_index.side_effect = Exception("Index already exists")

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        # Should not raise exception, just log warning
        vector_store.optimize_index()

    def test_get_stats(self, temp_db_path, mock_lancedb):
        """Test getting vector store statistics."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_table.__len__.return_value = 10

        # Mock pandas DataFrame for language distribution
        result_data = {
            "language": ["python", "python", "javascript", "python"]
        }
        mock_df = pd.DataFrame(result_data)
        mock_table.to_pandas.return_value = mock_df

        vector_store = VectorStore(temp_db_path, "test_table")
        vector_store.connect()

        stats = vector_store.get_stats()

        assert stats["table_name"] == "test_table"
        assert stats["total_chunks"] == 10
        assert "language_distribution" in stats
        assert stats["language_distribution"]["python"] == 3
        assert stats["language_distribution"]["javascript"] == 1

    def test_get_stats_error(self, temp_db_path, mock_lancedb):
        """Test error handling in get_stats."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb
        mock_table.__len__.side_effect = Exception("Stats error")

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        stats = vector_store.get_stats()

        assert "error" in stats

    def test_close(self, temp_db_path, mock_lancedb):
        """Test closing vector store connection."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)
        vector_store.connect()

        assert vector_store._connected

        vector_store.close()

        assert not vector_store._connected
        assert vector_store.db is None
        assert vector_store.table is None

    def test_context_manager(self, temp_db_path, mock_lancedb):
        """Test using VectorStore as context manager."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        with VectorStore(temp_db_path) as vector_store:
            assert vector_store._connected

        # Should be closed after context exit
        assert not vector_store._connected

    def test_ensure_connected_auto_connect(self, temp_db_path, mock_lancedb):
        """Test that operations auto-connect if not connected."""
        mock_lancedb_module, mock_db, mock_table = mock_lancedb

        vector_store = VectorStore(temp_db_path)

        # Call operation without explicit connect
        query_embedding = np.array([1.0, 2.0, 3.0] + [0.0] * 381)

        mock_search_query = Mock()
        mock_table.search.return_value = mock_search_query
        mock_search_query.limit.return_value = mock_search_query
        mock_search_query.to_pandas.return_value = pd.DataFrame()

        vector_store.search_similar(query_embedding)

        # Should have auto-connected
        assert vector_store._connected
        mock_lancedb_module.connect.assert_called_once()


class TestCodeChunkSchema:
    """Test cases for CodeChunkSchema Pydantic model."""

    def test_schema_creation(self):
        """Test creating CodeChunkSchema with valid data."""
        schema_data = {
            "id": "test_chunk",
            "file_path": "test.py",
            "content": "def test(): pass",
            "language": "python",
            "chunk_type": "function",
            "start_line": 1,
            "end_line": 1,
            "start_byte": 0,
            "end_byte": 16,
            "embedding": [1.0, 2.0, 3.0] + [0.0] * 381,
            "metadata": '{"author": "test"}',
            "dependencies": '[]',
            "complexity_score": 1.0,
            "created_at": "2025-01-01T00:00:00",
            "updated_at": "2025-01-01T00:00:00"
        }

        schema = CodeChunkSchema(**schema_data)

        assert schema.id == "test_chunk"
        assert schema.content == "def test(): pass"
        assert len(schema.embedding) == 384

    def test_schema_to_arrow(self):
        """Test converting schema to Arrow schema."""
        arrow_schema = CodeChunkSchema.to_arrow_schema()

        # Verify schema has expected fields
        field_names = [field.name for field in arrow_schema]
        expected_fields = [
            "id", "file_path", "content", "language", "chunk_type",
            "start_line", "end_line", "start_byte", "end_byte",
            "embedding", "metadata", "dependencies", "complexity_score",
            "created_at", "updated_at"
        ]

        for field in expected_fields:
            assert field in field_names


class TestSearchResult:
    """Test cases for SearchResult dataclass."""

    def test_search_result_creation(self, sample_chunks):
        """Test creating SearchResult object."""
        chunk = sample_chunks[0]

        result = SearchResult(
            chunk_id=chunk.id,
            chunk=chunk,
            similarity_score=0.95,
            metadata=chunk.metadata
        )

        assert result.chunk_id == chunk.id
        assert result.chunk == chunk
        assert result.similarity_score == 0.95
        assert result.metadata == chunk.metadata


class TestIntegration:
    """Integration tests for VectorStore with real LanceDB operations."""

    @pytest.mark.integration
    def test_full_workflow_integration(self, temp_db_path, sample_chunks, sample_embeddings):
        """Test complete workflow with real LanceDB (if available)."""
        try:
            import lancedb
        except ImportError:
            pytest.skip("LanceDB not available for integration test")

        vector_store = VectorStore(temp_db_path, "integration_test")

        with vector_store:
            # Add chunks
            vector_store.add_chunks(sample_chunks, sample_embeddings)

            # Search for similar chunks
            query_embedding = sample_embeddings[0]
            results = vector_store.search_similar(query_embedding, limit=2)

            assert len(results) > 0
            assert results[0].chunk_id in ["chunk_1", "chunk_2"]

            # Get chunk by ID
            chunk = vector_store.get_by_id("chunk_1")
            assert chunk is not None
            assert chunk.id == "chunk_1"

            # Update chunk
            updated_chunk = sample_chunks[0]
            updated_chunk.content = "def updated(): return 'modified'"
            vector_store.update_chunk(updated_chunk, sample_embeddings[0])

            # Verify update
            retrieved_chunk = vector_store.get_by_id("chunk_1")
            assert retrieved_chunk.content == "def updated(): return 'modified'"

            # Delete chunk
            vector_store.delete_chunks(["chunk_1"])

            # Verify deletion
            deleted_chunk = vector_store.get_by_id("chunk_1")
            assert deleted_chunk is None

            # Get stats
            stats = vector_store.get_stats()
            assert "total_chunks" in stats

            # Optimize index
            vector_store.optimize_index()  # Should not raise exception
