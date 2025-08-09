"""
Simple main entry point for Codebase Intelligence Auditor.

This is a simplified version that focuses on core functionality without
the complex multi-project management system.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console

# Import only the working components we identified in the audit
from codebase_gardener.utils.file_utils import FileUtilities
from codebase_gardener.config.settings import Settings

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="codebase-auditor")
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode with verbose logging",
)
def cli(debug: bool) -> None:
    """
    Codebase Intelligence Auditor - Simple AI-powered codebase analysis.
    
    Analyze codebases using local AI models without complex project management.
    """
    if debug:
        console.print("[dim]Debug mode enabled[/dim]")


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--output",
    type=click.Path(path_type=Path),
    help="Output file for analysis results (optional)",
)
def analyze(project_path: Path, output: Optional[Path]) -> None:
    """Analyze a codebase directory."""
    console.print(f"[green]Analyzing codebase: {project_path}[/green]")
    
    try:
        # Use the working FileUtilities from our audit
        file_utils = FileUtilities()
        
        def progress_callback(message):
            console.print(f"[dim]{message}[/dim]")
        
        # Find source files using the working component
        console.print("[blue]Discovering source files...[/blue]")
        source_files = file_utils.find_source_files(
            project_path, 
            progress_callback=progress_callback
        )
        
        console.print(f"[green]✓ Found {len(source_files)} source files[/green]")
        
        # For now, just list the files found
        if len(source_files) > 0:
            console.print("\n[bold]Source files discovered:[/bold]")
            for i, file_path in enumerate(source_files[:10]):  # Show first 10
                console.print(f"  {i+1}. {file_path.relative_to(project_path)}")
            
            if len(source_files) > 10:
                console.print(f"  ... and {len(source_files) - 10} more files")
        
        # Save results if output specified
        if output:
            with output.open('w') as f:
                f.write(f"# Codebase Analysis Results\n\n")
                f.write(f"**Project**: {project_path}\n")
                f.write(f"**Files Found**: {len(source_files)}\n\n")
                f.write("## Source Files\n\n")
                for file_path in source_files:
                    f.write(f"- {file_path.relative_to(project_path)}\n")
            
            console.print(f"[green]✓ Results saved to {output}[/green]")
        
        console.print("\n[yellow]Note: AI analysis will be implemented in Task 2[/yellow]")
        
    except Exception as e:
        console.print(f"[red]Error analyzing codebase: {e}[/red]")
        sys.exit(1)


@cli.command()
def test() -> None:
    """Test that core components are working."""
    console.print("[blue]Testing core components...[/blue]")
    
    try:
        # Test FileUtilities
        file_utils = FileUtilities()
        console.print("[green]✓ FileUtilities loaded successfully[/green]")
        
        # Test Settings
        settings = Settings()
        console.print(f"[green]✓ Settings loaded (data_dir: {settings.data_dir})[/green]")
        
        console.print("\n[green]All core components are working![/green]")
        
    except Exception as e:
        console.print(f"[red]Component test failed: {e}[/red]")
        sys.exit(1)


if __name__ == "__main__":
    cli()