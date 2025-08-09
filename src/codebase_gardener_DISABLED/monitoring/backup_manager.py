"""
Backup Manager for Codebase Gardener MVP

This module provides automated backup and recovery procedures for
user data, configurations, and system state.
"""

import hashlib
import json
import tarfile
import threading
import time
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from pathlib import Path
from typing import Any

import structlog

logger = structlog.get_logger(__name__)


class BackupType(Enum):
    """Types of backups."""
    FULL = "full"
    INCREMENTAL = "incremental"
    CONFIGURATION = "configuration"
    USER_DATA = "user_data"


class BackupStatus(Enum):
    """Backup operation status."""
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    RESTORED = "restored"


@dataclass
class BackupInfo:
    """Information about a backup."""
    id: str
    timestamp: datetime
    backup_type: BackupType
    status: BackupStatus
    file_path: Path
    size_bytes: int
    checksum: str
    source_paths: list[str]
    metadata: dict[str, Any]
    duration_seconds: float | None = None
    error_message: str | None = None


class BackupManager:
    """Automated backup and recovery management."""

    def __init__(self, data_dir: Path, backup_dir: Path):
        """Initialize backup manager."""
        self.data_dir = Path(data_dir)
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)

        # Backup configuration
        self.max_backups = {
            BackupType.FULL: 7,      # Keep 7 full backups
            BackupType.INCREMENTAL: 30,  # Keep 30 incremental backups
            BackupType.CONFIGURATION: 10,  # Keep 10 config backups
            BackupType.USER_DATA: 14     # Keep 14 user data backups
        }

        self.backup_schedule = {
            BackupType.FULL: timedelta(days=7),      # Weekly full backups
            BackupType.INCREMENTAL: timedelta(hours=6),  # Every 6 hours
            BackupType.CONFIGURATION: timedelta(days=1),  # Daily config backups
            BackupType.USER_DATA: timedelta(days=1)      # Daily user data backups
        }

        # Backup registry
        self.backup_registry_file = self.backup_dir / "backup_registry.json"
        self.backup_registry: list[BackupInfo] = []
        self._load_backup_registry()

        # Backup state
        self._backup_lock = threading.RLock()
        self._last_backup_times = {}

        # Critical paths to backup
        self.critical_paths = {
            'projects': self.data_dir / 'projects',
            'contexts': self.data_dir / 'contexts',
            'models': self.data_dir / 'models',
            'vector_stores': self.data_dir / 'vector_stores',
            'settings': self.data_dir / 'settings',
            'logs': self.data_dir / 'logs'
        }

        logger.info("Backup manager initialized",
                   data_dir=str(self.data_dir),
                   backup_dir=str(self.backup_dir))

    def _load_backup_registry(self):
        """Load backup registry from disk."""
        try:
            if self.backup_registry_file.exists():
                with open(self.backup_registry_file) as f:
                    registry_data = json.load(f)

                self.backup_registry = []
                for item in registry_data:
                    backup_info = BackupInfo(
                        id=item['id'],
                        timestamp=datetime.fromisoformat(item['timestamp']),
                        backup_type=BackupType(item['backup_type']),
                        status=BackupStatus(item['status']),
                        file_path=Path(item['file_path']),
                        size_bytes=item['size_bytes'],
                        checksum=item['checksum'],
                        source_paths=item['source_paths'],
                        metadata=item['metadata'],
                        duration_seconds=item.get('duration_seconds'),
                        error_message=item.get('error_message')
                    )
                    self.backup_registry.append(backup_info)

                logger.info("Backup registry loaded",
                           backup_count=len(self.backup_registry))
            else:
                logger.info("No existing backup registry found")

        except Exception as e:
            logger.error(f"Failed to load backup registry: {e}")
            self.backup_registry = []

    def _save_backup_registry(self):
        """Save backup registry to disk."""
        try:
            registry_data = []
            for backup_info in self.backup_registry:
                item = asdict(backup_info)
                item['timestamp'] = backup_info.timestamp.isoformat()
                item['backup_type'] = backup_info.backup_type.value
                item['status'] = backup_info.status.value
                item['file_path'] = str(backup_info.file_path)
                registry_data.append(item)

            with open(self.backup_registry_file, 'w') as f:
                json.dump(registry_data, f, indent=2)

        except Exception as e:
            logger.error(f"Failed to save backup registry: {e}")

    def _generate_backup_id(self, backup_type: BackupType) -> str:
        """Generate unique backup ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{backup_type.value}_{timestamp}"

    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA-256 checksum of a file."""
        try:
            sha256_hash = hashlib.sha256()
            with open(file_path, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    sha256_hash.update(chunk)
            return sha256_hash.hexdigest()
        except Exception as e:
            logger.error(f"Failed to calculate checksum: {e}", file_path=str(file_path))
            return ""

    def _get_changed_files(self, source_paths: list[Path],
                          since: datetime) -> list[Path]:
        """Get files that have changed since the specified time."""
        changed_files = []

        for source_path in source_paths:
            if not source_path.exists():
                continue

            if source_path.is_file():
                if datetime.fromtimestamp(source_path.stat().st_mtime) > since:
                    changed_files.append(source_path)
            else:
                # Recursively check directory
                for file_path in source_path.rglob('*'):
                    if file_path.is_file():
                        if datetime.fromtimestamp(file_path.stat().st_mtime) > since:
                            changed_files.append(file_path)

        return changed_files

    def create_backup(self, backup_type: BackupType,
                     source_paths: list[Path] | None = None,
                     metadata: dict[str, Any] | None = None) -> BackupInfo | None:
        """Create a backup of specified type."""
        with self._backup_lock:
            start_time = time.time()
            backup_id = self._generate_backup_id(backup_type)

            try:
                # Determine source paths
                if source_paths is None:
                    if backup_type == BackupType.FULL:
                        source_paths = list(self.critical_paths.values())
                    elif backup_type == BackupType.CONFIGURATION:
                        source_paths = [self.critical_paths['settings']]
                    elif backup_type == BackupType.USER_DATA:
                        source_paths = [
                            self.critical_paths['projects'],
                            self.critical_paths['contexts']
                        ]
                    else:  # INCREMENTAL
                        source_paths = list(self.critical_paths.values())

                # Filter existing paths
                existing_paths = [p for p in source_paths if p.exists()]
                if not existing_paths:
                    logger.warning("No source paths exist for backup",
                                 backup_type=backup_type.value)
                    return None

                # For incremental backups, only backup changed files
                if backup_type == BackupType.INCREMENTAL:
                    last_backup_time = self._last_backup_times.get(backup_type)
                    if last_backup_time:
                        changed_files = self._get_changed_files(existing_paths, last_backup_time)
                        if not changed_files:
                            logger.info("No changes detected for incremental backup")
                            return None

                # Create backup file
                backup_filename = f"{backup_id}.tar.gz"
                backup_file_path = self.backup_dir / backup_filename

                # Create backup info
                backup_info = BackupInfo(
                    id=backup_id,
                    timestamp=datetime.now(),
                    backup_type=backup_type,
                    status=BackupStatus.RUNNING,
                    file_path=backup_file_path,
                    size_bytes=0,
                    checksum="",
                    source_paths=[str(p) for p in existing_paths],
                    metadata=metadata or {}
                )

                # Add to registry
                self.backup_registry.append(backup_info)
                self._save_backup_registry()

                logger.info("Starting backup",
                           backup_id=backup_id,
                           backup_type=backup_type.value,
                           source_count=len(existing_paths))

                # Create tar.gz archive
                with tarfile.open(backup_file_path, 'w:gz') as tar:
                    for source_path in existing_paths:
                        if source_path.exists():
                            # Add with relative path to maintain structure
                            arcname = source_path.relative_to(self.data_dir)
                            tar.add(source_path, arcname=arcname)

                # Calculate file size and checksum
                file_stat = backup_file_path.stat()
                backup_info.size_bytes = file_stat.st_size
                backup_info.checksum = self._calculate_checksum(backup_file_path)
                backup_info.duration_seconds = time.time() - start_time
                backup_info.status = BackupStatus.COMPLETED

                # Update registry
                self._save_backup_registry()

                # Update last backup time
                self._last_backup_times[backup_type] = backup_info.timestamp

                logger.info("Backup completed",
                           backup_id=backup_id,
                           size_mb=backup_info.size_bytes / (1024 * 1024),
                           duration=backup_info.duration_seconds)

                # Cleanup old backups
                self._cleanup_old_backups(backup_type)

                return backup_info

            except Exception as e:
                # Mark backup as failed
                for backup in self.backup_registry:
                    if backup.id == backup_id:
                        backup.status = BackupStatus.FAILED
                        backup.error_message = str(e)
                        backup.duration_seconds = time.time() - start_time
                        break

                self._save_backup_registry()

                logger.error(f"Backup failed: {e}",
                           backup_id=backup_id,
                           backup_type=backup_type.value)

                # Clean up failed backup file
                if backup_file_path.exists():
                    try:
                        backup_file_path.unlink()
                    except Exception:
                        pass

                return None

    def restore_backup(self, backup_id: str,
                      restore_path: Path | None = None) -> bool:
        """Restore from a backup."""
        with self._backup_lock:
            try:
                # Find backup info
                backup_info = None
                for backup in self.backup_registry:
                    if backup.id == backup_id:
                        backup_info = backup
                        break

                if not backup_info:
                    logger.error("Backup not found", backup_id=backup_id)
                    return False

                if not backup_info.file_path.exists():
                    logger.error("Backup file not found",
                               backup_id=backup_id,
                               file_path=str(backup_info.file_path))
                    return False

                # Verify checksum
                current_checksum = self._calculate_checksum(backup_info.file_path)
                if current_checksum != backup_info.checksum:
                    logger.error("Backup file checksum mismatch",
                               backup_id=backup_id,
                               expected=backup_info.checksum,
                               actual=current_checksum)
                    return False

                # Determine restore path
                if restore_path is None:
                    restore_path = self.data_dir
                else:
                    restore_path = Path(restore_path)

                restore_path.mkdir(parents=True, exist_ok=True)

                logger.info("Starting restore",
                           backup_id=backup_id,
                           restore_path=str(restore_path))

                # Extract backup
                with tarfile.open(backup_info.file_path, 'r:gz') as tar:
                    tar.extractall(path=restore_path)

                # Update backup status
                backup_info.status = BackupStatus.RESTORED
                self._save_backup_registry()

                logger.info("Restore completed",
                           backup_id=backup_id,
                           restore_path=str(restore_path))

                return True

            except Exception as e:
                logger.error(f"Restore failed: {e}",
                           backup_id=backup_id)
                return False

    def _cleanup_old_backups(self, backup_type: BackupType):
        """Clean up old backups based on retention policy."""
        try:
            # Get backups of this type, sorted by timestamp (newest first)
            type_backups = [
                b for b in self.backup_registry
                if b.backup_type == backup_type and b.status == BackupStatus.COMPLETED
            ]
            type_backups.sort(key=lambda x: x.timestamp, reverse=True)

            max_backups = self.max_backups.get(backup_type, 10)

            if len(type_backups) > max_backups:
                backups_to_remove = type_backups[max_backups:]

                for backup in backups_to_remove:
                    try:
                        # Remove backup file
                        if backup.file_path.exists():
                            backup.file_path.unlink()

                        # Remove from registry
                        self.backup_registry.remove(backup)

                        logger.info("Old backup removed",
                                   backup_id=backup.id,
                                   backup_type=backup_type.value)

                    except Exception as e:
                        logger.error(f"Failed to remove old backup: {e}",
                                   backup_id=backup.id)

                self._save_backup_registry()

        except Exception as e:
            logger.error(f"Failed to cleanup old backups: {e}",
                        backup_type=backup_type.value)

    def get_backup_status(self) -> dict[str, Any]:
        """Get comprehensive backup status."""
        try:
            status = {
                'timestamp': datetime.now().isoformat(),
                'backup_dir': str(self.backup_dir),
                'total_backups': len(self.backup_registry),
                'backup_types': {},
                'recent_backups': [],
                'disk_usage': {}
            }

            # Analyze by backup type
            for backup_type in BackupType:
                type_backups = [b for b in self.backup_registry if b.backup_type == backup_type]
                completed_backups = [b for b in type_backups if b.status == BackupStatus.COMPLETED]

                status['backup_types'][backup_type.value] = {
                    'total': len(type_backups),
                    'completed': len(completed_backups),
                    'failed': len([b for b in type_backups if b.status == BackupStatus.FAILED]),
                    'last_backup': completed_backups[0].timestamp.isoformat() if completed_backups else None,
                    'next_scheduled': self._get_next_scheduled_backup(backup_type),
                    'retention_count': self.max_backups.get(backup_type, 0)
                }

            # Recent backups (last 10)
            recent_backups = sorted(self.backup_registry, key=lambda x: x.timestamp, reverse=True)[:10]
            status['recent_backups'] = [
                {
                    'id': b.id,
                    'timestamp': b.timestamp.isoformat(),
                    'type': b.backup_type.value,
                    'status': b.status.value,
                    'size_mb': b.size_bytes / (1024 * 1024),
                    'duration': b.duration_seconds
                }
                for b in recent_backups
            ]

            # Disk usage
            total_size = sum(b.size_bytes for b in self.backup_registry if b.status == BackupStatus.COMPLETED)
            status['disk_usage'] = {
                'total_size_bytes': total_size,
                'total_size_mb': total_size / (1024 * 1024),
                'backup_dir_exists': self.backup_dir.exists()
            }

            return status

        except Exception as e:
            logger.error(f"Failed to get backup status: {e}")
            return {'error': str(e)}

    def _get_next_scheduled_backup(self, backup_type: BackupType) -> str | None:
        """Get next scheduled backup time for a backup type."""
        try:
            last_backup_time = self._last_backup_times.get(backup_type)
            if not last_backup_time:
                # Find last completed backup of this type
                type_backups = [
                    b for b in self.backup_registry
                    if b.backup_type == backup_type and b.status == BackupStatus.COMPLETED
                ]
                if type_backups:
                    last_backup_time = max(b.timestamp for b in type_backups)
                else:
                    return "Now (no previous backup)"

            schedule_interval = self.backup_schedule.get(backup_type)
            if schedule_interval:
                next_backup_time = last_backup_time + schedule_interval
                if next_backup_time <= datetime.now():
                    return "Now (overdue)"
                else:
                    return next_backup_time.isoformat()

            return None

        except Exception as e:
            logger.error(f"Failed to calculate next scheduled backup: {e}")
            return None

    def run_scheduled_backups(self) -> list[BackupInfo]:
        """Run any scheduled backups that are due."""
        completed_backups = []

        try:
            for backup_type in BackupType:
                next_scheduled = self._get_next_scheduled_backup(backup_type)

                if next_scheduled and ("Now" in next_scheduled):
                    logger.info("Running scheduled backup", backup_type=backup_type.value)

                    backup_info = self.create_backup(
                        backup_type=backup_type,
                        metadata={'scheduled': True, 'trigger': 'automatic'}
                    )

                    if backup_info:
                        completed_backups.append(backup_info)

            return completed_backups

        except Exception as e:
            logger.error(f"Failed to run scheduled backups: {e}")
            return completed_backups

    def validate_backup(self, backup_id: str) -> dict[str, Any]:
        """Validate a backup's integrity."""
        try:
            # Find backup info
            backup_info = None
            for backup in self.backup_registry:
                if backup.id == backup_id:
                    backup_info = backup
                    break

            if not backup_info:
                return {'valid': False, 'error': 'Backup not found'}

            if not backup_info.file_path.exists():
                return {'valid': False, 'error': 'Backup file not found'}

            # Verify checksum
            current_checksum = self._calculate_checksum(backup_info.file_path)
            checksum_valid = current_checksum == backup_info.checksum

            # Verify tar file integrity
            tar_valid = False
            try:
                with tarfile.open(backup_info.file_path, 'r:gz') as tar:
                    # Try to list contents
                    members = tar.getmembers()
                    tar_valid = len(members) > 0
            except Exception:
                tar_valid = False

            return {
                'valid': checksum_valid and tar_valid,
                'backup_id': backup_id,
                'checksum_valid': checksum_valid,
                'tar_valid': tar_valid,
                'file_exists': backup_info.file_path.exists(),
                'size_bytes': backup_info.size_bytes,
                'timestamp': backup_info.timestamp.isoformat()
            }

        except Exception as e:
            logger.error(f"Failed to validate backup: {e}", backup_id=backup_id)
            return {'valid': False, 'error': str(e)}


def get_backup_manager(data_dir: Path, backup_dir: Path) -> BackupManager:
    """Get or create backup manager instance."""
    if not hasattr(get_backup_manager, '_instance'):
        get_backup_manager._instance = BackupManager(data_dir, backup_dir)
    return get_backup_manager._instance
