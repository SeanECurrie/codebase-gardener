# Development Best Practices

## Effective MCP Server Tool Usage

### When to Use MCP Tools During Development

#### Research and Documentation Phase
- **Use MCP tools FIRST** before implementing any new component
- **Search for existing patterns** in similar projects or libraries
- **Validate architectural decisions** against current best practices
- **Find optimization techniques** specific to the technology stack

#### Implementation Guidance
```python
# Before implementing Tree-sitter integration:
# 1. Use MCP search tools to find Tree-sitter Python examples
# 2. Research language-specific parsing patterns
# 3. Look for performance optimization techniques
# 4. Find error handling patterns for malformed code
```

#### Problem-Solving Workflow
1. **Encounter Issue**: Document the specific problem in memory file
2. **MCP Research**: Search for solutions, similar issues, and best practices
3. **Synthesize Solutions**: Combine research findings with project constraints
4. **Implement**: Apply solution with project-specific adaptations
5. **Document**: Update memory file with solution and lessons learned

### MCP Tool Selection Strategy

#### For AI/ML Components
- **Use documentation MCPs** for HuggingFace, Ollama, LanceDB specifics
- **Use code search MCPs** for implementation patterns and examples
- **Use performance MCPs** for optimization techniques and benchmarking

#### For System Integration
- **Use file system MCPs** for directory structure and permission patterns
- **Use configuration MCPs** for environment variable and settings management
- **Use testing MCPs** for test framework selection and patterns

## Memory File Patterns and Best Practices

### Memory File Structure
```markdown
# Task [N]: [Component Name] - [Date]

## Approach Decision
- Why this approach was chosen
- Alternatives considered and rejected
- Key architectural decisions

## Implementation Notes
- Specific challenges encountered
- Solutions implemented
- Code patterns established

## Integration Points
- How this component connects to others
- Dependencies and interfaces
- Data flow considerations

## Testing Strategy
- Test cases implemented
- Edge cases discovered
- Performance benchmarks

## Lessons Learned
- What worked well
- What would be done differently
- Patterns to reuse in future tasks

## Next Task Considerations
- What the next task should know
- Potential integration challenges
- Recommended approaches
```

### Memory File Naming Convention
- `[component]_task[N].md` - e.g., `treesitter_parser_task5.md`
- Include task number for easy cross-referencing
- Use descriptive component names that match code modules

### Cross-Task Memory References
```markdown
## References to Previous Tasks
- Task 2 (config_logging): Use established logging patterns
- Task 4 (error_handling): Apply retry decorators for API calls
- Task 7 (nomic_embeddings): Integrate with embedding cache patterns
```

## Documentation vs. Implementation Decision Framework

### When to Search for Documentation
- **New technology integration** (Tree-sitter, LanceDB, PEFT)
- **Performance optimization** techniques
- **Error handling patterns** for specific libraries
- **Best practices** for AI/ML workflows
- **Security considerations** for file operations

### When to Implement from Scratch
- **Project-specific business logic** (project registry, context management)
- **Integration glue code** between different components
- **Custom optimization** for Mac Mini M4 constraints
- **Domain-specific patterns** unique to codebase analysis

### Research-First Implementation Pattern
```python
# 1. Research Phase (use MCP tools)
# - Find 3-5 examples of similar implementations
# - Identify common patterns and anti-patterns
# - Understand performance implications

# 2. Design Phase (document in memory file)
# - Synthesize research into project-specific design
# - Consider integration with existing components
# - Plan error handling and testing approach

# 3. Implementation Phase
# - Start with simplest working version
# - Add complexity incrementally
# - Test each addition thoroughly

# 4. Review Phase (update memory file)
# - Document what worked and what didn't
# - Note patterns for future tasks
# - Identify optimization opportunities
```

## Code Quality Standards for AI/ML Projects

### Code Organization Principles
- **Separate concerns**: Data processing, model management, inference, UI
- **Dependency injection**: Make AI components easily testable and swappable
- **Configuration-driven**: Externalize model parameters and system settings
- **Error boundaries**: Isolate AI failures from system failures

### AI/ML Specific Code Standards

#### Model Management
```python
# Good: Clear separation of concerns
class LoRAAdapter:
    def __init__(self, adapter_path: Path, base_model: str):
        self.adapter_path = adapter_path
        self.base_model = base_model
        self._loaded = False
    
    def load(self) -> None:
        """Load adapter with proper error handling"""
        try:
            # Implementation with retry logic
            pass
        except AdapterLoadError as e:
            logger.error(f"Failed to load adapter: {e}")
            raise
    
    def unload(self) -> None:
        """Clean unload with memory cleanup"""
        # Implementation
        pass
```

#### Data Pipeline Standards
```python
# Good: Explicit data validation and transformation
@dataclass
class CodeChunk:
    content: str
    language: str
    file_path: Path
    start_line: int
    end_line: int
    
    def __post_init__(self):
        self.validate()
    
    def validate(self) -> None:
        """Validate chunk data integrity"""
        if not self.content.strip():
            raise ValueError("Code chunk cannot be empty")
        # Additional validation
```

#### Configuration Management
```python
# Good: Type-safe configuration with validation
class ModelConfig(BaseSettings):
    ollama_base_url: str = "http://localhost:11434"
    max_context_length: int = 4096
    embedding_batch_size: int = 32
    
    @validator('embedding_batch_size')
    def validate_batch_size(cls, v):
        if v < 1 or v > 128:
            raise ValueError('Batch size must be between 1 and 128')
        return v
```

## Testing Approaches for Machine Learning Components

### Testing Strategy Hierarchy

#### Unit Tests (Fast, Isolated)
- **Data validation**: Test input/output data structures
- **Configuration**: Test settings loading and validation
- **Utilities**: Test helper functions and data transformations
- **Mocked AI components**: Test logic without actual model inference

#### Integration Tests (Medium Speed, Component Interaction)
- **Model loading**: Test LoRA adapter loading/unloading
- **Data pipelines**: Test end-to-end data processing
- **Vector operations**: Test embedding generation and storage
- **Error handling**: Test failure scenarios and recovery

#### End-to-End Tests (Slow, Full System)
- **Project workflows**: Test complete project addition and analysis
- **Model switching**: Test project switching with different adapters
- **Performance**: Test system behavior under load
- **User scenarios**: Test realistic usage patterns

### AI/ML Testing Patterns

#### Deterministic Testing
```python
def test_code_chunking_deterministic():
    """Test that chunking produces consistent results"""
    code_sample = "def hello():\n    return 'world'"
    
    # Run chunking multiple times
    chunks1 = chunk_code(code_sample)
    chunks2 = chunk_code(code_sample)
    
    assert chunks1 == chunks2  # Should be deterministic
```

#### Quality Validation Testing
```python
def test_embedding_quality():
    """Test that embeddings capture semantic similarity"""
    similar_functions = [
        "def add(a, b): return a + b",
        "def sum_two(x, y): return x + y"
    ]
    
    embeddings = [embed_code(func) for func in similar_functions]
    similarity = cosine_similarity(embeddings[0], embeddings[1])
    
    assert similarity > 0.8  # Should be semantically similar
```

#### Performance Regression Testing
```python
def test_model_loading_performance():
    """Test that model loading stays within acceptable bounds"""
    start_time = time.time()
    
    adapter = LoRAAdapter("test_adapter.bin", "base_model")
    adapter.load()
    
    load_time = time.time() - start_time
    assert load_time < 5.0  # Should load within 5 seconds
```

### Mock Strategies for AI Components

#### Model Inference Mocking
```python
@pytest.fixture
def mock_ollama_client():
    """Mock Ollama client for testing"""
    with patch('ollama.Client') as mock:
        mock.return_value.generate.return_value = {
            'response': 'Mocked AI response'
        }
        yield mock
```

#### Embedding Mocking
```python
@pytest.fixture
def mock_embeddings():
    """Mock embedding generation for consistent testing"""
    def mock_embed(text: str) -> List[float]:
        # Return deterministic embedding based on text hash
        return [hash(text) % 100 / 100.0] * 384
    
    with patch('nomic_embed.embed', side_effect=mock_embed):
        yield
```

## Development Workflow Best Practices

### Task Execution Pattern
1. **Pre-Task Research**: Use MCP tools to understand the problem space
2. **Memory File Creation**: Document approach and architectural decisions
3. **Incremental Implementation**: Build in small, testable increments
4. **Continuous Testing**: Test each increment before moving forward
5. **Integration Validation**: Ensure new component works with existing system
6. **Memory File Update**: Document lessons learned and patterns established

### Git Workflow Integration
- **Feature branches**: One branch per task for clean history
- **Conventional commits**: Use consistent commit message format
- **Memory file commits**: Commit memory files with implementation
- **Steering file updates**: Update steering files when patterns change

### Code Review Checklist
- [ ] **Follows established patterns** from previous tasks
- [ ] **Integrates properly** with existing components
- [ ] **Handles errors gracefully** with appropriate logging
- [ ] **Includes comprehensive tests** for the component
- [ ] **Updates memory files** with lessons learned
- [ ] **Maintains performance** within Mac Mini M4 constraints
- [ ] **Preserves local-first** processing principles