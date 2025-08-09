#!/usr/bin/env bash
set -euo pipefail

# Codebase Gardener Production Deployment Installer
# Automated installation script for Mac Mini M4 production environment

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
INSTALL_LOG="/tmp/codebase-gardener-install.log"

# Configuration
SERVICE_USER="codebase-gardener"
INSTALL_DIR="/opt/codebase-gardener"
DATA_DIR="/var/lib/codebase-gardener"
LOG_DIR="/var/log/codebase-gardener"
VENV_DIR="$INSTALL_DIR/venv"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log() {
    echo -e "${BLUE}[INFO]${NC} $1" | tee -a "$INSTALL_LOG"
}

warn() {
    echo -e "${YELLOW}[WARN]${NC} $1" | tee -a "$INSTALL_LOG"
}

error() {
    echo -e "${RED}[ERROR]${NC} $1" | tee -a "$INSTALL_LOG"
}

success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1" | tee -a "$INSTALL_LOG"
}

# Check if running as root
check_root() {
    if [[ $EUID -ne 0 ]]; then
        error "This script must be run as root (use sudo)"
        exit 1
    fi
}

# Check system requirements
check_system() {
    log "Checking system requirements..."
    
    # Check macOS version
    if [[ "$(uname)" != "Darwin" ]]; then
        error "This installer is designed for macOS systems"
        exit 1
    fi
    
    # Check for required commands
    local required_commands=("python3" "pip3" "curl" "git")
    for cmd in "${required_commands[@]}"; do
        if ! command -v "$cmd" &> /dev/null; then
            error "Required command '$cmd' not found"
            exit 1
        fi
    done
    
    # Check Python version
    local python_version
    python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1,2)
    if [[ "$(printf '%s\n' "3.11" "$python_version" | sort -V | head -n1)" != "3.11" ]]; then
        error "Python 3.11 or higher is required. Found: $python_version"
        exit 1
    fi
    
    success "System requirements check passed"
}

# Install system dependencies
install_system_deps() {
    log "Installing system dependencies..."
    
    # Check if Homebrew is installed
    if ! command -v brew &> /dev/null; then
        log "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Install required packages
    local packages=("python@3.11" "git" "curl" "wget" "jq")
    for package in "${packages[@]}"; do
        if ! brew list "$package" &> /dev/null; then
            log "Installing $package..."
            brew install "$package"
        else
            log "$package already installed"
        fi
    done
    
    success "System dependencies installed"
}

# Install Ollama
install_ollama() {
    log "Installing Ollama..."
    
    if command -v ollama &> /dev/null; then
        log "Ollama already installed"
        return 0
    fi
    
    # Download and install Ollama
    curl -fsSL https://ollama.ai/install.sh | sh
    
    # Verify installation
    if command -v ollama &> /dev/null; then
        success "Ollama installed successfully"
    else
        error "Ollama installation failed"
        exit 1
    fi
}

# Create service user
create_service_user() {
    log "Creating service user: $SERVICE_USER"
    
    if id "$SERVICE_USER" &>/dev/null; then
        log "User $SERVICE_USER already exists"
        return 0
    fi
    
    # Create user with no login shell and home directory
    dscl . -create "/Users/$SERVICE_USER"
    dscl . -create "/Users/$SERVICE_USER" UserShell /usr/bin/false
    dscl . -create "/Users/$SERVICE_USER" RealName "Codebase Gardener Service"
    dscl . -create "/Users/$SERVICE_USER" UniqueID 501
    dscl . -create "/Users/$SERVICE_USER" PrimaryGroupID 20
    dscl . -create "/Users/$SERVICE_USER" NFSHomeDirectory "/var/empty"
    
    success "Service user $SERVICE_USER created"
}

# Create directory structure
create_directories() {
    log "Creating directory structure..."
    
    local directories=("$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR" "$DATA_DIR/models" "$DATA_DIR/vector_stores" "$DATA_DIR/projects")
    
    for dir in "${directories[@]}"; do
        if [[ ! -d "$dir" ]]; then
            mkdir -p "$dir"
            log "Created directory: $dir"
        fi
    done
    
    # Set ownership and permissions
    chown -R "$SERVICE_USER:staff" "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
    chmod -R 755 "$INSTALL_DIR" "$DATA_DIR" "$LOG_DIR"
    
    success "Directory structure created"
}

# Install Python application
install_python_app() {
    log "Installing Python application..."
    
    # Create virtual environment
    if [[ ! -d "$VENV_DIR" ]]; then
        log "Creating virtual environment..."
        python3 -m venv "$VENV_DIR"
    fi
    
    # Activate virtual environment and install dependencies
    source "$VENV_DIR/bin/activate"
    
    # Upgrade pip
    pip install --upgrade pip setuptools wheel
    
    # Install application in development mode
    cd "$PROJECT_ROOT"
    pip install -e ".[dev,performance]"
    
    # Install additional requirements if they exist
    if [[ -f "requirements.txt" ]]; then
        pip install -r requirements.txt
    fi
    
    # Set ownership
    chown -R "$SERVICE_USER:staff" "$VENV_DIR"
    
    success "Python application installed"
}

# Install systemd services (using launchd on macOS)
install_services() {
    log "Installing system services..."
    
    # Copy service files
    cp "$SCRIPT_DIR/services/"*.plist /Library/LaunchDaemons/
    
    # Set permissions
    chmod 644 /Library/LaunchDaemons/com.codebase-gardener.*.plist
    chown root:wheel /Library/LaunchDaemons/com.codebase-gardener.*.plist
    
    # Load services
    launchctl load /Library/LaunchDaemons/com.codebase-gardener.ollama.plist
    launchctl load /Library/LaunchDaemons/com.codebase-gardener.app.plist
    
    success "System services installed"
}

# Create configuration files
create_config() {
    log "Creating configuration files..."
    
    # Copy configuration templates
    cp "$SCRIPT_DIR/config/production.env" "$INSTALL_DIR/.env"
    cp "$SCRIPT_DIR/config/logging.conf" "$INSTALL_DIR/"
    
    # Set ownership
    chown "$SERVICE_USER:staff" "$INSTALL_DIR/.env" "$INSTALL_DIR/logging.conf"
    chmod 600 "$INSTALL_DIR/.env"
    chmod 644 "$INSTALL_DIR/logging.conf"
    
    success "Configuration files created"
}

# Install monitoring and health checks
install_monitoring() {
    log "Installing monitoring and health checks..."
    
    # Copy monitoring scripts
    cp "$SCRIPT_DIR/monitoring/"*.sh "$INSTALL_DIR/bin/"
    chmod +x "$INSTALL_DIR/bin/"*.sh
    chown "$SERVICE_USER:staff" "$INSTALL_DIR/bin/"*.sh
    
    # Install health check service
    cp "$SCRIPT_DIR/services/com.codebase-gardener.healthcheck.plist" /Library/LaunchDaemons/
    chmod 644 /Library/LaunchDaemons/com.codebase-gardener.healthcheck.plist
    chown root:wheel /Library/LaunchDaemons/com.codebase-gardener.healthcheck.plist
    launchctl load /Library/LaunchDaemons/com.codebase-gardener.healthcheck.plist
    
    success "Monitoring and health checks installed"
}

# Install backup system
install_backup() {
    log "Installing backup system..."
    
    # Copy backup scripts
    cp "$SCRIPT_DIR/backup/"*.sh "$INSTALL_DIR/bin/"
    chmod +x "$INSTALL_DIR/bin/"*.sh
    chown "$SERVICE_USER:staff" "$INSTALL_DIR/bin/"*.sh
    
    # Install backup service
    cp "$SCRIPT_DIR/services/com.codebase-gardener.backup.plist" /Library/LaunchDaemons/
    chmod 644 /Library/LaunchDaemons/com.codebase-gardener.backup.plist
    chown root:wheel /Library/LaunchDaemons/com.codebase-gardener.backup.plist
    launchctl load /Library/LaunchDaemons/com.codebase-gardener.backup.plist
    
    success "Backup system installed"
}

# Validate installation
validate_installation() {
    log "Validating installation..."
    
    # Check services are running
    local services=("com.codebase-gardener.ollama" "com.codebase-gardener.app")
    for service in "${services[@]}"; do
        if launchctl list | grep -q "$service"; then
            success "Service $service is running"
        else
            warn "Service $service is not running"
        fi
    done
    
    # Check Python application
    if "$VENV_DIR/bin/python" -c "import codebase_gardener; print('✓ Package imported successfully')"; then
        success "Python application validation passed"
    else
        error "Python application validation failed"
        exit 1
    fi
    
    # Check Ollama
    if ollama list &> /dev/null; then
        success "Ollama validation passed"
    else
        error "Ollama validation failed"
        exit 1
    fi
    
    success "Installation validation completed"
}

# Main installation function
main() {
    log "Starting Codebase Gardener production installation..."
    log "Installation log: $INSTALL_LOG"
    
    check_root
    check_system
    install_system_deps
    install_ollama
    create_service_user
    create_directories
    install_python_app
    create_config
    install_services
    install_monitoring
    install_backup
    validate_installation
    
    success "Codebase Gardener production installation completed!"
    log "Services can be managed with: launchctl [load|unload|start|stop] /Library/LaunchDaemons/com.codebase-gardener.*.plist"
    log "Logs are available in: $LOG_DIR"
    log "Configuration files are in: $INSTALL_DIR"
}

# Run main function
main "$@"