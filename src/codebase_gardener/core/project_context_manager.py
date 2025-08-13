"""
Project Context Manager for maintaining separate conversation states per project.

This module provides the ProjectContextManager class that handles:
- Separate conversation states for each project
- Context switching coordination with dynamic model loader
- Intelligent context pruning for memory management
- Session persistence across application restarts
- Integration with project registry for context lifecycle management
"""

import json
import threading
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any

import structlog

from ..config import settings
from ..utils.error_handling import CodebaseGardenerError, retry_with_backoff

logger = structlog.get_logger(__name__)


class ContextManagerError(CodebaseGardenerError):
    """Exception raised for context manager specific errors."""

    pass


@dataclass
class ConversationMessage:
    """Represents a single message in a conversation."""

    role: str  # 'user' or 'assistant'
    content: str
    timestamp: datetime
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            "role": self.role,
            "content": self.content,
            "timestamp": self.timestamp.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ConversationMessage":
        """Create message from dictionary."""
        return cls(
            role=data["role"],
            content=data["content"],
            timestamp=datetime.fromisoformat(data["timestamp"]),
            metadata=data.get("metadata", {}),
        )

    def importance_score(self) -> float:
        """Calculate importance score for pruning decisions."""
        # Base score from recency (newer messages are more important)
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / 168))  # Decay over a week

        # Boost score for certain content types
        content_score = 0.0
        if any(
            keyword in self.content.lower()
            for keyword in ["error", "important", "remember"]
        ):
            content_score += 0.3
        if len(self.content) > 200:  # Longer messages might be more important
            content_score += 0.2
        if self.role == "user":  # User messages are slightly more important
            content_score += 0.1

        return min(1.0, recency_score + content_score)


@dataclass
class ProjectContext:
    """Represents the conversation context for a specific project."""

    project_id: str
    conversation_history: list[ConversationMessage] = field(default_factory=list)
    analysis_cache: dict[str, Any] = field(default_factory=dict)
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: dict[str, Any] = field(default_factory=dict)

    def add_message(
        self, role: str, content: str, metadata: dict[str, Any] = None
    ) -> None:
        """Add a new message to the conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {},
        )
        self.conversation_history.append(message)
        self.last_accessed = datetime.now()

    def prune_history(self, max_messages: int = 50) -> None:
        """Prune conversation history to keep only most important messages."""
        if len(self.conversation_history) <= max_messages:
            return

        # Calculate importance scores and keep top messages
        scored_messages = [
            (msg, msg.importance_score()) for msg in self.conversation_history
        ]
        scored_messages.sort(key=lambda x: x[1], reverse=True)

        # Keep the most important messages
        self.conversation_history = [msg for msg, _ in scored_messages[:max_messages]]
        # Sort by timestamp to maintain chronological order
        self.conversation_history.sort(key=lambda x: x.timestamp)

    def get_recent_context(self, max_chars: int = 4000) -> str:
        """Get recent conversation context for model input."""
        if not self.conversation_history:
            return ""

        context_parts = []
        total_chars = 0

        # Work backwards from most recent messages
        for message in reversed(self.conversation_history):
            message_text = f"{message.role}: {message.content}\n"
            if total_chars + len(message_text) > max_chars:
                break
            context_parts.insert(0, message_text)
            total_chars += len(message_text)

        return "".join(context_parts)

    def to_dict(self) -> dict[str, Any]:
        """Convert context to dictionary for JSON serialization."""
        return {
            "project_id": self.project_id,
            "conversation_history": [
                msg.to_dict() for msg in self.conversation_history
            ],
            "analysis_cache": self.analysis_cache,
            "last_accessed": self.last_accessed.isoformat(),
            "metadata": self.metadata,
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ProjectContext":
        """Create context from dictionary."""
        context = cls(
            project_id=data["project_id"],
            analysis_cache=data.get("analysis_cache", {}),
            last_accessed=datetime.fromisoformat(data["last_accessed"]),
            metadata=data.get("metadata", {}),
        )

        # Reconstruct conversation history
        for msg_data in data.get("conversation_history", []):
            context.conversation_history.append(ConversationMessage.from_dict(msg_data))

        return context


class ProjectContextManager:
    """
    Manages conversation contexts for multiple projects.

    This class provides thread-safe context management with automatic
    persistence and intelligent memory management.
    """

    def __init__(self, max_active_contexts: int = 10):
        """
        Initialize the context manager.

        Args:
            max_active_contexts: Maximum number of contexts to keep in memory
        """
        self.max_active_contexts = max_active_contexts
        self._contexts: OrderedDict[str, ProjectContext] = OrderedDict()
        self._lock = threading.RLock()

        # Ensure contexts directory exists
        self.contexts_dir = settings.data_dir / "contexts"
        self.contexts_dir.mkdir(parents=True, exist_ok=True)

        logger.info(
            "ProjectContextManager initialized", max_active_contexts=max_active_contexts
        )

    def get_context(self, project_id: str) -> ProjectContext:
        """
        Get or create context for a project.

        Args:
            project_id: The project identifier

        Returns:
            ProjectContext for the project
        """
        with self._lock:
            # Check if context is already in memory
            if project_id in self._contexts:
                context = self._contexts[project_id]
                # Move to end (most recently used)
                self._contexts.move_to_end(project_id)
                context.last_accessed = datetime.now()
                return context

            # Try to load from disk
            context = self._load_context(project_id)
            if context is None:
                # Create new context
                context = ProjectContext(project_id=project_id)
                logger.info("Created new context", project_id=project_id)
            else:
                logger.info("Loaded context from disk", project_id=project_id)

            # Add to memory cache
            self._contexts[project_id] = context

            # Manage memory by evicting old contexts
            self._manage_memory()

            return context

    def save_context(self, project_id: str) -> None:
        """
        Save context to disk.

        Args:
            project_id: The project identifier
        """
        with self._lock:
            context = self._contexts.get(project_id)
            if context is None:
                logger.warning(
                    "Attempted to save non-existent context", project_id=project_id
                )
                return

            self._save_context_to_disk(context)

    def save_all_contexts(self) -> None:
        """Save all active contexts to disk."""
        with self._lock:
            for project_id, context in self._contexts.items():
                try:
                    self._save_context_to_disk(context)
                except Exception as e:
                    logger.error(
                        "Failed to save context", project_id=project_id, error=str(e)
                    )

    def add_message(
        self, project_id: str, role: str, content: str, metadata: dict[str, Any] = None
    ) -> None:
        """
        Add a message to project's conversation history.

        Args:
            project_id: The project identifier
            role: Message role ('user' or 'assistant')
            content: Message content
            metadata: Optional metadata dictionary
        """
        context = self.get_context(project_id)
        context.add_message(role, content, metadata)

        # Auto-save after adding message
        self.save_context(project_id)

        logger.debug("Message added to context", project_id=project_id, role=role)

    def get_conversation_context(self, project_id: str, max_chars: int = 4000) -> str:
        """
        Get recent conversation context for model input.

        Args:
            project_id: The project identifier
            max_chars: Maximum characters to include

        Returns:
            Formatted conversation context
        """
        context = self.get_context(project_id)
        return context.get_recent_context(max_chars)

    def clear_context(self, project_id: str) -> None:
        """
        Clear conversation history for a project.

        Args:
            project_id: The project identifier
        """
        with self._lock:
            context = self.get_context(project_id)
            context.conversation_history.clear()
            context.analysis_cache.clear()

            self.save_context(project_id)

            logger.info("Context cleared", project_id=project_id)

    def _load_context(self, project_id: str) -> ProjectContext | None:
        """Load context from disk."""
        context_file = self.contexts_dir / f"{project_id}.json"

        if not context_file.exists():
            return None

        try:
            with context_file.open("r", encoding="utf-8") as f:
                data = json.load(f)

            return ProjectContext.from_dict(data)

        except (json.JSONDecodeError, KeyError, ValueError) as e:
            logger.error(
                "Failed to load context from disk", project_id=project_id, error=str(e)
            )
            return None

    @retry_with_backoff(max_attempts=3)
    def _save_context_to_disk(self, context: ProjectContext) -> None:
        """Save context to disk atomically."""
        context_file = self.contexts_dir / f"{context.project_id}.json"
        temp_file = context_file.with_suffix(".tmp")

        try:
            with temp_file.open("w", encoding="utf-8") as f:
                json.dump(context.to_dict(), f, indent=2, ensure_ascii=False)

            # Atomic move
            temp_file.replace(context_file)

            logger.debug("Context saved to disk", project_id=context.project_id)

        except Exception as e:
            # Clean up temp file on error
            if temp_file.exists():
                temp_file.unlink()
            raise ContextManagerError(f"Failed to save context: {e}") from e

    def _manage_memory(self) -> None:
        """Manage memory by evicting least recently used contexts."""
        while len(self._contexts) > self.max_active_contexts:
            # Remove least recently used context (first item)
            project_id, context = self._contexts.popitem(last=False)

            # Save before evicting
            try:
                self._save_context_to_disk(context)
            except Exception as e:
                logger.error(
                    "Failed to save context during eviction",
                    project_id=project_id,
                    error=str(e),
                )

            logger.debug("Context evicted from memory", project_id=project_id)


# Global context manager instance
_context_manager_instance: ProjectContextManager | None = None
_context_manager_lock = threading.Lock()


def get_context_manager() -> ProjectContextManager:
    """
    Get the global context manager instance.

    Returns:
        ProjectContextManager: The global instance
    """
    global _context_manager_instance

    if _context_manager_instance is None:
        with _context_manager_lock:
            if _context_manager_instance is None:
                _context_manager_instance = ProjectContextManager()

    return _context_manager_instance
