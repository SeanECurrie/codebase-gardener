# AI/ML Architecture Context

## Why LoRA Adapters Instead of Full Fine-Tuning

### Technical Rationale
- **Memory Efficiency**: LoRA adapters are typically 1-10MB vs. full models at 1-10GB
- **Training Speed**: LoRA training takes minutes/hours vs. days/weeks for full fine-tuning
- **Storage Scalability**: Can store dozens of LoRA adapters vs. 2-3 full models on Mac Mini M4
- **Dynamic Loading**: Can switch between adapters in seconds vs. minutes for full models

### Quality Considerations
- **Sufficient Specialization**: LoRA captures project-specific patterns effectively
- **Base Model Preservation**: Retains general coding knowledge while adding project specifics
- **Incremental Learning**: Can retrain adapters as codebases evolve without starting from scratch

### Implementation Strategy
```
Base Model (Ollama) + Project-Specific LoRA Adapter = Specialized Assistant
```

## The Multi-Modal Understanding Stack

### Layer 1: Structural Analysis (Tree-sitter)
- **Purpose**: Understand code syntax and structure
- **Output**: Abstract Syntax Trees (ASTs), function/class boundaries, language-specific patterns
- **Integration**: Provides structured data for embedding generation and LoRA training

### Layer 2: Semantic Understanding (Nomic Embed Code)
- **Purpose**: Capture semantic meaning and relationships between code elements
- **Output**: High-dimensional vectors representing code semantics
- **Integration**: Enables similarity search and contextual retrieval

### Layer 3: Project-Specific Knowledge (LoRA Adapters)
- **Purpose**: Understand project-specific patterns, conventions, and business logic
- **Output**: Specialized model responses that understand the specific codebase
- **Integration**: Applied to base model during inference for project-specific analysis

### Layer 4: Contextual Storage (LanceDB Vector Stores)
- **Purpose**: Efficient storage and retrieval of code embeddings with metadata
- **Output**: Relevant code context for any given query
- **Integration**: Provides context to LoRA-adapted models for informed responses

## Memory Management Architecture

### Dynamic Model Loading Strategy

#### Memory Allocation Pattern
```
Base Model (Always Loaded): ~4GB
Active LoRA Adapter: ~10MB
Vector Store Cache: ~500MB
Conversation Context: ~50MB
Total Active Memory: ~4.5GB (within Mac Mini M4 8GB constraint)
```

#### Loading/Unloading Workflow
1. **Project Switch Request**: User selects new project
2. **Unload Current**: Release current LoRA adapter and conversation context
3. **Load New**: Load target LoRA adapter and conversation history
4. **Verify Compatibility**: Ensure adapter works with current base model
5. **Fallback**: If loading fails, continue with base model only

#### Caching Strategy
- **LRU Cache**: Keep 2-3 most recently used LoRA adapters in memory
- **Predictive Loading**: Pre-load adapters for projects user frequently switches between
- **Memory Pressure Response**: Aggressively unload cached adapters when memory is constrained

## Project Context Management

### Conversation State Architecture
```
Project Context = {
    conversation_history: List[Message],
    analysis_cache: Dict[query_hash, response],
    project_metadata: ProjectInfo,
    vector_store_state: VectorStoreSnapshot
}
```

### Context Switching Mechanics
1. **Serialize Current Context**: Save conversation history and analysis cache to disk
2. **Load Target Context**: Restore conversation history and analysis cache for target project
3. **Update Vector Store**: Switch to project-specific vector store
4. **Maintain Session Continuity**: Preserve UI state and user preferences

### Intelligent Context Pruning
- **Conversation History**: Keep last 50 exchanges, summarize older conversations
- **Analysis Cache**: Retain frequently accessed analyses, expire old ones
- **Vector Store**: Maintain full embeddings, cache frequently accessed vectors

## Integration Patterns

### Ollama Integration
- **Connection Management**: Persistent connection with retry logic and health checks
- **Model Management**: Ensure base models are downloaded and available
- **Inference Pipeline**: Base model + LoRA adapter + retrieved context → specialized response

### PEFT (Parameter Efficient Fine-Tuning) Integration
- **Training Data Preparation**: Convert parsed code into training examples
- **Training Pipeline**: Automated LoRA training when new projects are added
- **Model Validation**: Verify trained adapters work correctly before deployment

### LanceDB Integration
- **Multi-Tenant Architecture**: Separate vector stores per project with shared infrastructure
- **Similarity Search**: Semantic search within project-specific embeddings
- **Metadata Filtering**: Filter by file type, function type, complexity, etc.

### Tree-sitter Integration
- **Language Support**: Python, JavaScript, TypeScript, Java, Go, Rust (extensible)
- **AST Processing**: Extract functions, classes, imports, and structural relationships
- **Code Chunking**: Intelligent splitting based on semantic boundaries

## Quality Assurance for AI Components

### Model Performance Validation
- **Accuracy Testing**: Compare specialized vs. generic model responses
- **Consistency Testing**: Ensure similar queries produce consistent responses
- **Context Relevance**: Verify retrieved context improves response quality

### Training Pipeline Validation
- **Data Quality**: Ensure training data represents codebase accurately
- **Training Convergence**: Monitor loss curves and training metrics
- **Adapter Quality**: Validate that trained adapters improve over base model

### Vector Store Quality
- **Embedding Quality**: Verify embeddings capture semantic relationships
- **Search Relevance**: Test that similarity search returns relevant code
- **Performance Benchmarks**: Ensure search performance meets latency requirements

## Scalability Considerations

### Project Scaling (10+ Projects)
- **Storage**: Linear growth in LoRA adapters and vector stores
- **Memory**: Constant memory usage through dynamic loading
- **Performance**: Logarithmic search performance with proper indexing

### Codebase Size Scaling (Large Projects)
- **Chunking Strategy**: Intelligent code splitting to maintain embedding quality
- **Incremental Processing**: Process only changed files during updates
- **Hierarchical Embeddings**: Multi-level embeddings for different granularities

### Model Scaling (Larger Base Models)
- **Memory Constraints**: May need to use smaller base models or quantization
- **Training Time**: Larger models require longer LoRA training times
- **Quality Trade-offs**: Balance model size with available resources

## Error Handling and Fallback Strategies

### Model Loading Failures
- **Fallback to Base Model**: Continue with generic responses if LoRA fails to load
- **User Notification**: Clear indication when specialized model is unavailable
- **Retry Logic**: Attempt to reload failed adapters with exponential backoff

### Training Failures
- **Partial Training**: Use partially trained adapters if full training fails
- **Data Validation**: Verify training data quality before starting training
- **Resource Monitoring**: Pause training if system resources are constrained

### Vector Store Failures
- **Graceful Degradation**: Continue without context retrieval if vector store fails
- **Backup Strategies**: Maintain backup embeddings for critical projects
- **Rebuild Capabilities**: Ability to regenerate vector stores from source code
