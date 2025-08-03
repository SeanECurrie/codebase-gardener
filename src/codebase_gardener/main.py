"""
Main entry point for Codebase Gardener MVP.

This module provides the primary application launcher with project switching
support and command-line interface for project management.
"""

import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel

from codebase_gardener.config import settings

console = Console()


@click.group()
@click.version_option(version="0.1.0", prog_name="codebase-gardener")
@click.option(
    "--debug",
    is_flag=True,
    help="Enable debug mode with verbose logging",
)
def cli(debug: bool) -> None:
    """
    Codebase Gardener MVP - AI-powered project-specific codebase analysis.
    
    Create specialized AI assistants for individual codebases through LoRA
    adapters trained on specific projects. Switch between projects to get
    tailored analysis that understands your code's unique patterns.
    """
    if debug:
        settings.debug = True
        settings.log_level = "DEBUG"


@cli.command()
@click.option(
    "--host",
    default="127.0.0.1",
    help="Host to bind the web interface to",
)
@click.option(
    "--port",
    default=7860,
    help="Port to bind the web interface to",
)
def serve(host: str, port: int) -> None:
    """Start the Gradio web interface for project analysis."""
    console.print(
        Panel.fit(
            "[bold green]Starting Codebase Gardener Web Interface[/bold green]\n\n"
            f"Host: {host}\n"
            f"Port: {port}\n\n"
            "[dim]Use Ctrl+C to stop the server[/dim]",
            title="🌱 Codebase Gardener",
        )
    )
    
    try:
        # Import here to avoid loading heavy dependencies unless needed
        from codebase_gardener.ui.gradio_app import create_app
        
        app = create_app()
        app.launch(
            server_name=host,
            server_port=port,
            share=False,
            debug=settings.debug,
        )
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies for web interface: {e}[/red]")
        console.print("[yellow]Run: pip install -e .[dev] to install all dependencies[/yellow]")
        sys.exit(1)
    except KeyboardInterrupt:
        console.print("\n[yellow]Shutting down gracefully...[/yellow]")
    except Exception as e:
        console.print(f"[red]Error starting web interface: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("project_path", type=click.Path(exists=True, path_type=Path))
@click.option(
    "--name",
    help="Custom name for the project (defaults to directory name)",
)
def add(project_path: Path, name: Optional[str]) -> None:
    """Add a new codebase project for analysis."""
    project_name = name or project_path.name
    
    console.print(f"[green]Adding project: {project_name}[/green]")
    console.print(f"[dim]Path: {project_path}[/dim]")
    
    try:
        # Import here to avoid loading heavy dependencies unless needed
        from codebase_gardener.core.project_registry import ProjectRegistry
        
        registry = ProjectRegistry()
        registry.add_project(project_path, project_name)
        
        console.print(f"[green]✓ Project '{project_name}' added successfully![/green]")
        console.print("[dim]LoRA adapter training will begin automatically.[/dim]")
        
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error adding project: {e}[/red]")
        sys.exit(1)


@cli.command()
def list() -> None:
    """List all registered codebase projects."""
    try:
        from codebase_gardener.core.project_registry import ProjectRegistry
        
        registry = ProjectRegistry()
        projects = registry.list_projects()
        
        if not projects:
            console.print("[yellow]No projects registered yet.[/yellow]")
            console.print("[dim]Use 'codebase-gardener add <path>' to add your first project.[/dim]")
            return
        
        console.print("[bold]Registered Projects:[/bold]\n")
        for project in projects:
            status_color = "green" if project.status == "ready" else "yellow"
            console.print(f"• [{status_color}]{project.name}[/{status_color}] - {project.path}")
            console.print(f"  [dim]Status: {project.status} | Last updated: {project.last_updated}[/dim]\n")
            
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error listing projects: {e}[/red]")
        sys.exit(1)


@cli.command()
@click.argument("project_name")
def remove(project_name: str) -> None:
    """Remove a codebase project and its associated data."""
    console.print(f"[yellow]Removing project: {project_name}[/yellow]")
    
    if not click.confirm("This will delete all associated LoRA adapters and vector stores. Continue?"):
        console.print("[dim]Operation cancelled.[/dim]")
        return
    
    try:
        from codebase_gardener.core.project_registry import ProjectRegistry
        
        registry = ProjectRegistry()
        registry.remove_project(project_name)
        
        console.print(f"[green]✓ Project '{project_name}' removed successfully![/green]")
        
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error removing project: {e}[/red]")
        sys.exit(1)


@cli.command()
def init() -> None:
    """Initialize Codebase Gardener directory structure and configuration."""
    console.print("[green]Initializing Codebase Gardener...[/green]")
    
    try:
        from codebase_gardener.utils.directory_setup import initialize_directories
        
        initialize_directories()
        
        console.print("[green]✓ Initialization complete![/green]")
        console.print(f"[dim]Data directory: {settings.data_dir}[/dim]")
        console.print("[dim]You can now add projects with 'codebase-gardener add <path>'[/dim]")
        
    except ImportError as e:
        console.print(f"[red]Error: Missing dependencies: {e}[/red]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Error during initialization: {e}[/red]")
        sys.exit(1)


def main() -> None:
    """Main entry point for the CLI application."""
    try:
        cli()
    except KeyboardInterrupt:
        console.print("\n[yellow]Operation cancelled by user.[/yellow]")
        sys.exit(1)
    except Exception as e:
        console.print(f"[red]Unexpected error: {e}[/red]")
        if settings.debug:
            raise
        sys.exit(1)


if __name__ == "__main__":
    main()