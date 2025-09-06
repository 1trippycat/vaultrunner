#!/bin/bash

# VaultRunner Docker Helper Scripts
# Provides easy Docker management for VaultRunner

set -euo pipefail

# Colors for output
readonly RED='\033[0;31m'
readonly GREEN='\033[0;32m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly NC='\033[0m' # No Color

# Print colored output
print_info() { echo -e "${BLUE}[INFO]${NC} $1"; }
print_success() { echo -e "${GREEN}[SUCCESS]${NC} $1"; }
print_warning() { echo -e "${YELLOW}[WARNING]${NC} $1"; }
print_error() { echo -e "${RED}[ERROR]${NC} $1"; }

# Check if Docker is available
check_docker() {
    if ! command -v docker &> /dev/null; then
        print_error "Docker is not installed or not in PATH"
        exit 1
    fi
    
    if ! docker info &> /dev/null; then
        print_error "Docker daemon is not running"
        exit 1
    fi
}

# Build VaultRunner Docker image
build_image() {
    print_info "Building VaultRunner Docker image..."
    
    if docker build -t vaultrunner:latest .; then
        print_success "VaultRunner image built successfully"
    else
        print_error "Failed to build VaultRunner image"
        exit 1
    fi
}

# Start VaultRunner development environment
start_dev() {
    print_info "Starting VaultRunner development environment..."
    
    # Copy example env file if .env doesn't exist
    if [[ ! -f .env ]]; then
        print_info "Creating .env file from example..."
        cp .env.example .env
    fi
    
    if docker-compose up -d; then
        print_success "VaultRunner development environment started"
        print_info "Vault UI available at: http://localhost:8200"
        print_info "Root token: $(grep VAULT_ROOT_TOKEN .env | cut -d= -f2)"
    else
        print_error "Failed to start development environment"
        exit 1
    fi
}

# Stop VaultRunner development environment
stop_dev() {
    print_info "Stopping VaultRunner development environment..."
    
    if docker-compose down; then
        print_success "VaultRunner development environment stopped"
    else
        print_error "Failed to stop development environment"
        exit 1
    fi
}

# Run VaultRunner command in container
run_command() {
    local args=("$@")
    
    print_info "Running VaultRunner command: ${args[*]}"
    
    docker-compose run --rm vaultrunner "${args[@]}"
}

# Show logs
show_logs() {
    local service="${1:-vaultrunner}"
    
    print_info "Showing logs for service: $service"
    docker-compose logs -f "$service"
}

# Clean up Docker resources
cleanup() {
    print_info "Cleaning up VaultRunner Docker resources..."
    
    # Stop and remove containers
    docker-compose down --volumes --remove-orphans
    
    # Remove images
    if docker images -q vaultrunner &> /dev/null; then
        docker rmi vaultrunner:latest
    fi
    
    print_success "Cleanup completed"
}

# Show help
show_help() {
    cat << EOF
VaultRunner Docker Helper

Usage: $0 <command> [options]

Commands:
    build           Build VaultRunner Docker image
    start           Start development environment
    stop            Stop development environment
    run <args>      Run VaultRunner command in container
    logs [service]  Show logs (default: vaultrunner)
    cleanup         Clean up Docker resources
    help            Show this help message

Examples:
    $0 build
    $0 start
    $0 run secrets list
    $0 run --help
    $0 logs vault
    $0 stop
    $0 cleanup

Environment:
    Copy .env.example to .env and customize as needed.
EOF
}

# Main script logic
main() {
    check_docker
    
    case "${1:-help}" in
        build)
            build_image
            ;;
        start)
            start_dev
            ;;
        stop)
            stop_dev
            ;;
        run)
            shift
            run_command "$@"
            ;;
        logs)
            show_logs "${2:-vaultrunner}"
            ;;
        cleanup)
            cleanup
            ;;
        help|--help|-h)
            show_help
            ;;
        *)
            print_error "Unknown command: $1"
            show_help
            exit 1
            ;;
    esac
}

# Execute main function with all arguments
main "$@"