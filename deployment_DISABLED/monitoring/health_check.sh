#!/usr/bin/env bash
set -euo pipefail

# Codebase Gardener Health Check Script
# Monitors system health and service status

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="/var/log/codebase-gardener/health_check.log"
ALERT_FILE="/var/log/codebase-gardener/alerts.log"

# Configuration
MEMORY_THRESHOLD=80  # Percentage
CPU_THRESHOLD=80     # Percentage
DISK_THRESHOLD=90    # Percentage
OLLAMA_URL="http://127.0.0.1:11434"
APP_URL="http://127.0.0.1:7860"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Logging functions
log() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] INFO: $1" | tee -a "$LOG_FILE"
}

warn() {
    echo -e "${YELLOW}[$(date '+%Y-%m-%d %H:%M:%S')] WARN: $1${NC}" | tee -a "$LOG_FILE"
}

error() {
    echo -e "${RED}[$(date '+%Y-%m-%d %H:%M:%S')] ERROR: $1${NC}" | tee -a "$LOG_FILE" | tee -a "$ALERT_FILE"
}

success() {
    echo -e "${GREEN}[$(date '+%Y-%m-%d %H:%M:%S')] SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

alert() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] ALERT: $1" | tee -a "$ALERT_FILE"
}

# Check service status
check_service() {
    local service_name="$1"
    local service_label="com.codebase-gardener.$service_name"
    
    if launchctl list | grep -q "$service_label"; then
        local pid=$(launchctl list | grep "$service_label" | awk '{print $1}')
        if [[ "$pid" != "-" ]]; then
            success "Service $service_name is running (PID: $pid)"
            return 0
        else
            error "Service $service_name is loaded but not running"
            return 1
        fi
    else
        error "Service $service_name is not loaded"
        return 1
    fi
}

# Check memory usage
check_memory() {
    local memory_info
    memory_info=$(vm_stat | grep -E "Pages (free|active|inactive|speculative|wired down)")
    
    local page_size=4096
    local free_pages=$(echo "$memory_info" | grep "Pages free" | awk '{print $3}' | tr -d '.')
    local active_pages=$(echo "$memory_info" | grep "Pages active" | awk '{print $3}' | tr -d '.')
    local inactive_pages=$(echo "$memory_info" | grep "Pages inactive" | awk '{print $3}' | tr -d '.')
    local wired_pages=$(echo "$memory_info" | grep "Pages wired down" | awk '{print $4}' | tr -d '.')
    
    local total_pages=$((free_pages + active_pages + inactive_pages + wired_pages))
    local used_pages=$((active_pages + inactive_pages + wired_pages))
    local memory_usage=$((used_pages * 100 / total_pages))
    
    log "Memory usage: ${memory_usage}%"
    
    if [[ $memory_usage -gt $MEMORY_THRESHOLD ]]; then
        alert "High memory usage: ${memory_usage}% (threshold: ${MEMORY_THRESHOLD}%)"
        return 1
    else
        success "Memory usage within limits: ${memory_usage}%"
        return 0
    fi
}

# Check CPU usage
check_cpu() {
    local cpu_usage
    cpu_usage=$(top -l 1 -n 0 | grep "CPU usage" | awk '{print $3}' | tr -d '%')
    
    log "CPU usage: ${cpu_usage}%"
    
    if (( $(echo "$cpu_usage > $CPU_THRESHOLD" | bc -l) )); then
        alert "High CPU usage: ${cpu_usage}% (threshold: ${CPU_THRESHOLD}%)"
        return 1
    else
        success "CPU usage within limits: ${cpu_usage}%"
        return 0
    fi
}

# Check disk usage
check_disk() {
    local disk_usage
    disk_usage=$(df -h /var/lib/codebase-gardener | tail -1 | awk '{print $5}' | tr -d '%')
    
    log "Disk usage: ${disk_usage}%"
    
    if [[ $disk_usage -gt $DISK_THRESHOLD ]]; then
        alert "High disk usage: ${disk_usage}% (threshold: ${DISK_THRESHOLD}%)"
        return 1
    else
        success "Disk usage within limits: ${disk_usage}%"
        return 0
    fi
}

# Check Ollama health
check_ollama() {
    local response
    if response=$(curl -s -f --max-time 10 "$OLLAMA_URL/api/tags" 2>/dev/null); then
        success "Ollama service is responding"
        return 0
    else
        error "Ollama service is not responding at $OLLAMA_URL"
        return 1
    fi
}

# Check application health
check_app() {
    local response
    if response=$(curl -s -f --max-time 10 "$APP_URL/health" 2>/dev/null); then
        success "Application is responding"
        return 0
    else
        error "Application is not responding at $APP_URL"
        return 1
    fi
}

# Check log file sizes
check_logs() {
    local log_dir="/var/log/codebase-gardener"
    local max_size_mb=100
    
    for log_file in "$log_dir"/*.log; do
        if [[ -f "$log_file" ]]; then
            local size_mb
            size_mb=$(du -m "$log_file" | cut -f1)
            if [[ $size_mb -gt $max_size_mb ]]; then
                warn "Log file $log_file is large: ${size_mb}MB"
            fi
        fi
    done
}

# Check data directory integrity
check_data_integrity() {
    local data_dir="/var/lib/codebase-gardener"
    local required_dirs=("models" "vector_stores" "projects" "backups")
    
    for dir in "${required_dirs[@]}"; do
        if [[ ! -d "$data_dir/$dir" ]]; then
            error "Required data directory missing: $data_dir/$dir"
            return 1
        fi
    done
    
    success "Data directory integrity check passed"
    return 0
}

# Main health check function
main() {
    log "Starting health check..."
    
    local exit_code=0
    
    # Check services
    check_service "ollama" || exit_code=1
    check_service "app" || exit_code=1
    
    # Check system resources
    check_memory || exit_code=1
    check_cpu || exit_code=1
    check_disk || exit_code=1
    
    # Check application endpoints
    check_ollama || exit_code=1
    check_app || exit_code=1
    
    # Check system integrity
    check_logs
    check_data_integrity || exit_code=1
    
    if [[ $exit_code -eq 0 ]]; then
        success "Health check completed successfully"
    else
        error "Health check completed with issues"
    fi
    
    log "Health check finished"
    return $exit_code
}

# Run health check
main "$@"