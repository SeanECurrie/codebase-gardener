# Testing Guidelines

## Testing Philosophy

The Codebase Gardener MVP requires comprehensive testing due to its AI/ML components, local processing requirements, and Mac Mini M4 optimization constraints. Our testing approach emphasizes reliability, performance, and maintainability.

## Testing Hierarchy

### 1. Unit Tests (Fast, Isolated)
**Purpose**: Test individual components in isolation
**Speed**: <1 second per test
**Coverage Target**: >90% for non-AI components, >70% for AI components

#### What to Test
- **Data validation**: Input/output data structures
- **Configuration**: Settings loading and validation
- **Utilities**: Helper functions and data transformations
- **Business logic**: Core algorithms and decision logic
- **Error handling**: Exception scenarios and recovery

#### Example Structure
```python
# tests/unit/test_code_preprocessor.py
import pytest
from codebase_gardener.data.preprocessor import CodePreprocessor

class TestCodePreprocessor:
    @pytest.fixture
    def preprocessor(self):
        return CodePreprocessor()

    def test_chunk_python_function(self, preprocessor):
        """Test that Python functions are chunked correctly"""
        code = "def hello():\n    return 'world'"
        chunks = preprocessor.chunk_code(code, language="python")

        assert len(chunks) == 1
        assert chunks[0].content == code
        assert chunks[0].chunk_type == "function"

    def test_invalid_code_handling(self, preprocessor):
        """Test handling of malformed code"""
        invalid_code = "def incomplete_function("

        with pytest.raises(CodeParsingError):
            preprocessor.chunk_code(invalid_code, language="python")
```

### 2. Integration Tests (Medium Speed, Component Interaction)
**Purpose**: Test component interactions and data flow
**Speed**: 1-10 seconds per test
**Coverage Target**: >80% of integration points

#### What to Test
- **Model loading**: LoRA adapter loading/unloading
- **Data pipelines**: End-to-end data processing
- **Vector operations**: Embedding generation and storage
- **API interactions**: Ollama client communication
- **File operations**: Directory setup and management

#### Example Structure
```python
# tests/integration/test_lora_training_pipeline.py
import pytest
from unittest.mock import patch, MagicMock
from codebase_gardener.core.lora_training_pipeline import LoRATrainingPipeline

class TestLoRATrainingPipeline:
    @pytest.fixture
    def sample_codebase(self, tmp_path):
        """Create a sample codebase for testing"""
        code_dir = tmp_path / "sample_project"
        code_dir.mkdir()
        (code_dir / "main.py").write_text("def hello(): return 'world'")
        return code_dir

    @patch('codebase_gardener.models.peft_manager.PEFTManager')
    def test_training_pipeline_success(self, mock_peft, sample_codebase):
        """Test successful LoRA training pipeline"""
        pipeline = LoRATrainingPipeline()

        # Mock successful training
        mock_peft.return_value.train.return_value = True

        result = pipeline.train_project_adapter(
            project_path=sample_codebase,
            project_name="test_project"
        )

        assert result.success is True
        assert result.adapter_path.exists()
        mock_peft.return_value.train.assert_called_once()
```

### 3. End-to-End Tests (Slow, Full System)
**Purpose**: Test complete user workflows
**Speed**: 10-60 seconds per test
**Coverage Target**: >90% of user scenarios

#### What to Test
- **Project workflows**: Complete project addition and analysis
- **Model switching**: Project switching with different adapters
- **UI interactions**: Gradio interface functionality
- **Performance**: System behavior under realistic load
- **Error scenarios**: Recovery from various failure modes

#### Example Structure
```python
# tests/e2e/test_project_workflow.py
import pytest
from codebase_gardener.main import CodebaseGardener

class TestProjectWorkflow:
    @pytest.fixture
    def app(self):
        """Initialize application for testing"""
        return CodebaseGardener(test_mode=True)

    def test_complete_project_addition_workflow(self, app, sample_codebase):
        """Test adding a project and performing analysis"""
        # Add project
        project_id = app.add_project(
            name="test_project",
            path=sample_codebase
        )

        # Wait for training to complete
        app.wait_for_training(project_id, timeout=300)

        # Switch to project
        app.switch_project(project_id)

        # Perform analysis
        response = app.analyze_code("How does the hello function work?")

        assert project_id in app.list_projects()
        assert "hello" in response.lower()
        assert response != "I don't have information about this codebase"
```

## AI/ML Specific Testing Patterns

### Deterministic Testing
```python
def test_embedding_deterministic():
    """Test that embeddings are deterministic"""
    embedder = NomicEmbedder()
    code_sample = "def add(a, b): return a + b"

    # Generate embeddings multiple times
    embedding1 = embedder.embed(code_sample)
    embedding2 = embedder.embed(code_sample)

    # Should be identical
    assert np.allclose(embedding1, embedding2, rtol=1e-10)
```

### Quality Validation Testing
```python
def test_semantic_similarity():
    """Test that semantically similar code has similar embeddings"""
    embedder = NomicEmbedder()

    similar_functions = [
        "def add(a, b): return a + b",
        "def sum_two(x, y): return x + y",
        "def plus(num1, num2): return num1 + num2"
    ]

    embeddings = [embedder.embed(func) for func in similar_functions]

    # All pairs should have high similarity
    for i in range(len(embeddings)):
        for j in range(i + 1, len(embeddings)):
            similarity = cosine_similarity(embeddings[i], embeddings[j])
            assert similarity > 0.7, f"Low similarity between functions {i} and {j}"
```

### Performance Regression Testing
```python
def test_model_loading_performance():
    """Test that model loading stays within acceptable bounds"""
    loader = DynamicModelLoader()

    start_time = time.time()
    loader.load_adapter("test_adapter.bin")
    load_time = time.time() - start_time

    assert load_time < 5.0, f"Model loading took {load_time:.2f}s, expected <5s"

    # Test memory usage
    memory_usage = psutil.Process().memory_info().rss / 1024 / 1024
    assert memory_usage < 4096, f"Memory usage {memory_usage:.1f}MB exceeds 4GB limit"
```

## Mock Strategies

### AI Component Mocking
```python
@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for consistent testing"""
    with patch('ollama.Client') as mock:
        mock.return_value.generate.return_value = {
            'response': 'This is a mocked AI response about the code.',
            'done': True
        }
        yield mock

@pytest.fixture
def mock_embeddings():
    """Mock embedding generation for deterministic tests"""
    def mock_embed(text: str) -> List[float]:
        # Return deterministic embedding based on text hash
        hash_val = hash(text) % 1000
        return [hash_val / 1000.0] * 384

    with patch('codebase_gardener.models.nomic_embedder.embed', side_effect=mock_embed):
        yield
```

### File System Mocking
```python
@pytest.fixture
def mock_file_system(tmp_path):
    """Mock file system operations"""
    # Create temporary directory structure
    project_dir = tmp_path / "test_project"
    project_dir.mkdir()

    # Create sample files
    (project_dir / "main.py").write_text("def main(): pass")
    (project_dir / "utils.py").write_text("def helper(): pass")

    return project_dir
```

## Test Data Management

### Sample Codebases
```python
# tests/fixtures/sample_codebases.py
@pytest.fixture
def python_project(tmp_path):
    """Create a sample Python project"""
    project = tmp_path / "python_project"
    project.mkdir()

    # Main module
    (project / "main.py").write_text("""
def main():
    print("Hello, World!")
    return calculate_sum(1, 2)

def calculate_sum(a, b):
    return a + b

if __name__ == "__main__":
    main()
""")

    # Utility module
    (project / "utils.py").write_text("""
import json

def load_config(path):
    with open(path, 'r') as f:
        return json.load(f)

def save_config(config, path):
    with open(path, 'w') as f:
        json.dump(config, f, indent=2)
""")

    return project

@pytest.fixture
def javascript_project(tmp_path):
    """Create a sample JavaScript project"""
    project = tmp_path / "js_project"
    project.mkdir()

    (project / "index.js").write_text("""
function main() {
    console.log("Hello, World!");
    return calculateSum(1, 2);
}

function calculateSum(a, b) {
    return a + b;
}

module.exports = { main, calculateSum };
""")

    return project
```

### Test Configuration
```python
# tests/conftest.py
import pytest
import tempfile
import shutil
from pathlib import Path

@pytest.fixture(scope="session")
def test_data_dir():
    """Provide test data directory"""
    return Path(__file__).parent / "data"

@pytest.fixture
def temp_workspace(tmp_path):
    """Create temporary workspace for tests"""
    workspace = tmp_path / "workspace"
    workspace.mkdir()

    # Create .codebase-gardener directory
    cg_dir = workspace / ".codebase-gardener"
    cg_dir.mkdir()
    (cg_dir / "base_models").mkdir()
    (cg_dir / "projects").mkdir()
    (cg_dir / "active_project.json").write_text("{}")

    return workspace
```

## Performance Testing

### Benchmarking Framework
```python
# tests/performance/test_benchmarks.py
import pytest
import time
import psutil
from codebase_gardener.models.nomic_embedder import NomicEmbedder

class TestPerformanceBenchmarks:
    def test_embedding_generation_benchmark(self, benchmark):
        """Benchmark embedding generation performance"""
        embedder = NomicEmbedder()
        code_samples = [
            "def hello(): return 'world'",
            "class MyClass: pass",
            "import os; print(os.getcwd())"
        ] * 100  # 300 samples

        def generate_embeddings():
            return [embedder.embed(code) for code in code_samples]

        result = benchmark(generate_embeddings)

        # Assertions about performance
        assert benchmark.stats.mean < 10.0  # Should complete in <10 seconds

    def test_memory_usage_benchmark(self):
        """Test memory usage during typical operations"""
        process = psutil.Process()
        initial_memory = process.memory_info().rss

        # Perform memory-intensive operations
        loader = DynamicModelLoader()
        loader.load_adapter("test_adapter.bin")

        peak_memory = process.memory_info().rss
        memory_increase = (peak_memory - initial_memory) / 1024 / 1024

        assert memory_increase < 500, f"Memory increase {memory_increase:.1f}MB too high"
```

### Load Testing
```python
def test_concurrent_project_switching():
    """Test system behavior under concurrent load"""
    import threading
    import queue

    app = CodebaseGardener()
    results = queue.Queue()

    def switch_projects():
        try:
            for _ in range(10):
                app.switch_project("project_1")
                time.sleep(0.1)
                app.switch_project("project_2")
                time.sleep(0.1)
            results.put("success")
        except Exception as e:
            results.put(f"error: {e}")

    # Start multiple threads
    threads = [threading.Thread(target=switch_projects) for _ in range(3)]
    for thread in threads:
        thread.start()

    for thread in threads:
        thread.join()

    # Check results
    while not results.empty():
        result = results.get()
        assert result == "success", f"Concurrent test failed: {result}"
```

## Test Organization

### Directory Structure
```
tests/
├── unit/                   # Fast, isolated tests
│   ├── test_config/
│   ├── test_core/
│   ├── test_models/
│   ├── test_data/
│   └── test_utils/
├── integration/            # Component interaction tests
│   ├── test_pipelines/
│   ├── test_model_loading/
│   └── test_data_flow/
├── e2e/                   # End-to-end workflow tests
│   ├── test_project_workflows/
│   ├── test_ui_interactions/
│   └── test_error_scenarios/
├── performance/           # Performance and benchmark tests
│   ├── test_benchmarks/
│   ├── test_memory_usage/
│   └── test_load_testing/
├── fixtures/              # Shared test fixtures
│   ├── sample_codebases.py
│   ├── mock_responses.py
│   └── test_data.py
├── data/                  # Static test data
│   ├── sample_codebases/
│   ├── expected_outputs/
│   └── test_configs/
└── conftest.py           # Global test configuration
```

## Continuous Integration

### Test Execution Strategy
```yaml
# .github/workflows/test.yml
name: Test Suite

on: [push, pull_request]

jobs:
  test:
    runs-on: macos-latest

    steps:
    - uses: actions/checkout@v3

    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'

    - name: Install dependencies
      run: |
        pip install -e ".[dev]"

    - name: Run unit tests
      run: pytest tests/unit/ -v --cov=src/

    - name: Run integration tests
      run: pytest tests/integration/ -v

    - name: Run performance tests
      run: pytest tests/performance/ --benchmark-only
```

### Quality Gates
- **Unit Test Coverage**: >90% for non-AI components
- **Integration Test Coverage**: >80% of integration points
- **Performance Benchmarks**: Must not regress by >10%
- **Memory Usage**: Must stay within Mac Mini M4 constraints
- **Code Quality**: Black formatting, mypy type checking

## Testing Best Practices

### Test Writing Guidelines
1. **Descriptive Names**: Test names should describe what is being tested
2. **Single Responsibility**: Each test should test one specific behavior
3. **Arrange-Act-Assert**: Clear structure for test logic
4. **Independent Tests**: Tests should not depend on each other
5. **Deterministic**: Tests should produce consistent results

### AI/ML Testing Considerations
1. **Mock External Dependencies**: Don't rely on actual AI models in unit tests
2. **Test Edge Cases**: Handle malformed code, empty inputs, large files
3. **Performance Monitoring**: Track resource usage and timing
4. **Quality Validation**: Verify AI outputs meet quality standards
5. **Fallback Testing**: Ensure graceful degradation when AI components fail

### Mac Mini M4 Specific Testing
1. **Memory Constraints**: Test within 8GB RAM limits
2. **Thermal Management**: Monitor temperature during intensive tests
3. **Apple Silicon**: Test native ARM64 performance
4. **Resource Monitoring**: Track CPU, memory, and disk usage
5. **Concurrent Operations**: Test multiple operations simultaneously
