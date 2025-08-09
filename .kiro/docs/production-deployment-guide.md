# Codebase Gardener Production Deployment Guide

This guide provides comprehensive instructions for deploying the Codebase Gardener system in a production environment, specifically optimized for Mac Mini M4 systems.

## Overview

The production deployment uses a native systemd-style approach (adapted for macOS using launchd) to provide:

- **Automated Installation**: Complete system setup with dependency management
- **Service Management**: Dedicated services for Ollama and the Python application
- **Resource Optimization**: Memory and CPU constraints for Mac Mini M4
- **Health Monitoring**: Automated health checks and alerting
- **Backup & Recovery**: Comprehensive data protection
- **Operational Tools**: Maintenance and troubleshooting utilities

## System Requirements

### Hardware Requirements
- **Mac Mini M4** (8GB unified memory minimum)
- **Storage**: 100GB+ available disk space
- **Network**: Stable internet connection for initial setup

### Software Requirements
- **macOS**: 13.0 (Ventura) or later
- **Python**: 3.11 or higher
- **Homebrew**: Package manager for macOS
- **Administrative Access**: sudo privileges required

## Pre-Installation Checklist

Before starting the installation, ensure:

- [ ] System meets hardware and software requirements
- [ ] You have administrative (sudo) access
- [ ] Network connectivity is stable
- [ ] No conflicting services are running on ports 11434 (Ollama) or 7860 (Web UI)
- [ ] Sufficient disk space is available (100GB+ recommended)

## Installation Process

### Step 1: Download and Prepare

1. Clone or download the Codebase Gardener repository
2. Navigate to the project directory
3. Ensure the installation script is executable:

```bash
chmod +x deployment/install.sh
```

### Step 2: Run Installation

Execute the installation script with sudo privileges:

```bash
sudo deployment/install.sh
```

The installation process will:

1. **Check System Requirements**: Verify Python version, available commands
2. **Install System Dependencies**: Homebrew packages, Python tools
3. **Install Ollama**: LLM inference engine
4. **Create Service User**: Dedicated `codebase-gardener` user
5. **Create Directory Structure**: Data, logs, and configuration directories
6. **Install Python Application**: Virtual environment with all dependencies
7. **Configure Services**: launchd service files for automatic startup
8. **Setup Monitoring**: Health check and alerting systems
9. **Configure Backup**: Automated backup system
10. **Validate Installation**: Comprehensive system validation

### Step 3: Verify Installation

After installation completes, verify the system is running:

```bash
# Check service status
launchctl list | grep codebase-gardener

# Check application health
curl http://127.0.0.1:7860/health

# Check Ollama status
curl http://127.0.0.1:11434/api/tags

# View logs
tail -f /var/log/codebase-gardener/app.log
```

## Service Management

### Service Control

The system includes several services managed by launchd:

- **com.codebase-gardener.ollama**: Ollama LLM inference service
- **com.codebase-gardener.app**: Main Python application
- **com.codebase-gardener.healthcheck**: Health monitoring service
- **com.codebase-gardener.backup**: Automated backup service

### Managing Services

```bash
# Start a service
sudo launchctl load /Library/LaunchDaemons/com.codebase-gardener.app.plist

# Stop a service
sudo launchctl unload /Library/LaunchDaemons/com.codebase-gardener.app.plist

# Restart a service
sudo launchctl unload /Library/LaunchDaemons/com.codebase-gardener.app.plist
sudo launchctl load /Library/LaunchDaemons/com.codebase-gardener.app.plist

# Check service status
launchctl list | grep codebase-gardener
```

### Service Logs

Logs are centralized in `/var/log/codebase-gardener/`:

- `app.log`: Main application logs
- `app.error.log`: Application error logs
- `ollama.log`: Ollama service logs
- `ollama.error.log`: Ollama error logs
- `health_check.log`: Health monitoring logs
- `backup.log`: Backup operation logs

## Configuration

### Environment Configuration

The main configuration file is located at `/opt/codebase-gardener/.env`. Key settings include:

```bash
# Performance tuning for Mac Mini M4
CODEBASE_GARDENER_MAX_MEMORY_MB=2048
CODEBASE_GARDENER_MAX_WORKERS=2
CODEBASE_GARDENER_MAX_CONCURRENT_PROJECTS=5

# Ollama configuration
OLLAMA_BASE_URL=http://127.0.0.1:11434
OLLAMA_MAX_LOADED_MODELS=2

# Resource monitoring thresholds
CODEBASE_GARDENER_ALERT_MEMORY_THRESHOLD=80
CODEBASE_GARDENER_ALERT_CPU_THRESHOLD=80
CODEBASE_GARDENER_ALERT_DISK_THRESHOLD=90
```

### Applying Configuration Changes

After modifying configuration:

1. Restart the affected services
2. Monitor logs for any issues
3. Verify the changes took effect

```bash
# Restart application service
sudo launchctl unload /Library/LaunchDaemons/com.codebase-gardener.app.plist
sudo launchctl load /Library/LaunchDaemons/com.codebase-gardener.app.plist

# Check logs
tail -f /var/log/codebase-gardener/app.log
```

## Health Monitoring

### Automated Health Checks

The system includes automated health monitoring that checks:

- **Service Status**: All services are running
- **Resource Usage**: Memory, CPU, and disk usage
- **Application Health**: HTTP endpoints responding
- **Data Integrity**: Required directories and files exist

### Manual Health Check

Run a manual health check:

```bash
sudo -u codebase-gardener /opt/codebase-gardener/bin/health_check.sh
```

### Health Check Logs

Monitor health check results:

```bash
tail -f /var/log/codebase-gardener/health_check.log
```

### Alerts

Critical issues are logged to:

```bash
tail -f /var/log/codebase-gardener/alerts.log
```

## Backup and Recovery

### Automated Backups

The system automatically creates daily backups including:

- **Vector Stores**: LanceDB vector databases
- **Models**: LoRA adapters and model configurations
- **Project Data**: Project files and conversation history
- **Configuration**: Environment and service configurations

### Manual Backup

Create a manual backup:

```bash
sudo -u codebase-gardener /opt/codebase-gardener/bin/backup.sh
```

### List Available Backups

```bash
sudo -u codebase-gardener /opt/codebase-gardener/bin/restore.sh --list
```

### Restore from Backup

Interactive restore:

```bash
sudo -u codebase-gardener /opt/codebase-gardener/bin/restore.sh
```

Restore specific backup:

```bash
sudo -u codebase-gardener /opt/codebase-gardener/bin/restore.sh /path/to/backup.tar.gz
```

## Maintenance

### Regular Maintenance Tasks

1. **Monitor Logs**: Check for errors or warnings
2. **Review Alerts**: Address any system alerts
3. **Check Disk Space**: Ensure adequate storage
4. **Update Dependencies**: Keep system packages current
5. **Verify Backups**: Test backup integrity periodically

### Log Rotation

Logs are automatically rotated to prevent disk space issues. Configure rotation in `/opt/codebase-gardener/logging.conf`.

### Cleanup Old Data

Remove old backups and logs:

```bash
# Cleanup is automatic, but can be run manually
find /var/lib/codebase-gardener/backups -name "*.tar.gz" -mtime +30 -delete
```

## Troubleshooting

### Common Issues

#### Services Not Starting

1. Check service logs for errors
2. Verify configuration files
3. Ensure proper permissions
4. Check resource availability

```bash
# Check service status
launchctl list | grep codebase-gardener

# View error logs
tail -f /var/log/codebase-gardener/app.error.log
```

#### High Memory Usage

1. Check current memory usage
2. Review running processes
3. Adjust memory limits if needed
4. Consider reducing concurrent projects

```bash
# Check memory usage
vm_stat

# Check process memory
ps aux | grep codebase-gardener
```

#### Ollama Connection Issues

1. Verify Ollama service is running
2. Check network connectivity
3. Review Ollama logs
4. Test API endpoints

```bash
# Test Ollama API
curl http://127.0.0.1:11434/api/tags

# Check Ollama logs
tail -f /var/log/codebase-gardener/ollama.log
```

### Getting Help

1. **Check Logs**: Start with application and service logs
2. **Run Health Check**: Use the automated health check tool
3. **Review Configuration**: Verify all settings are correct
4. **Check Resources**: Ensure adequate memory and disk space

## Security Considerations

### Service User

The system runs under a dedicated `codebase-gardener` user with minimal privileges:

- No login shell access
- Restricted file permissions
- Limited system access

### Network Security

- Services bind to localhost only by default
- No external network access required for operation
- API endpoints are not exposed externally

### Data Protection

- All data stored locally
- Regular automated backups
- Encrypted backup storage (optional)

## Performance Optimization

### Mac Mini M4 Specific Optimizations

The deployment is optimized for Mac Mini M4 constraints:

- **Memory Limits**: Services limited to prevent system overload
- **CPU Affinity**: Optimized for Apple Silicon architecture
- **Thermal Management**: Resource limits prevent thermal throttling
- **Storage Optimization**: Efficient vector store operations

### Monitoring Performance

```bash
# Monitor system resources
top -l 1 -n 0

# Check service resource usage
ps aux | grep codebase-gardener

# Monitor disk I/O
iostat 1
```

## Upgrading

### Application Updates

1. Stop services
2. Backup current installation
3. Update application code
4. Restart services
5. Verify functionality

```bash
# Stop services
sudo launchctl unload /Library/LaunchDaemons/com.codebase-gardener.*.plist

# Create backup
sudo -u codebase-gardener /opt/codebase-gardener/bin/backup.sh

# Update application (example)
cd /path/to/new/version
sudo deployment/install.sh

# Verify installation
curl http://127.0.0.1:7860/health
```

### System Updates

Keep the underlying system updated:

```bash
# Update Homebrew packages
brew update && brew upgrade

# Update Python packages
/opt/codebase-gardener/venv/bin/pip install --upgrade pip
```

## Support and Documentation

### Additional Resources

- **Application Logs**: `/var/log/codebase-gardener/`
- **Configuration Files**: `/opt/codebase-gardener/`
- **Data Directory**: `/var/lib/codebase-gardener/`
- **Service Files**: `/Library/LaunchDaemons/com.codebase-gardener.*.plist`

### Operational Runbooks

Detailed operational procedures are available in the deployment directory:

- `deployment/monitoring/health_check.sh`: Health monitoring
- `deployment/backup/backup.sh`: Backup procedures
- `deployment/backup/restore.sh`: Recovery procedures

This production deployment provides a robust, scalable foundation for running the Codebase Gardener system in production environments while maintaining the local-first processing principles and Mac Mini M4 optimizations.
