# Codebase Gardener - Operations Guide

This guide provides comprehensive operational procedures for monitoring, maintaining, and troubleshooting the Codebase Gardener MVP in production environments.

## Overview

The Codebase Gardener operational monitoring system provides:

- **Enhanced System Health Monitoring** - Production-grade metrics and alerting
- **Comprehensive Logging** - Structured logging with diagnostic tools
- **Automated Backup & Recovery** - Data protection and disaster recovery
- **Operational Dashboard** - Real-time monitoring interface
- **Maintenance Automation** - Scheduled maintenance and operational procedures

## Quick Start

### Starting Operational Monitoring

```bash
# Start the application with operational monitoring
python -m src.codebase_gardener.main serve --enable-monitoring

# Or access the operational dashboard directly
python -c "
from src.codebase_gardener.monitoring import create_operational_dashboard
from pathlib import Path
dashboard = create_operational_dashboard(Path('data'))
dashboard.launch(server_name='0.0.0.0', server_port=7861)
"
```

### Accessing the Dashboard

- **Main Application**: http://localhost:7860
- **Operational Dashboard**: http://localhost:7861
- **System Status**: Available through both interfaces

## System Health Monitoring

### Health Check Commands

```bash
# Quick health check
python -c "
from src.codebase_gardener.monitoring import get_system_health_monitor
monitor = get_system_health_monitor()
health = monitor.comprehensive_health_check()
print(f'Status: {health[\"overall_status\"]}')
print(f'Integration: {health[\"integration_health\"][\"score\"]}%')
"

# Detailed health report
python -c "
from src.codebase_gardener.monitoring import get_system_health_monitor
import json
monitor = get_system_health_monitor()
health = monitor.comprehensive_health_check()
print(json.dumps(health, indent=2, default=str))
"
```

### Health Status Levels

- **🟢 HEALTHY** - All systems operating normally
- **🟡 WARNING** - Some issues detected, system functional
- **🔴 CRITICAL** - Serious issues requiring immediate attention
- **⚪ UNKNOWN** - Status cannot be determined

### Performance Thresholds (Mac Mini M4)

| Metric | Warning | Critical |
|--------|---------|----------|
| CPU Usage | 75% | 90% |
| Memory Usage | 80% | 95% |
| Disk Usage | 85% | 95% |
| Response Time | 3s | 10s |
| Integration Score | 80% | 60% |

## Alerting System

### Alert Levels

- **🔵 INFO** - Informational messages
- **🟡 WARNING** - Issues requiring attention
- **🔴 CRITICAL** - Urgent issues requiring immediate action

### Managing Alerts

```bash
# View recent alerts
python -c "
from src.codebase_gardener.monitoring import get_operational_monitor
from pathlib import Path
monitor = get_operational_monitor(Path('data'))
alerts = monitor.get_alerts(hours=24)
for alert in alerts[:5]:
    print(f'{alert.timestamp}: {alert.level.value} - {alert.message}')
"

# Acknowledge an alert
python -c "
from src.codebase_gardener.monitoring import get_operational_monitor
from pathlib import Path
monitor = get_operational_monitor(Path('data'))
success = monitor.acknowledge_alert('ALERT_ID')
print('Alert acknowledged' if success else 'Failed to acknowledge alert')
"

# Resolve an alert
python -c "
from src.codebase_gardener.monitoring import get_operational_monitor
from pathlib import Path
monitor = get_operational_monitor(Path('data'))
success = monitor.resolve_alert('ALERT_ID')
print('Alert resolved' if success else 'Failed to resolve alert')
"
```

### Alert Thresholds

Alerts are automatically generated when:
- CPU usage exceeds 75% (warning) or 90% (critical)
- Memory usage exceeds 80% (warning) or 95% (critical)
- Disk usage exceeds 85% (warning) or 95% (critical)
- Integration health drops below 80% (warning) or 60% (critical)
- Component failures are detected

## Logging Management

### Log Files

| Log Type | File | Purpose |
|----------|------|---------|
| Main | `codebase_gardener.log` | General application logs |
| Error | `codebase_gardener_error.log` | Errors and exceptions |
| Performance | `codebase_gardener_performance.log` | Performance metrics |
| Audit | `codebase_gardener_audit.log` | User actions and events |

### Log Analysis

```bash
# Search error logs
python -c "
from src.codebase_gardener.monitoring import get_logging_manager
from pathlib import Path
manager = get_logging_manager(Path('data/logs'))
errors = manager.search_logs('error', hours=24, max_results=10)
for error in errors:
    print(f'{error.get(\"timestamp\")}: {error.get(\"message\")}')
"

# Performance summary
python -c "
from src.codebase_gardener.monitoring import get_logging_manager
from pathlib import Path
manager = get_logging_manager(Path('data/logs'))
summary = manager.get_performance_summary(hours=24)
for op, data in summary.get('operations', {}).items():
    print(f'{op}: {data[\"avg_duration\"]:.3f}s avg ({data[\"count\"]} ops)')
"

# Export logs
python -c "
from src.codebase_gardener.monitoring import get_logging_manager
from pathlib import Path
manager = get_logging_manager(Path('data/logs'))
success = manager.export_logs('main', Path('exported_logs.json'), hours=24)
print('Logs exported' if success else 'Export failed')
"
```

### Log Rotation

- **Automatic**: Logs rotate at 10MB with 5 backup files
- **Retention**: 30 days for all log types
- **Manual Cleanup**: Use the maintenance system

## Backup & Recovery

### Backup Types

| Type | Frequency | Content | Retention |
|------|-----------|---------|-----------|
| Full | Weekly | All data and configurations | 7 backups |
| Incremental | 6 hours | Changed files only | 30 backups |
| Configuration | Daily | Settings and configs | 10 backups |
| User Data | Daily | Projects and contexts | 14 backups |

### Manual Backup Operations

```bash
# Create full backup
python -c "
from src.codebase_gardener.monitoring import get_backup_manager, BackupType
from pathlib import Path
manager = get_backup_manager(Path('data'), Path('data/backups'))
backup = manager.create_backup(BackupType.FULL)
print(f'Backup created: {backup.id} ({backup.size_bytes / (1024*1024):.1f}MB)' if backup else 'Backup failed')
"

# List recent backups
python -c "
from src.codebase_gardener.monitoring import get_backup_manager
from pathlib import Path
manager = get_backup_manager(Path('data'), Path('data/backups'))
status = manager.get_backup_status()
for backup in status['recent_backups'][:5]:
    print(f'{backup[\"id\"]}: {backup[\"type\"]} - {backup[\"size_mb\"]:.1f}MB ({backup[\"status\"]})')
"

# Validate backup
python -c "
from src.codebase_gardener.monitoring import get_backup_manager
from pathlib import Path
manager = get_backup_manager(Path('data'), Path('data/backups'))
validation = manager.validate_backup('BACKUP_ID')
print(f'Backup valid: {validation[\"valid\"]}')
"

# Restore from backup
python -c "
from src.codebase_gardener.monitoring import get_backup_manager
from pathlib import Path
manager = get_backup_manager(Path('data'), Path('data/backups'))
success = manager.restore_backup('BACKUP_ID')
print('Restore successful' if success else 'Restore failed')
"
```

### Recovery Procedures

#### System Recovery
1. Stop the application
2. Identify the latest good backup
3. Restore from backup
4. Validate system integrity
5. Restart the application

#### Data Recovery
1. Identify corrupted data
2. Find relevant backup
3. Restore specific data
4. Validate data integrity

## Maintenance Management

### Scheduled Maintenance

| Task | Frequency | Purpose |
|------|-----------|---------|
| Health Check | 30 minutes | System validation |
| Data Cleanup | Daily | Remove old data |
| Backup Maintenance | Weekly | Backup validation |
| Log Rotation | Daily | Log management |

### Manual Maintenance

```bash
# Schedule maintenance task
python -c "
from src.codebase_gardener.monitoring import get_maintenance_manager, MaintenanceType
from pathlib import Path
from datetime import datetime, timedelta
manager = get_maintenance_manager(Path('data'))
task_id = manager.schedule_maintenance(
    MaintenanceType.HEALTH_CHECK,
    datetime.now() + timedelta(minutes=5),
    'Manual health check'
)
print(f'Task scheduled: {task_id}')
"

# Execute maintenance task
python -c "
from src.codebase_gardener.monitoring import get_maintenance_manager
from pathlib import Path
manager = get_maintenance_manager(Path('data'))
success = manager.execute_maintenance_task('TASK_ID')
print('Task completed' if success else 'Task failed')
"

# View maintenance status
python -c "
from src.codebase_gardener.monitoring import get_maintenance_manager
from pathlib import Path
manager = get_maintenance_manager(Path('data'))
status = manager.get_maintenance_status()
print(f'Total tasks: {status[\"total_tasks\"]}')
print(f'Running: {status[\"running_tasks\"]}')
print(f'Scheduled: {status[\"scheduled_tasks\"]}')
"
```

### Available Runbooks

- **system_health_check.md** - System health validation procedures
- **backup_procedures.md** - Backup and recovery procedures
- **log_management.md** - Log analysis and management
- **system_update.md** - Zero-downtime update procedures

## Troubleshooting

### Common Issues

#### High CPU Usage
1. Check for runaway processes
2. Review recent operations
3. Consider reducing concurrent operations
4. Check for infinite loops in code

#### High Memory Usage
1. Check for memory leaks
2. Clear caches if necessary
3. Restart components if needed
4. Review large data operations

#### Integration Issues
1. Check component initialization
2. Verify configuration files
3. Review error logs
4. Restart failed components

#### Backup Failures
1. Check disk space
2. Verify permissions
3. Review error logs
4. Check source data integrity

### Diagnostic Commands

```bash
# System diagnostics
python -c "
from src.codebase_gardener.monitoring import get_logging_manager
from pathlib import Path
manager = get_logging_manager(Path('data/logs'))
diagnostics = manager.get_diagnostic_info()
print(f'Python version: {diagnostics[\"system_info\"][\"python_version\"]}')
print(f'Recent errors: {len(diagnostics[\"recent_errors\"])}')
"

# Performance analysis
python -c "
from src.codebase_gardener.monitoring import get_operational_monitor
from pathlib import Path
monitor = get_operational_monitor(Path('data'))
summary = monitor.get_operational_summary()
print(f'CPU: {summary[\"system_metrics\"][\"cpu_percent\"]:.1f}%')
print(f'Memory: {summary[\"system_metrics\"][\"memory_mb\"]:.0f}MB')
print(f'Uptime: {summary[\"uptime_hours\"]:.1f}h')
"
```

### Emergency Procedures

#### System Unresponsive
1. Check system resources (CPU, memory, disk)
2. Review recent error logs
3. Restart the application
4. If persistent, restore from backup

#### Data Corruption
1. Stop the application immediately
2. Identify the scope of corruption
3. Restore from the latest good backup
4. Validate data integrity
5. Restart the application

#### Component Failures
1. Check component-specific error logs
2. Verify configuration files
3. Restart individual components
4. If persistent, check dependencies

## Performance Optimization

### Mac Mini M4 Specific

- **Memory Management**: Keep usage under 400MB for optimal performance
- **CPU Utilization**: Monitor for sustained high usage
- **Disk I/O**: Use SSD storage for best performance
- **Network**: Local-first processing minimizes network dependencies

### Monitoring Intervals

- **Health Checks**: 30 seconds (configurable)
- **Metrics Collection**: 30 seconds (configurable)
- **Alert Processing**: Real-time
- **Backup Scheduling**: Automatic based on type

### Optimization Tips

1. **Reduce Monitoring Frequency**: Increase intervals if performance is impacted
2. **Cleanup Old Data**: Regular cleanup prevents disk space issues
3. **Monitor Resource Usage**: Keep within Mac Mini M4 constraints
4. **Optimize Queries**: Use appropriate time ranges for data retrieval

## Security Considerations

### Data Protection
- All data stored locally (local-first approach)
- Backups encrypted at rest
- No external data transmission for core operations

### Access Control
- Operational dashboard requires local access
- Log files protected by file system permissions
- Backup files secured with checksums

### Audit Trail
- All operational actions logged
- User actions tracked in audit logs
- System changes recorded with timestamps

## Integration with Main Application

### CLI Commands

```bash
# Enhanced serve command with monitoring
python -m src.codebase_gardener.main serve --enable-monitoring

# Status command with operational info
python -m src.codebase_gardener.main status --detailed

# Backup command
python -m src.codebase_gardener.main backup --type full

# Maintenance command
python -m src.codebase_gardener.main maintain --task health_check
```

### Programmatic Access

```python
from src.codebase_gardener.monitoring import (
    get_operational_monitor,
    get_logging_manager,
    get_backup_manager,
    get_maintenance_manager
)
from pathlib import Path

# Initialize monitoring components
data_dir = Path("data")
operational_monitor = get_operational_monitor(data_dir)
logging_manager = get_logging_manager(data_dir / "logs")
backup_manager = get_backup_manager(data_dir, data_dir / "backups")
maintenance_manager = get_maintenance_manager(data_dir)

# Use monitoring capabilities
health_summary = operational_monitor.get_operational_summary()
log_stats = logging_manager.get_log_statistics()
backup_status = backup_manager.get_backup_status()
maintenance_status = maintenance_manager.get_maintenance_status()
```

## Support and Maintenance

### Regular Maintenance Tasks

- **Daily**: Review alerts, check system health, validate backups
- **Weekly**: Analyze performance trends, cleanup old data, test recovery procedures
- **Monthly**: Review and update operational procedures, validate all runbooks

### Monitoring Best Practices

1. **Proactive Monitoring**: Address warnings before they become critical
2. **Regular Testing**: Test backup and recovery procedures regularly
3. **Documentation**: Keep operational procedures up to date
4. **Performance Tracking**: Monitor trends over time
5. **Capacity Planning**: Plan for growth and resource needs

For additional support or questions about operational procedures, refer to the runbooks in the `data/maintenance/runbooks/` directory or check the system logs for detailed diagnostic information.