#!/usr/bin/env python3
"""
Codebase Intelligence Auditor - Single File Implementation

A simple, pragmatic codebase analysis tool that uses gpt-oss-20b via Ollama
to provide comprehensive intelligence about code architecture, tech debt, 
and documentation gaps.

Usage:
    auditor = CodebaseAuditor()
    result = auditor.analyze_codebase(".")
    response = auditor.chat("What are the main architecture issues?")
    report = auditor.export_markdown()
"""

import os
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Optional, Dict, Any

# Add the src directory to Python path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    import ollama
except ImportError:
    print("Error: ollama package not found. Install with: pip install ollama")
    sys.exit(1)

try:
    from simple_file_utils import SimpleFileUtilities
except ImportError:
    print("Error: Could not import SimpleFileUtilities. Make sure simple_file_utils.py is in the same directory.")
    sys.exit(1)


class CodebaseAuditor:
    """
    Single-file codebase auditor that analyzes code using gpt-oss-20b.
    
    Provides comprehensive analysis, chat functionality, and markdown export.
    """
    
    def __init__(self, ollama_host: str = "http://localhost:11434"):
        """Initialize the auditor with Ollama client and file utilities."""
        self.client = ollama.Client(ollama_host)
        self.file_utils = SimpleFileUtilities()
        self.analysis_results: Optional[Dict[str, Any]] = None
        
        # Hardcoded analysis prompt for comprehensive review
        self.analysis_prompt = """You are a senior code reviewer analyzing this codebase. Provide a comprehensive analysis with:

1. **Architecture Overview**
   - Main components and their responsibilities
   - How components interact and depend on each other
   - Overall design patterns used
   - Key architectural decisions

2. **Code Quality Issues**
   - Inconsistent naming conventions (with specific examples and file names)
   - Duplicated logic that could be consolidated (with specific locations)
   - Missing or inconsistent error handling (with specific examples)
   - Overly complex functions or classes (with specific file names and line numbers)
   - Code smells and anti-patterns

3. **Documentation Analysis**
   - Missing docstrings (specific files and functions)
   - Outdated comments or documentation
   - README accuracy vs actual codebase
   - Missing or incomplete API documentation

4. **Key Insights and Recommendations**
   - Most critical issues to address first (prioritized list)
   - Strengths of the current architecture
   - Specific recommendations for improvement
   - Technical debt that should be addressed

Be specific with file names and line numbers when possible. Focus on actionable insights that would help a developer or AI agent understand and improve this codebase.

Codebase files:
{file_contents}"""

        self.chat_prompt = """Based on your previous analysis of this codebase:

{previous_analysis}

User question: {user_question}

Provide a helpful, specific answer based on your analysis. Reference specific files, functions, or code patterns when relevant."""

    def analyze_codebase(self, directory_path: str, progress_callback=None) -> str:
        """
        Analyze the entire codebase and store results.
        
        Args:
            directory_path: Path to the codebase directory
            progress_callback: Optional callback for progress updates
            
        Returns:
            Summary message about the analysis
        """
        try:
            dir_path = Path(directory_path).resolve()
            
            if not dir_path.exists() or not dir_path.is_dir():
                return f"Error: Directory '{directory_path}' does not exist or is not accessible."
            
            if progress_callback:
                progress_callback("Starting codebase analysis...")
            
            # Find source files using existing FileUtilities
            print("🔍 Discovering source files...")
            source_files = self.file_utils.find_source_files(
                dir_path, 
                progress_callback=progress_callback
            )
            
            if not source_files:
                return f"No source files found in '{directory_path}'"
            
            print(f"📁 Found {len(source_files)} source files")
            
            # Read and combine file contents
            if progress_callback:
                progress_callback(f"Reading {len(source_files)} source files...")
            
            file_contents = self._read_and_combine_files(source_files, progress_callback)
            
            if not file_contents.strip():
                return "Error: No readable content found in source files"
            
            # Send to gpt-oss-20b for analysis
            print("🤖 Analyzing codebase with gpt-oss-20b...")
            if progress_callback:
                progress_callback("Sending codebase to gpt-oss-20b for analysis...")
            
            full_prompt = self.analysis_prompt.format(file_contents=file_contents)
            
            response = self.client.generate(
                model='gpt-oss-20b',
                prompt=full_prompt
            )
            
            analysis_text = response['response']
            
            # Store results
            self.analysis_results = {
                'full_analysis': analysis_text,
                'file_list': [str(f) for f in source_files],
                'directory_path': str(dir_path),
                'timestamp': datetime.now().isoformat(),
                'file_count': len(source_files)
            }
            
            print("✅ Analysis complete!")
            if progress_callback:
                progress_callback("Analysis complete! You can now ask questions or export the report.")
            
            return f"Analysis complete! Analyzed {len(source_files)} files. Ask me questions or export markdown report."
            
        except Exception as e:
            error_msg = f"Analysis failed: {str(e)}"
            print(f"❌ {error_msg}")
            if progress_callback:
                progress_callback(f"❌ {error_msg}")
            return error_msg
    
    def _read_and_combine_files(self, source_files: List[Path], progress_callback=None) -> str:
        """Read and combine source files into a single context string."""
        combined_content = []
        files_read = 0
        
        for file_path in source_files:
            try:
                # Progress feedback every 10 files
                if progress_callback and files_read % 10 == 0:
                    progress_callback(f"Reading files... {files_read}/{len(source_files)}")
                
                # Read file content safely
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # Add file header and content
                relative_path = file_path.relative_to(Path(self.analysis_results['directory_path']) if self.analysis_results else file_path.parent)
                combined_content.append(f"\n=== FILE: {relative_path} ===\n{content}\n")
                
                files_read += 1
                
            except Exception as e:
                print(f"⚠️  Warning: Could not read {file_path}: {e}")
                continue
        
        if progress_callback:
            progress_callback(f"Successfully read {files_read}/{len(source_files)} files")
        
        return "\n".join(combined_content)
    
    def chat(self, question: str) -> str:
        """
        Ask questions about the analyzed codebase.
        
        Args:
            question: User's question about the codebase
            
        Returns:
            AI response based on the analysis
        """
        if not self.analysis_results:
            return "Error: No codebase analysis available. Please run analyze_codebase() first."
        
        try:
            full_prompt = self.chat_prompt.format(
                previous_analysis=self.analysis_results['full_analysis'],
                user_question=question
            )
            
            response = self.client.generate(
                model='gpt-oss-20b',
                prompt=full_prompt
            )
            
            return response['response']
            
        except Exception as e:
            return f"Chat failed: {str(e)}"
    
    def export_markdown(self) -> str:
        """
        Export analysis results as formatted markdown.
        
        Returns:
            Markdown-formatted analysis report
        """
        if not self.analysis_results:
            return "Error: No analysis results to export. Please run analyze_codebase() first."
        
        timestamp = datetime.fromisoformat(self.analysis_results['timestamp']).strftime("%Y-%m-%d %H:%M:%S")
        
        markdown_report = f"""# Codebase Analysis Report

**Generated:** {timestamp}  
**Directory:** `{self.analysis_results['directory_path']}`  
**Files Analyzed:** {self.analysis_results['file_count']}

---

{self.analysis_results['full_analysis']}

---

## Files Analyzed

The following {self.analysis_results['file_count']} source files were included in this analysis:

"""
        
        # Add file list
        for file_path in sorted(self.analysis_results['file_list']):
            relative_path = Path(file_path).relative_to(self.analysis_results['directory_path'])
            markdown_report += f"- `{relative_path}`\n"
        
        markdown_report += f"""
---

*Report generated by Codebase Intelligence Auditor using gpt-oss-20b*
"""
        
        return markdown_report


def main():
    """Simple CLI interface for the codebase auditor."""
    print("🔍 Codebase Intelligence Auditor")
    print("=" * 40)
    
    auditor = CodebaseAuditor()
    
    while True:
        print("\nCommands:")
        print("  analyze <directory>  - Analyze a codebase")
        print("  chat <question>      - Ask questions about the analysis")
        print("  export              - Export markdown report")
        print("  quit                - Exit")
        
        try:
            command = input("\n> ").strip()
            
            if command.lower() in ['quit', 'exit', 'q']:
                print("Goodbye!")
                break
            elif command.startswith('analyze '):
                directory = command[8:].strip()
                if not directory:
                    print("Please specify a directory to analyze")
                    continue
                result = auditor.analyze_codebase(directory, progress_callback=print)
                print(f"\n{result}")
            elif command.startswith('chat '):
                question = command[5:].strip()
                if not question:
                    print("Please ask a question")
                    continue
                response = auditor.chat(question)
                print(f"\n{response}")
            elif command == 'export':
                report = auditor.export_markdown()
                filename = f"codebase_analysis_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write(report)
                print(f"Report exported to {filename}")
            else:
                print("Unknown command. Try 'analyze <directory>', 'chat <question>', 'export', or 'quit'")
                
        except KeyboardInterrupt:
            print("\nGoodbye!")
            break
        except Exception as e:
            print(f"Error: {e}")


if __name__ == "__main__":
    main()