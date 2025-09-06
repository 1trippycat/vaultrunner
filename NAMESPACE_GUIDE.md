# VaultRunner Enhanced Features for Docker/ENV Users

This guide shows the new namespace and migration features designed to help you transition from Docker secrets, environment variables, and other less secure secret management to HashiCorp Vault.

## Namespace Support

VaultRunner now supports optional namespaces for organizing secrets. If no namespace is specified, secrets go into a "shared" namespace by default.

### Basic Secret Operations with Namespaces

```bash
# Add secret to default "shared" namespace
vaultrunner secrets add database/password

# Add secret to specific namespace
vaultrunner secrets add database/password --namespace myapp

# Get secret from specific namespace
vaultrunner secrets get database/password --namespace myapp

# List secrets in a namespace
vaultrunner secrets list --namespace myapp
```

## Namespace Management

```bash
# List all available namespaces
vaultrunner namespace list

# List secrets in a namespace
vaultrunner namespace secrets --namespace myapp

# Copy all secrets from one namespace to another
vaultrunner namespace copy shared myapp-prod

# Delete all secrets in a namespace (requires confirmation)
vaultrunner namespace delete temp-namespace --confirm
```

## Bulk Operations

Perfect for migrating from existing systems or managing multiple secrets:

```bash
# Set multiple secrets from JSON
vaultrunner bulk-set '{"DB_HOST":"localhost","DB_PORT":"5432"}' --namespace myapp

# Set secrets from JSON file
vaultrunner bulk-set secrets.json --namespace myapp --from-file

# Get multiple secrets at once
vaultrunner bulk-get DB_HOST DB_PORT DB_NAME --namespace myapp

# Export as environment variables
vaultrunner bulk-get DB_HOST DB_PORT --namespace myapp --format env
```

## Migration from Docker/ENV Files

### From .env Files

If you have a `.env` file like:
```
DATABASE_URL=postgres://user:pass@localhost/db
API_KEY=abc123
SECRET_TOKEN=xyz789
```

Import it:
```bash
# Import to shared namespace
vaultrunner import env .env

# Import to specific namespace
vaultrunner import env .env --namespace myapp
```

### From docker-compose.yml

Import environment variables from your docker-compose file:
```bash
vaultrunner import docker-compose docker-compose.yml --namespace myapp
```

### Export Back to ENV Format

```bash
# Export secrets as .env format
vaultrunner export env --namespace myapp --output myapp.env

# Export for docker-compose
vaultrunner export docker-compose --namespace myapp --output docker-env.txt
```

## Development Workflow Examples

### Scenario 1: Team Development
```bash
# Each developer gets their own namespace
vaultrunner namespace copy shared dev-john
vaultrunner namespace copy shared dev-jane

# Shared secrets stay in 'shared' namespace
vaultrunner secrets add api/external-service --namespace shared

# Personal dev secrets
vaultrunner secrets add database/url --namespace dev-john
```

### Scenario 2: Environment Promotion
```bash
# Development secrets
vaultrunner bulk-set dev-secrets.json --namespace development

# Copy to staging when ready
vaultrunner namespace copy development staging

# Copy to production (with review)
vaultrunner namespace copy staging production
```

### Scenario 3: Migration from Docker Secrets
```bash
# 1. Export your existing docker secrets to a file
echo "DB_PASSWORD=mypassword" > docker-secrets.env
echo "API_KEY=myapikey" >> docker-secrets.env

# 2. Import to VaultRunner
vaultrunner import env docker-secrets.env --namespace myapp

# 3. Verify import
vaultrunner namespace secrets --namespace myapp

# 4. Export for docker-compose integration
vaultrunner export docker-compose --namespace myapp
```

## Configuration Tips

### Setting Default Namespace
In your `.vaultrunner.yml`:
```yaml
secret_namespace: myapp  # Use this instead of 'shared'
environment: development
auto_backup: true
```

### Multiple Environment Setup
```bash
# Different namespaces for different environments
vaultrunner bulk-set dev-config.json --namespace myapp-dev
vaultrunner bulk-set staging-config.json --namespace myapp-staging
vaultrunner bulk-set prod-config.json --namespace myapp-prod
```

## Security Best Practices

1. **Use namespaces to isolate environments**
   ```bash
   vaultrunner secrets add api-key --namespace production
   vaultrunner secrets add api-key --namespace development
   ```

2. **Regular backups** (automated with `auto_backup: true`)

3. **Use dry-run for testing**
   ```bash
   vaultrunner bulk-set secrets.json --namespace prod --dry-run
   ```

4. **Verify before deletion**
   ```bash
   vaultrunner namespace secrets --namespace temp
   vaultrunner namespace delete temp --confirm
   ```

## Common Migration Patterns

### From Docker Swarm Secrets
```bash
# Export Docker secrets to env format first
docker secret ls --format "{{.Name}}" | while read secret; do
    echo "${secret}=$(docker secret inspect $secret --format '{{.Spec.Data}}')" >> docker-migration.env
done

# Import to VaultRunner
vaultrunner import env docker-migration.env --namespace production
```

### From Kubernetes Secrets
```bash
# Export K8s secrets to files first, then import
kubectl get secrets -o json | jq '.items[] | .data' > k8s-secrets.json
vaultrunner bulk-set k8s-secrets.json --namespace k8s-migration --from-file
```

### From Environment Variables
```bash
# Export current environment to file
env | grep "^API_\|^DB_\|^SECRET_" > current-env.txt
vaultrunner import env current-env.txt --namespace myapp
```

This enhanced VaultRunner gives you the power of HashiCorp Vault with the simplicity you're used to from Docker secrets and environment variables!