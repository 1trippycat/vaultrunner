#!/bin/bash

# VaultRunner Installation Script
# Installs VaultRunner - HashiCorp Vault Docker Integration Tool
# 
# Usage:
#   curl -sSL https://raw.githubusercontent.com/1trippycat/core/main/vaultrunner/install.sh | bash
#   OR
#   wget -qO- https://raw.githubusercontent.com/1trippycat/core/main/vaultrunner/install.sh | bash
#   OR
#   git clone https://github.com/1trippycat/core.git && cd core/vaultrunner && ./install.sh

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Configuration
readonly VAULTRUNNER_DIR="${HOME}/.local/share/vaultrunner"
readonly BIN_DIR="${HOME}/.local/bin"
readonly WRAPPER_SCRIPT="${BIN_DIR}/vaultrunner"
readonly VENV_DIR="${VAULTRUNNER_DIR}/.venv"

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1" >&2
}

# Check if running as root
check_not_root() {
    if [[ $EUID -eq 0 ]]; then
        log_error "This script should not be run as root for security reasons."
        log_info "Run as a regular user to install VaultRunner in your home directory."
        exit 1
    fi
}

# Check system requirements
check_requirements() {
    log_info "Checking system requirements..."
    
    # Check Python 3
    if ! command -v python3 &> /dev/null; then
        log_error "Python 3 is required but not found in PATH"
        log_info "Please install Python 3.8 or later:"
        log_info "  - Ubuntu/Debian: sudo apt update && sudo apt install python3 python3-pip"
        log_info "  - RHEL/CentOS: sudo yum install python3 python3-pip"
        log_info "  - macOS: brew install python3"
        exit 1
    fi
    
    # Check Python version
    local python_version
    python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
    local major minor
    IFS='.' read -r major minor <<< "$python_version"
    
    if [[ $major -lt 3 ]] || [[ $major -eq 3 && $minor -lt 8 ]]; then
        log_error "Python 3.8 or later is required (found Python $python_version)"
        exit 1
    fi
    
    log_success "Python $python_version found"
    
    # Check pip
    if ! command -v pip3 &> /dev/null && ! python3 -m pip --version &> /dev/null; then
        log_error "pip is required but not found"
        log_info "Please install pip3 or ensure 'python3 -m pip' works"
        exit 1
    fi
    
    # Check optional tools
    local missing_optional=()
    
    if ! command -v docker &> /dev/null; then
        missing_optional+=("docker")
    fi
    
    if ! command -v git &> /dev/null; then
        missing_optional+=("git")
    fi
    
    if [[ ${#missing_optional[@]} -gt 0 ]]; then
        log_warning "Optional tools not found: ${missing_optional[*]}"
        log_info "VaultRunner will work without them, but some features may be limited"
    fi
}

# Create installation directories
create_directories() {
    log_info "Creating installation directories..."
    
    mkdir -p "$VAULTRUNNER_DIR"
    mkdir -p "$BIN_DIR"
    
    log_success "Directories created"
}

# Download or copy VaultRunner source
install_source() {
    log_info "Installing VaultRunner source code..."
    
    # Check if we're running from a git clone
    if [[ -f "$(dirname "$0")/vaultrunner/main.py" ]]; then
        log_info "Installing from local source..."
        cp -r "$(dirname "$0")/vaultrunner" "$VAULTRUNNER_DIR/"
        cp "$(dirname "$0")/requirements.txt" "$VAULTRUNNER_DIR/"
    else
        log_info "Downloading from GitHub..."
        
        # Check if git is available
        if ! command -v git &> /dev/null; then
            log_error "Git is required to download VaultRunner from GitHub"
            log_info "Either install git or download the repository manually"
            exit 1
        fi
        
        # Clone to temporary directory
        local temp_dir
        temp_dir=$(mktemp -d)
        
        if ! git clone --depth 1 https://github.com/1trippycat/core.git "$temp_dir"; then
            log_error "Failed to download VaultRunner from GitHub"
            rm -rf "$temp_dir"
            exit 1
        fi
        
        # Copy VaultRunner files
        cp -r "$temp_dir/vaultrunner" "$VAULTRUNNER_DIR/"
        cp "$temp_dir/vaultrunner/requirements.txt" "$VAULTRUNNER_DIR/"
        
        # Cleanup
        rm -rf "$temp_dir"
    fi
    
    log_success "Source code installed to $VAULTRUNNER_DIR"
}

# Install Python dependencies
install_dependencies() {
    log_info "Installing Python dependencies..."
    
    # Create virtual environment
    log_info "Creating virtual environment..."
    if ! python3 -m venv "$VENV_DIR"; then
        log_error "Failed to create virtual environment"
        exit 1
    fi
    log_success "Virtual environment created at $VENV_DIR"
    
    # Install dependencies in virtual environment
    log_info "Installing dependencies in virtual environment..."
    if ! "$VENV_DIR/bin/python" -m pip install --upgrade pip; then
        log_error "Failed to upgrade pip in virtual environment"
        exit 1
    fi
    
    if ! "$VENV_DIR/bin/python" -m pip install -r "$VAULTRUNNER_DIR/requirements.txt"; then
        log_error "Failed to install Python dependencies"
        log_info "You may need to install them manually:"
        log_info "  $VENV_DIR/bin/python -m pip install -r $VAULTRUNNER_DIR/requirements.txt"
        exit 1
    fi
    
    log_success "Dependencies installed"
}

# Create wrapper script
create_wrapper() {
    log_info "Creating VaultRunner wrapper script..."
    
    cat > "$WRAPPER_SCRIPT" << EOF
#!/bin/bash

# VaultRunner Global Wrapper
# Installed by VaultRunner installation script

set -euo pipefail

# VaultRunner installation directory
readonly VAULTRUNNER_DIR="$VAULTRUNNER_DIR"
readonly VENV_DIR="$VENV_DIR"
readonly VAULTRUNNER_PYTHON="\$VAULTRUNNER_DIR/vaultrunner/main.py"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "Error: Python 3 is required but not found in PATH" >&2
    echo "Please ensure Python 3 is installed and in your PATH" >&2
    exit 1
fi

# Check if virtual environment exists
if [[ ! -f "\$VENV_DIR/bin/activate" ]]; then
    echo "Error: VaultRunner virtual environment not found at: \$VENV_DIR" >&2
    echo "Try reinstalling VaultRunner:" >&2
    echo "  curl -sSL https://raw.githubusercontent.com/1trippycat/core/main/vaultrunner/install.sh | bash" >&2
    exit 1
fi

# Check if VaultRunner Python app exists
if [[ ! -f "\$VAULTRUNNER_PYTHON" ]]; then
    echo "Error: VaultRunner not found at: \$VAULTRUNNER_PYTHON" >&2
    echo "Try reinstalling VaultRunner:" >&2
    echo "  curl -sSL https://raw.githubusercontent.com/1trippycat/core/main/vaultrunner/install.sh | bash" >&2
    exit 1
fi

# Activate virtual environment and execute VaultRunner
export PYTHONPATH="\$VAULTRUNNER_DIR:\${PYTHONPATH:-}"
exec "\$VENV_DIR/bin/python" "\$VAULTRUNNER_PYTHON" "\$@"
EOF
    
    chmod +x "$WRAPPER_SCRIPT"
    
    log_success "Wrapper script created at $WRAPPER_SCRIPT"
}

# Check and update PATH
check_path() {
    log_info "Checking PATH configuration..."
    
    if [[ ":$PATH:" != *":$BIN_DIR:"* ]]; then
        log_warning "$BIN_DIR is not in your PATH"
        
        # Detect shell and provide appropriate instructions
        local shell_name
        shell_name=$(basename "$SHELL")
        
        case "$shell_name" in
            bash)
                local rc_file="$HOME/.bashrc"
                ;;
            zsh)
                local rc_file="$HOME/.zshrc"
                ;;
            fish)
                log_info "For Fish shell, run: fish_add_path $BIN_DIR"
                return
                ;;
            *)
                local rc_file="$HOME/.profile"
                ;;
        esac
        
        log_info "To add $BIN_DIR to your PATH, add this line to $rc_file:"
        echo
        echo "    export PATH=\"\$HOME/.local/bin:\$PATH\""
        echo
        log_info "Then restart your terminal or run: source $rc_file"
    else
        log_success "$BIN_DIR is already in your PATH"
    fi
}

# Test installation
test_installation() {
    log_info "Testing VaultRunner installation..."
    
    # Test the wrapper script directly
    if "$WRAPPER_SCRIPT" --version &> /dev/null; then
        log_success "VaultRunner installed successfully!"
        
        # Show version
        echo
        log_info "VaultRunner version:"
        "$WRAPPER_SCRIPT" --version
        
        echo
        log_info "Try running: vaultrunner --help"
    else
        log_warning "Installation completed but test failed"
        log_info "You may need to:"
        log_info "1. Add $BIN_DIR to your PATH (see instructions above)"
        log_info "2. Restart your terminal"
        log_info "3. Check virtual environment: $VENV_DIR"
        log_info "4. Reinstall if needed: $0"
    fi
}

# Install example templates function
install_example_templates() {
    log_info "Setting up example templates..."
    
    # Create a temporary project directory to test template installation
    temp_project_dir=$(mktemp -d)
    
    # Change to temp directory and run template install
    (
        cd "$temp_project_dir"
        if "$WRAPPER_SCRIPT" templates install --force &> /dev/null; then
            log_success "Example templates created successfully"
            log_info "Templates will be auto-generated in project directories when you run VaultRunner"
        else
            log_warning "Could not pre-install templates (this is normal)"
            log_info "Templates will be created when you first run 'vaultrunner templates install'"
        fi
    )
    
    # Clean up temp directory
    rm -rf "$temp_project_dir"
}

# Uninstall function
uninstall() {
    log_info "Uninstalling VaultRunner..."
    
    rm -rf "$VAULTRUNNER_DIR"
    rm -f "$WRAPPER_SCRIPT"
    
    log_success "VaultRunner uninstalled"
    log_info "You may want to remove $BIN_DIR from your PATH if you added it"
    log_info "Virtual environment was removed: $VENV_DIR"
}

# Main installation function
main() {
    echo
    log_info "VaultRunner - HashiCorp Vault Docker Integration Tool"
    log_info "Installation starting..."
    echo
    
    # Parse arguments
    if [[ $# -gt 0 && "$1" == "--uninstall" ]]; then
        uninstall
        exit 0
    fi
    
    # Run installation steps
    check_not_root
    check_requirements
    create_directories
    install_source
    install_dependencies
    create_wrapper
    check_path
    test_installation
    install_example_templates
    
    echo
    log_success "Installation completed!"
    echo
    log_info "Quick start:"
    log_info "  vaultrunner --help              # Show help"
    log_info "  vaultrunner templates install   # Install example templates"
    log_info "  vaultrunner secrets list        # List secrets"
    log_info "  vaultrunner namespace list      # List namespaces"
    log_info "  vaultrunner docker start        # Start Vault container"
    log_info "  vaultrunner vault deploy         # Deploy Vault server"
    echo
    log_info "For more information, visit:"
    log_info "  https://github.com/1trippycat/core/tree/main/vaultrunner"
    echo
}

# Handle script errors
trap 'log_error "Installation failed on line $LINENO"' ERR

# Run main function
main "$@"