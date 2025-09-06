# Core Concepts

Understanding the fundamental concepts behind VaultRunner will help you use it effectively for secure secret management in your containerized applications.

## 🏗️ Architecture Overview

VaultRunner follows a layered architecture that separates concerns and provides flexibility:

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   CLI Layer     │    │  Command Layer  │    │   Vault Layer   │
│                 │    │                 │    │                 │
│ • User Interface│    │ • Secrets Mgmt  │    │ • HashiCorp     │
│ • Configuration │    │ • Templates     │    │ • Vault Client  │
│ • Validation    │    │ • Deployment    │    │ • Auth & Tokens │
└─────────────────┘    └─────────────────┘    └─────────────────┘
         │                       │                       │
         └───────────────────────┼───────────────────────┘
                                 │
                    ┌─────────────────┐
                    │  Docker Layer   │
                    │                 │
                    │ • Compose Files │
                    │ • Secret Inject │
                    │ • Service Mgmt  │
                    └─────────────────┘
```

## 🔐 Namespaces

### What are Namespaces?

Namespaces in VaultRunner provide **isolation and organization** for your secrets. Think of them as separate compartments where related secrets are stored together.

### Namespace Benefits

- **Environment Isolation**: Keep `production`, `staging`, and `development` secrets separate
- **Team Organization**: Different teams can have their own namespaces
- **Application Grouping**: Group secrets by application or service
- **Access Control**: Control who can access which namespaces

### Namespace Examples

```bash
# Environment-based namespaces
vaultrunner secrets add db/password "prod123" --namespace production
vaultrunner secrets add db/password "dev456" --namespace development

# Application-based namespaces
vaultrunner secrets add api/key "key123" --namespace myapp-backend
vaultrunner secrets add api/key "key456" --namespace myapp-frontend

# Team-based namespaces
vaultrunner secrets add token "token123" --namespace team-alpha
vaultrunner secrets add token "token456" --namespace team-beta
```

### Default Namespace

If no namespace is specified, VaultRunner uses the `default` namespace:

```bash
# These are equivalent
vaultrunner secrets add db/password "mypass"
vaultrunner secrets add db/password "mypass" --namespace default
```

## 🔄 Migration Workflows

### The Migration Process

VaultRunner provides a streamlined migration workflow:

1. **Import** existing secrets from various sources
2. **Transform** them into Vault-compatible format
3. **Deploy** with automatic secret injection
4. **Verify** that secrets are properly injected

### Supported Sources

- **Environment Files** (`.env`)
- **Docker Secrets**
- **Docker Compose Files**
- **Kubernetes Secrets**
- **JSON/YAML Files**
- **Command Line Input**

### Migration Example

```bash
# 1. Import from .env file
vaultrunner import env .env --namespace myapp

# 2. Review imported secrets
vaultrunner secrets list --namespace myapp

# 3. Deploy with Vault integration
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml

# 4. Verify secret injection
docker compose logs app | grep -i vault
```

## 📄 Templates

### Template System

VaultRunner uses templates to generate configuration files with Vault integration:

- **Docker Compose Templates**: Generate compose files with secret references
- **Kubernetes Templates**: Generate K8s manifests with Vault annotations
- **Environment Templates**: Generate .env files from Vault secrets

### Template Types

#### Docker Compose Templates

```yaml
# Generated docker-compose.vault.yml
version: '3.8'
services:
  app:
    image: myapp:latest
    environment:
      - DATABASE_PASSWORD=${VAULT_SECRET_myapp/database/password}
      - API_KEY=${VAULT_SECRET_myapp/api/key}
    secrets:
      - database_password
      - api_key

secrets:
  database_password:
    external: true
  api_key:
    external: true
```

#### Kubernetes Templates

```yaml
# Generated deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: myapp
spec:
  template:
    spec:
      containers:
      - name: app
        env:
        - name: DATABASE_PASSWORD
          valueFrom:
            secretKeyRef:
              name: vault-secret
              key: database/password
```

### Template Commands

```bash
# Generate Docker Compose template
vaultrunner templates create docker-compose --namespace myapp

# Generate Kubernetes template
vaultrunner templates create kubernetes --namespace myapp

# Render template to stdout
vaultrunner templates render docker-compose --namespace myapp
```

## 🚀 Deployment Integration

### How Deployment Works

VaultRunner's deployment system:

1. **Reads** your Docker Compose configuration
2. **Injects** Vault secret references
3. **Deploys** the application with secret access
4. **Verifies** secret injection

### Deployment Modes

#### Standard Deployment

```bash
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml
```

#### Dry Run Mode

```bash
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml --dry-run
```

#### Sidecar Deployment

```bash
vaultrunner deploy --namespace myapp --compose-file docker-compose.yml --sidecar
```

### Secret Injection Methods

#### Environment Variables

```yaml
services:
  app:
    environment:
      - DATABASE_PASSWORD=${VAULT_SECRET_myapp/database/password}
```

#### Docker Secrets

```yaml
services:
  app:
    secrets:
      - database_password

secrets:
  database_password:
    external: true
```

#### Volume Mounts

```yaml
services:
  app:
    volumes:
      - type: volume
        source: vault-secrets
        target: /vault/secrets
```

## 🔧 Configuration Hierarchy

VaultRunner uses a hierarchical configuration system:

### 1. Global Configuration

```yaml
# ~/.vaultrunner/config.yml
vault:
  addr: https://vault.company.com:8200
  token: ${VAULT_TOKEN}
  namespace: default

logging:
  level: info
```

### 2. Project Configuration

```yaml
# .vaultrunner.yml (in project root)
vault:
  namespace: myapp

docker:
  compose_file: docker-compose.yml
```

### 3. Environment Variables

```bash
export VAULT_ADDR=https://vault.company.com:8200
export VAULT_TOKEN=your-token
export VAULTRUNNER_NAMESPACE=myapp
```

### 4. Command Line Arguments

```bash
vaultrunner deploy --namespace production --vault-addr https://prod-vault.company.com:8200
```

## 🛡️ Security Model

### Authentication

VaultRunner supports multiple authentication methods:

- **Token Authentication**: Direct Vault tokens
- **AppRole**: Application-specific authentication
- **Kubernetes Auth**: Service account authentication
- **AWS IAM**: AWS IAM role authentication

### Authorization

- **Namespace-based Access**: Users can only access authorized namespaces
- **Path-based Permissions**: Granular permissions on secret paths
- **Audit Logging**: All operations are logged for compliance

### Secret Handling

- **No Secret Persistence**: Secrets are never stored locally
- **Memory-only Operations**: Secrets exist only in memory during operations
- **Secure Communication**: All communication with Vault is encrypted

## 🔐 Advanced Security Features

### Password Protection

VaultRunner supports enterprise-grade password protection for all operations:

- **Master Password**: Single password to access all vault operations
- **Encrypted Key Storage**: Vault keys are encrypted with AES-256
- **PBKDF2 Key Derivation**: Secure password hashing with salt
- **Automatic Prompting**: Password automatically requested for secure operations

### SSL Certificate Generation

Automatic SSL certificate generation for secure communication:

- **Self-Signed Certificates**: Generated for development and testing
- **Certificate Authority**: Custom CA support for production
- **Automatic Renewal**: Certificate lifecycle management
- **Secure Storage**: Certificates stored in encrypted key storage

### Encrypted Backup System

Comprehensive backup and restore functionality:

- **Password-Protected Backups**: All backups encrypted with user password
- **Namespace Isolation**: Backup and restore specific namespaces
- **Metadata Preservation**: Backup includes timestamps and version info
- **Verification**: Restore operations verify data integrity

### Secure Key Management

Advanced key management system:

- **AES-256 Encryption**: Industry-standard encryption for stored keys
- **Secure File Storage**: Keys stored in platform-specific secure locations
- **Export/Import**: Encrypted key export for backup and migration
- **Password Changes**: Secure password update without data loss

## 🔄 Workflows

### Development Workflow

```bash
# 1. Setup local Vault
docker run -d --name vault-dev -p 8200:8200 vault:latest

# 2. Configure VaultRunner
export VAULT_ADDR=http://localhost:8200
export VAULT_TOKEN=root

# 3. Add development secrets
vaultrunner secrets add db/password "dev123" --namespace myapp-dev

# 4. Deploy locally
vaultrunner deploy --namespace myapp-dev --compose-file docker-compose.yml
```

### Production Workflow

```bash
# 1. Use production Vault
export VAULT_ADDR=https://vault.company.com:8200
export VAULT_TOKEN=${PROD_VAULT_TOKEN}

# 2. Deploy to production
vaultrunner deploy --namespace myapp-prod --compose-file docker-compose.prod.yml

# 3. Verify deployment
docker compose logs app | grep -i vault
```

### Secure Production Workflow

```bash
# 1. Initialize secure vault (one-time setup)
vaultrunner secure init

# 2. Export encrypted key for backup
vaultrunner secure export-key prod-vault-key.enc

# 3. Create encrypted backup before changes
vaultrunner backup create --namespace production --output prod-backup.enc

# 4. Deploy with security
vaultrunner deploy --namespace production --compose-file docker-compose.yml

# 5. Change password periodically
vaultrunner secure change-password
```

### CI/CD Integration

```yaml
# .github/workflows/deploy.yml
name: Deploy
on: [push]

jobs:
  deploy:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v2
    - name: Deploy with VaultRunner
      run: |
        export VAULT_ADDR=${{ secrets.VAULT_ADDR }}
        export VAULT_TOKEN=${{ secrets.VAULT_TOKEN }}
        vaultrunner deploy --namespace production --compose-file docker-compose.yml
```

## 📊 Monitoring & Observability

### Health Checks

```bash
# Check Vault connectivity
vaultrunner vault status

# Validate configuration
vaultrunner docker validate docker-compose.yml
```

### Logging

VaultRunner provides comprehensive logging:

- **Operation Logs**: All Vault operations are logged
- **Error Tracking**: Detailed error information
- **Audit Trail**: Complete audit trail for compliance

### Metrics

Monitor your VaultRunner usage:

- **Secret Access Patterns**: Track which secrets are accessed
- **Deployment Success Rates**: Monitor deployment success
- **Performance Metrics**: Track operation performance

## 🎯 Best Practices

### Namespace Organization

- Use consistent naming conventions
- Group related applications together
- Separate environments clearly
- Document namespace purposes

### Secret Management

- Rotate secrets regularly
- Use strong, random values
- Avoid hardcoding secrets
- Use appropriate permission levels

### Deployment Practices

- Always test deployments in staging first
- Use dry-run mode for validation
- Monitor logs after deployment
- Have rollback procedures ready

### Security Practices

- Use least-privilege access
- Rotate Vault tokens regularly
- Enable audit logging
- Keep VaultRunner updated

This foundation will help you effectively use VaultRunner for secure, scalable secret management in your containerized applications.
