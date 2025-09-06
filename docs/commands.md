# Command Reference

This document provides a comprehensive reference for all VaultRunner commands and their options.

## 📋 Command Overview

VaultRunner organizes commands into logical groups:

| Command Group | Description | Key Commands |
|---------------|-------------|--------------|
| **Secrets** | Secret management operations | `add`, `get`, `list`, `delete` |
| **Templates** | Template generation and rendering | `create`, `render`, `validate` |
| **Deploy** | Namespace-aware deployments | `deploy` |
| **Docker** | Docker-specific operations | `upgrade`, `validate` |
| **Bulk** | Batch operations | `bulk-set`, `bulk-get` |
| **Export** | Configuration export | `export` |
| **Vault** | Vault server operations | `status`, `auth` |
| **Secure** | Security management | `init`, `export-key`, `change-password` |
| **Backup** | Backup and restore | `create`, `restore` |

## 🔐 Secrets Commands

### `secrets add`

Add a new secret to Vault.

```bash
vaultrunner secrets add <path> <value> [OPTIONS]
```

**Parameters:**
- `path`: Secret path (e.g., `database/password`)
- `value`: Secret value

**Options:**
- `--namespace, -n`: Secret namespace (default: from config)
- `--file, -f`: Read value from file instead of argument
- `--vault-addr`: Override Vault server address

**Examples:**
```bash
# Add a simple secret
vaultrunner secrets add database/password "mysecret"

# Add with namespace
vaultrunner secrets add api/key "apikey123" --namespace production

# Read from file
vaultrunner secrets add ssl/cert "$(cat cert.pem)" --namespace myapp
```

### `secrets get`

Retrieve a secret from Vault.

```bash
vaultrunner secrets get <path> [OPTIONS]
```

**Parameters:**
- `path`: Secret path to retrieve

**Options:**
- `--namespace, -n`: Secret namespace
- `--all`: Get all secrets in namespace
- `--json`: Output in JSON format

**Examples:**
```bash
# Get specific secret
vaultrunner secrets get database/password

# Get all secrets in namespace
vaultrunner secrets get --all --namespace myapp

# Get in JSON format
vaultrunner secrets get database/password --json
```

### `secrets list`

List secrets in a namespace.

```bash
vaultrunner secrets list [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace
- `--prefix`: Filter by path prefix
- `--json`: Output in JSON format

**Examples:**
```bash
# List all secrets in default namespace
vaultrunner secrets list

# List secrets in specific namespace
vaultrunner secrets list --namespace production

# Filter by prefix
vaultrunner secrets list --prefix database
```

### `secrets delete`

Delete a secret from Vault.

```bash
vaultrunner secrets delete <path> [OPTIONS]
```

**Parameters:**
- `path`: Secret path to delete

**Options:**
- `--namespace, -n`: Secret namespace
- `--force`: Skip confirmation prompt

**Examples:**
```bash
# Delete specific secret
vaultrunner secrets delete database/password

# Delete with namespace
vaultrunner secrets delete api/key --namespace production

# Force delete without confirmation
vaultrunner secrets delete old/secret --force
```

## 📄 Templates Commands

### `templates create`

Create templates for various platforms.

```bash
vaultrunner templates create <type> [OPTIONS]
```

**Parameters:**
- `type`: Template type (`docker-compose`, `kubernetes`, `env`)

**Options:**
- `--namespace, -n`: Secret namespace
- `--output, -o`: Output file path
- `--compose-file`: Source compose file for docker-compose templates

**Examples:**
```bash
# Create Docker Compose template
vaultrunner templates create docker-compose --namespace myapp

# Create Kubernetes template
vaultrunner templates create kubernetes --namespace production

# Save to specific file
vaultrunner templates create env --namespace myapp --output .env.vault
```

### `templates render`

Render a template to stdout.

```bash
vaultrunner templates render <type> [OPTIONS]
```

**Parameters:**
- `type`: Template type to render

**Options:**
- `--namespace, -n`: Secret namespace
- `--compose-file`: Source compose file

**Examples:**
```bash
# Render Docker Compose template
vaultrunner templates render docker-compose --namespace myapp

# Render with custom compose file
vaultrunner templates render docker-compose --compose-file docker-compose.prod.yml
```

### `templates validate`

Validate a template file.

```bash
vaultrunner templates validate <file> [OPTIONS]
```

**Parameters:**
- `file`: Template file to validate

**Options:**
- `--type`: Template type (`docker-compose`, `kubernetes`, `env`)

**Examples:**
```bash
# Validate Docker Compose template
vaultrunner templates validate docker-compose.vault.yml --type docker-compose

# Validate Kubernetes template
vaultrunner templates validate deployment.yaml --type kubernetes
```

## 🚀 Deploy Command

### `deploy`

Deploy applications with Vault secret injection.

```bash
vaultrunner deploy [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace
- `--compose-file, -f`: Docker Compose file (default: docker-compose.yml)
- `--vault-addr`: Override Vault server address
- `--env-file`: Environment file to load
- `--services`: Comma-separated list of services to deploy
- `--network`: Docker network to use
- `--auto-networks`: Automatically detect networks
- `--sidecar`: Deploy with VaultRunner sidecar
- `--dry-run`: Show deployment plan without executing

**Examples:**
```bash
# Basic deployment
vaultrunner deploy --namespace myapp

# Deploy specific services
vaultrunner deploy --namespace production --services web,api

# Dry run deployment
vaultrunner deploy --namespace staging --dry-run

# Deploy with sidecar
vaultrunner deploy --namespace myapp --sidecar
```

## 🐳 Docker Commands

### `docker upgrade`

Upgrade Docker Compose files with Vault integration.

```bash
vaultrunner docker upgrade <compose-file> [OPTIONS]
```

**Parameters:**
- `compose-file`: Docker Compose file to upgrade

**Options:**
- `--namespace, -n`: Secret namespace
- `--output, -o`: Output file path
- `--backup`: Create backup of original file

**Examples:**
```bash
# Upgrade compose file
vaultrunner docker upgrade docker-compose.yml --namespace myapp

# Upgrade with backup
vaultrunner docker upgrade docker-compose.yml --backup

# Save to different file
vaultrunner docker upgrade docker-compose.yml --output docker-compose.vault.yml
```

### `docker validate`

Validate Docker Compose files.

```bash
vaultrunner docker validate <compose-file>
```

**Parameters:**
- `compose-file`: Docker Compose file to validate

**Examples:**
```bash
# Validate compose file
vaultrunner docker validate docker-compose.yml

# Validate multiple files
vaultrunner docker validate docker-compose.yml docker-compose.prod.yml
```

## 📦 Bulk Commands

### `bulk-set`

Set multiple secrets from a file.

```bash
vaultrunner bulk-set [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace
- `--input, -i`: Input file (JSON/YAML)
- `--format`: Input format (`json`, `yaml`, `env`)

**Examples:**
```bash
# Import from JSON
vaultrunner bulk-set --input secrets.json --namespace myapp

# Import from YAML
vaultrunner bulk-set --input secrets.yaml --format yaml --namespace production

# Import from .env
vaultrunner bulk-set --input .env --format env --namespace staging
```

### `bulk-get`

Get multiple secrets to a file.

```bash
vaultrunner bulk-get [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace
- `--output, -o`: Output file
- `--format`: Output format (`json`, `yaml`, `env`)
- `--prefix`: Filter by path prefix

**Examples:**
```bash
# Export to JSON
vaultrunner bulk-get --namespace myapp --output secrets.json

# Export specific prefix
vaultrunner bulk-get --namespace production --prefix database --output db-secrets.json

# Export as environment file
vaultrunner bulk-get --namespace staging --format env --output .env
```

## 📤 Export Command

### `export`

Export VaultRunner configuration.

```bash
vaultrunner export [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace
- `--output, -o`: Output file
- `--format`: Export format (`json`, `yaml`, `env`)
- `--include-config`: Include VaultRunner configuration

**Examples:**
```bash
# Export secrets as JSON
vaultrunner export --namespace myapp --output vault-secrets.json

# Export as environment file
vaultrunner export --namespace production --format env --output .env

# Export with configuration
vaultrunner export --include-config --output full-config.yaml
```

## 🔒 Vault Commands

### `vault status`

Check Vault server status.

```bash
vaultrunner vault status
```

**Examples:**
```bash
# Check Vault status
vaultrunner vault status
```

### `vault auth`

Check authentication status.

```bash
vaultrunner vault auth
```

**Examples:**
```bash
# Check auth status
vaultrunner vault auth
```

## 🔄 Import Commands

### `import env`

Import secrets from .env files.

```bash
vaultrunner import env <env-file> [OPTIONS]
```

**Parameters:**
- `env-file`: Environment file to import

**Options:**
- `--namespace, -n`: Target namespace
- `--prefix`: Path prefix for imported secrets
- `--dry-run`: Show what would be imported

**Examples:**
```bash
# Import .env file
vaultrunner import env .env --namespace myapp

# Import with prefix
vaultrunner import env config.env --namespace production --prefix config

# Dry run import
vaultrunner import env .env --dry-run
```

### `import docker`

Import secrets from Docker Compose files.

```bash
vaultrunner import docker <compose-file> [OPTIONS]
```

**Parameters:**
- `compose-file`: Docker Compose file to import from

**Options:**
- `--namespace, -n`: Target namespace
- `--dry-run`: Show what would be imported

**Examples:**
```bash
# Import from compose file
vaultrunner import docker docker-compose.yml --namespace myapp

# Dry run import
vaultrunner import docker docker-compose.yml --dry-run
```

## 🏗️ Namespace Commands

### `namespace create`

Create a new namespace.

```bash
vaultrunner namespace create <name> [OPTIONS]
```

**Parameters:**
- `name`: Namespace name

**Options:**
- `--description`: Namespace description

**Examples:**
```bash
# Create namespace
vaultrunner namespace create myapp

# Create with description
vaultrunner namespace create production --description "Production environment"
```

### `namespace list`

List all namespaces.

```bash
vaultrunner namespace list
```

**Examples:**
```bash
# List namespaces
vaultrunner namespace list
```

### `namespace delete`

Delete a namespace.

```bash
vaultrunner namespace delete <name> [OPTIONS]
```

**Parameters:**
- `name`: Namespace name

**Options:**
- `--force`: Skip confirmation

**Examples:**
```bash
# Delete namespace
vaultrunner namespace delete old-namespace

# Force delete
vaultrunner namespace delete old-namespace --force
```

## 🔐 Secure Commands

### `secure init`

Initialize secure vault with password protection and SSL certificates.

```bash
vaultrunner secure init [OPTIONS]
```

**Options:**
- `--vault-addr`: Vault server address
- `--ssl-cert`: Custom SSL certificate file
- `--ssl-key`: Custom SSL private key file

**Examples:**
```bash
# Initialize secure vault
vaultrunner secure init

# Initialize with custom SSL certificates
vaultrunner secure init --ssl-cert mycert.pem --ssl-key mykey.pem
```

### `secure export-key`

Export encrypted vault key for backup.

```bash
vaultrunner secure export-key <output-file> [OPTIONS]
```

**Parameters:**
- `output-file`: Output file for encrypted key

**Options:**
- `--vault-addr`: Vault server address

**Examples:**
```bash
# Export encrypted vault key
vaultrunner secure export-key vault-key.enc

# Export to specific location
vaultrunner secure export-key /secure/backup/vault-key.enc
```

### `secure change-password`

Change the master password for vault access.

```bash
vaultrunner secure change-password [OPTIONS]
```

**Options:**
- `--vault-addr`: Vault server address

**Examples:**
```bash
# Change master password
vaultrunner secure change-password
```

## 💾 Backup Commands

### `backup create`

Create encrypted backup of vault secrets.

```bash
vaultrunner backup create [OPTIONS]
```

**Options:**
- `--namespace, -n`: Secret namespace to backup
- `--output, -o`: Output file for backup
- `--vault-addr`: Vault server address
- `--include-metadata`: Include backup metadata

**Examples:**
```bash
# Create backup of all namespaces
vaultrunner backup create --output vault-backup.enc

# Backup specific namespace
vaultrunner backup create --namespace production --output prod-backup.enc

# Include metadata in backup
vaultrunner backup create --include-metadata --output full-backup.enc
```

### `backup restore`

Restore secrets from encrypted backup.

```bash
vaultrunner backup restore <backup-file> [OPTIONS]
```

**Parameters:**
- `backup-file`: Encrypted backup file to restore from

**Options:**
- `--namespace, -n`: Target namespace for restore
- `--vault-addr`: Vault server address
- `--dry-run`: Show what would be restored

**Examples:**
```bash
# Restore from backup
vaultrunner backup restore vault-backup.enc

# Restore to specific namespace
vaultrunner backup restore prod-backup.enc --namespace production

# Dry run restore
vaultrunner backup restore vault-backup.enc --dry-run
```

## ⚙️ Global Options

All commands support these global options:

- `--help, -h`: Show help message
- `--version, -V`: Show version information
- `--config`: Configuration file path
- `--log-level`: Logging level (`debug`, `info`, `warning`, `error`)
- `--dry-run`: Show what would be done
- `--vault-addr`: Vault server address
- `--vault-token`: Vault authentication token

## 📊 Exit Codes

VaultRunner uses standard exit codes:

- `0`: Success
- `1`: General error
- `2`: Invalid arguments
- `130`: Interrupted by user (Ctrl+C)

## 🔍 Examples

### Complete Workflow

```bash
# 1. Setup namespace
vaultrunner namespace create myapp

# 2. Add secrets
vaultrunner secrets add database/password "secret123" --namespace myapp
vaultrunner secrets add api/key "apikey456" --namespace myapp

# 3. Create deployment template
vaultrunner templates create docker-compose --namespace myapp

# 4. Deploy application
vaultrunner deploy --namespace myapp --compose-file docker-compose.vault.yml

# 5. Verify deployment
docker compose logs | grep -i vault
```

### Migration Workflow

```bash
# 1. Import existing secrets
vaultrunner import env .env --namespace production

# 2. Bulk export for backup
vaultrunner bulk-get --namespace production --output backup.json

# 3. Deploy with new setup
vaultrunner deploy --namespace production --compose-file docker-compose.yml
```

### CI/CD Integration

```bash
# In CI/CD pipeline
export VAULT_ADDR=$VAULT_ADDR
export VAULT_TOKEN=$VAULT_TOKEN

# Deploy to staging
vaultrunner deploy --namespace staging --dry-run
vaultrunner deploy --namespace staging

# Deploy to production
vaultrunner deploy --namespace production --vault-addr $PROD_VAULT_ADDR
```

This reference covers all available commands. Use `vaultrunner <command> --help` for detailed help on any specific command.