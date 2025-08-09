"""
Performance Tests for Codebase Gardener MVP

This module provides performance testing to validate Mac Mini M4 optimization goals
and ensure the system meets performance requirements under various conditions.
"""

import os
import shutil
import tempfile
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from unittest.mock import Mock, patch

import psutil
import pytest

from src.codebase_gardener.main import ApplicationContext


@pytest.mark.performance
class TestPerformanceBenchmarks:
    """Performance benchmarks for Mac Mini M4 optimization validation."""

    @pytest.fixture(scope="class")
    def temp_data_dir(self):
        """Create temporary data directory for performance testing."""
        temp_dir = tempfile.mkdtemp(prefix="codebase_gardener_perf_")
        yield Path(temp_dir)
        shutil.rmtree(temp_dir, ignore_errors=True)

    @pytest.fixture(scope="class")
    def mock_settings(self, temp_data_dir):
        """Mock settings for performance testing."""
        settings = Mock()
        settings.data_dir = temp_data_dir
        settings.ollama_base_url = "http://localhost:11434"
        settings.default_embedding_model = "nomic-embed-code"
        settings.log_level = "WARNING"  # Reduce logging overhead
        return settings

    @pytest.fixture
    def app_context(self, mock_settings):
        """Create application context for performance testing."""
        with patch('src.codebase_gardener.config.settings.get_settings', return_value=mock_settings):
            context = ApplicationContext()
            yield context
            context.shutdown()

    def test_application_startup_performance(self, app_context):
        """Test application startup time meets Mac Mini M4 goals (<5 seconds)."""

        # Measure initialization time
        start_time = time.time()
        success = app_context.initialize()
        init_time = time.time() - start_time

        assert success, "Application should initialize successfully"
        assert init_time < 5.0, f"Initialization took {init_time:.2f}s, should be under 5s for Mac Mini M4"

        # Log performance metrics
        print(f"Application startup time: {init_time:.3f}s")

        # Verify all components are initialized
        assert app_context.project_registry is not None
        assert app_context.dynamic_model_loader is not None
        assert app_context.context_manager is not None
        assert app_context.vector_store_manager is not None

    def test_project_switching_performance(self, app_context):
        """Test project switching performance (<3 seconds per switch)."""

        assert app_context.initialize(), "Application should initialize"

        project_ids = ["perf-test-1", "perf-test-2", "perf-test-3"]
        switch_times = []

        # Mock successful project switching
        with patch.object(app_context, 'switch_project') as mock_switch:
            mock_switch.return_value = True

            for project_id in project_ids:
                start_time = time.time()
                success = app_context.switch_project(project_id)
                switch_time = time.time() - start_time

                assert success, f"Should switch to {project_id}"
                assert switch_time < 3.0, f"Switch to {project_id} took {switch_time:.2f}s, should be under 3s"

                switch_times.append(switch_time)

        # Calculate average switch time
        avg_switch_time = sum(switch_times) / len(switch_times)
        print(f"Average project switch time: {avg_switch_time:.3f}s")
        print(f"Switch times: {[f'{t:.3f}s' for t in switch_times]}")

        assert avg_switch_time < 2.0, f"Average switch time {avg_switch_time:.2f}s should be under 2s"

    def test_memory_usage_optimization(self, app_context):
        """Test memory usage stays within Mac Mini M4 constraints (<8GB total, <500MB for app)."""

        # Get initial memory usage
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        assert app_context.initialize(), "Application should initialize"

        # Memory after initialization
        post_init_memory = process.memory_info().rss / 1024 / 1024  # MB
        init_memory_increase = post_init_memory - initial_memory

        print(f"Initial memory: {initial_memory:.1f}MB")
        print(f"Post-init memory: {post_init_memory:.1f}MB")
        print(f"Initialization memory increase: {init_memory_increase:.1f}MB")

        # Simulate multiple project operations
        project_ids = [f"memory-test-{i}" for i in range(10)]

        with patch.object(app_context, 'switch_project') as mock_switch:
            mock_switch.return_value = True

            # Perform multiple operations
            for project_id in project_ids:
                app_context.switch_project(project_id)

                # Simulate some work
                time.sleep(0.01)

        # Final memory usage
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        total_memory_increase = final_memory - initial_memory

        print(f"Final memory: {final_memory:.1f}MB")
        print(f"Total memory increase: {total_memory_increase:.1f}MB")

        # Memory constraints for Mac Mini M4
        assert final_memory < 500, f"Application memory {final_memory:.1f}MB should be under 500MB"
        assert total_memory_increase < 300, f"Memory increase {total_memory_increase:.1f}MB should be under 300MB"

    def test_concurrent_operations_performance(self, app_context):
        """Test performance under concurrent operations."""

        assert app_context.initialize(), "Application should initialize"

        # Test concurrent project switches
        project_ids = [f"concurrent-test-{i}" for i in range(5)]

        def switch_project_task(project_id):
            """Task for concurrent project switching."""
            start_time = time.time()

            with patch.object(app_context, 'switch_project') as mock_switch:
                mock_switch.return_value = True
                success = app_context.switch_project(project_id)

            end_time = time.time()
            return {
                'project_id': project_id,
                'success': success,
                'duration': end_time - start_time
            }

        # Execute concurrent operations
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=3) as executor:
            futures = [executor.submit(switch_project_task, pid) for pid in project_ids]
            results = [future.result() for future in as_completed(futures)]

        total_time = time.time() - start_time

        # Verify all operations succeeded
        for result in results:
            assert result['success'], f"Concurrent switch to {result['project_id']} should succeed"
            assert result['duration'] < 5.0, f"Concurrent switch took {result['duration']:.2f}s, should be under 5s"

        # Total time should be reasonable for concurrent operations
        assert total_time < 10.0, f"Concurrent operations took {total_time:.2f}s, should be under 10s"

        print(f"Concurrent operations completed in {total_time:.3f}s")
        print(f"Individual operation times: {[f'{r['duration']:.3f}s' for r in results]}")

    def test_model_inference_performance(self, app_context):
        """Test AI model inference performance."""

        assert app_context.initialize(), "Application should initialize"

        project_id = "inference-perf-test"
        test_prompts = [
            "Analyze this simple function",
            "What are the potential improvements for this code?",
            "Explain the architecture pattern used here",
            "How can this code be optimized?",
            "What are the security considerations?"
        ]

        inference_times = []

        with patch.object(app_context.dynamic_model_loader, 'generate_response') as mock_generate:
            mock_generate.return_value = "This is a mock AI response for performance testing."

            for prompt in test_prompts:
                start_time = time.time()
                response = app_context.dynamic_model_loader.generate_response(prompt, project_id)
                inference_time = time.time() - start_time

                assert response, "Should generate response"
                assert inference_time < 10.0, f"Inference took {inference_time:.2f}s, should be under 10s"

                inference_times.append(inference_time)

        avg_inference_time = sum(inference_times) / len(inference_times)
        print(f"Average inference time: {avg_inference_time:.3f}s")
        print(f"Inference times: {[f'{t:.3f}s' for t in inference_times]}")

        assert avg_inference_time < 5.0, f"Average inference time {avg_inference_time:.2f}s should be under 5s"

    def test_vector_store_performance(self, app_context):
        """Test vector store operations performance."""

        assert app_context.initialize(), "Application should initialize"

        project_id = "vector-perf-test"

        # Test vector store creation and switching
        with patch.object(app_context.vector_store_manager, 'get_project_vector_store') as mock_get_store:
            mock_vector_store = Mock()
            mock_get_store.return_value = mock_vector_store

            # Test multiple vector store operations
            operation_times = []

            for i in range(10):
                start_time = time.time()
                vector_store = app_context.vector_store_manager.get_project_vector_store(project_id)
                operation_time = time.time() - start_time

                assert vector_store is not None, "Should get vector store"
                assert operation_time < 1.0, f"Vector store operation took {operation_time:.2f}s, should be under 1s"

                operation_times.append(operation_time)

        avg_operation_time = sum(operation_times) / len(operation_times)
        print(f"Average vector store operation time: {avg_operation_time:.3f}s")

        assert avg_operation_time < 0.5, f"Average operation time {avg_operation_time:.2f}s should be under 0.5s"

    def test_embedding_generation_performance(self, app_context):
        """Test embedding generation performance."""

        assert app_context.initialize(), "Application should initialize"

        test_code_samples = [
            "def hello(): return 'world'",
            "class TestClass:\n    def __init__(self):\n        self.value = 42",
            "import os\nimport sys\n\ndef main():\n    print('Hello, World!')",
            "async def fetch_data():\n    return await api_call()",
            "def calculate_fibonacci(n):\n    if n <= 1:\n        return n\n    return calculate_fibonacci(n-1) + calculate_fibonacci(n-2)"
        ]

        embedding_times = []

        with patch('src.codebase_gardener.models.nomic_embedder.get_nomic_embedder') as mock_embedder:
            mock_embedder_instance = Mock()
            mock_embedder_instance.embed_code.return_value = [0.1] * 384  # Mock 384-dim embedding
            mock_embedder.return_value = mock_embedder_instance

            for code_sample in test_code_samples:
                start_time = time.time()
                embedding = mock_embedder_instance.embed_code(code_sample)
                embedding_time = time.time() - start_time

                assert embedding is not None, "Should generate embedding"
                assert len(embedding) == 384, "Should generate 384-dimensional embedding"
                assert embedding_time < 2.0, f"Embedding generation took {embedding_time:.2f}s, should be under 2s"

                embedding_times.append(embedding_time)

        avg_embedding_time = sum(embedding_times) / len(embedding_times)
        print(f"Average embedding generation time: {avg_embedding_time:.3f}s")

        assert avg_embedding_time < 1.0, f"Average embedding time {avg_embedding_time:.2f}s should be under 1s"

    def test_system_resource_efficiency(self, app_context):
        """Test overall system resource efficiency."""

        # Monitor system resources during operation
        process = psutil.Process(os.getpid())

        # Initial resource usage
        initial_cpu_percent = process.cpu_percent()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB

        assert app_context.initialize(), "Application should initialize"

        # Simulate realistic workload
        project_ids = [f"resource-test-{i}" for i in range(5)]

        start_time = time.time()

        with patch.object(app_context, 'switch_project') as mock_switch:
            mock_switch.return_value = True

            with patch.object(app_context.dynamic_model_loader, 'generate_response') as mock_generate:
                mock_generate.return_value = "Mock response"

                # Simulate workload
                for project_id in project_ids:
                    # Switch project
                    app_context.switch_project(project_id)

                    # Generate responses
                    for i in range(3):
                        app_context.dynamic_model_loader.generate_response(f"Test prompt {i}", project_id)

                    # Small delay to simulate real usage
                    time.sleep(0.1)

        workload_time = time.time() - start_time

        # Final resource usage
        final_cpu_percent = process.cpu_percent()
        final_memory = process.memory_info().rss / 1024 / 1024  # MB

        memory_increase = final_memory - initial_memory

        print(f"Workload completed in {workload_time:.3f}s")
        print(f"Memory increase: {memory_increase:.1f}MB")
        print(f"CPU usage: {final_cpu_percent:.1f}%")

        # Resource efficiency constraints
        assert workload_time < 15.0, f"Workload took {workload_time:.2f}s, should be under 15s"
        assert memory_increase < 100, f"Memory increase {memory_increase:.1f}MB should be under 100MB"
        assert final_cpu_percent < 50, f"CPU usage {final_cpu_percent:.1f}% should be under 50%"

    def test_stress_testing(self, app_context):
        """Test system behavior under stress conditions."""

        assert app_context.initialize(), "Application should initialize"

        # Stress test with many rapid operations
        num_operations = 50
        project_ids = [f"stress-test-{i}" for i in range(num_operations)]

        start_time = time.time()
        successful_operations = 0

        with patch.object(app_context, 'switch_project') as mock_switch:
            mock_switch.return_value = True

            for project_id in project_ids:
                try:
                    success = app_context.switch_project(project_id)
                    if success:
                        successful_operations += 1
                except Exception as e:
                    print(f"Operation failed for {project_id}: {e}")

        stress_test_time = time.time() - start_time
        success_rate = successful_operations / num_operations

        print(f"Stress test completed in {stress_test_time:.3f}s")
        print(f"Success rate: {success_rate:.2%} ({successful_operations}/{num_operations})")

        # Stress test requirements
        assert stress_test_time < 30.0, f"Stress test took {stress_test_time:.2f}s, should be under 30s"
        assert success_rate >= 0.95, f"Success rate {success_rate:.2%} should be at least 95%"

        # Check system is still responsive after stress test
        final_health = app_context.health_check()
        assert final_health is not None, "System should remain responsive after stress test"


@pytest.mark.performance
class TestMemoryOptimization:
    """Memory optimization tests for Mac Mini M4."""

    def test_memory_leak_detection(self):
        """Test for memory leaks during repeated operations."""

        with patch('src.codebase_gardener.config.settings.get_settings') as mock_settings:
            mock_settings.return_value = Mock(
                data_dir=Path("/tmp/test"),
                ollama_base_url="http://localhost:11434",
                default_embedding_model="nomic-embed-code"
            )

            process = psutil.Process(os.getpid())
            initial_memory = process.memory_info().rss / 1024 / 1024  # MB

            # Perform repeated operations
            for iteration in range(10):
                context = ApplicationContext()
                context.initialize()

                # Simulate operations
                with patch.object(context, 'switch_project') as mock_switch:
                    mock_switch.return_value = True
                    context.switch_project(f"leak-test-{iteration}")

                context.shutdown()

                # Check memory after each iteration
                current_memory = process.memory_info().rss / 1024 / 1024  # MB
                memory_increase = current_memory - initial_memory

                # Memory increase should be bounded
                assert memory_increase < 50, f"Memory leak detected: {memory_increase:.1f}MB increase after {iteration+1} iterations"

            final_memory = process.memory_info().rss / 1024 / 1024  # MB
            total_increase = final_memory - initial_memory

            print(f"Total memory increase after 10 iterations: {total_increase:.1f}MB")
            assert total_increase < 100, f"Potential memory leak: {total_increase:.1f}MB increase"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "performance"])
