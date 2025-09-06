# VaultRunner

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Docker](https://img.shields.io/badge/docker-supported-blue.svg)](https://www.docker.com/)

VaultRunner is a comprehensive HashiCorp Vault Docker integration tool designed for developers transitioning from Docker secrets, environment variables, and other less secure secret management to enterprise-grade HashiCorp Vault.

## ✨ Features

- **🔐 Secret Management**: Secure storage and retrieval with optional namespace support
- **📁 Namespace Organization**: Organize secrets by project, environment, or team
- **🔄 Migration Tools**: Easy import from .env files, Docker secrets, and docker-compose.yml
- **📄 Smart Templates**: Auto-generated Docker, Kubernetes, and deployment templates
- **🚀 Bulk Operations**: Set and get multiple secrets at once
- **🐳 Docker Integration**: Seamless Docker container and Docker Compose support
- **📤 Export Utilities**: Export secrets as .env, JSON, or docker-compose formats
- **🛡️ Enterprise Security**: Password protection, SSL certificates, encrypted key storage
- **💾 Backup & Restore**: Encrypted backup and restore functionality
- **🔧 Modular Design**: Clean, maintainable architecture with separated concerns

## 🎯 Perfect For

- **Docker users** migrating to HashiCorp Vault
- **Teams** needing organized secret management
- **DevOps engineers** wanting simple but secure workflows
- **Developers** who don't want to learn complex Vault concepts
- **Projects** requiring environment-specific secret isolation
- **AI/ML applications** with complex secret management needs

## 🚀 Quick Start

### Installation
```bash
# Install VaultRunner globally
curl -sSL https://raw.githubusercontent.com/1trippycat/vaultrunner/main/install.sh | bash

# Or install locally for development
git clone https://github.com/1trippycat/vaultrunner.git
cd vaultrunner
pip install -e .
```

### Basic Usage
```bash
# Show help
vaultrunner --help

# Add secrets to different namespaces
vaultrunner secrets add database/password "secret123" --namespace myapp
vaultrunner secrets add api/key "abc123" --namespace myapp

# List secrets in a namespace
vaultrunner secrets list --namespace myapp

# Deploy with namespace support
vaultrunner deploy --namespace production --compose-file docker-compose.yml
```

## 📖 Core Concepts

### Namespaces
VaultRunner uses namespaces to organize secrets by project, environment, or team:

```bash
# Development environment
vaultrunner secrets add db/password "dev123" --namespace myapp-dev

# Production environment
vaultrunner secrets add db/password "prod456" --namespace myapp-prod

# Shared secrets
vaultrunner secrets add api/external-key "shared123" --namespace shared
```

### Migration Workflow
```bash
# 1. Import existing secrets
vaultrunner import env .env --namespace myapp

# 2. Deploy with Vault integration
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml

# 3. Verify secrets are injected
docker compose logs app | grep -i vault
```

## � Command Reference

### Secrets Management

```bash
# Add secret to namespace
vaultrunner secrets add database/password --namespace myapp

# Get secret from namespace
vaultrunner secrets get database/password --namespace myapp

# List secrets in namespace
vaultrunner secrets list --namespace myapp

# Delete secret
vaultrunner secrets delete database/password --namespace myapp --force
```

### Namespace Operations

```bash
# List all namespaces
vaultrunner namespace list

# List secrets in namespace
vaultrunner namespace secrets --namespace myapp

# Copy namespace
vaultrunner namespace copy myapp-dev myapp-prod

# Delete namespace
vaultrunner namespace delete temp --confirm
```

### Deployment with Namespaces

```bash
# Deploy with specific namespace
vaultrunner deploy --namespace production --compose-file docker-compose.yml

# Deploy with custom Vault address
vaultrunner deploy --namespace staging --vault-addr http://vault.company.com:8200

# Deploy with environment variables
vaultrunner deploy --namespace myapp --env-file .env.prod --compose-file docker-compose.yml

# Dry run deployment
vaultrunner deploy --namespace myapp --dry-run --compose-file docker-compose.yml
```

### Bulk Operations

```bash
# Set multiple secrets from JSON
vaultrunner bulk-set '{"DB_HOST":"localhost","DB_PORT":"5432"}' --namespace myapp

# Set from file
vaultrunner bulk-set secrets.json --namespace myapp --from-file

# Get multiple secrets
vaultrunner bulk-get DB_HOST DB_PORT --namespace myapp

# Export as environment variables
vaultrunner bulk-get DB_HOST DB_PORT --namespace myapp --format env
```

### Migration Tools

```bash
# Import from .env file
vaultrunner import env .env --namespace myapp

# Import from docker-compose
vaultrunner import docker-compose docker-compose.yml --namespace myapp

# Export to .env format
vaultrunner export env --namespace myapp --output myapp.env

# Export to docker-compose format
vaultrunner export docker-compose --namespace myapp --output docker-env.txt
```

### Template System

```bash
# Install templates
vaultrunner templates install

# Generate docker-compose template
vaultrunner templates generate docker-compose --namespace myapp

# Generate deployment script
vaultrunner templates generate deployment --namespace production --output deploy.sh

# Generate Kubernetes manifests
vaultrunner templates generate kubernetes --namespace myapp --output k8s-secrets.yaml
```

## 🐳 Docker Integration

### Layered Architecture Support
VaultRunner works seamlessly with complex Docker Compose setups:

```yaml
# docker-compose.yml (main file)
name: myapp
include:
  - docker-compose.core-data.yml
  - docker-compose.ai-ml.yml
  - docker-compose.app.yml
```

### Deployment Examples

```bash
# Deploy entire stack with namespace
vaultrunner deploy --namespace production --compose-file docker-compose.yml

# Deploy specific services
vaultrunner deploy --namespace staging --services app,api --compose-file docker-compose.yml

# Deploy with Vault sidecar
vaultrunner deploy --namespace myapp --sidecar --compose-file docker-compose.yml
```

### Network Integration
VaultRunner automatically detects and integrates with your Docker networks:

```bash
# Deploy on detected networks
vaultrunner deploy --namespace myapp --auto-networks

# Deploy on specific network
vaultrunner deploy --namespace myapp --network myapp-net
```

## 🔄 Migration Examples

### From .env Files
```bash
# Import existing .env
vaultrunner import env .env --namespace myapp

# Deploy with Vault integration
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml
```

### From Docker Secrets
```bash
# Export Docker secrets
docker secret ls --format "{{.Name}}" | xargs -I {} sh -c 'echo "{}=$(docker secret inspect {} --format "{{.Spec.Data}}")"' > docker-secrets.env

# Import to VaultRunner
vaultrunner import env docker-secrets.env --namespace production

# Deploy securely
vaultrunner deploy --namespace production --compose-file docker-compose.yml
```

### From Kubernetes
```bash
# Export K8s secrets
kubectl get secrets -o json | jq '.items[] | .data' > k8s-secrets.json

# Import to VaultRunner
vaultrunner bulk-set k8s-secrets.json --namespace k8s-migration --from-file

# Generate K8s manifests
vaultrunner templates generate kubernetes --namespace myapp
```

## 🛠️ Configuration

Create `.vaultrunner.yml` in your project:

```yaml
# Vault connection
vault_addr: "http://localhost:8200"
vault_token: "your-token"

# Namespace settings
default_namespace: myapp
secret_namespace: production

# Deployment settings
environment: production
auto_backup: true
backup_retention_days: 30

# Docker settings
compose_file: docker-compose.yml
network_mode: bridge

# Export settings
export_format: env
```

## 🔧 Development

### Local Setup
```bash
# Clone and setup
git clone https://github.com/1trippycat/vaultrunner.git
cd vaultrunner

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt
pip install -e .

# Run tests
python -m pytest

# Run directly
python src/vaultrunner/main.py --help
```

### Project Structure
```
vaultrunner/
├── src/vaultrunner/
│   ├── commands/          # Command implementations
│   ├── config/           # Configuration management
│   ├── core/            # Core CLI and initialization
│   ├── models/          # Data models
│   ├── security/        # Security utilities
│   ├── utils/           # Utility functions
│   └── vault/           # Vault client integration
├── docs/               # Comprehensive documentation
├── docker/            # Docker configurations
├── install.sh         # Installation script
└── pyproject.toml     # Python project configuration
```

## 🤖 MCP Server Integration

VaultRunner is designed to work as an MCP (Model Context Protocol) server:

```bash
# Run as MCP server
vaultrunner mcp-server --port 3000
(ALPHA FEATURE -- make an issue if you find a bug)
# Connect to MCP client
# Server provides tools for:
# - Secret management with namespaces
# - Deployment automation
# - Template generation
# - Migration workflows
```

### MCP Tools Available
- `vault_secrets_add`: Add secrets with namespace support
- `vault_secrets_get`: Retrieve secrets from namespaces
- `vault_deploy`: Deploy applications with secret injection
- `vault_templates_generate`: Generate configuration templates
- `vault_migrate`: Migrate from existing secret systems

## 🛡️ Security

VaultRunner follows security best practices:

- ✅ Input validation and sanitization
- ✅ Secure secret handling (no secrets in logs)
- ✅ Environment verification
- ✅ No hardcoded credentials
- ✅ Principle of least privilege
- ✅ SSL/TLS verification for Vault connections
- ✅ Namespace isolation for multi-tenant scenarios
- ✅ **Password Protection**: All operations require password authentication
- ✅ **Encrypted Key Storage**: Vault keys are encrypted with AES-256
- ✅ **SSL Certificate Generation**: Automatic SSL certificate creation
- ✅ **Backup Encryption**: Encrypted backups with password protection

### Secure Vault Initialization

```bash
# Initialize secure vault with password protection
vaultrunner secure init

# Export encrypted vault key for backup
vaultrunner secure export-key backup-key.enc

# Change vault password
vaultrunner secure change-password
```

### Encrypted Backup & Restore

```bash
# Create encrypted backup
vaultrunner backup create --namespace production --password

# Restore from encrypted backup
vaultrunner backup restore backup-file.enc --password
```

## 📚 Documentation

- [📖 Complete Documentation](./docs/)
- [🔧 API Reference](./docs/api.md)
- [🚀 Migration Guide](./docs/migration.md)
- [🐳 Docker Integration](./docs/docker.md)
- [🔗 MCP Server Guide](./docs/mcp-server.md)

## 📝 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📚 [Documentation](./docs/)
- 🐛 [Issues](https://github.com/1trippycat/vaultrunner/issues)
- 💬 [Discussions](https://github.com/1trippycat/vaultrunner/discussions)

## 🔗 Related Projects

- [HashiCorp Vault](https://www.vaultproject.io/)
- [Docker](https://www.docker.com/)
- [Docker Compose](https://docs.docker.com/compose/)

---

**VaultRunner** - Simplifying HashiCorp Vault integration for modern containerized applications.