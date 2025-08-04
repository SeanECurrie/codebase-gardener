"""
LanceDB Vector Storage System

This module provides a vector storage system using LanceDB for efficient similarity search
and metadata filtering of code chunks. It integrates with the Nomic embeddings system
and supports project-specific vector stores for multi-tenant architecture.
"""

import json
import logging
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

import lancedb
import numpy as np
import pyarrow as pa
from lancedb.pydantic import LanceModel, Vector

from codebase_gardener.data.preprocessor import CodeChunk
from codebase_gardener.utils.error_handling import VectorStoreError, retry_with_exponential_backoff
from codebase_gardener.config.settings import Settings

logger = logging.getLogger(__name__)


@dataclass
class SearchResult:
    """Result from vector similarity search."""
    chunk_id: str
    chunk: CodeChunk
    similarity_score: float
    metadata: Dict[str, Any]


class CodeChunkSchema(LanceModel):
    """Pydantic schema for storing code chunks in LanceDB."""
    
    # Core identifiers
    id: str
    file_path: str
    
    # Content and structure
    content: str
    language: str
    chunk_type: str
    start_line: int
    end_line: int
    start_byte: int
    end_byte: int
    
    # Vector embedding (384 dimensions for Nomic embeddings)
    embedding: Vector(384)
    
    # Metadata as JSON string for flexibility
    metadata: str
    dependencies: str
    complexity_score: float
    
    # Timestamps
    created_at: str
    updated_at: str


class VectorStore:
    """
    LanceDB-based vector storage system for code chunks.
    
    Provides efficient similarity search, metadata filtering, and batch operations
    optimized for Mac Mini M4 constraints.
    """
    
    def __init__(self, db_path: Path, table_name: str = "code_chunks"):
        """
        Initialize the vector store.
        
        Args:
            db_path: Path to the LanceDB database directory
            table_name: Name of the table to store code chunks
        """
        self.db_path = db_path
        self.table_name = table_name
        self.db = None
        self.table = None
        self._connected = False
        
        # Ensure database directory exists
        self.db_path.mkdir(parents=True, exist_ok=True)
        
        logger.info(f"Initialized VectorStore with db_path={db_path}, table={table_name}")
    
    def connect(self) -> None:
        """Connect to LanceDB and initialize table if needed."""
        try:
            self.db = lancedb.connect(str(self.db_path))
            self._connected = True
            
            # Check if table exists, create if not
            if self.table_name not in self.db.table_names():
                logger.info(f"Creating new table: {self.table_name}")
                self._create_table()
            else:
                logger.info(f"Opening existing table: {self.table_name}")
                self.table = self.db.open_table(self.table_name)
                
        except Exception as e:
            raise VectorStoreError(f"Failed to connect to LanceDB: {e}") from e
    
    def _create_table(self) -> None:
        """Create a new table with the CodeChunk schema."""
        try:
            # Create empty table with schema
            self.table = self.db.create_table(
                self.table_name,
                schema=CodeChunkSchema.to_arrow_schema()
            )
            logger.info(f"Created table {self.table_name} with schema")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to create table {self.table_name}: {e}") from e
    
    def _ensure_connected(self) -> None:
        """Ensure database connection is established."""
        if not self._connected or self.db is None:
            self.connect()
    
    def _chunk_to_schema(self, chunk: CodeChunk, embedding: np.ndarray) -> Dict[str, Any]:
        """Convert CodeChunk to schema-compatible dictionary."""
        now = datetime.now().isoformat()
        
        return {
            "id": chunk.id,
            "file_path": str(chunk.file_path),
            "content": chunk.content,
            "language": chunk.language,
            "chunk_type": chunk.chunk_type.value if hasattr(chunk.chunk_type, 'value') else str(chunk.chunk_type),
            "start_line": chunk.start_line,
            "end_line": chunk.end_line,
            "start_byte": chunk.start_byte,
            "end_byte": chunk.end_byte,
            "embedding": embedding.tolist(),
            "metadata": json.dumps(chunk.metadata),
            "dependencies": json.dumps(chunk.dependencies),
            "complexity_score": chunk.complexity_score,
            "created_at": now,
            "updated_at": now
        }
    
    def _schema_to_chunk(self, row: Dict[str, Any]) -> CodeChunk:
        """Convert schema row back to CodeChunk object."""
        from codebase_gardener.data.preprocessor import ChunkType
        
        # Parse chunk type
        chunk_type_str = row["chunk_type"]
        try:
            chunk_type = ChunkType(chunk_type_str)
        except ValueError:
            # Fallback for unknown chunk types
            chunk_type = ChunkType.OTHER
        
        return CodeChunk(
            id=row["id"],
            file_path=Path(row["file_path"]),
            content=row["content"],
            language=row["language"],
            chunk_type=chunk_type,
            start_line=row["start_line"],
            end_line=row["end_line"],
            start_byte=row["start_byte"],
            end_byte=row["end_byte"],
            metadata=json.loads(row["metadata"]),
            dependencies=json.loads(row["dependencies"]),
            complexity_score=row["complexity_score"]
        )
    
    @retry_with_exponential_backoff(max_retries=3)
    def add_chunks(self, chunks: List[CodeChunk], embeddings: List[np.ndarray]) -> None:
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
        
        self._ensure_connected()
        
        try:
            # Convert chunks to schema format
            data = []
            for chunk, embedding in zip(chunks, embeddings):
                data.append(self._chunk_to_schema(chunk, embedding))
            
            # Add to table
            self.table.add(data)
            
            logger.info(f"Added {len(chunks)} chunks to vector store")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to add chunks to vector store: {e}") from e
    
    @retry_with_exponential_backoff(max_retries=3)
    def search_similar(
        self,
        query_embedding: np.ndarray,
        limit: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[SearchResult]:
        """
        Search for similar code chunks using vector similarity.
        
        Args:
            query_embedding: Query vector for similarity search
            limit: Maximum number of results to return
            filters: Optional metadata filters (e.g., {"language": "python"})
            
        Returns:
            List of SearchResult objects ordered by similarity
            
        Raises:
            VectorStoreError: If search fails
        """
        self._ensure_connected()
        
        try:
            # Start with vector search
            search_query = self.table.search(query_embedding.tolist()).limit(limit)
            
            # Apply filters if provided
            if filters:
                filter_conditions = []
                for key, value in filters.items():
                    if isinstance(value, str):
                        filter_conditions.append(f"{key} = '{value}'")
                    else:
                        filter_conditions.append(f"{key} = {value}")
                
                if filter_conditions:
                    where_clause = " AND ".join(filter_conditions)
                    search_query = search_query.where(where_clause)
            
            # Execute search and get results
            results = search_query.to_pandas()
            
            # Convert to SearchResult objects
            search_results = []
            for _, row in results.iterrows():
                chunk = self._schema_to_chunk(row.to_dict())
                
                search_result = SearchResult(
                    chunk_id=chunk.id,
                    chunk=chunk,
                    similarity_score=1.0 - row.get("_distance", 0.0),  # Convert distance to similarity
                    metadata=chunk.metadata
                )
                search_results.append(search_result)
            
            logger.info(f"Found {len(search_results)} similar chunks")
            return search_results
            
        except Exception as e:
            raise VectorStoreError(f"Failed to search similar chunks: {e}") from e
    
    @retry_with_exponential_backoff(max_retries=3)
    def get_by_id(self, chunk_id: str) -> Optional[CodeChunk]:
        """
        Retrieve a specific chunk by its ID.
        
        Args:
            chunk_id: Unique identifier of the chunk
            
        Returns:
            CodeChunk object if found, None otherwise
            
        Raises:
            VectorStoreError: If retrieval fails
        """
        self._ensure_connected()
        
        try:
            # Query by ID
            results = self.table.search().where(f"id = '{chunk_id}'").limit(1).to_pandas()
            
            if results.empty:
                return None
            
            # Convert first result to CodeChunk
            row = results.iloc[0].to_dict()
            return self._schema_to_chunk(row)
            
        except Exception as e:
            raise VectorStoreError(f"Failed to get chunk by ID {chunk_id}: {e}") from e
    
    @retry_with_exponential_backoff(max_retries=3)
    def update_chunk(self, chunk: CodeChunk, embedding: np.ndarray) -> None:
        """
        Update an existing chunk with new content and embedding.
        
        Args:
            chunk: Updated CodeChunk object
            embedding: Updated embedding vector
            
        Raises:
            VectorStoreError: If update fails
        """
        self._ensure_connected()
        
        try:
            # Delete existing chunk
            self.table.delete(f"id = '{chunk.id}'")
            
            # Add updated chunk
            data = [self._chunk_to_schema(chunk, embedding)]
            self.table.add(data)
            
            logger.info(f"Updated chunk {chunk.id}")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to update chunk {chunk.id}: {e}") from e
    
    @retry_with_exponential_backoff(max_retries=3)
    def delete_chunks(self, chunk_ids: List[str]) -> None:
        """
        Delete chunks by their IDs.
        
        Args:
            chunk_ids: List of chunk IDs to delete
            
        Raises:
            VectorStoreError: If deletion fails
        """
        self._ensure_connected()
        
        try:
            # Build delete condition
            if len(chunk_ids) == 1:
                condition = f"id = '{chunk_ids[0]}'"
            else:
                id_list = "', '".join(chunk_ids)
                condition = f"id IN ('{id_list}')"
            
            # Execute deletion
            self.table.delete(condition)
            
            logger.info(f"Deleted {len(chunk_ids)} chunks")
            
        except Exception as e:
            raise VectorStoreError(f"Failed to delete chunks: {e}") from e
    
    @retry_with_exponential_backoff(max_retries=3)
    def optimize_index(self) -> None:
        """
        Create or optimize vector index for better search performance.
        
        Raises:
            VectorStoreError: If index optimization fails
        """
        self._ensure_connected()
        
        try:
            # Create vector index on embedding column
            self.table.create_index(
                column="embedding",
                index_type="IVF_FLAT",
                num_partitions=256,
                num_sub_vectors=96
            )
            
            logger.info("Optimized vector index")
            
        except Exception as e:
            # Index creation might fail if already exists, log but don't raise
            logger.warning(f"Index optimization failed (may already exist): {e}")
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get statistics about the vector store.
        
        Returns:
            Dictionary with store statistics
        """
        self._ensure_connected()
        
        try:
            # Get table stats
            stats = {
                "table_name": self.table_name,
                "total_chunks": len(self.table),
                "schema": str(self.table.schema),
                "db_path": str(self.db_path)
            }
            
            # Get language distribution
            results = self.table.to_pandas()
            if not results.empty:
                language_counts = results["language"].value_counts().to_dict()
                stats["language_distribution"] = language_counts
            
            return stats
            
        except Exception as e:
            logger.warning(f"Failed to get vector store stats: {e}")
            return {"error": str(e)}
    
    def close(self) -> None:
        """Close database connection and cleanup resources."""
        if self._connected:
            self.db = None
            self.table = None
            self._connected = False
            logger.info("Closed vector store connection")
    
    def __enter__(self):
        """Context manager entry."""
        self.connect()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        self.close()