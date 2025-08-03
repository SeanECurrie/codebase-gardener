"""
Settings and configuration management for Codebase Gardener.

This module provides centralized configuration using Pydantic BaseSettings
with environment variable support and validation.
"""

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field, field_validator, ConfigDict
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """
    Application settings with environment variable support.
    
    All settings can be overridden via environment variables with the
    CODEBASE_GARDENER_ prefix (e.g., CODEBASE_GARDENER_DEBUG=true).
    """
    
    # Application settings
    app_name: str = "Codebase Gardener"
    debug: bool = False
    log_level: str = "INFO"
    
    # Model settings
    ollama_base_url: str = "http://localhost:11434"
    default_embedding_model: str = "nomic-embed-code"
    max_context_length: int = 4096
    embedding_batch_size: int = 32
    
    # Storage settings
    data_dir: Path = Field(default_factory=lambda: Path.home() / ".codebase-gardener")
    vector_db_path: Optional[Path] = None
    
    # Performance settings
    max_workers: int = 4
    memory_limit_gb: int = 6  # Conservative limit for Mac Mini M4
    
    # Training settings
    lora_rank: int = 16
    lora_alpha: int = 32
    lora_dropout: float = 0.1
    training_batch_size: int = 4
    
    model_config = ConfigDict(
        env_prefix="CODEBASE_GARDENER_",
        case_sensitive=False
    )
        
    @field_validator('vector_db_path')
    @classmethod
    def set_vector_db_path(cls, v, info):
        """Set default vector database path if not provided."""
        if v is None:
            data_dir = info.data.get('data_dir', Path.home() / ".codebase-gardener")
            return data_dir / "vector_store"
        return v
    
    @field_validator('embedding_batch_size')
    @classmethod
    def validate_batch_size(cls, v):
        """Validate embedding batch size is reasonable."""
        if v < 1 or v > 128:
            raise ValueError('Batch size must be between 1 and 128')
        return v
    
    @field_validator('memory_limit_gb')
    @classmethod
    def validate_memory_limit(cls, v):
        """Validate memory limit is reasonable for Mac Mini M4."""
        if v < 2 or v > 16:
            raise ValueError('Memory limit must be between 2 and 16 GB')
        return v
    
    def model_post_init(self, __context) -> None:
        """Ensure data directory exists after initialization."""
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self.vector_db_path.mkdir(parents=True, exist_ok=True)


@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    
    Uses LRU cache to ensure settings are only loaded once and reused
    across the application.
    """
    return Settings()