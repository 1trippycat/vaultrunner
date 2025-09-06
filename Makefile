# VaultRunner Makefile
# Provides convenient commands for development and Docker operations

.PHONY: help build start stop clean test lint install dev-install docker-build docker-start docker-stop docker-clean venv

# Default target
help:
	@echo "VaultRunner - HashiCorp Vault Docker Integration Tool"
	@echo ""
	@echo "Available targets:"
	@echo "  help          Show this help message"
	@echo "  venv          Create and activate virtual environment"
	@echo "  install       Install VaultRunner locally"
	@echo "  dev-install   Install in development mode"
	@echo "  test          Run tests"
	@echo "  lint          Run linting checks"
	@echo "  clean         Clean up build artifacts"
	@echo ""
	@echo "Docker targets:"
	@echo "  docker-build  Build Docker image"
	@echo "  docker-start  Start development environment"
	@echo "  docker-stop   Stop development environment"
	@echo "  docker-clean  Clean up Docker resources"
	@echo "  docker-run    Run VaultRunner in container (use: make docker-run ARGS='secrets list')"
	@echo ""
	@echo "Examples:"
	@echo "  make venv && source .venv/bin/activate"
	@echo "  make dev-install"
	@echo "  make docker-start"
	@echo "  make docker-run ARGS='secrets add myapp/db/password'"
	@echo "  make docker-run ARGS='--help'"

# Virtual environment setup
venv:
	python3 -m venv .venv
	@echo "Virtual environment created."
	@echo "Activate with: source .venv/bin/activate"

# Python installation targets
install: venv
	.venv/bin/pip install .

dev-install: venv
	.venv/bin/pip install -e .[dev]

# Testing and quality
test:
	python -m pytest tests/ -v

lint:
	flake8 src/
	mypy src/

# Cleanup
clean:
	rm -rf build/
	rm -rf dist/
	rm -rf *.egg-info/
	find . -type d -name __pycache__ -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete

# Docker targets
docker-build:
	docker build -t vaultrunner:latest .

docker-start:
	@if [ ! -f .env ]; then \
		echo "Creating .env file from example..."; \
		cp .env.example .env; \
	fi
	docker-compose up -d
	@echo "VaultRunner development environment started"
	@echo "Vault UI: http://localhost:8200"
	@echo "Root token: $$(grep VAULT_ROOT_TOKEN .env | cut -d= -f2)"

docker-stop:
	docker-compose down

docker-clean:
	docker-compose down --volumes --remove-orphans
	docker rmi vaultrunner:latest 2>/dev/null || true

docker-run:
	docker-compose run --rm vaultrunner $(ARGS)

# Development workflow
dev-start: docker-start
	@echo "Development environment ready!"
	@echo "Try: make docker-run ARGS='--help'"

dev-stop: docker-stop

# Quick test in Docker
docker-test:
	make docker-run ARGS="--version"
	make docker-run ARGS="--help"