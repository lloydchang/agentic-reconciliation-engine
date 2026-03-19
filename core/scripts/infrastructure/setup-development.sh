#!/bin/bash

# Development Environment Setup Script
# Sets up local development environment for Agentic Reconciliation Engine

set -euo pipefail

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
PURPLE='\033[0;35m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

# Default values
SKIP_TOOLS=false
SKIP_GIT=false
SKIP_VENV=false
SKIP_PRECOMMIT=false
PYTHON_VERSION="3.11"
GO_VERSION="1.21"
NODE_VERSION="18"
VERBOSE=false

# Help function
show_help() {
    cat << EOF
Development Environment Setup Script

USAGE:
    $0 [OPTIONS]

OPTIONS:
    --skip-tools           Skip development tools installation
    --skip-git             Skip git configuration
    --skip-venv            Skip Python virtual environment setup
    --skip-precommit       Skip pre-commit hooks setup
    --python-version <ver> Python version (default: 3.11)
    --go-version <ver>     Go version (default: 1.21)
    --node-version <ver>   Node.js version (default: 18)
    -v, --verbose          Enable verbose output
    -h, --help             Show this help message

EXAMPLES:
    $0                                    # Full setup
    $0 --skip-tools --skip-git           # Skip tools and git setup
    $0 --python-version 3.10             # Use different Python version
    $0 --skip-venv                       # Skip virtual environment

DESCRIPTION:
    This script sets up a complete development environment including
    development tools, git configuration, Python virtual environment,
    and pre-commit hooks.

EOF
}

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_warn() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_step() {
    echo -e "${PURPLE}[STEP]${NC} $1"
}

log_debug() {
    if [[ "$VERBOSE" == "true" ]]; then
        echo -e "${CYAN}[DEBUG]${NC} $1"
    fi
}

# Parse command line arguments
parse_args() {
    while [[ $# -gt 0 ]]; do
        case $1 in
            --skip-tools)
                SKIP_TOOLS=true
                shift
                ;;
            --skip-git)
                SKIP_GIT=true
                shift
                ;;
            --skip-venv)
                SKIP_VENV=true
                shift
                ;;
            --skip-precommit)
                SKIP_PRECOMMIT=true
                shift
                ;;
            --python-version)
                PYTHON_VERSION="$2"
                shift 2
                ;;
            --go-version)
                GO_VERSION="$2"
                shift 2
                ;;
            --node-version)
                NODE_VERSION="$2"
                shift 2
                ;;
            -v|--verbose)
                VERBOSE=true
                shift
                ;;
            -h|--help)
                show_help
                exit 0
                ;;
            *)
                log_error "Unknown option: $1"
                show_help
                exit 1
                ;;
        esac
    done
}

# Check if running in project root
check_project_root() {
    if [[ ! -f "README.md" ]] || [[ ! -d "core/ai" ]]; then
        log_error "This script must be run from the project root directory"
        exit 1
    fi
    
    log_debug "Running from project root: $(pwd)"
}

# Install development tools
install_dev_tools() {
    if [[ "$SKIP_TOOLS" == "true" ]]; then
        log_info "Skipping development tools installation"
        return 0
    fi
    
    log_step "Installing development tools..."
    
    # Detect OS
    local os=$(uname -s)
    case "$os" in
        Darwin)
            install_tools_macos
            ;;
        Linux)
            install_tools_linux
            ;;
        *)
            log_error "Unsupported OS: $os"
            exit 1
            ;;
    esac
}

# Install tools on macOS
install_tools_macos() {
    log_info "Installing tools on macOS..."
    
    # Check for Homebrew
    if ! command -v brew &> /dev/null; then
        log_info "Installing Homebrew..."
        /bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"
    fi
    
    # Update Homebrew
    log_info "Updating Homebrew..."
    brew update
    
    # Install development tools
    local tools=(
        "git"
        "go@$GO_VERSION"
        "python@$PYTHON_VERSION"
        "node@$NODE_VERSION"
        "make"
        "jq"
        "yq"
        "shellcheck"
        "pre-commit"
        "gh"
        "kubectl"
        "kind"
        "docker"
        "docker-compose"
        "vscode"
    )
    
    for tool in "${tools[@]}"; do
        if ! command -v "${tool%%@*}" &> /dev/null; then
            log_info "Installing $tool..."
            brew install "$tool" || brew install --cask "$tool" || {
                log_warn "Failed to install $tool"
            }
        else
            log_debug "$tool already installed"
        fi
    done
}

# Install tools on Linux
install_tools_linux() {
    log_info "Installing tools on Linux..."
    
    # Update package manager
    if command -v apt-get &> /dev/null; then
        sudo apt-get update
    elif command -v yum &> /dev/null; then
        sudo yum update -y
    fi
    
    # Install basic tools
    local basic_tools=("git" "make" "jq" "curl" "wget" "vim")
    for tool in "${basic_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y "$tool"
            elif command -v yum &> /dev/null; then
                sudo yum install -y "$tool"
            fi
        fi
    done
    
    # Install Go
    if ! command -v go &> /dev/null; then
        log_info "Installing Go $GO_VERSION..."
        cd /tmp
        wget "https://go.dev/dl/go${GO_VERSION}.linux-amd64.tar.gz"
        sudo rm -rf /usr/local/go
        sudo tar -C /usr/local -xzf "go${GO_VERSION}.linux-amd64.tar.gz"
        echo 'export PATH=$PATH:/usr/local/go/bin' >> ~/.bashrc
        cd -
    fi
    
    # Install Python
    if ! command -v python3 &> /dev/null; then
        log_info "Installing Python $PYTHON_VERSION..."
        if command -v apt-get &> /dev/null; then
            sudo apt-get install -y "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-venv" "python${PYTHON_VERSION}-pip"
        elif command -v yum &> /dev/null; then
            sudo yum install -y "python${PYTHON_VERSION}" "python${PYTHON_VERSION}-pip"
        fi
    fi
    
    # Install Node.js
    if ! command -v node &> /dev/null; then
        log_info "Installing Node.js $NODE_VERSION..."
        curl -fsSL https://deb.nodesource.com/setup_${NODE_VERSION}.x | sudo -E bash -
        sudo apt-get install -y nodejs
    fi
    
    # Install other tools
    local other_tools=("shellcheck" "pre-commit")
    for tool in "${other_tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_info "Installing $tool..."
            if command -v apt-get &> /dev/null; then
                sudo apt-get install -y "$tool"
            elif command -v yum &> /dev/null; then
                sudo yum install -y "$tool"
            fi
        fi
    done
}

# Configure git
setup_git() {
    if [[ "$SKIP_GIT" == "true" ]]; then
        log_info "Skipping git configuration"
        return 0
    fi
    
    log_step "Setting up git configuration..."
    
    # Check if git is configured
    if ! git config --global user.name &> /dev/null || ! git config --global user.email &> /dev/null; then
        log_info "Git user configuration not found"
        echo "Please enter your git configuration:"
        read -p "Git user name: " git_name
        read -p "Git user email: " git_email
        
        git config --global user.name "$git_name"
        git config --global user.email "$git_email"
        
        log_success "Git configuration set"
    else
        log_debug "Git already configured"
    fi
    
    # Set default git settings
    git config --global init.defaultBranch main
    git config --global pull.rebase false
    git config --global push.autoSetupRemote true
    
    # Set up git aliases
    git config --global alias.st status
    git config --global alias.co checkout
    git config --global alias.br branch
    git config --global alias.cm commit
    git config --global alias.df diff
    git config --global alias.lg "log --oneline --graph --decorate --all"
    
    log_success "Git setup completed"
}

# Setup Python virtual environment
setup_python_venv() {
    if [[ "$SKIP_VENV" == "true" ]]; then
        log_info "Skipping Python virtual environment setup"
        return 0
    fi
    
    log_step "Setting up Python virtual environment..."
    
    # Check Python version
    local python_cmd="python3"
    if command -v "python$PYTHON_VERSION" &> /dev/null; then
        python_cmd="python$PYTHON_VERSION"
    fi
    
    local python_version
    python_version=$("$python_cmd" --version 2>&1 | cut -d' ' -f2)
    log_info "Using Python $python_version"
    
    # Create virtual environment
    local venv_dir="venv"
    if [[ ! -d "$venv_dir" ]]; then
        log_info "Creating virtual environment..."
        "$python_cmd" -m venv "$venv_dir"
    else
        log_debug "Virtual environment already exists"
    fi
    
    # Activate virtual environment and install packages
    log_info "Installing Python packages..."
    
    # Create activation script
    cat > activate.sh << 'EOF'
#!/bin/bash
# Activate Python virtual environment
source venv/bin/activate
echo "Virtual environment activated"
echo "Python: $(python --version)"
echo "Pip: $(pip --version)"
EOF
    chmod +x activate.sh
    
    # Install requirements
    if [[ -f "requirements.txt" ]]; then
        ./venv/bin/pip install -r requirements.txt
    fi
    
    # Install development packages
    ./venv/bin/pip install --upgrade pip
    ./venv/bin/pip install pytest pytest-cov black flake8 mypy pre-commit
    
    log_success "Python virtual environment setup completed"
}

# Setup pre-commit hooks
setup_precommit() {
    if [[ "$SKIP_PRECOMMIT" == "true" ]]; then
        log_info "Skipping pre-commit hooks setup"
        return 0
    fi
    
    log_step "Setting up pre-commit hooks..."
    
    # Check if pre-commit is available
    if ! command -v pre-commit &> /dev/null; then
        log_error "pre-commit not found. Install it first or use --skip-precommit"
        return 1
    fi
    
    # Create .pre-commit-config.yaml if it doesn't exist
    if [[ ! -f ".pre-commit-config.yaml" ]]; then
        log_info "Creating .pre-commit-config.yaml..."
        cat > .pre-commit-config.yaml << 'EOF'
repos:
  - repo: https://github.com/pre-commit/pre-commit-hooks
    rev: v4.4.0
    hooks:
      - id: trailing-whitespace
      - id: end-of-file-fixer
      - id: check-yaml
      - id: check-added-large-files
      - id: check-merge-conflict
      - id: debug-statements

  - repo: https://github.com/psf/black
    rev: 23.3.0
    hooks:
      - id: black
        language_version: python3

  - repo: https://github.com/pycqa/flake8
    rev: 6.0.0
    hooks:
      - id: flake8
        args: [--max-line-length=88, --extend-ignore=E203,W503]

  - repo: https://github.com/pre-commit/mirrors-mypy
    rev: v1.3.0
    hooks:
      - id: mypy
        additional_dependencies: [types-all]

  - repo: https://github.com/koalaman/shellcheck-precommit
    rev: v0.9.0
    hooks:
      - id: shellcheck

  - repo: https://github.com/dnephin/pre-commit-golang
    rev: v0.5.1
    hooks:
      - id: go-fmt
      - id: go-vet
      - id: go-lint
      - id: go-mod-tidy
EOF
    fi
    
    # Install pre-commit hooks
    if [[ -f ".pre-commit-config.yaml" ]]; then
        log_info "Installing pre-commit hooks..."
        pre-commit install
        pre-commit install --hook-type commit-msg
        
        log_success "Pre-commit hooks installed"
    else
        log_warn ".pre-commit-config.yaml not found"
    fi
}

# Setup development environment variables
setup_env_vars() {
    log_step "Setting up environment variables..."
    
    # Create .env file if it doesn't exist
    if [[ ! -f ".env" ]]; then
        log_info "Creating .env file..."
        cat > .env << EOF
# Development Environment Variables
export PYTHONPATH="\$PYTHONPATH:$(pwd)"
export GO_PATH="\$HOME/go"
export PATH="\$PATH:\$GO_PATH/bin"
export KUBECONFIG="\$HOME/.kube/config"

# AI Agent Development
export AI_DEBUG=true
export AI_LOG_LEVEL=debug
export SKILLS_PATH="$(pwd)/core/ai/skills"

# GitOps Development
export GITOPS_DEBUG=true
export FLUX_LOG_LEVEL=debug

# Docker
export DOCKER_BUILDKIT=1
export COMPOSE_DOCKER_CLI_BUILD=1
EOF
        log_success "Created .env file"
    else
        log_debug ".env file already exists"
    fi
    
    # Create development scripts directory
    mkdir -p scripts/dev
    
    # Create activation script
    cat > scripts/dev/activate.sh << 'EOF'
#!/bin/bash
# Development environment activation script

# Source environment variables
if [[ -f ".env" ]]; then
    set -a
    source .env
    set +a
fi

# Activate Python virtual environment
if [[ -d "venv" ]]; then
    source venv/bin/activate
fi

# Set up Go path
if [[ -d "$HOME/go" ]]; then
    export PATH="$PATH:$HOME/go/bin"
fi

echo "Development environment activated"
echo "Python: $(python --version 2>/dev/null || echo 'Not available')"
echo "Go: $(go version 2>/dev/null || echo 'Not available')"
echo "Node: $(node --version 2>/dev/null || echo 'Not available')"
EOF
    chmod +x scripts/dev/activate.sh
    
    log_success "Environment setup completed"
}

# Verify setup
verify_setup() {
    log_step "Verifying development setup..."
    
    # Check tools
    local tools=("git" "go" "python3" "node" "kubectl" "docker")
    local missing_tools=()
    
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            missing_tools+=("$tool")
        else
            log_debug "$tool: $(command -v "$tool")"
        fi
    done
    
    if [[ ${#missing_tools[@]} -gt 0 ]]; then
        log_warn "Missing tools: ${missing_tools[*]}"
    else
        log_success "All required tools are installed"
    fi
    
    # Check Python virtual environment
    if [[ -d "venv" ]]; then
        log_success "Python virtual environment exists"
    else
        log_warn "Python virtual environment not found"
    fi
    
    # Check git configuration
    if git config --global user.name &> /dev/null; then
        log_success "Git is configured"
    else
        log_warn "Git is not configured"
    fi
    
    # Check pre-commit hooks
    if [[ -f ".pre-commit-config.yaml" ]]; then
        log_success "Pre-commit configuration exists"
    else
        log_warn "Pre-commit configuration not found"
    fi
}

# Show next steps
show_next_steps() {
    log_step "Development environment setup completed!"
    
    cat << EOF

${GREEN}🎉 Development environment is ready!${NC}

Quick start:
1. Activate the development environment:
   source scripts/dev/activate.sh

2. Run tests:
   make test

3. Start development:
   make dev

4. Check code quality:
   make lint

Useful commands:
- make help                    # Show all available commands
- source scripts/dev/activate.sh  # Activate development environment
- pre-commit run --all-files   # Run all pre-commit hooks
- kubectl cluster-info        # Check Kubernetes cluster

Configuration files:
- .env                         # Environment variables
- .pre-commit-config.yaml     # Pre-commit hooks
- requirements.txt             # Python dependencies
- go.mod                       # Go dependencies

Documentation:
- README.md                    # Project overview
- docs/developer-guide/        # Development guide
- core/ai/skills/             # AI skills documentation

EOF
}

# Main function
main() {
    log_info "Development Environment Setup Script"
    
    check_project_root
    parse_args "$@"
    
    log_info "Configuration:"
    log_info "  Skip tools: $SKIP_TOOLS"
    log_info "  Skip git: $SKIP_GIT"
    log_info "  Skip venv: $SKIP_VENV"
    log_info "  Skip precommit: $SKIP_PRECOMMIT"
    log_info "  Python version: $PYTHON_VERSION"
    log_info "  Go version: $GO_VERSION"
    log_info "  Node version: $NODE_VERSION"
    
    install_dev_tools
    setup_git
    setup_python_venv
    setup_precommit
    setup_env_vars
    verify_setup
    show_next_steps
    
    log_success "Development environment setup completed!"
}

# Run main function with all arguments
main "$@"
