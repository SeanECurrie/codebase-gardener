#!/usr/bin/env python3
"""
Crotchety Code Auditor - A focused, no-nonsense AI assistant for code analysis.

Uses OpenAI's gpt-oss:20b model via Ollama to provide brutally honest code audits
with the personality of a veteran software engineer obsessed with clean, simple code.

This leverages ALL the existing Codebase Gardener components but strips away the
complexity to focus on the core experience: point to a codebase, analyze it, chat about it.
"""

import sys
import time
from pathlib import Path
from typing import List, Optional

import gradio as gr
import structlog
from rich.console import Console
from rich.panel import Panel

# Import existing components - USE WHAT WE BUILT!
from src.codebase_gardener.models.ollama_client import OllamaClient, ensure_model_available
from src.codebase_gardener.models.nomic_embedder import NomicEmbedder
from src.codebase_gardener.utils.file_utils import FileUtilities
from src.codebase_gardener.config.settings import get_settings
from src.codebase_gardener.data.preprocessor import CodePreprocessor

console = Console()
logger = structlog.get_logger(__name__)

# The crotchety engineer personality
CROTCHETY_SYSTEM_PROMPT = """You are a crotchety veteran software engineer with 30+ years of experience. You are OBSESSED with:

- KISS (Keep It Simple, Stupid) principles
- Clean, readable code that doesn't need comments to understand
- Proper error handling and edge cases
- Documentation that actually explains WHY, not what
- Code that a junior developer can understand in 6 months
- Eliminating unnecessary complexity and over-engineering

You have ZERO patience for:
- Clever code that's hard to read
- Missing error handling
- Functions longer than 20 lines
- Classes with more than 5 methods
- Unclear variable names
- Code without tests
- Documentation that just repeats the code

Your responses are:
- Direct and honest (sometimes brutally so)
- Focused on practical improvements
- Backed by decades of experience
- Obsessed with maintainability
- Always suggest the SIMPLEST solution that works

You assume the codebase is robust but AI agents have gotten off track. You're looking for TRUTH and real analysis. You analyze FULL FILES, not snippets.

When you find issues, you explain WHY they matter and HOW to fix them simply."""

class CrotchetyCodeAuditor:
    """
    The main auditor that coordinates all the existing components
    to provide focused code analysis with a crotchety personality.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.console = Console()
        self.codebase_path: Optional[Path] = None
        self.analysis_complete = False
        
        # Initialize existing components
        self.ollama_client = OllamaClient(self.settings)
        self.embedder = NomicEmbedder(self.settings)
        self.file_utils = FileUtilities()
        
        # Create preprocessor with safe settings
        try:
            self.preprocessor = CodePreprocessor(self.settings)
        except AttributeError as e:
            # Fallback if settings are missing attributes
            logger.warning(f"Settings missing attributes: {e}")
            from src.codebase_gardener.data.preprocessor import PreprocessingConfig
            config = PreprocessingConfig()
            self.preprocessor = CodePreprocessor(config)
        
        # Model configuration - try gpt-oss:20b first, fallback to available models
        self.model_name = "gpt-oss:20b"
        self.fallback_models = ["llama3.2:3b", "llama3.1:8b", "llama2:7b", "codellama:7b"]
        
        logger.info("Crotchety Code Auditor initialized")
    
    def ensure_model_ready(self) -> bool:
        """Ensure gpt-oss:20b is available, install if needed."""
        try:
            # Verify health first
            if not self.ollama_client.health_check():
                self.console.print("[red]❌ Ollama service not available[/red]")
                self.console.print("[dim]Make sure Ollama is running: brew services start ollama[/dim]")
                return False
            
            # Check what models are available
            try:
                available_models = self.ollama_client.list_models()
                model_names = [model.model for model in available_models]
                
                # Try gpt-oss:20b first
                if self.model_name in model_names:
                    self.console.print(f"[green]✓ Model {self.model_name} is ready![/green]")
                    return True
                else:
                    self.console.print(f"[yellow]Model {self.model_name} not found. Trying to install...[/yellow]")
                    try:
                        self.ollama_client.pull_model(self.model_name, stream=False)
                        self.console.print(f"[green]✓ Model {self.model_name} installed successfully![/green]")
                        return True
                    except Exception as e:
                        self.console.print(f"[yellow]⚠️ Could not install {self.model_name}: {e}[/yellow]")
                        self.console.print("[dim]Trying fallback models...[/dim]")
                    
                    # Try fallback models - check what's actually available
                    try:
                        available_models = self.ollama_client.list_models()
                        model_names = [model.model for model in available_models]
                        
                        for fallback_model in self.fallback_models:
                            if fallback_model in model_names:
                                self.model_name = fallback_model
                                self.console.print(f"[green]✓ Using fallback model: {fallback_model}[/green]")
                                return True
                    except Exception as e:
                        self.console.print(f"[yellow]Could not check available models: {e}[/yellow]")
                    
                    # If no fallback available, use what we have
                    if model_names:
                        # Use the first available model
                        self.model_name = model_names[0]
                        self.console.print(f"[green]✓ Using available model: {self.model_name}[/green]")
                        return True
                    
                    self.console.print("[red]❌ No suitable models available[/red]")
                    return False
            except Exception as e:
                self.console.print(f"[red]❌ Error checking models: {e}[/red]")
                return False
                
        except Exception as e:
            self.console.print(f"[red]❌ Error setting up model: {e}[/red]")
            return False
    
    def select_codebase(self, path: str) -> tuple[str, bool]:
        """Select and analyze a codebase directory."""
        try:
            self.console.print(f"[dim]Starting analysis of: {path}[/dim]")
            codebase_path = Path(path).expanduser().resolve()
            
            if not codebase_path.exists():
                return f"❌ Path does not exist: {codebase_path}", False
            
            if not codebase_path.is_dir():
                return f"❌ Path is not a directory: {codebase_path}", False
            
            self.console.print(f"[dim]Finding source files...[/dim]")
            # Use existing file utilities to find source files
            source_files = self.file_utils.find_source_files(codebase_path)
            
            if not source_files:
                return f"❌ No source files found in: {codebase_path}", False
            
            self.console.print(f"[dim]Found {len(source_files)} source files[/dim]")
            self.codebase_path = codebase_path
            
            # Start analysis
            self.console.print(f"[dim]Analyzing codebase structure...[/dim]")
            analysis_result = self._analyze_codebase(source_files)
            
            self.console.print(f"[green]Analysis complete![/green]")
            return analysis_result, True
            
        except Exception as e:
            logger.error(f"Error selecting codebase: {e}")
            self.console.print(f"[red]Error during analysis: {e}[/red]")
            return f"❌ Error analyzing codebase: {e}", False
    
    def _analyze_codebase(self, source_files: List[Path]) -> str:
        """Analyze the codebase using existing components."""
        analysis_parts = [
            f"# 🔍 Codebase Analysis Complete",
            f"",
            f"**Path:** `{self.codebase_path}`",
            f"**Files Found:** {len(source_files)} source files",
            f"**Languages Detected:** {self._detect_languages(source_files)}",
            f"",
            f"## 📊 Analysis Summary",
            f""
        ]
        
        # Use existing preprocessor to analyze code structure
        try:
            total_lines = 0
            total_functions = 0
            total_classes = 0
            
            # Sample a few files for detailed analysis
            sample_files = source_files[:5]  # Analyze first 5 files in detail
            
            for file_path in sample_files:
                try:
                    content = file_path.read_text(encoding='utf-8')
                    total_lines += len(content.splitlines())
                    
                    # Use existing preprocessor to get code chunks
                    chunks = self.preprocessor.process_file(file_path, content)
                    
                    for chunk in chunks:
                        if chunk.chunk_type.name == 'FUNCTION':
                            total_functions += 1
                        elif chunk.chunk_type.name == 'CLASS':
                            total_classes += 1
                            
                except Exception as e:
                    logger.warning(f"Error analyzing {file_path}: {e}")
                    continue
            
            analysis_parts.extend([
                f"- **Total Lines Analyzed:** {total_lines:,}",
                f"- **Functions Found:** {total_functions}",
                f"- **Classes Found:** {total_classes}",
                f"- **Average File Size:** {total_lines // len(sample_files) if sample_files else 0} lines",
                f"",
                f"## 🎯 Ready for Code Review",
                f"",
                f"I've analyzed your codebase structure. Now I'm ready to provide brutally honest feedback about your code.",
                f"",
                f"**What I can help with:**",
                f"- Review specific files for code quality issues",
                f"- Identify over-engineered solutions",
                f"- Suggest simpler, cleaner alternatives", 
                f"- Point out missing error handling",
                f"- Recommend better documentation",
                f"- Find code that violates KISS principles",
                f"",
                f"**Just paste your code below and I'll tell you what I really think about it.**"
            ])
            
            self.analysis_complete = True
            
        except Exception as e:
            analysis_parts.extend([
                f"⚠️ **Analysis Error:** {e}",
                f"",
                f"But I can still review individual files if you paste them below."
            ])
        
        return "\n".join(analysis_parts)
    
    def _detect_languages(self, source_files: List[Path]) -> str:
        """Detect programming languages in the codebase."""
        extensions = set()
        for file_path in source_files:
            if file_path.suffix:
                extensions.add(file_path.suffix.lower())
        
        # Map extensions to languages
        lang_map = {
            '.py': 'Python', '.js': 'JavaScript', '.ts': 'TypeScript',
            '.java': 'Java', '.go': 'Go', '.rs': 'Rust', '.cpp': 'C++',
            '.c': 'C', '.rb': 'Ruby', '.php': 'PHP', '.swift': 'Swift',
            '.kt': 'Kotlin', '.scala': 'Scala', '.sh': 'Shell'
        }
        
        languages = [lang_map.get(ext, ext) for ext in sorted(extensions)]
        return ", ".join(languages[:5])  # Show first 5 languages
    
    def chat_with_crotchety_engineer(self, message: str, history: List[dict]) -> tuple[List[dict], str]:
        """Chat with the crotchety engineer about code."""
        if not message.strip():
            return history, ""
        
        if not self.codebase_path:
            history.append({"role": "user", "content": message})
            history.append({
                "role": "assistant", 
                "content": "Hold on there, hotshot. You need to select a codebase first. I can't review code that doesn't exist."
            })
            return history, ""
        
        try:
            # Prepare the conversation for the crotchety engineer
            messages = [{"role": "system", "content": CROTCHETY_SYSTEM_PROMPT}]
            
            # Add recent conversation history
            for msg in history[-6:]:  # Last 6 messages for context
                messages.append(msg)
            
            # Add current message
            messages.append({"role": "user", "content": message})
            
            # Get response from gpt-oss:20b using existing Ollama client
            response = self.ollama_client.chat(
                model=self.model_name,
                messages=messages,
                stream=False
            )
            
            assistant_response = response.get('message', {}).get('content', 'Error getting response')
            
            # Add to history
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": assistant_response})
            
            logger.info("Generated crotchety response", message_length=len(message))
            
            return history, ""
            
        except Exception as e:
            error_response = f"*grumbles* Something went wrong with my analysis: {str(e)}\n\nTry again, and this time make sure your code actually compiles."
            history.append({"role": "user", "content": message})
            history.append({"role": "assistant", "content": error_response})
            logger.error(f"Chat error: {e}")
            return history, ""

def create_crotchety_interface() -> gr.Blocks:
    """Create the Gradio interface for the Crotchety Code Auditor."""
    
    auditor = CrotchetyCodeAuditor()
    
    # Check if model is ready
    if not auditor.ensure_model_ready():
        # Create error interface
        with gr.Blocks(title="Crotchety Code Auditor - Setup Required") as error_app:
            gr.Markdown("# ❌ Setup Required")
            gr.Markdown("""
            The gpt-oss:20b model is not available. Please:
            
            1. Make sure Ollama is running: `brew services start ollama`
            2. Install the model: `ollama pull gpt-oss:20b`
            3. Restart this application
            """)
        return error_app
    
    # Create main interface
    with gr.Blocks(
        title="Crotchety Code Auditor",
        theme=gr.themes.Monochrome(),
        css="""
        .crotchety-header { 
            background: #2d3748; 
            color: #e2e8f0; 
            padding: 20px; 
            border-radius: 8px; 
            margin-bottom: 20px;
        }
        .analysis-result {
            background: #f7fafc;
            padding: 15px;
            border-radius: 8px;
            border-left: 4px solid #4a5568;
        }
        """
    ) as app:
        
        # Header
        gr.Markdown("""
        # 👴 Crotchety Code Auditor
        
        *A brutally honest AI code reviewer powered by gpt-oss:20b*
        
        I'm a veteran software engineer with 30+ years of experience. I hate clever code, love simple solutions, and will tell you exactly what's wrong with your codebase. No sugar-coating.
        """, elem_classes=["crotchety-header"])
        
        # State
        analysis_state = gr.State(value={"codebase_selected": False, "analysis_complete": False})
        
        # Step 1: Codebase Selection
        with gr.Row():
            with gr.Column():
                gr.Markdown("## 📁 Step 1: Select Your Codebase")
                codebase_input = gr.Textbox(
                    label="Codebase Directory Path",
                    placeholder="/path/to/your/codebase (or drag folder here)",
                    info="Point me to the directory containing your code. I'll analyze it and tell you what I think."
                )
                analyze_btn = gr.Button("🔍 Analyze This Codebase", variant="primary", size="lg")
        
        # Analysis Results
        analysis_output = gr.Markdown(
            value="👆 **Select a codebase directory above to get started.**",
            elem_classes=["analysis-result"]
        )
        
        # Step 2: Chat Interface (initially hidden)
        with gr.Column(visible=False) as chat_section:
            gr.Markdown("## 💬 Step 2: Code Review Chat")
            gr.Markdown("Now paste your code below and I'll give you my honest opinion about it.")
            
            chatbot = gr.Chatbot(
                label="Crotchety Engineer",
                height=400,
                type="messages",
                placeholder="I'm ready to review your code. Paste it here and I'll tell you what's wrong with it."
            )
            
            with gr.Row():
                chat_input = gr.Textbox(
                    label="Your Code or Question",
                    placeholder="Paste your code here, or ask me about architecture, patterns, etc...",
                    lines=5,
                    scale=4
                )
                send_btn = gr.Button("📨 Send", variant="primary", scale=1)
            
            clear_btn = gr.Button("🗑️ Clear Chat", variant="secondary")
        
        # Event Handlers
        def handle_analysis(path):
            result, success = auditor.select_codebase(path)
            
            if success:
                # Show chat section
                return (
                    result,
                    gr.update(visible=True),  # Show chat section
                    {"codebase_selected": True, "analysis_complete": True}
                )
            else:
                return (
                    result,
                    gr.update(visible=False),  # Hide chat section
                    {"codebase_selected": False, "analysis_complete": False}
                )
        
        # Analysis button
        analyze_btn.click(
            fn=handle_analysis,
            inputs=[codebase_input],
            outputs=[analysis_output, chat_section, analysis_state]
        )
        
        # Chat functionality
        send_btn.click(
            fn=auditor.chat_with_crotchety_engineer,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        chat_input.submit(
            fn=auditor.chat_with_crotchety_engineer,
            inputs=[chat_input, chatbot],
            outputs=[chatbot, chat_input]
        )
        
        clear_btn.click(
            fn=lambda: ([], ""),
            outputs=[chatbot, chat_input]
        )
    
    return app

def main():
    """Main entry point for the Crotchety Code Auditor."""
    console.print(
        Panel.fit(
            "[bold]🔧 Crotchety Code Auditor[/bold]\n\n"
            "A focused, no-nonsense AI code reviewer\n"
            "Powered by gpt-oss:20b and existing Codebase Gardener components\n\n"
            "[dim]Starting web interface...[/dim]",
            title="🌱 Codebase Analysis",
        )
    )
    
    try:
        app = create_crotchety_interface()
        app.launch(
            server_name="127.0.0.1",
            server_port=7860,
            share=False,
            debug=False,
            show_error=True
        )
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting application: {e}[/red]")
        sys.exit(1)

if __name__ == "__main__":
    main()