"""
Integration test for the complete pipeline: File → Parser → Preprocessor → Embeddings

This test validates that our components work together with REAL data, not just mocks.
It processes this actual codebase to ensure our assumptions are correct.
"""

import os
import time
from pathlib import Path
import pytest
import psutil
from typing import List

from codebase_gardener.config.settings import Settings
from codebase_gardener.data.parser import TreeSitterParser
from codebase_gardener.data.preprocessor import CodePreprocessor
from codebase_gardener.models.nomic_embedder import NomicEmbedder


class TestEndToEndPipeline:
    """Integration tests for the complete processing pipeline."""
    
    @pytest.fixture
    def real_settings(self):
        """Create settings for real integration testing."""
        # Use a temporary directory for testing
        test_data_dir = Path("/tmp/codebase_gardener_integration_test")
        test_data_dir.mkdir(exist_ok=True)
        
        settings = Settings()
        settings.data_dir = test_data_dir
        settings.embedding_model = "microsoft/codebert-base"  # Real model
        settings.embedding_batch_size = 8  # Smaller for testing
        settings.log_level = "INFO"
        
        return settings
    
    @pytest.fixture
    def real_codebase_files(self):
        """Get actual Python files from this codebase for testing."""
        src_dir = Path("src/codebase_gardener")
        if not src_dir.exists():
            pytest.skip("Source directory not found - run from project root")
        
        python_files = list(src_dir.rglob("*.py"))
        if len(python_files) < 5:
            pytest.skip("Not enough Python files found for integration test")
        
        # Limit to first 10 files to keep test reasonable
        return python_files[:10]
    
    def test_complete_pipeline_with_real_codebase(self, real_settings, real_codebase_files):
        """Test the complete pipeline with real files from this codebase."""
        print(f"\n🧪 Testing pipeline with {len(real_codebase_files)} real Python files")
        
        # Initialize components
        from codebase_gardener.data.parser import SupportedLanguage
        from codebase_gardener.data.preprocessor import PreprocessingConfig
        
        parser = TreeSitterParser(SupportedLanguage.PYTHON)
        
        # Create preprocessing config from settings
        preprocessing_config = PreprocessingConfig(
            max_chunk_size=real_settings.max_chunk_size,
            min_chunk_size=real_settings.min_chunk_size,
            overlap_size=real_settings.chunk_overlap
        )
        preprocessor = CodePreprocessor(preprocessing_config)
        embedder = NomicEmbedder(real_settings)
        
        # Track performance metrics
        start_time = time.time()
        start_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        all_chunks = []
        all_embeddings = []
        
        # Process each file
        for file_path in real_codebase_files:
            print(f"  📄 Processing: {file_path.name}")
            
            # Read file content
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
            except Exception as e:
                print(f"    ⚠️  Skipping {file_path}: {e}")
                continue
            
            if not content.strip():
                continue
            
            # Parse with Tree-sitter
            try:
                parse_result = parser.parse(content, "python")
                assert not parse_result.has_errors, f"Parser errors in {file_path}"
            except Exception as e:
                print(f"    ⚠️  Parse failed for {file_path}: {e}")
                continue
            
            # Preprocess into chunks
            try:
                chunks = preprocessor.preprocess_code(content, "python", file_path)
                print(f"    📦 Generated {len(chunks)} chunks")
                all_chunks.extend(chunks)
            except Exception as e:
                print(f"    ⚠️  Preprocessing failed for {file_path}: {e}")
                continue
        
        # Generate embeddings for all chunks
        if all_chunks:
            print(f"\n🔮 Generating embeddings for {len(all_chunks)} chunks...")
            try:
                embeddings = embedder.embed_chunks(all_chunks)
                all_embeddings.extend(embeddings)
                print(f"    ✅ Generated {len(embeddings)} embeddings")
            except Exception as e:
                pytest.fail(f"Embedding generation failed: {e}")
        
        # Calculate performance metrics
        end_time = time.time()
        end_memory = psutil.Process().memory_info().rss / 1024 / 1024  # MB
        
        processing_time = end_time - start_time
        memory_used = end_memory - start_memory
        
        # Print results
        print(f"\n📊 Performance Results:")
        print(f"    ⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"    🧠 Memory used: {memory_used:.1f} MB")
        print(f"    📁 Files processed: {len(real_codebase_files)}")
        print(f"    📦 Chunks generated: {len(all_chunks)}")
        print(f"    🔮 Embeddings created: {len(all_embeddings)}")
        
        if all_chunks:
            print(f"    ⚡ Chunks per second: {len(all_chunks) / processing_time:.1f}")
        
        # Validate results
        assert len(all_chunks) > 0, "No chunks were generated"
        assert len(all_embeddings) == len(all_chunks), "Embedding count mismatch"
        assert processing_time < 300, f"Processing too slow: {processing_time:.1f}s"  # 5 min max
        assert memory_used < 2000, f"Memory usage too high: {memory_used:.1f}MB"  # 2GB max
        
        # Validate embedding quality
        if all_embeddings:
            embedding_dim = len(all_embeddings[0])
            print(f"    📏 Embedding dimension: {embedding_dim}")
            assert embedding_dim > 0, "Invalid embedding dimension"
            
            # Check that embeddings are not all zeros
            import numpy as np
            first_embedding = np.array(all_embeddings[0])
            assert np.any(first_embedding != 0), "Embeddings are all zeros"
        
        print(f"\n✅ Integration test passed!")
    
    def test_configuration_with_real_environment(self, real_settings):
        """Test that configuration works with real environment variables."""
        print(f"\n🔧 Testing configuration system...")
        
        # Test data directory creation
        assert real_settings.data_dir.exists(), "Data directory not created"
        
        # Test embedding model configuration
        embedder = NomicEmbedder(real_settings)
        model_info = embedder.get_model_info()
        
        print(f"    📋 Model: {model_info['model_name']}")
        print(f"    📏 Embedding dim: {model_info['embedding_dimension']}")
        print(f"    🔢 Batch size: {model_info['batch_size']}")
        
        assert model_info['model_name'] == real_settings.embedding_model
        assert model_info['embedding_dimension'] > 0
        
        print(f"✅ Configuration test passed!")
    
    def test_cache_persistence_with_real_files(self, real_settings, real_codebase_files):
        """Test that caching works with real file content."""
        if not real_codebase_files:
            pytest.skip("No real files available for cache test")
        
        print(f"\n💾 Testing cache persistence...")
        
        embedder = NomicEmbedder(real_settings)
        embedder.clear_cache()  # Start fresh
        
        # Read a real file
        test_file = real_codebase_files[0]
        with open(test_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create a simple chunk for testing
        from codebase_gardener.data.preprocessor import CodeChunk, ChunkType
        test_chunk = CodeChunk(
            id="test_cache",
            content=content[:500],  # First 500 chars
            language="python",
            chunk_type=ChunkType.MODULE,
            file_path=test_file,
            start_line=1,
            end_line=10,
            start_byte=0,
            end_byte=500,
            metadata={},
            dependencies=[],
            complexity_score=1.0
        )
        
        # First embedding (should generate)
        start_time = time.time()
        embedding1 = embedder.embed_single(test_chunk)
        first_time = time.time() - start_time
        
        # Second embedding (should use cache)
        start_time = time.time()
        embedding2 = embedder.embed_single(test_chunk)
        second_time = time.time() - start_time
        
        print(f"    ⏱️  First embedding: {first_time:.3f}s")
        print(f"    ⏱️  Second embedding: {second_time:.3f}s")
        print(f"    🚀 Speedup: {first_time / second_time:.1f}x")
        
        # Validate cache worked
        import numpy as np
        np.testing.assert_array_equal(embedding1, embedding2)
        assert second_time < first_time / 2, "Cache didn't provide speedup"
        
        # Check cache stats
        cache_stats = embedder.cache.get_stats()
        print(f"    📊 Cache entries: {cache_stats['memory_entries']} memory, {cache_stats['disk_entries']} disk")
        
        assert cache_stats['memory_entries'] > 0 or cache_stats['disk_entries'] > 0
        
        print(f"✅ Cache test passed!")


if __name__ == "__main__":
    # Allow running this test directly for manual validation
    import sys
    sys.exit(pytest.main([__file__, "-v", "-s"]))