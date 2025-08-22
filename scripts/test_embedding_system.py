#!/usr/bin/env python3
"""
Test script to validate the embedding system functionality.
"""

import sys
import tempfile
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from codebase_gardener.data.embedding_manager import (  # noqa: E402
    EmbeddingManager,
    EmbeddingManagerConfig,
)
from codebase_gardener.data.embeddings import (  # noqa: E402
    EmbeddingConfig,
    NomicEmbeddings,
)
from codebase_gardener.data.preprocessor import ChunkType, CodeChunk  # noqa: E402
from codebase_gardener.data.vector_store import VectorStore  # noqa: E402


def create_sample_chunk():
    """Create a sample code chunk for testing."""
    return CodeChunk(
        id="test_chunk_validation",
        content="""def fibonacci(n):
    '''Calculate the nth Fibonacci number.'''
    if n <= 1:
        return n
    return fibonacci(n-1) + fibonacci(n-2)""",
        language="python",
        chunk_type=ChunkType.FUNCTION,
        file_path=Path("test_fibonacci.py"),
        start_line=1,
        end_line=5,
        start_byte=0,
        end_byte=120,
        metadata={
            "element_name": "fibonacci",
            "has_docstring": True,
            "complexity": 3.2,
        },
        dependencies=["fibonacci"],  # Recursive call
        complexity_score=3.2,
    )


def test_embeddings_basic():
    """Test basic embedding generation."""
    print("Testing basic embedding generation...")

    # Use CPU and development config to avoid any hardware issues
    config = EmbeddingConfig(
        model_name="sentence-transformers/all-MiniLM-L6-v2",  # Smaller, reliable model
        device="cpu",
        batch_size=1,
        cache_embeddings=False,
    )

    try:
        embeddings_gen = NomicEmbeddings(config)
        chunk = create_sample_chunk()

        # Test single embedding
        result = embeddings_gen.embed_chunk(chunk)
        print(
            f"✅ Single embedding generated: dimension={result.dimension}, valid={result.is_valid}"
        )

        # Test query embedding
        query_embedding = embeddings_gen.embed_query(
            "function to calculate fibonacci sequence"
        )
        print(f"✅ Query embedding generated: dimension={query_embedding.shape[0]}")

        # Test batch embedding
        chunks = [chunk, chunk]  # Duplicate for testing
        batch_results = embeddings_gen.embed_chunks_batch(chunks)
        print(f"✅ Batch embeddings generated: count={len(batch_results)}")

        return True

    except Exception as e:
        print(f"❌ Basic embedding test failed: {e}")
        return False


def test_vector_store_basic():
    """Test basic vector store functionality."""
    print("Testing vector store functionality...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "test_vector_store"
            vector_store = VectorStore(db_path)

            # Test connection
            vector_store.connect()
            print("✅ Vector store connection successful")

            # Test health check
            health = vector_store.health_check()
            print(
                f"✅ Vector store health check: status={health.get('status', 'unknown')}"
            )

            return True

    except Exception as e:
        print(f"❌ Vector store test failed: {e}")
        return False


def test_integration():
    """Test full integration."""
    print("Testing embedding manager integration...")

    try:
        with tempfile.TemporaryDirectory() as temp_dir:
            db_path = Path(temp_dir) / "integration_test_db"
            vector_store = VectorStore(db_path)
            vector_store.connect()

            # Use safe configuration
            embedding_config = EmbeddingConfig(
                model_name="sentence-transformers/all-MiniLM-L6-v2",
                device="cpu",
                batch_size=1,
                cache_embeddings=False,
            )

            manager_config = EmbeddingManagerConfig(
                embedding_config=embedding_config,
                batch_size=1,
                validate_embeddings=False,
                enable_incremental_updates=False,
            )

            manager = EmbeddingManager(vector_store, manager_config)

            # Test processing chunks
            chunk = create_sample_chunk()
            result = manager.process_chunks([chunk])

            print("✅ Integration test successful:")
            print(f"   Processed: {result.processed_chunks}")
            print(f"   Success rate: {result.success_rate:.1f}%")
            print(f"   Processing time: {result.total_processing_time:.2f}s")

            # Test health check
            health = manager.health_check()
            print(f"✅ System health: {health.get('status', 'unknown')}")

            return True

    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("EMBEDDING SYSTEM VALIDATION")
    print("=" * 60)

    tests = [
        test_embeddings_basic,
        test_vector_store_basic,
        test_integration,
    ]

    passed = 0
    total = len(tests)

    for test_func in tests:
        print(f"\n--- Running {test_func.__name__} ---")
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_func.__name__} PASSED")
            else:
                print(f"❌ {test_func.__name__} FAILED")
        except Exception as e:
            print(f"❌ {test_func.__name__} ERROR: {e}")

    print("\n" + "=" * 60)
    print("VALIDATION RESULTS")
    print("=" * 60)
    print(f"Tests passed: {passed}/{total}")

    if passed == total:
        print("🎉 All embedding system tests passed!")
        return True
    else:
        print(f"⚠️  {total - passed} test(s) failed.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
