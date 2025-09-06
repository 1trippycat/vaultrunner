"""
Templates Command Module

Handles template file generation and management.
Creates useful templates for Docker, Kubernetes, and environment file integration.
"""

import os
import json
from pathlib import Path
from argparse import ArgumentParser, Namespace
from typing import Dict, List, Any

from ..models.config import VaultRunnerConfig
from ..utils.logging import get_logger
from ..vault.client import VaultClient

logger = get_logger(__name__)


def register_templates_parser(subparsers):
    """Register templates subcommand parser."""
    parser = subparsers.add_parser(
        "templates",
        help="Manage template files",
        description="Generate and manage template files for Docker, Kubernetes, and environment integration",
    )

    templates_subparsers = parser.add_subparsers(
        dest="templates_command", help="Template operations"
    )

    # List templates command
    list_parser = templates_subparsers.add_parser(
        "list", help="List available templates"
    )

    # Install templates command
    install_parser = templates_subparsers.add_parser(
        "install", help="Install example templates"
    )
    install_parser.add_argument(
        "--force", "-f", action="store_true", help="Overwrite existing templates"
    )

    # Generate template command
    generate_parser = templates_subparsers.add_parser(
        "generate", help="Generate a specific template"
    )
    generate_parser.add_argument(
        "template_type",
        choices=["docker-compose", "env", "kubernetes", "deployment", "backup"],
        help="Type of template to generate",
    )
    generate_parser.add_argument(
        "--namespace", "-n", help="Target namespace for secrets"
    )
    generate_parser.add_argument("--output", "-o", help="Output file path")

    # Show template command
    show_parser = templates_subparsers.add_parser("show", help="Show template content")
    show_parser.add_argument("template_name", help="Template name to show")


class TemplatesCommand:
    """Template management command handler."""

    def __init__(self, config: VaultRunnerConfig):
        self.config = config
        self.vault_client = VaultClient(config)
        self.templates_dir = Path(config.vault_dir) / "templates"

    def execute(self, args: Namespace) -> int:
        """Execute templates command."""
        try:
            if args.templates_command == "list":
                return self._list_templates(args)
            elif args.templates_command == "install":
                return self._install_templates(args)
            elif args.templates_command == "generate":
                return self._generate_template(args)
            elif args.templates_command == "show":
                return self._show_template(args)
            else:
                logger.error("Unknown templates command: %s", args.templates_command)
                return 1
        except Exception as e:
            logger.error("Templates command failed: %s", str(e))
            return 1

    def _list_templates(self, args: Namespace) -> int:
        """List available templates."""
        if not self.templates_dir.exists():
            print(
                "No templates directory found. Run 'vaultrunner templates install' to create example templates."
            )
            return 0

        templates = list(self.templates_dir.glob("*.template"))
        if not templates:
            print("No templates found in .vault/templates/")
            return 0

        print("Available templates:")
        for template in sorted(templates):
            template_name = template.stem
            print(f"  - {template_name}")

            # Try to read description from template
            try:
                with open(template, "r", encoding="utf-8") as f:
                    first_line = f.readline().strip()
                    if first_line.startswith("#"):
                        description = first_line[1:].strip()
                        print(f"    {description}")
            except Exception:
                pass

        return 0

    def _install_templates(self, args: Namespace) -> int:
        """Install example templates."""
        # Create templates directory
        self.templates_dir.mkdir(parents=True, exist_ok=True)

        templates = self._get_example_templates()
        installed_count = 0

        for template_name, template_content in templates.items():
            template_file = self.templates_dir / f"{template_name}.template"

            if template_file.exists() and not args.force:
                logger.warning(
                    "Template already exists (use --force to overwrite): %s",
                    template_name,
                )
                continue

            try:
                with open(template_file, "w", encoding="utf-8") as f:
                    f.write(template_content)
                installed_count += 1
                logger.info("Installed template: %s", template_name)
            except Exception as e:
                logger.error("Failed to install template %s: %s", template_name, str(e))

        print(f"Installed {installed_count} templates to {self.templates_dir}")
        return 0

    def _generate_template(self, args: Namespace) -> int:
        """Generate a specific template."""
        namespace = args.namespace or self.config.get_effective_namespace()

        generators = {
            "docker-compose": self._generate_docker_compose_template,
            "env": self._generate_env_template,
            "kubernetes": self._generate_kubernetes_template,
            "deployment": self._generate_deployment_template,
            "backup": self._generate_backup_template,
        }

        generator = generators.get(args.template_type)
        if not generator:
            logger.error("Unknown template type: %s", args.template_type)
            return 1

        try:
            content = generator(namespace)

            if args.output:
                with open(args.output, "w", encoding="utf-8") as f:
                    f.write(content)
                print(f"Template generated: {args.output}")
            else:
                print(content)

            return 0
        except Exception as e:
            logger.error("Failed to generate template: %s", str(e))
            return 1

    def _show_template(self, args: Namespace) -> int:
        """Show template content."""
        template_file = self.templates_dir / f"{args.template_name}.template"

        if not template_file.exists():
            logger.error("Template not found: %s", args.template_name)
            return 1

        try:
            with open(template_file, "r", encoding="utf-8") as f:
                print(f"=== Template: {args.template_name} ===")
                print(f.read())
            return 0
        except Exception as e:
            logger.error("Failed to read template: %s", str(e))
            return 1

    def _get_example_templates(self) -> Dict[str, str]:
        """Get example templates to install."""
        return {
            "docker-compose-env": """# Docker Compose Environment Template
# Generated by VaultRunner - pulls secrets from Vault for docker-compose
# Usage: vaultrunner templates generate docker-compose --namespace myapp > docker-compose.override.yml

version: '3.8'
services:
  app:
    environment:
      # Database Configuration
      - DATABASE_URL=$$VAULT_SECRET:{{namespace}}/database/url
      - DB_HOST=$$VAULT_SECRET:{{namespace}}/database/host
      - DB_PORT=$$VAULT_SECRET:{{namespace}}/database/port
      - DB_NAME=$$VAULT_SECRET:{{namespace}}/database/name
      - DB_USER=$$VAULT_SECRET:{{namespace}}/database/user
      - DB_PASSWORD=$$VAULT_SECRET:{{namespace}}/database/password
      
      # API Configuration
      - API_KEY=$$VAULT_SECRET:{{namespace}}/api/key
      - JWT_SECRET=$$VAULT_SECRET:{{namespace}}/api/jwt_secret
      - EXTERNAL_API_TOKEN=$$VAULT_SECRET:{{namespace}}/api/external_token
      
      # Application Settings
      - APP_ENV={{namespace}}
      - LOG_LEVEL=info
""",
            "kubernetes-secrets": """# Kubernetes Secrets Template
# Generated by VaultRunner - creates K8s secrets from Vault
apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: {{namespace}}
type: Opaque
data:
  # Database secrets (base64 encoded)
  db-host: $$VAULT_SECRET_B64:{{namespace}}/database/host
  db-password: $$VAULT_SECRET_B64:{{namespace}}/database/password
  db-user: $$VAULT_SECRET_B64:{{namespace}}/database/user
  
  # API secrets
  api-key: $$VAULT_SECRET_B64:{{namespace}}/api/key
  jwt-secret: $$VAULT_SECRET_B64:{{namespace}}/api/jwt_secret
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - secretRef:
            name: app-secrets
""",
            "env-file": """# Environment File Template
# Generated by VaultRunner - exports secrets as environment variables
# Usage: source <(vaultrunner templates generate env --namespace myapp)

# Database Configuration
export DATABASE_URL="$$VAULT_SECRET:{{namespace}}/database/url"
export DB_HOST="$$VAULT_SECRET:{{namespace}}/database/host"
export DB_PORT="$$VAULT_SECRET:{{namespace}}/database/port"
export DB_NAME="$$VAULT_SECRET:{{namespace}}/database/name"
export DB_USER="$$VAULT_SECRET:{{namespace}}/database/user"
export DB_PASSWORD="$$VAULT_SECRET:{{namespace}}/database/password"

# API Configuration
export API_KEY="$$VAULT_SECRET:{{namespace}}/api/key"
export JWT_SECRET="$$VAULT_SECRET:{{namespace}}/api/jwt_secret"
export EXTERNAL_API_TOKEN="$$VAULT_SECRET:{{namespace}}/api/external_token"

# Application Settings
export APP_ENV="{{namespace}}"
export LOG_LEVEL="info"
""",
            "deployment-script": """#!/bin/bash
# Deployment Script Template
# Generated by VaultRunner - deploys with secrets from Vault

set -euo pipefail

NAMESPACE="{{namespace}}"
VAULT_ADDR="${VAULT_ADDR:-http://localhost:8200}"

echo "🚀 Starting deployment for namespace: $NAMESPACE"

# Fetch secrets from Vault
echo "📦 Retrieving secrets from Vault..."
DB_PASSWORD=$(vaultrunner secrets get database/password --namespace "$NAMESPACE")
API_KEY=$(vaultrunner secrets get api/key --namespace "$NAMESPACE")

# Export as environment variables
export DB_PASSWORD
export API_KEY
export APP_ENV="$NAMESPACE"

# Deploy application
echo "🔧 Deploying application..."
if [ -f "docker-compose.yml" ]; then
    docker-compose up -d
elif [ -f "deployment.yaml" ]; then
    kubectl apply -f deployment.yaml
else
    echo "❌ No deployment configuration found"
    exit 1
fi

echo "✅ Deployment completed successfully!"
""",
            "backup-script": """#!/bin/bash
# Vault Backup Script Template  
# Generated by VaultRunner - backs up namespace secrets

set -euo pipefail

NAMESPACE="${1:-{{namespace}}}"
BACKUP_DIR="./backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/vault_backup_${NAMESPACE}_${TIMESTAMP}.json"

echo "💾 Creating backup for namespace: $NAMESPACE"

# Create backup directory
mkdir -p "$BACKUP_DIR"

# Get all secrets from namespace
echo "📥 Exporting secrets..."
vaultrunner bulk-get $(vaultrunner namespace secrets --namespace "$NAMESPACE" | tail -n +2 | sed 's/^  - //') \
    --namespace "$NAMESPACE" \
    --format json > "$BACKUP_FILE"

echo "✅ Backup saved to: $BACKUP_FILE"
echo "📊 Backup size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Optional: compress backup
if command -v gzip &> /dev/null; then
    gzip "$BACKUP_FILE"
    echo "🗜️ Backup compressed: ${BACKUP_FILE}.gz"
fi
""",
        }

    def _generate_docker_compose_template(self, namespace: str) -> str:
        """Generate docker-compose template with current secrets."""
        try:
            # Get current secrets from namespace
            secret_names = self.vault_client.list_secrets(namespace) or []

            content = f"""# Docker Compose Environment Override
# Generated by VaultRunner for namespace: {namespace}
# Run: docker-compose -f docker-compose.yml -f docker-compose.override.yml up

version: '3.8'
services:
  app:
    environment:
"""

            for secret_name in secret_names:
                env_name = secret_name.upper().replace("/", "_").replace("-", "_")
                content += (
                    f"      - {env_name}=${{VAULT_SECRET:{namespace}/{secret_name}}}\n"
                )

            content += f"""      
      # Application Settings
      - APP_ENV={namespace}
      - VAULT_NAMESPACE={namespace}
"""

            return content

        except Exception:
            # Fallback to generic template
            return f"""# Docker Compose Environment Template
# Generated by VaultRunner for namespace: {namespace}

version: '3.8'
services:
  app:
    environment:
      - DATABASE_URL=${{VAULT_SECRET:{namespace}/database/url}}
      - API_KEY=${{VAULT_SECRET:{namespace}/api/key}}
      - APP_ENV={namespace}
"""

    def _generate_env_template(self, namespace: str) -> str:
        """Generate environment file template."""
        try:
            secret_names = self.vault_client.list_secrets(namespace) or []

            content = f"""# Environment Variables
# Generated by VaultRunner for namespace: {namespace}
# Usage: source <(vaultrunner templates generate env --namespace {namespace})

"""

            for secret_name in secret_names:
                env_name = secret_name.upper().replace("/", "_").replace("-", "_")
                content += f'export {env_name}="$(vaultrunner secrets get {secret_name} --namespace {namespace})"\n'

            content += f'\n# Application Settings\nexport APP_ENV="{namespace}"\n'

            return content

        except Exception:
            return f"""# Environment Variables Template
# Generated by VaultRunner for namespace: {namespace}

export DATABASE_URL="$(vaultrunner secrets get database/url --namespace {namespace})"
export API_KEY="$(vaultrunner secrets get api/key --namespace {namespace})"
export APP_ENV="{namespace}"
"""

    def _generate_kubernetes_template(self, namespace: str) -> str:
        """Generate Kubernetes secrets template."""
        return f"""apiVersion: v1
kind: Secret
metadata:
  name: app-secrets
  namespace: {namespace}
type: Opaque
stringData:
  # Add your secrets here - VaultRunner will populate from Vault
  database-url: "$(vaultrunner secrets get database/url --namespace {namespace})"
  api-key: "$(vaultrunner secrets get api/key --namespace {namespace})"
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: app
  namespace: {namespace}
spec:
  template:
    spec:
      containers:
      - name: app
        envFrom:
        - secretRef:
            name: app-secrets
"""

    def _generate_deployment_template(self, namespace: str) -> str:
        """Generate deployment script template."""
        return f"""#!/bin/bash
# Deployment Script for {namespace}
# Generated by VaultRunner

set -euo pipefail

NAMESPACE="{namespace}"
echo "🚀 Deploying to namespace: $NAMESPACE"

# Source environment variables from Vault
source <(vaultrunner templates generate env --namespace "$NAMESPACE")

# Deploy based on available files
if [ -f "docker-compose.yml" ]; then
    echo "📦 Starting Docker Compose deployment..."
    docker-compose up -d
elif [ -f "deployment.yaml" ]; then
    echo "☸️ Deploying to Kubernetes..."
    kubectl apply -f deployment.yaml
else
    echo "❌ No deployment configuration found"
    exit 1
fi

echo "✅ Deployment completed!"
"""

    def _generate_backup_template(self, namespace: str) -> str:
        """Generate backup script template."""
        return f"""#!/bin/bash
# Backup Script for {namespace}
# Generated by VaultRunner

set -euo pipefail

NAMESPACE="{namespace}"
BACKUP_DIR="./vault-backups"
TIMESTAMP=$(date +"%Y%m%d_%H%M%S")
BACKUP_FILE="$BACKUP_DIR/backup_${{NAMESPACE}}_${{TIMESTAMP}}.json"

mkdir -p "$BACKUP_DIR"

echo "💾 Backing up namespace: $NAMESPACE"

# Export all secrets to JSON
vaultrunner bulk-get $(vaultrunner namespace secrets --namespace "$NAMESPACE" | grep "^  -" | sed 's/^  - //') \\
    --namespace "$NAMESPACE" \\
    --format json > "$BACKUP_FILE"

echo "✅ Backup saved: $BACKUP_FILE"
echo "📊 Size: $(du -h "$BACKUP_FILE" | cut -f1)"

# Compress if available
if command -v gzip &> /dev/null; then
    gzip "$BACKUP_FILE"
    echo "🗜️ Compressed: ${{BACKUP_FILE}}.gz"
fi
"""
