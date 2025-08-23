"""
Configuration management using Pydantic BaseSettings.

This module provides centralized configuration for the Codebase Gardener application
with automatic environment variable support and type validation.
"""

from pathlib import Path

from pydantic import ConfigDict, Field, field_validator
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.

    All settings can be overridden using environment variables with the
    CODEBASE_GARDENER_ prefix. For example, to override debug mode:
    export CODEBASE_GARDENER_DEBUG=true
    """

    # Application settings
    app_name: str = Field(default="Codebase Gardener", description="Application name")
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Data storage settings
    data_dir: Path = Field(
        default_factory=lambda: Path.home() / ".codebase-gardener",
        description="Base directory for application data",
    )
    projects_dir: Path | None = Field(
        default=None, description="Directory containing project-specific data"
    )
    base_models_dir: Path | None = Field(
        default=None, description="Directory for base AI models"
    )

    # AI/ML Model settings
    ollama_base_url: str = Field(
        default="http://localhost:11434", description="Base URL for Ollama API"
    )
    ollama_timeout: int = Field(
        default=30, description="Timeout for Ollama API calls in seconds"
    )
    default_base_model: str = Field(
        default="microsoft/DialoGPT-small",
        description="Default base model for LoRA fine-tuning",
    )
    embedding_model: str = Field(
        default="microsoft/codebert-base",
        description="Embedding model for code analysis",
    )
    embedding_cache_size: int = Field(
        default=1000,
        description="Maximum number of embeddings to cache",
        ge=100,
        le=10000,
    )
    embedding_device: str = Field(
        default="auto", description="Device for embedding model (auto, cpu, cuda, mps)"
    )

    # Vector database settings
    vector_db_path: Path | None = Field(
        default=None, description="Path to vector database storage"
    )
    embedding_batch_size: int = Field(
        default=32, description="Batch size for embedding generation", ge=1, le=128
    )
    max_chunk_size: int = Field(
        default=2048,
        description="Maximum size of code chunks for embedding",
        ge=100,
        le=5000,
    )
    min_chunk_size: int = Field(
        default=50,
        description="Minimum size of code chunks for embedding",
        ge=10,
        le=500,
    )
    chunk_overlap: int = Field(
        default=100, description="Overlap between adjacent chunks", ge=0, le=500
    )

    # Training settings
    lora_rank: int = Field(
        default=16, description="LoRA adapter rank for fine-tuning", ge=1, le=64
    )
    lora_alpha: int = Field(
        default=32, description="LoRA alpha parameter for fine-tuning", ge=1, le=128
    )
    training_batch_size: int = Field(
        default=4, description="Batch size for LoRA training", ge=1, le=16
    )
    max_training_steps: int = Field(
        default=1000,
        description="Maximum training steps for LoRA adapters",
        ge=100,
        le=10000,
    )

    # Performance settings
    max_workers: int = Field(
        default=4, description="Maximum number of worker threads", ge=1, le=16
    )
    max_memory_mb: int = Field(
        default=6000,  # 6GB for Mac Mini M4 8GB
        description="Memory limit in MB for AI operations",
        ge=1024,
        le=16384,
    )
    supported_languages: str = Field(
        default="python,javascript,typescript,java,go,rust",
        description="Comma-separated list of supported programming languages",
    )

    # UI settings
    gradio_host: str = Field(
        default="127.0.0.1", description="Host for Gradio web interface"
    )
    gradio_port: int = Field(
        default=7860, description="Port for Gradio web interface", ge=1024, le=65535
    )
    gradio_share: bool = Field(
        default=False, description="Enable Gradio sharing (creates public URL)"
    )

    # Development settings
    enable_profiling: bool = Field(
        default=False, description="Enable performance profiling"
    )
    cache_embeddings: bool = Field(
        default=True, description="Cache embeddings to disk for reuse"
    )

    # Code preprocessing settings
    preserve_comments: bool = Field(
        default=True, description="Preserve comments during code preprocessing"
    )
    preserve_docstrings: bool = Field(
        default=True, description="Preserve docstrings during code preprocessing"
    )
    normalize_whitespace: bool = Field(
        default=True, description="Normalize whitespace during code preprocessing"
    )
    calculate_complexity: bool = Field(
        default=True, description="Calculate complexity scores for code chunks"
    )

    model_config = ConfigDict(
        env_prefix="CODEBASE_GARDENER_",
        case_sensitive=False,
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",  # Allow extra environment variables without failing
    )

    @field_validator("log_level")
    @classmethod
    def validate_log_level(cls, v):
        """Validate log level is one of the standard levels."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        if v.upper() not in valid_levels:
            raise ValueError(f"log_level must be one of {valid_levels}")
        return v.upper()

    @field_validator("data_dir", mode="before")
    @classmethod
    def validate_data_dir(cls, v):
        """Ensure data directory is a Path object and create if needed."""
        if isinstance(v, str):
            v = Path(v)

        # Expand user home directory
        v = v.expanduser().resolve()

        # Create directory if it doesn't exist
        v.mkdir(parents=True, exist_ok=True)

        return v

    @field_validator("projects_dir", mode="before")
    @classmethod
    def set_projects_dir(cls, v, info):
        """Set projects directory relative to data directory if not specified."""
        if v is None and info.data.get("data_dir"):
            data_dir = info.data["data_dir"]
            if isinstance(data_dir, str):
                data_dir = Path(data_dir)
            return data_dir / "projects"
        return v

    @field_validator("base_models_dir", mode="before")
    @classmethod
    def set_base_models_dir(cls, v, info):
        """Set base models directory relative to data directory if not specified."""
        if v is None and info.data.get("data_dir"):
            data_dir = info.data["data_dir"]
            if isinstance(data_dir, str):
                data_dir = Path(data_dir)
            return data_dir / "base_models"
        return v

    @field_validator("vector_db_path", mode="before")
    @classmethod
    def set_vector_db_path(cls, v, info):
        """Set vector database path relative to data directory if not specified."""
        if v is None and info.data.get("data_dir"):
            data_dir = info.data["data_dir"]
            if isinstance(data_dir, str):
                data_dir = Path(data_dir)
            return data_dir / "vector_store"
        return v

    @field_validator("ollama_base_url")
    @classmethod
    def validate_ollama_url(cls, v):
        """Validate Ollama URL format."""
        if not v.startswith(("http://", "https://")):
            raise ValueError("ollama_base_url must start with http:// or https://")
        return v.rstrip("/")  # Remove trailing slash

    def create_directories(self) -> None:
        """Create all necessary directories for the application."""
        directories = [
            self.data_dir,
            self.projects_dir,
            self.base_models_dir,
            self.vector_db_path.parent if self.vector_db_path else None,
        ]

        for directory in directories:
            if directory:
                directory.mkdir(parents=True, exist_ok=True)

    def get_project_dir(self, project_name: str) -> Path:
        """Get the directory path for a specific project."""
        project_dir = self.projects_dir / project_name
        project_dir.mkdir(parents=True, exist_ok=True)
        return project_dir

    def get_lora_adapter_path(self, project_name: str) -> Path:
        """Get the path for a project's LoRA adapter."""
        return self.get_project_dir(project_name) / "lora_adapter.bin"

    def get_project_vector_store_path(self, project_name: str) -> Path:
        """Get the path for a project's vector store."""
        return self.get_project_dir(project_name) / "vector_store"

    def get_project_context_path(self, project_name: str) -> Path:
        """Get the path for a project's context file."""
        return self.get_project_dir(project_name) / "context.json"


# Global settings instance
settings = Settings()


def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


def reload_settings() -> Settings:
    """Reload settings from environment variables."""
    global settings
    settings = Settings()
    return settings
