"""
Logging Manager for Codebase Gardener MVP

This module provides structured logging, log management, and diagnostic tools
for production operational monitoring.
"""

import json
import logging
import logging.handlers
import os
import sys
import threading
import traceback
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any

import structlog

# Configure structlog for consistent structured logging
structlog.configure(
    processors=[
        structlog.stdlib.filter_by_level,
        structlog.stdlib.add_logger_name,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer()
    ],
    context_class=dict,
    logger_factory=structlog.stdlib.LoggerFactory(),
    wrapper_class=structlog.stdlib.BoundLogger,
    cache_logger_on_first_use=True,
)

logger = structlog.get_logger(__name__)


class LogLevel:
    """Log level constants."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LoggingManager:
    """Comprehensive logging management and diagnostics."""

    def __init__(self, log_dir: Path, app_name: str = "codebase_gardener"):
        """Initialize logging manager."""
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        self.app_name = app_name
        self.log_files = {
            'main': self.log_dir / f"{app_name}.log",
            'error': self.log_dir / f"{app_name}_error.log",
            'performance': self.log_dir / f"{app_name}_performance.log",
            'audit': self.log_dir / f"{app_name}_audit.log"
        }

        # Logging configuration
        self.max_log_size = 10 * 1024 * 1024  # 10MB
        self.backup_count = 5
        self.log_retention_days = 30

        # Performance tracking
        self.performance_metrics = {}
        self._lock = threading.RLock()

        # Initialize loggers
        self._setup_loggers()

        logger.info("Logging manager initialized",
                   log_dir=str(self.log_dir),
                   app_name=app_name)

    def _setup_loggers(self):
        """Set up structured logging with rotation."""
        # Main application logger
        main_logger = logging.getLogger(self.app_name)
        main_logger.setLevel(logging.INFO)

        # Main log file with rotation
        main_handler = logging.handlers.RotatingFileHandler(
            self.log_files['main'],
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        main_handler.setLevel(logging.INFO)

        # Error log file with rotation
        error_handler = logging.handlers.RotatingFileHandler(
            self.log_files['error'],
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        error_handler.setLevel(logging.ERROR)

        # Performance log file
        performance_handler = logging.handlers.RotatingFileHandler(
            self.log_files['performance'],
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        performance_handler.setLevel(logging.INFO)

        # Audit log file
        audit_handler = logging.handlers.RotatingFileHandler(
            self.log_files['audit'],
            maxBytes=self.max_log_size,
            backupCount=self.backup_count
        )
        audit_handler.setLevel(logging.INFO)

        # JSON formatter for structured logging
        json_formatter = logging.Formatter(
            '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
            '"logger": "%(name)s", "message": "%(message)s", '
            '"module": "%(module)s", "function": "%(funcName)s", "line": %(lineno)d}'
        )

        # Set formatters
        main_handler.setFormatter(json_formatter)
        error_handler.setFormatter(json_formatter)
        performance_handler.setFormatter(json_formatter)
        audit_handler.setFormatter(json_formatter)

        # Add handlers to loggers
        main_logger.addHandler(main_handler)
        main_logger.addHandler(error_handler)

        # Console handler for development
        if os.getenv('CODEBASE_GARDENER_DEBUG'):
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setLevel(logging.DEBUG)
            console_formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            console_handler.setFormatter(console_formatter)
            main_logger.addHandler(console_handler)

        # Store handlers for later use
        self.handlers = {
            'main': main_handler,
            'error': error_handler,
            'performance': performance_handler,
            'audit': audit_handler
        }

    def log_performance_metric(self, operation: str, duration: float,
                             metadata: dict[str, Any] | None = None):
        """Log a performance metric."""
        try:
            with self._lock:
                timestamp = datetime.now()

                # Store in memory for quick access
                if operation not in self.performance_metrics:
                    self.performance_metrics[operation] = []

                metric_data = {
                    'timestamp': timestamp.isoformat(),
                    'operation': operation,
                    'duration': duration,
                    'metadata': metadata or {}
                }

                self.performance_metrics[operation].append(metric_data)

                # Keep only recent metrics (last 1000 per operation)
                if len(self.performance_metrics[operation]) > 1000:
                    self.performance_metrics[operation] = self.performance_metrics[operation][-1000:]

                # Log to performance file
                performance_logger = logging.getLogger(f"{self.app_name}.performance")
                performance_logger.addHandler(self.handlers['performance'])
                performance_logger.info(json.dumps(metric_data))

        except Exception as e:
            logger.error(f"Failed to log performance metric: {e}",
                        operation=operation, duration=duration)

    def log_audit_event(self, event_type: str, user: str, action: str,
                       resource: str, metadata: dict[str, Any] | None = None):
        """Log an audit event."""
        try:
            audit_data = {
                'timestamp': datetime.now().isoformat(),
                'event_type': event_type,
                'user': user,
                'action': action,
                'resource': resource,
                'metadata': metadata or {}
            }

            # Log to audit file
            audit_logger = logging.getLogger(f"{self.app_name}.audit")
            audit_logger.addHandler(self.handlers['audit'])
            audit_logger.info(json.dumps(audit_data))

        except Exception as e:
            logger.error(f"Failed to log audit event: {e}",
                        event_type=event_type, action=action)

    def log_error_with_context(self, error: Exception, context: dict[str, Any]):
        """Log an error with full context and stack trace."""
        try:
            error_data = {
                'timestamp': datetime.now().isoformat(),
                'error_type': type(error).__name__,
                'error_message': str(error),
                'stack_trace': traceback.format_exc(),
                'context': context
            }

            # Log to main and error logs
            error_logger = logging.getLogger(f"{self.app_name}.error")
            error_logger.addHandler(self.handlers['error'])
            error_logger.error(json.dumps(error_data))

        except Exception as e:
            # Fallback logging if structured logging fails
            print(f"Critical logging failure: {e}", file=sys.stderr)
            print(f"Original error: {error}", file=sys.stderr)

    def get_performance_summary(self, operation: str | None = None,
                              hours: int = 24) -> dict[str, Any]:
        """Get performance metrics summary."""
        try:
            with self._lock:
                cutoff_time = datetime.now() - timedelta(hours=hours)
                summary = {}

                operations_to_analyze = [operation] if operation else list(self.performance_metrics.keys())

                for op in operations_to_analyze:
                    if op not in self.performance_metrics:
                        continue

                    # Filter recent metrics
                    recent_metrics = [
                        m for m in self.performance_metrics[op]
                        if datetime.fromisoformat(m['timestamp']) > cutoff_time
                    ]

                    if not recent_metrics:
                        continue

                    durations = [m['duration'] for m in recent_metrics]

                    summary[op] = {
                        'count': len(recent_metrics),
                        'avg_duration': sum(durations) / len(durations),
                        'min_duration': min(durations),
                        'max_duration': max(durations),
                        'total_duration': sum(durations),
                        'recent_metrics': recent_metrics[-5:]  # Last 5 metrics
                    }

                return {
                    'timestamp': datetime.now().isoformat(),
                    'hours_analyzed': hours,
                    'operations': summary,
                    'total_operations': len(summary)
                }

        except Exception as e:
            logger.error(f"Failed to get performance summary: {e}")
            return {'error': str(e)}

    def search_logs(self, log_type: str = 'main',
                   search_term: str | None = None,
                   level: str | None = None,
                   hours: int = 24,
                   max_results: int = 100) -> list[dict[str, Any]]:
        """Search through log files."""
        try:
            if log_type not in self.log_files:
                raise ValueError(f"Invalid log type: {log_type}")

            log_file = self.log_files[log_type]
            if not log_file.exists():
                return []

            cutoff_time = datetime.now() - timedelta(hours=hours)
            results = []

            with open(log_file) as f:
                for line in f:
                    try:
                        log_entry = json.loads(line.strip())

                        # Check timestamp
                        log_time = datetime.fromisoformat(log_entry.get('timestamp', ''))
                        if log_time < cutoff_time:
                            continue

                        # Check level filter
                        if level and log_entry.get('level') != level:
                            continue

                        # Check search term
                        if search_term:
                            log_text = json.dumps(log_entry).lower()
                            if search_term.lower() not in log_text:
                                continue

                        results.append(log_entry)

                        if len(results) >= max_results:
                            break

                    except (json.JSONDecodeError, ValueError):
                        # Skip malformed log entries
                        continue

            return results[:max_results]

        except Exception as e:
            logger.error(f"Failed to search logs: {e}",
                        log_type=log_type, search_term=search_term)
            return []

    def get_log_statistics(self) -> dict[str, Any]:
        """Get statistics about log files."""
        try:
            stats = {}

            for log_type, log_file in self.log_files.items():
                if log_file.exists():
                    file_stat = log_file.stat()

                    # Count lines (approximate)
                    line_count = 0
                    try:
                        with open(log_file) as f:
                            line_count = sum(1 for _ in f)
                    except Exception:
                        line_count = 0

                    stats[log_type] = {
                        'file_path': str(log_file),
                        'size_bytes': file_stat.st_size,
                        'size_mb': file_stat.st_size / (1024 * 1024),
                        'modified': datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
                        'line_count': line_count,
                        'exists': True
                    }
                else:
                    stats[log_type] = {
                        'file_path': str(log_file),
                        'exists': False
                    }

            return {
                'timestamp': datetime.now().isoformat(),
                'log_dir': str(self.log_dir),
                'retention_days': self.log_retention_days,
                'max_size_mb': self.max_log_size / (1024 * 1024),
                'backup_count': self.backup_count,
                'files': stats
            }

        except Exception as e:
            logger.error(f"Failed to get log statistics: {e}")
            return {'error': str(e)}

    def cleanup_old_logs(self):
        """Clean up old log files."""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.log_retention_days)
            cleaned_files = []

            # Clean up rotated log files
            for log_type, log_file in self.log_files.items():
                log_dir = log_file.parent
                log_name = log_file.stem

                # Find rotated log files (e.g., app.log.1, app.log.2, etc.)
                for rotated_file in log_dir.glob(f"{log_name}.log.*"):
                    try:
                        if rotated_file.stat().st_mtime < cutoff_time.timestamp():
                            rotated_file.unlink()
                            cleaned_files.append(str(rotated_file))
                    except Exception as e:
                        logger.warning(f"Failed to clean up {rotated_file}: {e}")

            logger.info("Log cleanup completed",
                       cleaned_files=len(cleaned_files),
                       retention_days=self.log_retention_days)

            return cleaned_files

        except Exception as e:
            logger.error(f"Failed to cleanup old logs: {e}")
            return []

    def export_logs(self, log_type: str, output_file: Path,
                   hours: int = 24, format: str = 'json') -> bool:
        """Export logs to a file."""
        try:
            if log_type not in self.log_files:
                raise ValueError(f"Invalid log type: {log_type}")

            log_entries = self.search_logs(log_type=log_type, hours=hours, max_results=10000)

            with open(output_file, 'w') as f:
                if format == 'json':
                    json.dump(log_entries, f, indent=2)
                elif format == 'csv':
                    # Simple CSV export
                    if log_entries:
                        headers = list(log_entries[0].keys())
                        f.write(','.join(headers) + '\n')

                        for entry in log_entries:
                            values = [str(entry.get(h, '')) for h in headers]
                            f.write(','.join(values) + '\n')
                else:
                    # Plain text format
                    for entry in log_entries:
                        f.write(f"{entry.get('timestamp', '')} - {entry.get('level', '')} - {entry.get('message', '')}\n")

            logger.info("Logs exported",
                       log_type=log_type,
                       output_file=str(output_file),
                       entries_exported=len(log_entries))

            return True

        except Exception as e:
            logger.error(f"Failed to export logs: {e}",
                        log_type=log_type, output_file=str(output_file))
            return False

    def get_diagnostic_info(self) -> dict[str, Any]:
        """Get comprehensive diagnostic information."""
        try:
            return {
                'timestamp': datetime.now().isoformat(),
                'logging_manager': {
                    'log_dir': str(self.log_dir),
                    'app_name': self.app_name,
                    'max_log_size_mb': self.max_log_size / (1024 * 1024),
                    'backup_count': self.backup_count,
                    'retention_days': self.log_retention_days
                },
                'log_statistics': self.get_log_statistics(),
                'performance_summary': self.get_performance_summary(hours=1),  # Last hour
                'recent_errors': self.search_logs('error', hours=1, max_results=10),
                'system_info': {
                    'python_version': sys.version,
                    'platform': sys.platform,
                    'executable': sys.executable
                }
            }

        except Exception as e:
            logger.error(f"Failed to get diagnostic info: {e}")
            return {'error': str(e)}


def get_logging_manager(log_dir: Path, app_name: str = "codebase_gardener") -> LoggingManager:
    """Get or create logging manager instance."""
    if not hasattr(get_logging_manager, '_instance'):
        get_logging_manager._instance = LoggingManager(log_dir, app_name)
    return get_logging_manager._instance
