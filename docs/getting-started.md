# Getting Started with VaultRunner

Welcome to VaultRunner! This guide will get you up and running with secure secret management for your containerized applications.

## 📋 Prerequisites

Before installing VaultRunner, ensure you have:

- **Python 3.8+** installed
- **Docker and Docker Compose** (for deployment features)
- **HashiCorp Vault** server (local or remote)
- **Git** (for cloning the repository)

## 🚀 Installation

### Option 1: Install from Source (Recommended for Development)

```bash
# Clone the repository
git clone https://github.com/1trippycat/core.git
cd core/vaultrunner

# Install in development mode
pip install -e .

# Verify installation
vaultrunner --version
```

### Option 2: Install from PyPI (Coming Soon)

```bash
# When available on PyPI
pip install vaultrunner
```

### Option 3: Docker Installation

```bash
# Build and run with Docker
docker build -t vaultrunner .
docker run --rm vaultrunner --help
```

## ⚙️ Configuration

### 1. Vault Server Setup

VaultRunner needs access to a HashiCorp Vault server. You can:

**Use a local Vault dev server:**

```bash
# Start local Vault for development
docker run -d --name vault-dev \
  -p 8200:8200 \
  -e VAULT_DEV_ROOT_TOKEN_ID=myroot \
  vault:latest

export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=myroot
```

**Use an existing Vault server:**

```bash
export VAULT_ADDR=https://vault.mycompany.com:8200
export VAULT_TOKEN=your-vault-token
```

### 2. VaultRunner Configuration

Create a configuration file `.vaultrunner.yml` in your project:

```yaml
# .vaultrunner.yml
vault:
  addr: http://localhost:8200
  token: myroot
  namespace: default

logging:
  level: info

docker:
  compose_file: docker-compose.yml
```

### 3. Secure Vault Initialization

For enhanced security, initialize VaultRunner with password protection:

```bash
# Initialize secure vault (recommended)
vaultrunner secure init

# This will:
# - Prompt for a master password
# - Generate SSL certificates
# - Encrypt your vault token
# - Create secure key storage
```

**Alternative: Basic Setup (less secure)**

If you prefer not to use password protection:

```bash
# Skip secure initialization
# Vault token will be stored in plain text
export VAULT_TOKEN=myroot
```

## 🏃‍♂️ Your First Secrets

### 1. Add Your First Secret

```bash
# Add a simple secret (will prompt for password if secure vault is initialized)
vaultrunner secrets add database/password "mysecretpassword"

# Add with custom namespace
vaultrunner secrets add api/key "myapikey" --namespace myapp
```

### 2. List Secrets

```bash
# List all secrets (will prompt for password if secure vault is initialized)
vaultrunner secrets list

# List secrets in specific namespace
vaultrunner secrets list --namespace myapp
```

### 3. Retrieve Secrets

```bash
# Get a specific secret (will prompt for password if secure vault is initialized)
vaultrunner secrets get database/password

# Get all secrets in namespace
vaultrunner secrets get --namespace myapp
```

## 🚀 Your First Deployment

### 1. Create a Docker Compose File

```yaml
# docker-compose.yml
version: '3.8'
services:
  app:
    image: nginx:latest
    environment:
      - DATABASE_PASSWORD=${DATABASE_PASSWORD}
      - API_KEY=${API_KEY}
    ports:
      - "8080:80"
```

### 2. Deploy with Vault Integration

```bash
# Deploy with namespace
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml

# Deploy with dry-run first
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml --dry-run
```

### 3. Verify Deployment

```bash
# Check if services are running
docker compose ps

# Check logs for secret injection
docker compose logs app | grep -i vault

# Verify environment variables
docker compose exec app env | grep -E '(DATABASE|API)'
```

## 🔄 Migration Example

### Migrate from .env Files

```bash
# 1. Import existing .env file
vaultrunner import env .env --namespace myapp

# 2. Update docker-compose.yml to use Vault
vaultrunner templates create docker-compose --namespace myapp

# 3. Deploy with Vault integration
vaultrunner deploy --namespace myapp --compose-file docker-compose.vault.yml
```

## 💾 Backup & Restore

### Create Encrypted Backup

```bash
# Create encrypted backup of all secrets
vaultrunner backup create --namespace myapp --output myapp-backup.enc

# This will:
# - Prompt for encryption password
# - Collect all secrets in namespace
# - Create encrypted backup file
```

### Restore from Backup

```bash
# Restore secrets from encrypted backup
vaultrunner backup restore myapp-backup.enc --namespace myapp

# This will:
# - Prompt for decryption password
# - Restore all secrets to namespace
# - Verify restoration
```

## 🧪 Testing Your Setup

### Run the Test Suite

```bash
# Run all tests
python -m pytest

# Run with coverage
python -m pytest --cov=vaultrunner
```

### Validate Configuration

```bash
# Check Vault connection
vaultrunner vault status

# Validate Docker setup
vaultrunner docker validate docker-compose.yml
```

## 🐛 Troubleshooting

### Common Issues

#### "Vault server not reachable"

```bash
# Check Vault address
echo $VAULT_ADDR

# Test Vault connection
curl $VAULT_ADDR/v1/sys/health
```

#### "Permission denied"

```bash
# Check Vault token
echo $VAULT_TOKEN

# Verify token has necessary permissions
vaultrunner vault auth check
```

#### "Docker compose file not found"

```bash
# Check current directory
pwd
ls -la docker-compose.yml

# Use absolute path
vaultrunner deploy --compose-file /path/to/docker-compose.yml
```

## 📚 Next Steps

Now that you have VaultRunner running, explore:

- **[Core Concepts](../core-concepts.md)** - Learn about namespaces and workflows
- **[Command Reference](../commands.md)** - Discover all available commands
- **[Migration Guide](../migration.md)** - Migrate existing applications
- **[Docker Integration](../docker.md)** - Advanced Docker features

## 🎯 Quick Reference

```bash
# Add secrets
vaultrunner secrets add path/to/secret "value" --namespace myapp

# Deploy applications
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml

# Import from .env
vaultrunner import env .env --namespace myapp

# List secrets
vaultrunner secrets list --namespace myapp

# Get help
vaultrunner --help
vaultrunner <command> --help
```

Happy deploying! 🚀
