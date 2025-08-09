# Enhanced Crotchety Code Auditor - Requirements Document

## Introduction

Transform the existing Crotchety Code Auditor into a working, intelligent code reviewer that uses direct gpt-oss:20b integration. The goal is to fix what's broken, enhance what works, and leverage all the existing components we've already built.

## Current State

### What We Have (Working)
- ✅ **OllamaClient**: Robust client with retry logic and error handling
- ✅ **NomicEmbedder**: Code embedding generation with caching
- ✅ **FileUtilities**: File discovery and processing
- ✅ **CodePreprocessor**: Code parsing and chunking
- ✅ **Gradio Interface**: Web UI framework
- ✅ **gpt-oss:20b**: Model installed and working via Ollama

### What's Broken
- ❌ **300-second hang**: System hangs on "finding source files"
- ❌ **Method name mismatch**: `discover_source_files` vs `find_source_files`
- ❌ **Limited context**: Ollama constrains context window usage
- ❌ **No streaming**: Responses come all at once

### What We Want
- 🎯 **Fix the hang**: Make it actually work
- 🎯 **Direct model access**: Use HuggingFace Transformers for better control
- 🎯 **Streaming responses**: See responses as they generate
- 🎯 **Codebase learning**: Train LoRA adapters on specific codebases
- 🎯 **Better analysis**: Use full 8k context window

## Requirements

### Requirement 1: Fix Critical Issues

**Goal**: Make the current system actually work

#### What to Fix
1. Fix `discover_source_files` vs `find_source_files` method name issue
2. Add timeout protection to prevent 300-second hangs
3. Add progress feedback during analysis
4. Fix any other blocking issues

#### Use Existing Components
- Enhance existing `FileUtilities.find_source_files` method
- Use existing error handling patterns from `OllamaClient`
- Leverage existing logging infrastructure

### Requirement 2: Direct gpt-oss:20b Integration

**Goal**: Replace Ollama with direct HuggingFace Transformers access

#### What to Build
1. New `DirectGPTOSSClient` class that loads gpt-oss:20b directly
2. 8-bit quantization for Mac Mini M4 memory efficiency
3. Fallback to existing `OllamaClient` if direct loading fails

#### Use Existing Components
- Follow same interface patterns as existing `OllamaClient`
- Use existing retry logic and error handling
- Integrate with existing settings and configuration

#### Technical Implementation
```python
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch

class DirectGPTOSSClient:
    def __init__(self, settings):
        self.model = AutoModelForCausalLM.from_pretrained(
            "EleutherAI/gpt-oss-20B",
            load_in_8bit=True,
            device_map="auto",
            torch_dtype=torch.float16
        )
        self.tokenizer = AutoTokenizer.from_pretrained("EleutherAI/gpt-oss-20B")
```

### Requirement 3: Streaming Response Generation

**Goal**: Show responses as they generate instead of waiting for completion

#### What to Build
1. Streaming generator in `DirectGPTOSSClient`
2. Enhanced Gradio interface with streaming chat
3. Token-by-token response display

#### Use Existing Components
- Enhance existing Gradio interface from previous work
- Use existing chat interface patterns
- Integrate with existing crotchety personality prompts

### Requirement 4: LoRA Training for Codebase Learning

**Goal**: Train model adapters on specific codebases for personalized feedback

#### What to Build
1. `LoRATrainer` class using PEFT library
2. Training data preparation from existing codebase analysis
3. Dynamic adapter loading/unloading

#### Use Existing Components
- Use existing `CodePreprocessor` to prepare training data
- Use existing `FileUtilities` to gather codebase files
- Use existing `NomicEmbedder` patterns for data processing

#### Technical Implementation
```python
from peft import LoraConfig, get_peft_model

class LoRATrainer:
    def train_on_codebase(self, codebase_path):
        # Use existing FileUtilities to find files
        files = self.file_utils.find_source_files(codebase_path)

        # Use existing CodePreprocessor to parse
        chunks = self.preprocessor.process_files(files)

        # Train LoRA adapter
        lora_config = LoraConfig(
            r=64,
            target_modules=["q_proj", "v_proj"],
            task_type="CAUSAL_LM"
        )
```

### Requirement 5: Enhanced Codebase Analysis

**Goal**: Use full 8k context window for deeper analysis

#### What to Build
1. Enhanced analysis that uses full context window
2. Cross-file relationship understanding
3. Architectural pattern recognition

#### Use Existing Components
- Enhance existing `CodePreprocessor` to handle larger contexts
- Use existing `NomicEmbedder` for semantic understanding
- Build on existing crotchety personality prompts

### Requirement 6: Persistent Memory

**Goal**: Remember previous conversations and codebase knowledge

#### What to Build
1. SQLite database for conversation history
2. Codebase knowledge storage
3. Session restoration

#### Use Existing Components
- Use existing database patterns from other components
- Integrate with existing settings and configuration
- Build on existing logging infrastructure

## Implementation Strategy

### Phase 1: Fix What's Broken (Priority 1)
1. Fix the 300-second hang issue
2. Correct method name mismatches
3. Add basic error handling and timeouts
4. Make the current system actually work

### Phase 2: Direct Model Integration
1. Implement `DirectGPTOSSClient` with HuggingFace Transformers
2. Add 8-bit quantization for Mac Mini M4
3. Implement streaming response generation
4. Maintain fallback to existing `OllamaClient`

### Phase 3: LoRA Training
1. Implement `LoRATrainer` using existing components
2. Add training data preparation pipeline
3. Implement adapter management and loading
4. Integrate with codebase analysis workflow

### Phase 4: Enhanced Analysis and Memory
1. Enhance analysis to use full 8k context
2. Add persistent memory with SQLite
3. Implement conversation history and knowledge retention
4. Polish the crotchety engineer personality

## Key Principles

### Use What We Have
- **Don't rebuild**: Enhance and adapt existing components
- **Follow patterns**: Use established patterns from `OllamaClient`, `NomicEmbedder`, etc.
- **Maintain compatibility**: Keep existing interfaces working
- **Leverage infrastructure**: Use existing logging, error handling, configuration

### Keep It Simple
- **Fix first**: Make it work before making it fancy
- **Incremental**: Add features one at a time
- **Fallbacks**: Always have a working fallback option
- **Practical**: Focus on what actually improves the experience

### Focus on Value
- **Working system**: Priority #1 is making it actually work
- **Better analysis**: Use the model's full capabilities
- **Codebase learning**: Make it understand specific codebases
- **Streaming UX**: Immediate feedback is better than waiting

## Success Criteria

### It Works
- ✅ Doesn't hang for 300 seconds
- ✅ Can analyze a codebase and provide feedback
- ✅ Uses gpt-oss:20b effectively
- ✅ Provides streaming responses
- ✅ Learns from specific codebases via LoRA training

### It's Better
- ✅ Faster than current Ollama-based system
- ✅ More intelligent feedback through codebase learning
- ✅ Better user experience with streaming
- ✅ Runs efficiently on Mac Mini M4

## Dependencies

### New Libraries Needed
- `transformers>=4.30.0` - Direct model loading
- `accelerate>=0.20.0` - Memory optimization
- `bitsandbytes>=0.39.0` - 8-bit quantization
- `peft>=0.4.0` - LoRA training

### Existing Components to Enhance
- `OllamaClient` → `DirectGPTOSSClient`
- `FileUtilities` → Enhanced with timeout protection
- `CodePreprocessor` → Enhanced for larger contexts
- `NomicEmbedder` → Integration with LoRA training
- Gradio interface → Streaming chat support

## Risk Mitigation

### Technical Risks
- **Memory constraints**: Use 8-bit quantization, fallback to Ollama
- **Model loading issues**: Comprehensive error handling, fallback options
- **Training complexity**: Start simple, enhance incrementally

### Implementation Risks
- **Breaking existing code**: Maintain backward compatibility
- **Over-engineering**: Focus on working first, fancy second
- **Scope creep**: Stick to core requirements, enhance later
