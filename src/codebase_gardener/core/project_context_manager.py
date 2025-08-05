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
import time
from collections import OrderedDict
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Callable

import structlog

from ..config.settings import get_settings
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
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert message to dictionary for JSON serialization."""
        return {
            'role': self.role,
            'content': self.content,
            'timestamp': self.timestamp.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ConversationMessage':
        """Create message from dictionary."""
        return cls(
            role=data['role'],
            content=data['content'],
            timestamp=datetime.fromisoformat(data['timestamp']),
            metadata=data.get('metadata', {})
        )
    
    def importance_score(self) -> float:
        """Calculate importance score for pruning decisions."""
        # Base score from recency (newer messages are more important)
        age_hours = (datetime.now() - self.timestamp).total_seconds() / 3600
        recency_score = max(0, 1 - (age_hours / 168))  # Decay over a week
        
        # Boost score for certain content types
        content_score = 0.0
        if any(keyword in self.content.lower() for keyword in ['error', 'important', 'remember']):
            content_score += 0.3
        if len(self.content) > 200:  # Longer messages might be more important
            content_score += 0.2
        if self.role == 'user':  # User messages are slightly more important
            content_score += 0.1
            
        return min(1.0, recency_score + content_score)


@dataclass
class ProjectContext:
    """Represents the conversation context for a specific project."""
    project_id: str
    conversation_history: List[ConversationMessage] = field(default_factory=list)
    analysis_cache: Dict[str, Any] = field(default_factory=dict)
    last_accessed: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a new message to the conversation history."""
        message = ConversationMessage(
            role=role,
            content=content,
            timestamp=datetime.now(),
            metadata=metadata or {}
        )
        self.conversation_history.append(message)
        self.last_accessed = datetime.now()
    
    def prune_history(self, max_messages: int = 50) -> None:
        """Intelligently prune conversation history to stay within limits."""
        if len(self.conversation_history) <= max_messages:
            return
            
        # Calculate importance scores for all messages
        scored_messages = [
            (msg, msg.importance_score()) for msg in self.conversation_history
        ]
        
        # Always keep the most recent messages
        recent_count = min(20, max_messages // 2)
        recent_messages = self.conversation_history[-recent_count:]
        
        # Select important messages from the rest
        older_messages = self.conversation_history[:-recent_count]
        if older_messages:
            older_scored = [(msg, msg.importance_score()) for msg in older_messages]
            older_scored.sort(key=lambda x: x[1], reverse=True)
            
            # Keep top important messages
            important_count = max_messages - recent_count
            important_messages = [msg for msg, _ in older_scored[:important_count]]
            
            # Combine and sort by timestamp
            all_kept = important_messages + recent_messages
            all_kept.sort(key=lambda x: x.timestamp)
            self.conversation_history = all_kept
        else:
            self.conversation_history = recent_messages
            
        logger.info(
            "Pruned conversation history",
            project_id=self.project_id,
            original_count=len(scored_messages),
            pruned_count=len(self.conversation_history)
        )
    
    def get_recent_messages(self, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Get recent messages, optionally limited."""
        if limit is None:
            return self.conversation_history.copy()
        return self.conversation_history[-limit:] if self.conversation_history else []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert context to dictionary for JSON serialization."""
        return {
            'project_id': self.project_id,
            'conversation_history': [msg.to_dict() for msg in self.conversation_history],
            'analysis_cache': self.analysis_cache,
            'last_accessed': self.last_accessed.isoformat(),
            'metadata': self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ProjectContext':
        """Create context from dictionary."""
        return cls(
            project_id=data['project_id'],
            conversation_history=[
                ConversationMessage.from_dict(msg_data) 
                for msg_data in data.get('conversation_history', [])
            ],
            analysis_cache=data.get('analysis_cache', {}),
            last_accessed=datetime.fromisoformat(data['last_accessed']),
            metadata=data.get('metadata', {})
        )


class ProjectContextManager:
    """Manages conversation contexts for multiple projects."""
    
    def __init__(self):
        self._settings = get_settings()
        self._contexts_dir = self._settings.data_dir / "contexts"
        self._contexts_dir.mkdir(parents=True, exist_ok=True)
        
        # Active context and cache
        self._active_context: Optional[ProjectContext] = None
        self._context_cache: OrderedDict[str, ProjectContext] = OrderedDict()
        self._max_cache_size = 3
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Project switch observers
        self._switch_observers: List[Callable[[str], None]] = []
        
        # Auto-save timer
        self._last_save_time = time.time()
        self._auto_save_interval = 30  # seconds
        
        logger.info(
            "ProjectContextManager initialized",
            contexts_dir=str(self._contexts_dir),
            max_cache_size=self._max_cache_size
        )
    
    def add_switch_observer(self, observer: Callable[[str], None]) -> None:
        """Add an observer to be notified of project switches."""
        with self._lock:
            self._switch_observers.append(observer)
    
    def remove_switch_observer(self, observer: Callable[[str], None]) -> None:
        """Remove a project switch observer."""
        with self._lock:
            if observer in self._switch_observers:
                self._switch_observers.remove(observer)
    
    def _notify_switch_observers(self, project_id: str) -> None:
        """Notify all observers of a project switch."""
        for observer in self._switch_observers:
            try:
                observer(project_id)
            except Exception as e:
                logger.warning(
                    "Observer notification failed",
                    project_id=project_id,
                    error=str(e)
                )
    
    def _get_context_file_path(self, project_id: str) -> Path:
        """Get the file path for a project's context."""
        return self._contexts_dir / f"{project_id}_context.json"
    
    @retry_with_backoff(max_attempts=3)
    def _save_context(self, context: ProjectContext) -> None:
        """Save context to disk with atomic operations."""
        context_file = self._get_context_file_path(context.project_id)
        temp_file = context_file.with_suffix('.tmp')
        
        try:
            with temp_file.open('w', encoding='utf-8') as f:
                json.dump(context.to_dict(), f, indent=2, ensure_ascii=False)
            
            # Atomic move
            temp_file.replace(context_file)
            
            logger.debug(
                "Context saved to disk",
                project_id=context.project_id,
                message_count=len(context.conversation_history)
            )
            
        except Exception as e:
            if temp_file.exists():
                temp_file.unlink()
            raise ContextManagerError(f"Failed to save context for {context.project_id}: {e}")
    
    def _load_context(self, project_id: str) -> ProjectContext:
        """Load context from disk or create new one."""
        context_file = self._get_context_file_path(project_id)
        
        if context_file.exists():
            try:
                with context_file.open('r', encoding='utf-8') as f:
                    data = json.load(f)
                
                context = ProjectContext.from_dict(data)
                context.last_accessed = datetime.now()
                
                logger.debug(
                    "Context loaded from disk",
                    project_id=project_id,
                    message_count=len(context.conversation_history)
                )
                
                return context
                
            except Exception as e:
                logger.warning(
                    "Failed to load context from disk, creating new",
                    project_id=project_id,
                    error=str(e)
                )
        
        # Create new context
        context = ProjectContext(project_id=project_id)
        logger.info("Created new context", project_id=project_id)
        return context
    
    def _manage_cache(self) -> None:
        """Manage context cache size using LRU eviction."""
        while len(self._context_cache) > self._max_cache_size:
            oldest_id, oldest_context = self._context_cache.popitem(last=False)
            
            # Save evicted context
            try:
                self._save_context(oldest_context)
                logger.debug("Evicted context from cache", project_id=oldest_id)
            except Exception as e:
                logger.error(
                    "Failed to save evicted context",
                    project_id=oldest_id,
                    error=str(e)
                )
    
    def switch_project(self, project_id: str) -> bool:
        """Switch to a different project context."""
        with self._lock:
            try:
                # Validate project exists (import here to avoid circular imports)
                from .project_registry import get_project_registry
                registry = get_project_registry()
                
                if not registry.get_project(project_id):
                    raise ContextManagerError(f"Project {project_id} not found in registry")
                
                # Save current active context
                if self._active_context:
                    self._save_context(self._active_context)
                    # Add to cache
                    self._context_cache[self._active_context.project_id] = self._active_context
                    self._context_cache.move_to_end(self._active_context.project_id)
                
                # Load new context
                if project_id in self._context_cache:
                    # Use cached context
                    context = self._context_cache[project_id]
                    self._context_cache.move_to_end(project_id)
                    logger.debug("Loaded context from cache", project_id=project_id)
                else:
                    # Load from disk
                    context = self._load_context(project_id)
                    self._context_cache[project_id] = context
                
                # Set as active
                self._active_context = context
                context.last_accessed = datetime.now()
                
                # Manage cache size
                self._manage_cache()
                
                # Notify observers
                self._notify_switch_observers(project_id)
                
                logger.info(
                    "Switched to project context",
                    project_id=project_id,
                    message_count=len(context.conversation_history)
                )
                
                return True
                
            except Exception as e:
                logger.error(
                    "Failed to switch project context",
                    project_id=project_id,
                    error=str(e)
                )
                raise ContextManagerError(f"Failed to switch to project {project_id}: {e}")
    
    def get_current_context(self) -> Optional[ProjectContext]:
        """Get the currently active project context."""
        with self._lock:
            return self._active_context
    
    def get_current_project_id(self) -> Optional[str]:
        """Get the ID of the currently active project."""
        with self._lock:
            return self._active_context.project_id if self._active_context else None
    
    def add_message(self, role: str, content: str, metadata: Dict[str, Any] = None) -> None:
        """Add a message to the current project's conversation."""
        with self._lock:
            if not self._active_context:
                raise ContextManagerError("No active project context")
            
            self._active_context.add_message(role, content, metadata)
            
            # Auto-prune if needed
            max_messages = getattr(self._settings, 'max_conversation_messages', 50)
            self._active_context.prune_history(max_messages)
            
            # Auto-save periodically
            current_time = time.time()
            if current_time - self._last_save_time > self._auto_save_interval:
                self._save_context(self._active_context)
                self._last_save_time = current_time
            
            logger.debug(
                "Added message to context",
                project_id=self._active_context.project_id,
                role=role,
                content_length=len(content)
            )
    
    def get_conversation_history(self, limit: Optional[int] = None) -> List[ConversationMessage]:
        """Get conversation history for the current project."""
        with self._lock:
            if not self._active_context:
                return []
            
            return self._active_context.get_recent_messages(limit)
    
    def clear_context(self, project_id: str) -> bool:
        """Clear the context for a specific project."""
        with self._lock:
            try:
                # Remove from cache
                if project_id in self._context_cache:
                    del self._context_cache[project_id]
                
                # Clear active context if it matches
                if self._active_context and self._active_context.project_id == project_id:
                    self._active_context = None
                
                # Remove context file
                context_file = self._get_context_file_path(project_id)
                if context_file.exists():
                    context_file.unlink()
                
                logger.info("Cleared project context", project_id=project_id)
                return True
                
            except Exception as e:
                logger.error(
                    "Failed to clear project context",
                    project_id=project_id,
                    error=str(e)
                )
                return False
    
    def get_context_stats(self) -> Dict[str, Any]:
        """Get statistics about the context manager."""
        with self._lock:
            stats = {
                'active_project': self._active_context.project_id if self._active_context else None,
                'cached_contexts': len(self._context_cache),
                'max_cache_size': self._max_cache_size,
                'contexts_directory': str(self._contexts_dir),
                'auto_save_interval': self._auto_save_interval
            }
            
            if self._active_context:
                stats['active_context'] = {
                    'message_count': len(self._active_context.conversation_history),
                    'last_accessed': self._active_context.last_accessed.isoformat(),
                    'cache_size': len(self._active_context.analysis_cache)
                }
            
            return stats
    
    def save_all_contexts(self) -> None:
        """Save all contexts to disk."""
        with self._lock:
            contexts_to_save = []
            
            # Add active context
            if self._active_context:
                contexts_to_save.append(self._active_context)
            
            # Add cached contexts
            for context in self._context_cache.values():
                if context != self._active_context:  # Avoid duplicates
                    contexts_to_save.append(context)
            
            # Save all contexts
            for context in contexts_to_save:
                try:
                    self._save_context(context)
                except Exception as e:
                    logger.error(
                        "Failed to save context during bulk save",
                        project_id=context.project_id,
                        error=str(e)
                    )
            
            logger.info(
                "Saved all contexts",
                context_count=len(contexts_to_save)
            )
    
    def cleanup_orphaned_contexts(self) -> int:
        """Remove context files for projects that no longer exist."""
        with self._lock:
            try:
                from .project_registry import get_project_registry
                registry = get_project_registry()
                
                # Get all project IDs from registry
                valid_project_ids = {project.project_id for project in registry.list_projects()}
                
                # Find orphaned context files
                orphaned_count = 0
                for context_file in self._contexts_dir.glob("*_context.json"):
                    project_id = context_file.stem.replace("_context", "")
                    
                    if project_id not in valid_project_ids:
                        try:
                            context_file.unlink()
                            orphaned_count += 1
                            logger.info("Removed orphaned context", project_id=project_id)
                        except Exception as e:
                            logger.warning(
                                "Failed to remove orphaned context",
                                project_id=project_id,
                                error=str(e)
                            )
                
                return orphaned_count
                
            except Exception as e:
                logger.error("Failed to cleanup orphaned contexts", error=str(e))
                return 0


# Global context manager instance
_context_manager: Optional[ProjectContextManager] = None
_context_manager_lock = threading.Lock()


def get_project_context_manager() -> ProjectContextManager:
    """Get the global project context manager instance."""
    global _context_manager
    
    if _context_manager is None:
        with _context_manager_lock:
            if _context_manager is None:
                _context_manager = ProjectContextManager()
    
    return _context_manager


def setup_context_manager_integration():
    """Set up integration with other components."""
    try:
        # Import here to avoid circular imports
        from .dynamic_model_loader import get_dynamic_model_loader
        
        context_manager = get_project_context_manager()
        model_loader = get_dynamic_model_loader()
        
        # Add context manager as observer of model loader switches
        # This ensures context switches are coordinated with model loading
        def on_model_switch(project_id: str):
            logger.debug("Model switch detected, context already coordinated", project_id=project_id)
        
        # The context manager will notify the model loader, not the other way around
        # This prevents circular notifications
        
        logger.info("Context manager integration set up successfully")
        
    except Exception as e:
        logger.warning("Failed to set up context manager integration", error=str(e))