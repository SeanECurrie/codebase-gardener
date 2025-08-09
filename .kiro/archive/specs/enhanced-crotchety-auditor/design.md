# Enhanced Crotchety Code Auditor - Design Document

## Overview

This design transforms the existing Crotchety Code Auditor by fixing critical issues and enhancing it with direct gpt-oss:20b integration, streaming responses, and LoRA-based codebase learning. The approach emphasizes using and enhancing existing components rather than rebuilding from scratch.

## Architecture

### High-Level Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Gradio UI     │    │  Enhanced        │    │  DirectGPTOSS   │
│   (Enhanced)    │◄──►│  CrotchetyAuditor│◄──►│  Client         │
│                 │    │                  │    │  (New)          │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  FileUtilities  │    │  CodePreprocessor│    │  NomicEmbedder  │
│  (Enhanced)     │◄──►│  (Enhanced)      │◄──►│  (Existing)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
                                │
                                ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│  LoRATrainer    │    │  MemoryManager   │    │  OllamaClient   │
│  (New)          │◄──►│  (New)           │    │  (Fallback)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘
```

### Component Relationships

1. **Enhanced CrotchetyAuditor**: Main orchestrator that coordinates all components
2. **DirectGPTOSSClient**: New direct HuggingFace integration with streaming
3. **Enhanced FileUtilities**: Fixed method names, added timeout protection
4. **Enhanced CodePreprocessor**: Larger context handling, better chunking
5. **LoRATrainer**: New component for codebase-specific training
6. **MemoryManager**: New component for persistent conversation history
7. **Existing Components**: NomicEmbedder, OllamaClient (fallback), Gradio UI (enhanced)

## Components and Interfaces

### 1. Enhanced CrotchetyAuditor (Main Orchestrator)

**Purpose**: Coordinates all components and manages the analysis workflow

**Enhancements to Existing**:
```python
class CrotchetyCodeAuditor:
    def __init__(self):
        # Use existing components
        self.file_utils = FileUtilities()  # Enhanced version
        self.preprocessor = CodePreprocessor()  # Enhanced version
        self.embedder = NomicEmbedder()  # Existing

        # New components
        self.direct_client = DirectGPTOSSClient()  # New
        self.lora_trainer = LoRATrainer()  # New
        self.memory_manager = MemoryManager()  # New

        # Fallback
        self.ollama_client = OllamaClient()  # Existing fallback

    def analyze_codebase(self, path: str) -> AnalysisResult:
        """Enhanced analysis with timeout protection and progress feedback"""
        # Fix: Use correct method name and add timeout
        with timeout(30):  # Prevent 300-second hangs
            files = self.file_utils.find_source_files(path)  # Fixed method name

        # Use existing preprocessing with enhancements
        chunks = self.preprocessor.process_files(files)

        # Generate embeddings using existing component
        embeddings = self.embedder.embed_chunks(chunks)

        # Store in memory for future reference
        self.memory_manager.store_codebase_knowledge(path, chunks, embeddings)

        return AnalysisResult(files=files, chunks=chunks, embeddings=embeddings)
```

**Key Fixes**:
- Fix `discover_source_files` → `find_source_files` method name
- Add timeout protection to prevent hangs
- Add progress feedback during analysis
- Integrate with new components while maintaining existing functionality

### 2. DirectGPTOSSClient (New Component)

**Purpose**: Direct HuggingFace Transformers integration with streaming support

**Interface Design** (follows existing OllamaClient patterns):
```python
class DirectGPTOSSClient:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.model = None
        self.tokenizer = None
        self._model_loaded = False

    @property
    def model(self):
        """Lazy loading like existing OllamaClient"""
        if not self._model_loaded:
            self._load_model()
        return self._model

    def _load_model(self):
        """Load with 8-bit quantization for Mac Mini M4"""
        try:
            self.model = AutoModelForCausalLM.from_pretrained(
                "EleutherAI/gpt-oss-20B",
                load_in_8bit=True,  # Memory efficiency
                device_map="auto",  # Optimal placement
                torch_dtype=torch.float16
            )
            self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-oss-20B")
            self._model_loaded = True
        except Exception as e:
            logger.error(f"Failed to load direct model: {e}")
            raise ModelLoadingError(f"Could not load gpt-oss:20b directly: {e}")

    def generate_stream(self, prompt: str, **kwargs) -> Iterator[str]:
        """Streaming generation - new capability"""
        inputs = self.tokenizer(prompt, return_tensors="pt")

        # Use existing parameter patterns
        generation_kwargs = {
            'max_new_tokens': kwargs.get('max_new_tokens', 512),
            'temperature': kwargs.get('temperature', 0.7),
            'top_p': kwargs.get('top_p', 0.9),
            'repetition_penalty': kwargs.get('repetition_penalty', 1.1),
            'do_sample': True,
            'pad_token_id': self.tokenizer.eos_token_id
        }

        # Stream tokens as they generate
        with torch.no_grad():
            for output in self.model.generate(**inputs, **generation_kwargs):
                yield self.tokenizer.decode(output, skip_special_tokens=True)

    def generate(self, prompt: str, **kwargs) -> str:
        """Non-streaming generation - maintains existing interface"""
        # Collect all streaming tokens for compatibility
        return ''.join(self.generate_stream(prompt, **kwargs))

    def health_check(self) -> bool:
        """Health check like existing OllamaClient"""
        try:
            return self._model_loaded and self.model is not None
        except Exception:
            return False
```

**Key Design Decisions**:
- Follows same interface patterns as existing `OllamaClient`
- Lazy loading for performance
- 8-bit quantization for Mac Mini M4 memory efficiency
- Streaming and non-streaming interfaces
- Comprehensive error handling with fallback support

### 3. Enhanced FileUtilities

**Purpose**: Fix critical issues and add timeout protection

**Enhancements to Existing**:
```python
class FileUtilities:
    # Existing methods remain unchanged

    def find_source_files(self, path: Path, timeout: int = 30) -> List[Path]:
        """Enhanced with timeout protection to prevent hangs"""

        @timeout_decorator(timeout)
        def _find_files():
            # Use existing logic but with timeout protection
            return self._discover_source_files_impl(path)

        try:
            return _find_files()
        except TimeoutError:
            logger.error(f"File discovery timed out after {timeout} seconds")
            raise FileDiscoveryError(f"File discovery timed out for {path}")
        except Exception as e:
            logger.error(f"File discovery failed: {e}")
            raise FileDiscoveryError(f"Could not discover files in {path}: {e}")

    # Remove or fix any references to discover_source_files
    # Ensure all code uses find_source_files consistently
```

**Key Fixes**:
- Add timeout protection to prevent 300-second hangs
- Ensure consistent method naming
- Enhanced error handling with specific exceptions
- Progress feedback during long operations

### 4. Enhanced CodePreprocessor

**Purpose**: Handle larger contexts and improve chunking for 8k token window

**Enhancements to Existing**:
```python
class CodePreprocessor:
    def __init__(self, settings: Settings):
        # Use existing initialization
        self.settings = settings
        # Enhance for larger contexts
        self.max_chunk_size = 6000  # Larger chunks for 8k context
        self.context_overlap = 200   # Overlap for continuity

    def process_files_for_context(self, files: List[Path]) -> List[CodeChunk]:
        """Enhanced processing for full context window utilization"""
        chunks = []

        for file_path in files:
            # Use existing file processing logic
            file_chunks = self.process_file(file_path)

            # Enhance: Combine related chunks for larger context
            combined_chunks = self._combine_for_context(file_chunks)
            chunks.extend(combined_chunks)

        return chunks

    def _combine_for_context(self, chunks: List[CodeChunk]) -> List[CodeChunk]:
        """New: Combine chunks to utilize full 8k context window"""
        combined = []
        current_chunk = None
        current_size = 0

        for chunk in chunks:
            chunk_size = len(chunk.content)

            if current_size + chunk_size < self.max_chunk_size:
                # Combine chunks
                if current_chunk is None:
                    current_chunk = chunk
                    current_size = chunk_size
                else:
                    current_chunk = self._merge_chunks(current_chunk, chunk)
                    current_size += chunk_size
            else:
                # Save current and start new
                if current_chunk:
                    combined.append(current_chunk)
                current_chunk = chunk
                current_size = chunk_size

        if current_chunk:
            combined.append(current_chunk)

        return combined
```

**Key Enhancements**:
- Larger chunk sizes to utilize 8k context window
- Intelligent chunk combination for better analysis
- Maintains existing processing logic
- Enhanced for cross-file relationship understanding

### 5. LoRATrainer (New Component)

**Purpose**: Train codebase-specific adapters using existing components

**Design**:
```python
class LoRATrainer:
    def __init__(self, direct_client: DirectGPTOSSClient, file_utils: FileUtilities,
                 preprocessor: CodePreprocessor):
        # Use existing components
        self.direct_client = direct_client
        self.file_utils = file_utils
        self.preprocessor = preprocessor

        # LoRA configuration
        self.lora_config = LoraConfig(
            r=64,  # Rank
            lora_alpha=16,
            target_modules=["q_proj", "v_proj", "k_proj", "o_proj"],
            lora_dropout=0.05,
            bias="none",
            task_type="CAUSAL_LM"
        )

    def train_on_codebase(self, codebase_path: Path,
                         progress_callback=None) -> LoRAAdapter:
        """Train LoRA adapter on specific codebase"""

        # Use existing components for data preparation
        if progress_callback:
            progress_callback(0.1, "Finding source files...")
        files = self.file_utils.find_source_files(codebase_path)

        if progress_callback:
            progress_callback(0.3, "Processing code files...")
        chunks = self.preprocessor.process_files(files)

        if progress_callback:
            progress_callback(0.5, "Preparing training data...")
        training_data = self._prepare_training_data(chunks)

        if progress_callback:
            progress_callback(0.7, "Training LoRA adapter...")
        adapter = self._train_adapter(training_data)

        if progress_callback:
            progress_callback(1.0, "Training complete!")

        return adapter

    def _prepare_training_data(self, chunks: List[CodeChunk]) -> Dataset:
        """Convert code chunks to instruction-following format"""
        examples = []

        for chunk in chunks:
            # Create instruction-following examples
            instruction = f"Analyze this {chunk.language} code and provide feedback:"
            input_text = chunk.content

            # Use crotchety engineer persona
            output = self._generate_example_response(chunk)

            examples.append({
                'instruction': instruction,
                'input': input_text,
                'output': output
            })

        return Dataset.from_list(examples)

    def _train_adapter(self, dataset: Dataset) -> LoRAAdapter:
        """Train the LoRA adapter"""
        # Get base model from direct client
        base_model = self.direct_client.model

        # Apply LoRA configuration
        model = get_peft_model(base_model, self.lora_config)

        # Training configuration
        training_args = TrainingArguments(
            output_dir=f"./lora_adapters/{hash(str(dataset))}",
            per_device_train_batch_size=1,  # Small batch for Mac Mini M4
            gradient_accumulation_steps=4,
            warmup_steps=100,
            max_steps=1000,  # Reasonable for codebase adaptation
            fp16=True,  # Memory efficiency
            logging_steps=50,
            save_steps=500,
        )

        # Train
        trainer = Trainer(
            model=model,
            args=training_args,
            train_dataset=dataset,
            tokenizer=self.direct_client.tokenizer,
        )

        trainer.train()

        # Save adapter
        adapter_path = training_args.output_dir
        model.save_pretrained(adapter_path)

        return LoRAAdapter(adapter_path, base_model)
```

**Key Design Decisions**:
- Uses existing components for data preparation
- Follows established patterns from other components
- Memory-efficient training for Mac Mini M4
- Progress feedback during training
- Persistent adapter storage

### 6. MemoryManager (New Component)

**Purpose**: Persistent conversation history and codebase knowledge

**Design**:
```python
class MemoryManager:
    def __init__(self, settings: Settings):
        self.settings = settings
        self.db_path = settings.data_dir / "memory.db"
        self._init_database()

    def _init_database(self):
        """Initialize SQLite database with schema"""
        with sqlite3.connect(self.db_path) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS conversations (
                    id INTEGER PRIMARY KEY,
                    codebase_path TEXT,
                    timestamp DATETIME,
                    user_message TEXT,
                    assistant_response TEXT,
                    context TEXT
                );

                CREATE TABLE IF NOT EXISTS codebase_knowledge (
                    id INTEGER PRIMARY KEY,
                    codebase_path TEXT,
                    knowledge_type TEXT,
                    content TEXT,
                    timestamp DATETIME
                );

                CREATE INDEX IF NOT EXISTS idx_codebase_path
                ON conversations(codebase_path);
            """)

    def store_conversation(self, codebase_path: str, user_message: str,
                          assistant_response: str, context: str = None):
        """Store conversation for future reference"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT INTO conversations
                (codebase_path, timestamp, user_message, assistant_response, context)
                VALUES (?, ?, ?, ?, ?)
            """, (codebase_path, datetime.now(), user_message, assistant_response, context))

    def get_conversation_history(self, codebase_path: str, limit: int = 10) -> List[Dict]:
        """Retrieve recent conversation history"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT user_message, assistant_response, timestamp
                FROM conversations
                WHERE codebase_path = ?
                ORDER BY timestamp DESC
                LIMIT ?
            """, (codebase_path, limit))

            return [{'user': row[0], 'assistant': row[1], 'timestamp': row[2]}
                   for row in cursor.fetchall()]

    def store_codebase_knowledge(self, codebase_path: str, knowledge_type: str,
                                content: str):
        """Store codebase-specific knowledge"""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO codebase_knowledge
                (codebase_path, knowledge_type, content, timestamp)
                VALUES (?, ?, ?, ?)
            """, (codebase_path, knowledge_type, content, datetime.now()))
```

**Key Design Decisions**:
- Simple SQLite database for local storage
- Conversation history per codebase
- Knowledge storage for patterns and insights
- Follows existing database patterns from other components

### 7. Enhanced Gradio Interface

**Purpose**: Add streaming support and parameter controls

**Enhancements to Existing**:
```python
def create_enhanced_interface():
    """Enhanced Gradio interface with streaming and controls"""

    with gr.Blocks(title="Enhanced Crotchety Code Auditor") as app:
        # State management
        auditor_state = gr.State(CrotchetyCodeAuditor())
        current_codebase = gr.State(None)

        # Main interface
        with gr.Row():
            with gr.Column(scale=2):
                # Codebase selection
                codebase_path = gr.Textbox(
                    label="Codebase Path",
                    placeholder="/path/to/your/codebase"
                )
                analyze_btn = gr.Button("Analyze Codebase")

                # Analysis status
                status_display = gr.Textbox(
                    label="Status",
                    interactive=False
                )

                # Parameter controls (new)
                with gr.Accordion("Model Parameters", open=False):
                    temperature = gr.Slider(0.0, 1.0, 0.7, label="Temperature")
                    top_p = gr.Slider(0.0, 1.0, 0.9, label="Top P")
                    repetition_penalty = gr.Slider(1.0, 2.0, 1.1, label="Repetition Penalty")

            with gr.Column(scale=3):
                # Enhanced chat interface with streaming
                chatbot = gr.Chatbot(
                    type="messages",  # Modern format
                    label="Crotchety Engineer"
                )

                msg_input = gr.Textbox(
                    label="Ask the crotchety engineer...",
                    placeholder="Paste code or ask about your codebase"
                )

                send_btn = gr.Button("Send")

        # Event handlers
        def analyze_codebase(path, auditor, progress=gr.Progress()):
            """Enhanced analysis with progress feedback"""
            try:
                progress(0.1, desc="Starting analysis...")
                result = auditor.analyze_codebase(path)

                progress(0.5, desc="Training LoRA adapter...")
                adapter = auditor.lora_trainer.train_on_codebase(path)

                progress(1.0, desc="Analysis complete!")
                return f"✅ Analyzed {len(result.files)} files", path

            except Exception as e:
                return f"❌ Analysis failed: {e}", None

        def chat_with_streaming(message, history, codebase, auditor, temp, top_p, rep_penalty):
            """Enhanced chat with streaming responses"""
            if not codebase:
                history.append({"role": "user", "content": message})
                history.append({"role": "assistant", "content": "Please analyze a codebase first."})
                return history, ""

            # Add user message
            history.append({"role": "user", "content": message})

            # Generate streaming response
            prompt = auditor._build_crotchety_prompt(message, codebase)

            assistant_message = ""
            history.append({"role": "assistant", "content": ""})

            # Stream tokens
            for token in auditor.direct_client.generate_stream(
                prompt,
                temperature=temp,
                top_p=top_p,
                repetition_penalty=rep_penalty
            ):
                assistant_message += token
                history[-1]["content"] = assistant_message
                yield history, ""

            # Store conversation
            auditor.memory_manager.store_conversation(codebase, message, assistant_message)

            return history, ""

        # Wire up events
        analyze_btn.click(
            analyze_codebase,
            inputs=[codebase_path, auditor_state],
            outputs=[status_display, current_codebase]
        )

        send_btn.click(
            chat_with_streaming,
            inputs=[msg_input, chatbot, current_codebase, auditor_state,
                   temperature, top_p, repetition_penalty],
            outputs=[chatbot, msg_input]
        )

    return app
```

**Key Enhancements**:
- Streaming chat interface
- Parameter controls for model behavior
- Progress feedback during analysis
- Integration with all new components
- Maintains existing UI patterns

## Data Models

### Core Data Structures

```python
@dataclass
class AnalysisResult:
    files: List[Path]
    chunks: List[CodeChunk]
    embeddings: List[np.ndarray]
    lora_adapter: Optional[LoRAAdapter] = None
    timestamp: datetime = field(default_factory=datetime.now)

@dataclass
class LoRAAdapter:
    adapter_path: Path
    base_model: str
    training_data_hash: str
    created_at: datetime = field(default_factory=datetime.now)

@dataclass
class ConversationEntry:
    user_message: str
    assistant_response: str
    context: str
    timestamp: datetime = field(default_factory=datetime.now)
```

### Database Schema

```sql
-- Conversations table
CREATE TABLE conversations (
    id INTEGER PRIMARY KEY,
    codebase_path TEXT NOT NULL,
    timestamp DATETIME NOT NULL,
    user_message TEXT NOT NULL,
    assistant_response TEXT NOT NULL,
    context TEXT
);

-- Codebase knowledge table
CREATE TABLE codebase_knowledge (
    id INTEGER PRIMARY KEY,
    codebase_path TEXT NOT NULL,
    knowledge_type TEXT NOT NULL,  -- 'patterns', 'issues', 'suggestions'
    content TEXT NOT NULL,
    timestamp DATETIME NOT NULL
);

-- Indexes for performance
CREATE INDEX idx_conversations_codebase ON conversations(codebase_path);
CREATE INDEX idx_knowledge_codebase ON codebase_knowledge(codebase_path);
```

## Error Handling

### Error Hierarchy

```python
class CrotchetyAuditorError(Exception):
    """Base exception for all auditor errors"""
    pass

class ModelLoadingError(CrotchetyAuditorError):
    """Raised when direct model loading fails"""
    pass

class FileDiscoveryError(CrotchetyAuditorError):
    """Raised when file discovery fails or times out"""
    pass

class LoRATrainingError(CrotchetyAuditorError):
    """Raised when LoRA training fails"""
    pass

class MemoryError(CrotchetyAuditorError):
    """Raised when memory operations fail"""
    pass
```

### Fallback Strategy

```python
class FallbackManager:
    def __init__(self, direct_client: DirectGPTOSSClient, ollama_client: OllamaClient):
        self.direct_client = direct_client
        self.ollama_client = ollama_client

    def generate_with_fallback(self, prompt: str, **kwargs) -> str:
        """Try direct client first, fallback to Ollama"""
        try:
            return self.direct_client.generate(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Direct client failed: {e}, falling back to Ollama")
            return self.ollama_client.generate(prompt, **kwargs)

    def generate_stream_with_fallback(self, prompt: str, **kwargs) -> Iterator[str]:
        """Try streaming first, fallback to non-streaming"""
        try:
            yield from self.direct_client.generate_stream(prompt, **kwargs)
        except Exception as e:
            logger.warning(f"Streaming failed: {e}, falling back to non-streaming")
            response = self.ollama_client.generate(prompt, **kwargs)
            yield response
```

## Testing Strategy

### Unit Testing Approach

1. **Component Testing**: Test each enhanced component individually
2. **Integration Testing**: Test component interactions
3. **Fallback Testing**: Verify fallback mechanisms work
4. **Performance Testing**: Ensure Mac Mini M4 compatibility

### Test Structure

```python
class TestDirectGPTOSSClient:
    def test_model_loading_with_quantization(self):
        """Test 8-bit model loading"""
        pass

    def test_streaming_generation(self):
        """Test streaming token generation"""
        pass

    def test_fallback_on_failure(self):
        """Test fallback to Ollama on failure"""
        pass

class TestEnhancedFileUtilities:
    def test_timeout_protection(self):
        """Test timeout prevents hangs"""
        pass

    def test_method_name_consistency(self):
        """Test find_source_files works correctly"""
        pass

class TestLoRATrainer:
    def test_training_data_preparation(self):
        """Test training data creation from code chunks"""
        pass

    def test_adapter_training(self):
        """Test LoRA adapter training"""
        pass
```

## Deployment Considerations

### Mac Mini M4 Optimization

1. **Memory Management**: 8-bit quantization, lazy loading
2. **Resource Monitoring**: Track memory and CPU usage
3. **Thermal Management**: Batch processing to avoid sustained high load
4. **Storage**: Efficient adapter and memory storage

### Configuration

```python
class EnhancedSettings(Settings):
    # Direct model settings
    use_direct_model: bool = True
    model_quantization: str = "8bit"
    device_map: str = "auto"

    # LoRA settings
    lora_rank: int = 64
    lora_alpha: int = 16
    lora_dropout: float = 0.05

    # Memory settings
    max_conversation_history: int = 100
    memory_db_path: Path = Path("~/.codebase-gardener/memory.db")

    # Timeout settings
    file_discovery_timeout: int = 30
    analysis_timeout: int = 300
```

This design provides a comprehensive enhancement to the existing Crotchety Code Auditor while maximizing reuse of existing components and following established patterns. The implementation focuses on fixing critical issues first, then adding enhanced capabilities through direct model integration, LoRA training, and persistent memory.
