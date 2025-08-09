#!/usr/bin/env bash
set -euo pipefail

# Codebase Gardener Restore Script
# Restores system data from backups

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DATA_DIR="/var/lib/codebase-gardener"
BACKUP_DIR="$DATA_DIR/backups"
LOG_FILE="/var/log/codebase-gardener/restore.log"

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

# List available backups
list_backups() {
    log "Available backups:"
    
    local backups=()
    while IFS= read -r -d '' backup; do
        backups+=("$backup")
    done < <(find "$BACKUP_DIR" -name "codebase-gardener_*.tar.gz" -print0 | sort -z)
    
    if [[ ${#backups[@]} -eq 0 ]]; then
        warn "No backups found in $BACKUP_DIR"
        return 1
    fi
    
    for i in "${!backups[@]}"; do
        local backup_file="${backups[$i]}"
        local backup_name=$(basename "$backup_file" .tar.gz)
        local backup_date=$(echo "$backup_name" | sed 's/codebase-gardener_//' | sed 's/_/ /')
        local backup_size=$(du -sh "$backup_file" | cut -f1)
        
        echo "  [$i] $backup_name ($backup_size) - $backup_date"
    done
    
    return 0
}

# Extract backup
extract_backup() {
    local backup_file="$1"
    local extract_dir="$2"
    
    log "Extracting backup: $backup_file"
    
    if [[ ! -f "$backup_file" ]]; then
        error "Backup file not found: $backup_file"
        return 1
    fi
    
    # Verify backup integrity
    if ! tar -tzf "$backup_file" > /dev/null 2>&1; then
        error "Backup file is corrupted: $backup_file"
        return 1
    fi
    
    # Extract backup
    mkdir -p "$extract_dir"
    tar -xzf "$backup_file" -C "$extract_dir"
    
    success "Backup extracted to: $extract_dir"
    return 0
}

# Stop services before restore
stop_services() {
    log "Stopping services before restore..."
    
    local services=("com.codebase-gardener.app" "com.codebase-gardener.ollama")
    
    for service in "${services[@]}"; do
        if launchctl list | grep -q "$service"; then
            log "Stopping service: $service"
            launchctl unload "/Library/LaunchDaemons/$service.plist" 2>/dev/null || true
        fi
    done
    
    # Wait for services to stop
    sleep 5
    
    success "Services stopped"
}

# Start services after restore
start_services() {
    log "Starting services after restore..."
    
    local services=("com.codebase-gardener.ollama" "com.codebase-gardener.app")
    
    for service in "${services[@]}"; do
        log "Starting service: $service"
        launchctl load "/Library/LaunchDaemons/$service.plist"
    done
    
    # Wait for services to start
    sleep 10
    
    success "Services started"
}

# Restore vector stores
restore_vector_stores() {
    local backup_path="$1"
    local vector_stores_backup="$backup_path/data/vector_stores"
    local vector_stores_target="$DATA_DIR/vector_stores"
    
    if [[ -d "$vector_stores_backup" ]]; then
        log "Restoring vector stores..."
        
        # Backup existing vector stores
        if [[ -d "$vector_stores_target" ]]; then
            mv "$vector_stores_target" "${vector_stores_target}.backup.$(date +%s)"
        fi
        
        # Restore vector stores
        cp -r "$vector_stores_backup" "$vector_stores_target"
        chown -R codebase-gardener:staff "$vector_stores_target"
        
        success "Vector stores restored"
    else
        warn "No vector stores found in backup"
    fi
}

# Restore models
restore_models() {
    local backup_path="$1"
    local models_backup="$backup_path/data/models"
    local lora_backup="$backup_path/data/lora_adapters"
    local models_target="$DATA_DIR/models"
    local lora_target="$DATA_DIR/lora_adapters"
    
    if [[ -d "$models_backup" ]]; then
        log "Restoring models..."
        
        # Backup existing models
        if [[ -d "$models_target" ]]; then
            mv "$models_target" "${models_target}.backup.$(date +%s)"
        fi
        
        # Restore models
        cp -r "$models_backup" "$models_target"
        chown -R codebase-gardener:staff "$models_target"
        
        success "Models restored"
    else
        warn "No models found in backup"
    fi
    
    if [[ -d "$lora_backup" ]]; then
        log "Restoring LoRA adapters..."
        
        # Backup existing LoRA adapters
        if [[ -d "$lora_target" ]]; then
            mv "$lora_target" "${lora_target}.backup.$(date +%s)"
        fi
        
        # Restore LoRA adapters
        cp -r "$lora_backup" "$lora_target"
        chown -R codebase-gardener:staff "$lora_target"
        
        success "LoRA adapters restored"
    else
        warn "No LoRA adapters found in backup"
    fi
}

# Restore projects
restore_projects() {
    local backup_path="$1"
    local projects_backup="$backup_path/data/projects"
    local projects_target="$DATA_DIR/projects"
    
    if [[ -d "$projects_backup" ]]; then
        log "Restoring project data..."
        
        # Backup existing projects
        if [[ -d "$projects_target" ]]; then
            mv "$projects_target" "${projects_target}.backup.$(date +%s)"
        fi
        
        # Restore projects
        cp -r "$projects_backup" "$projects_target"
        chown -R codebase-gardener:staff "$projects_target"
        
        success "Project data restored"
    else
        warn "No project data found in backup"
    fi
}

# Restore configuration
restore_config() {
    local backup_path="$1"
    local config_backup="$backup_path/config"
    local install_dir="/opt/codebase-gardener"
    
    if [[ -d "$config_backup" ]]; then
        log "Restoring configuration files..."
        
        # Restore environment configuration
        if [[ -f "$config_backup/.env" ]]; then
            cp "$config_backup/.env" "$install_dir/"
            chown codebase-gardener:staff "$install_dir/.env"
            chmod 600 "$install_dir/.env"
        fi
        
        # Restore logging configuration
        if [[ -f "$config_backup/logging.conf" ]]; then
            cp "$config_backup/logging.conf" "$install_dir/"
            chown codebase-gardener:staff "$install_dir/logging.conf"
        fi
        
        # Restore service files
        for plist in "$config_backup"/*.plist; do
            if [[ -f "$plist" ]]; then
                cp "$plist" /Library/LaunchDaemons/
                chown root:wheel "/Library/LaunchDaemons/$(basename "$plist")"
                chmod 644 "/Library/LaunchDaemons/$(basename "$plist")"
            fi
        done
        
        success "Configuration files restored"
    else
        warn "No configuration files found in backup"
    fi
}

# Verify restore
verify_restore() {
    log "Verifying restore..."
    
    local required_dirs=("$DATA_DIR/vector_stores" "$DATA_DIR/models" "$DATA_DIR/projects")
    local missing_dirs=()
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$dir" ]]; then
            missing_dirs+=("$dir")
        fi
    done
    
    if [[ ${#missing_dirs[@]} -gt 0 ]]; then
        error "Missing directories after restore: ${missing_dirs[*]}"
        return 1
    fi
    
    success "Restore verification passed"
    return 0
}

# Interactive restore
interactive_restore() {
    log "Starting interactive restore process..."
    
    # List available backups
    if ! list_backups; then
        return 1
    fi
    
    # Get user selection
    echo -n "Select backup to restore (number): "
    read -r selection
    
    # Find selected backup
    local backups=()
    while IFS= read -r -d '' backup; do
        backups+=("$backup")
    done < <(find "$BACKUP_DIR" -name "codebase-gardener_*.tar.gz" -print0 | sort -z)
    
    if [[ ! "$selection" =~ ^[0-9]+$ ]] || [[ "$selection" -ge ${#backups[@]} ]]; then
        error "Invalid selection: $selection"
        return 1
    fi
    
    local backup_file="${backups[$selection]}"
    local backup_name=$(basename "$backup_file" .tar.gz)
    
    # Confirm restore
    echo -n "Are you sure you want to restore from $backup_name? This will overwrite current data. (y/N): "
    read -r confirm
    
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        log "Restore cancelled by user"
        return 0
    fi
    
    # Perform restore
    restore_from_backup "$backup_file"
}

# Restore from specific backup
restore_from_backup() {
    local backup_file="$1"
    local backup_name=$(basename "$backup_file" .tar.gz)
    local extract_dir="/tmp/restore_$$"
    
    log "Starting restore from: $backup_name"
    
    # Extract backup
    if ! extract_backup "$backup_file" "$extract_dir"; then
        return 1
    fi
    
    local backup_path="$extract_dir/$backup_name"
    
    # Stop services
    stop_services
    
    # Restore components
    restore_vector_stores "$backup_path"
    restore_models "$backup_path"
    restore_projects "$backup_path"
    restore_config "$backup_path"
    
    # Start services
    start_services
    
    # Verify restore
    if verify_restore; then
        success "Restore completed successfully"
    else
        error "Restore completed with issues"
    fi
    
    # Cleanup
    rm -rf "$extract_dir"
    
    log "Restore process finished"
}

# Main function
main() {
    local backup_file="${1:-}"
    
    if [[ -z "$backup_file" ]]; then
        interactive_restore
    else
        if [[ ! -f "$backup_file" ]]; then
            error "Backup file not found: $backup_file"
            return 1
        fi
        restore_from_backup "$backup_file"
    fi
}

# Handle command line arguments
case "${1:-}" in
    --help|-h)
        echo "Usage: $0 [backup_file|--list|--help]"
        echo "  backup_file  Path to backup file to restore"
        echo "  --list       List available backups"
        echo "  --help       Show this help message"
        echo ""
        echo "If no backup file is specified, interactive mode will be used."
        exit 0
        ;;
    --list)
        list_backups
        exit 0
        ;;
    *)
        main "$@"
        ;;
esac