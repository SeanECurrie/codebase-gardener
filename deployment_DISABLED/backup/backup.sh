#!/usr/bin/env bash
set -euo pipefail

# Codebase Gardener Backup Script
# Creates comprehensive backups of all system data

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="/var/lib/codebase-gardener"
BACKUP_DIR="$DATA_DIR/backups"
LOG_FILE="/var/log/codebase-gardener/backup.log"

# Configuration
RETENTION_DAYS=30
COMPRESSION="gzip"
BACKUP_PREFIX="codebase-gardener"
TIMESTAMP=$(date '+%Y%m%d_%H%M%S')
BACKUP_NAME="${BACKUP_PREFIX}_${TIMESTAMP}"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m'

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Create backup directory structure
create_backup_structure() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    log "Creating backup structure at $backup_path"
    
    mkdir -p "$backup_path"/{data,config,logs,metadata}
    
    success "Backup structure created"
}

# Backup vector stores
backup_vector_stores() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local vector_store_dir="$DATA_DIR/vector_stores"
    
    if [[ -d "$vector_store_dir" ]]; then
        log "Backing up vector stores..."
        
        # Copy vector store files
        cp -r "$vector_store_dir" "$backup_path/data/"
        
        # Create manifest of vector stores
        find "$vector_store_dir" -type f -name "*.lance" > "$backup_path/metadata/vector_stores.manifest"
        
        success "Vector stores backed up"
    else
        warn "Vector store directory not found: $vector_store_dir"
    fi
}

# Backup models and LoRA adapters
backup_models() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local models_dir="$DATA_DIR/models"
    local lora_dir="$DATA_DIR/lora_adapters"
    
    if [[ -d "$models_dir" ]]; then
        log "Backing up models..."
        cp -r "$models_dir" "$backup_path/data/"
        
        # Create model manifest
        find "$models_dir" -type f > "$backup_path/metadata/models.manifest"
        
        success "Models backed up"
    else
        warn "Models directory not found: $models_dir"
    fi
    
    if [[ -d "$lora_dir" ]]; then
        log "Backing up LoRA adapters..."
        cp -r "$lora_dir" "$backup_path/data/"
        
        # Create LoRA manifest
        find "$lora_dir" -type f -name "*.bin" > "$backup_path/metadata/lora_adapters.manifest"
        
        success "LoRA adapters backed up"
    else
        warn "LoRA adapters directory not found: $lora_dir"
    fi
}

# Backup project data
backup_projects() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local projects_dir="$DATA_DIR/projects"
    
    if [[ -d "$projects_dir" ]]; then
        log "Backing up project data..."
        
        # Copy project files
        cp -r "$projects_dir" "$backup_path/data/"
        
        # Create project manifest
        find "$projects_dir" -type f -name "*.json" > "$backup_path/metadata/projects.manifest"
        
        success "Project data backed up"
    else
        warn "Projects directory not found: $projects_dir"
    fi
}

# Backup configuration files
backup_config() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local install_dir="/opt/codebase-gardener"
    
    log "Backing up configuration files..."
    
    # Backup environment configuration
    if [[ -f "$install_dir/.env" ]]; then
        cp "$install_dir/.env" "$backup_path/config/"
    fi
    
    # Backup logging configuration
    if [[ -f "$install_dir/logging.conf" ]]; then
        cp "$install_dir/logging.conf" "$backup_path/config/"
    fi
    
    # Backup service files
    cp /Library/LaunchDaemons/com.codebase-gardener.*.plist "$backup_path/config/" 2>/dev/null || true
    
    success "Configuration files backed up"
}

# Backup logs (recent only)
backup_logs() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local log_dir="/var/log/codebase-gardener"
    
    if [[ -d "$log_dir" ]]; then
        log "Backing up recent logs..."
        
        # Backup logs from last 7 days
        find "$log_dir" -name "*.log" -mtime -7 -exec cp {} "$backup_path/logs/" \;
        
        success "Recent logs backed up"
    else
        warn "Log directory not found: $log_dir"
    fi
}

# Create backup metadata
create_metadata() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    local metadata_file="$backup_path/metadata/backup_info.json"
    
    log "Creating backup metadata..."
    
    cat > "$metadata_file" << EOF
{
    "backup_name": "$BACKUP_NAME",
    "timestamp": "$TIMESTAMP",
    "date": "$(date -Iseconds)",
    "hostname": "$(hostname)",
    "system_info": {
        "os": "$(uname -s)",
        "version": "$(uname -r)",
        "architecture": "$(uname -m)"
    },
    "backup_size": "$(du -sh "$backup_path" | cut -f1)",
    "components": {
        "vector_stores": $([ -d "$backup_path/data/vector_stores" ] && echo "true" || echo "false"),
        "models": $([ -d "$backup_path/data/models" ] && echo "true" || echo "false"),
        "lora_adapters": $([ -d "$backup_path/data/lora_adapters" ] && echo "true" || echo "false"),
        "projects": $([ -d "$backup_path/data/projects" ] && echo "true" || echo "false"),
        "config": $([ -d "$backup_path/config" ] && echo "true" || echo "false"),
        "logs": $([ -d "$backup_path/logs" ] && echo "true" || echo "false")
    }
}
EOF
    
    success "Backup metadata created"
}

# Compress backup
compress_backup() {
    local backup_path="$BACKUP_DIR/$BACKUP_NAME"
    
    if [[ "$COMPRESSION" == "gzip" ]]; then
        log "Compressing backup with gzip..."
        
        cd "$BACKUP_DIR"
        tar -czf "${BACKUP_NAME}.tar.gz" "$BACKUP_NAME"
        rm -rf "$BACKUP_NAME"
        
        success "Backup compressed: ${BACKUP_NAME}.tar.gz"
    elif [[ "$COMPRESSION" == "none" ]]; then
        log "Backup compression disabled"
    else
        warn "Unknown compression method: $COMPRESSION"
    fi
}

# Clean old backups
cleanup_old_backups() {
    log "Cleaning up backups older than $RETENTION_DAYS days..."
    
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*.tar.gz" -mtime +$RETENTION_DAYS -delete
    find "$BACKUP_DIR" -name "${BACKUP_PREFIX}_*" -type d -mtime +$RETENTION_DAYS -exec rm -rf {} + 2>/dev/null || true
    
    success "Old backups cleaned up"
}

# Verify backup integrity
verify_backup() {
    local backup_file="$BACKUP_DIR/${BACKUP_NAME}.tar.gz"
    
    if [[ -f "$backup_file" ]]; then
        log "Verifying backup integrity..."
        
        if tar -tzf "$backup_file" > /dev/null 2>&1; then
            success "Backup integrity verified"
            return 0
        else
            error "Backup integrity check failed"
            return 1
        fi
    else
        error "Backup file not found: $backup_file"
        return 1
    fi
}

# Send backup notification
send_notification() {
    local status="$1"
    local message="$2"
    
    # Log notification (could be extended to send emails, Slack messages, etc.)
    if [[ "$status" == "success" ]]; then
        success "Backup notification: $message"
    else
        error "Backup notification: $message"
    fi
}

# Main backup function
main() {
    log "Starting backup process: $BACKUP_NAME"
    
    # Ensure backup directory exists
    mkdir -p "$BACKUP_DIR"
    
    local exit_code=0
    
    # Create backup structure
    create_backup_structure
    
    # Backup components
    backup_vector_stores
    backup_models
    backup_projects
    backup_config
    backup_logs
    
    # Create metadata
    create_metadata
    
    # Compress backup
    compress_backup
    
    # Verify backup
    if ! verify_backup; then
        exit_code=1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    # Send notification
    if [[ $exit_code -eq 0 ]]; then
        send_notification "success" "Backup completed successfully: $BACKUP_NAME"
        success "Backup process completed successfully"
    else
        send_notification "error" "Backup completed with errors: $BACKUP_NAME"
        error "Backup process completed with errors"
    fi
    
    log "Backup process finished"
    return $exit_code
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [--help|--dry-run]"
        echo "  --help     Show this help message"
        echo "  --dry-run  Show what would be backed up without actually doing it"
        exit 0
        ;;
    --dry-run)
        log "DRY RUN: Would create backup $BACKUP_NAME"
        log "DRY RUN: Would backup vector stores, models, projects, config, and logs"
        log "DRY RUN: Would compress and verify backup"
        log "DRY RUN: Would cleanup backups older than $RETENTION_DAYS days"
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac