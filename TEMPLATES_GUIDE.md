# VaultRunner Templates System

VaultRunner's template system helps you quickly generate configuration files for Docker, Kubernetes, and deployment workflows that integrate with HashiCorp Vault.

## How Templates Work

Templates are stored in `.vault/templates/` within your project directory and provide:

1. **Example patterns** for common secret management scenarios
2. **Generated configurations** based on your actual secrets
3. **Ready-to-use scripts** for deployment and backup workflows
4. **Namespace-aware templates** that work with your secret organization

## Quick Start

```bash
# Install example templates in your project
vaultrunner templates install

# List available templates
vaultrunner templates list

# Show a specific template
vaultrunner templates show docker-compose-env

# Generate a template for your namespace
vaultrunner templates generate docker-compose --namespace myapp
```

## Available Template Types

### 1. Docker Compose Templates
Perfect for Docker users transitioning to Vault:

```bash
# Generate docker-compose environment override
vaultrunner templates generate docker-compose --namespace myapp --output docker-compose.override.yml

# This creates a file that pulls secrets from Vault:
# services:
#   app:
#     environment:
#       - DATABASE_URL=${VAULT_SECRET:myapp/database/url}
#       - API_KEY=${VAULT_SECRET:myapp/api/key}
```

### 2. Environment File Templates
For shell/script integration:

```bash
# Generate environment variables file
vaultrunner templates generate env --namespace production --output prod.env

# Source the generated file:
# source <(vaultrunner templates generate env --namespace production)
```

### 3. Kubernetes Templates
For Kubernetes deployments:

```bash
# Generate Kubernetes secrets manifest
vaultrunner templates generate kubernetes --namespace myapp --output k8s-secrets.yaml

# Creates K8s Secret with data pulled from Vault
```

### 4. Deployment Scripts
Automated deployment with secret injection:

```bash
# Generate deployment script
vaultrunner templates generate deployment --namespace staging --output deploy.sh
chmod +x deploy.sh

# Script automatically pulls secrets and deploys
./deploy.sh
```

### 5. Backup Scripts
Backup your namespace secrets:

```bash
# Generate backup script
vaultrunner templates generate backup --namespace production --output backup.sh
chmod +x backup.sh

# Creates timestamped backups of all secrets
./backup.sh
```

## Example Workflow: Docker User Migration

### Step 1: Current Docker Setup
You have a `docker-compose.yml` with hardcoded secrets:
```yaml
services:
  app:
    environment:
      - DATABASE_URL=postgres://user:pass@localhost/db
      - API_KEY=abc123
```

### Step 2: Move Secrets to Vault
```bash
# Import your secrets to VaultRunner
vaultrunner secrets add database/url "postgres://user:pass@localhost/db" --namespace myapp
vaultrunner secrets add api/key "abc123" --namespace myapp
```

### Step 3: Generate Templates
```bash
# Install templates if not already done
vaultrunner templates install

# Generate docker-compose override
vaultrunner templates generate docker-compose --namespace myapp --output docker-compose.override.yml
```

### Step 4: Update Your Deployment
Your new `docker-compose.override.yml`:
```yaml
version: '3.8'
services:
  app:
    environment:
      - DATABASE_URL=${VAULT_SECRET:myapp/database/url}
      - API_KEY=${VAULT_SECRET:myapp/api/key}
      - APP_ENV=myapp
```

### Step 5: Deploy Securely
```bash
# Generate deployment script
vaultrunner templates generate deployment --namespace myapp --output deploy.sh
chmod +x deploy.sh

# Deploy with secrets from Vault
./deploy.sh
```

## Template Features

### Namespace Integration
Templates automatically work with your namespace structure:
```bash
# Different environments, same template
vaultrunner templates generate env --namespace development
vaultrunner templates generate env --namespace staging  
vaultrunner templates generate env --namespace production
```

### Smart Secret Detection
Templates adapt to your actual secrets:
- If you have secrets in Vault, they're included in generated templates
- Missing secrets are shown as placeholders
- Templates suggest common secret names (database/url, api/key, etc.)

### Ready-to-Run Scripts
Generated scripts include:
- Error handling (`set -euo pipefail`)
- Logging and status messages
- Automatic detection of deployment type (Docker vs K8s)
- Backup compression and timestamping

## Customizing Templates

### Edit Existing Templates
```bash
# Show template content
vaultrunner templates show docker-compose-env

# Templates are stored in .vault/templates/
ls .vault/templates/
```

### Create Your Own Templates
Templates use simple variable substitution:
- `{{namespace}}` - replaced with target namespace
- `$$VAULT_SECRET:{{namespace}}/path` - placeholder for secret reference

### Template Variables
Available in all templates:
- `{{namespace}}` - Target namespace name
- Current date/time (in script templates)
- Dynamic secret lists (when connected to Vault)

## Advanced Usage

### Team Templates
Share templates across your team by committing `.vault/templates/` to git:
```bash
# Add templates to version control
git add .vault/templates/
git commit -m "Add VaultRunner templates for team"
```

### CI/CD Integration
Use templates in your CI/CD pipelines:
```bash
# In your CI script
vaultrunner templates generate deployment --namespace $CI_ENVIRONMENT --output deploy.sh
./deploy.sh
```

### Multi-Environment Deployment
```bash
# Generate configs for all environments
for env in development staging production; do
    vaultrunner templates generate docker-compose --namespace $env --output docker-compose.$env.yml
done
```

## Template Updates

When you upgrade VaultRunner, you can refresh templates:
```bash
# Update templates with new features
vaultrunner templates install --force

# This preserves your custom templates and updates examples
```

## Security Features

Templates follow VaultRunner's security-first design:
- **No secrets in files**: Templates reference Vault paths, not actual secret values
- **Runtime secret injection**: Secrets are fetched only when scripts run
- **Namespace isolation**: Templates respect namespace boundaries
- **Secure permissions**: Generated script files get appropriate permissions

## Migration Patterns

### From Docker Secrets
```bash
# 1. Export Docker secrets to env file
# 2. Import to VaultRunner
vaultrunner import env docker-secrets.env --namespace myapp
# 3. Generate new docker-compose template
vaultrunner templates generate docker-compose --namespace myapp
```

### From Environment Variables
```bash
# 1. Export current env vars
env | grep "^API_\|^DB_" > current.env
# 2. Import to VaultRunner  
vaultrunner import env current.env --namespace myapp
# 3. Generate deployment template
vaultrunner templates generate deployment --namespace myapp
```

### From Kubernetes ConfigMaps/Secrets
```bash
# 1. Generate backup of current config
vaultrunner templates generate backup --namespace k8s-migration
# 2. Import secrets to VaultRunner
# 3. Generate new K8s manifests
vaultrunner templates generate kubernetes --namespace myapp
```

This template system makes VaultRunner incredibly practical for real-world Docker and Kubernetes workflows while maintaining enterprise-grade security!