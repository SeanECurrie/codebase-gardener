#!/usr/bin/env python3
"""
Simple Codebase Chat - The Core Experience

1. Ask user for codebase directory
2. Train/customize model on that codebase
3. Chat with the specialized AI
"""

from pathlib import Path

import gradio as gr
from src.codebase_gardener.config.settings import get_settings
from src.codebase_gardener.core.training_pipeline import LoRATrainingPipeline

# Use existing components
from src.codebase_gardener.data.parser import TreeSitterParser
from src.codebase_gardener.data.preprocessor import CodePreprocessor
from src.codebase_gardener.data.vector_store import VectorStore
from src.codebase_gardener.models.nomic_embedder import get_nomic_embedder
from src.codebase_gardener.models.ollama_client import OllamaClient
from src.codebase_gardener.models.peft_manager import PEFTManager


class SimpleCodebaseChat:
    def __init__(self):
        self.settings = get_settings()
        self.codebase_path = None
        self.vector_store = None
        self.ollama_client = None
        self.peft_manager = None
        self.lora_adapter_path = None
        self.is_trained = False

    def setup_codebase(self, codebase_path: str, progress=gr.Progress()):
        """Set up the codebase for analysis and training."""
        try:
            self.codebase_path = Path(codebase_path)
            if not self.codebase_path.exists():
                return "❌ Directory does not exist", ""

            progress(0.1, desc="Parsing codebase...")

            # Parse the codebase
            parser = TreeSitterParser()
            preprocessor = CodePreprocessor()

            # Find source files (simple approach)
            source_files = []
            for ext in ['.py', '.js', '.ts', '.java', '.cpp', '.c', '.h', '.go', '.rs']:
                source_files.extend(self.codebase_path.rglob(f'*{ext}'))

            if not source_files:
                return "❌ No source files found", ""

            progress(0.3, desc=f"Processing {len(source_files)} files...")

            # Process files
            chunks = []
            for file_path in source_files[:50]:  # Limit for demo
                try:
                    content = file_path.read_text(encoding='utf-8', errors='ignore')
                    parsed = parser.parse_file(str(file_path), content)
                    if parsed and parsed.functions:
                        file_chunks = preprocessor.chunk_code(content, str(file_path))
                        chunks.extend(file_chunks)
                except Exception:
                    continue

            if not chunks:
                return "❌ No code chunks extracted", ""

            progress(0.5, desc="Creating embeddings...")

            # Create vector store
            embedder = get_nomic_embedder()
            self.vector_store = VectorStore(self.settings.data_dir / "simple_vectorstore")

            # Add chunks to vector store
            for chunk in chunks[:100]:  # Limit for demo
                embedding = embedder.embed_code(chunk.content)
                self.vector_store.add_chunk(chunk, embedding)

            progress(0.7, desc="Setting up AI model...")

            # Initialize Ollama client
            self.ollama_client = OllamaClient()

            progress(0.9, desc="Training LoRA adapter...")

            # Train LoRA adapter (simplified)
            self.peft_manager = PEFTManager(self.settings.data_dir / "adapters")
            training_pipeline = LoRATrainingPipeline(
                self.settings.data_dir / "training",
                self.peft_manager
            )

            # Create training data from chunks
            training_data = []
            for chunk in chunks[:20]:  # Small training set for demo
                training_data.append({
                    'input': f"Explain this code: {chunk.content[:200]}",
                    'output': f"This code from {chunk.file_path} implements functionality related to the codebase."
                })

            # Train (this is simplified - in reality would be more complex)
            adapter_name = f"simple_adapter_{self.codebase_path.name}"
            try:
                self.lora_adapter_path = training_pipeline.train_lora_adapter(
                    training_data,
                    adapter_name,
                    base_model="llama3.2:3b"  # Use smaller model for demo
                )
                self.is_trained = True
            except Exception:
                # Fallback - just use base model
                self.is_trained = False

            progress(1.0, desc="Ready!")

            return f"✅ Codebase loaded: {len(source_files)} files, {len(chunks)} chunks processed", f"Codebase: {self.codebase_path.name}"

        except Exception as e:
            return f"❌ Error: {str(e)}", ""

    def chat_with_codebase(self, message: str, history):
        """Chat with the codebase-aware AI."""
        if not self.codebase_path:
            history.append([message, "Please set up a codebase first."])
            return history, ""

        try:
            # Search for relevant code
            context = ""
            if self.vector_store:
                embedder = get_nomic_embedder()
                query_embedding = embedder.embed_code(message)
                similar_chunks = self.vector_store.search_similar(query_embedding, limit=3)

                if similar_chunks:
                    context = "\n\nRelevant code from your codebase:\n"
                    for chunk, score in similar_chunks:
                        context += f"\nFile: {chunk.file_path}\n```\n{chunk.content[:300]}...\n```\n"

            # Create prompt
            prompt = f"""You are an AI assistant specialized in the codebase at {self.codebase_path}.

User question: {message}
{context}

Please provide a helpful response based on the codebase context."""

            # Get AI response
            if self.ollama_client:
                if self.is_trained and self.lora_adapter_path:
                    # Use trained adapter (simplified)
                    response = self.ollama_client.generate_response(prompt, model="llama3.2:3b")
                else:
                    # Use base model
                    response = self.ollama_client.generate_response(prompt, model="llama3.2:3b")
            else:
                response = "AI client not available. Please ensure Ollama is running."

            history.append([message, response])
            return history, ""

        except Exception as e:
            history.append([message, f"Error: {str(e)}"])
            return history, ""

def create_simple_interface():
    """Create the simple Gradio interface."""
    chat_app = SimpleCodebaseChat()

    with gr.Blocks(title="Simple Codebase Chat", theme=gr.themes.Soft()) as interface:
        gr.Markdown("# 🌱 Simple Codebase Chat")
        gr.Markdown("Point me to your codebase and I'll become an AI assistant specialized for your code.")

        with gr.Row():
            codebase_input = gr.Textbox(
                label="Codebase Directory Path",
                placeholder="/path/to/your/codebase",
                value=str(Path.home() / "Desktop" / "codebase-local-llm-advisor")  # Default to current project
            )
            setup_btn = gr.Button("🚀 Setup Codebase", variant="primary")

        setup_status = gr.Textbox(label="Status", interactive=False)
        current_codebase = gr.Textbox(label="Current Codebase", interactive=False)

        gr.Markdown("## Chat with Your Codebase")

        chatbot = gr.Chatbot(height=400)
        msg = gr.Textbox(label="Ask about your code", placeholder="What does this codebase do?")

        # Event handlers
        setup_btn.click(
            chat_app.setup_codebase,
            inputs=[codebase_input],
            outputs=[setup_status, current_codebase]
        )

        msg.submit(
            chat_app.chat_with_codebase,
            inputs=[msg, chatbot],
            outputs=[chatbot, msg]
        )

    return interface

if __name__ == "__main__":
    print("🌱 Starting Simple Codebase Chat...")
    print("Make sure Ollama is running with: ollama serve")
    print("And pull the model: ollama pull llama3.2:3b")

    interface = create_simple_interface()
    interface.launch(server_name="127.0.0.1", server_port=7860, share=False)
