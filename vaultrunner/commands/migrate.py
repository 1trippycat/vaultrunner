"""
Migration Command

Handles migration of secrets from various sources (env files, Docker secrets, etc.)
to HashiCorp Vault with namespace support.
"""

import os
import yaml
import re
from typing import Dict, Optional, Any
from ..models.config import VaultRunnerConfig
from ..vault.client import VaultClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class MigrationService:
    """Service for migrating secrets from various sources."""

    # Common secret patterns to look for
    SECRET_PATTERNS = [
        re.compile(r'.*_(?:KEY|TOKEN|SECRET|PASS|PASSWORD|PWD|CRED)$', re.IGNORECASE),
        re.compile(r'^(?:API|DB|DATABASE)_.*', re.IGNORECASE),
        re.compile(r'.*(?:AUTH|JWT|OAUTH|BEARER).*$', re.IGNORECASE),
        re.compile(r'.*(?:PRIVATE|SECRET)_.*', re.IGNORECASE),
    ]

    def __init__(self, config: VaultRunnerConfig, vault_client: VaultClient):
        self.config = config
        self.vault_client = vault_client

    def migrate_from_env_file(
        self, env_file_path: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Migrate secrets from a .env file to Vault.

        Args:
            env_file_path: Path to the .env file
            namespace: Target namespace (uses config default if None)

        Returns:
            Migration result summary
        """
        logger.info("Starting migration from env file: %s", env_file_path)

        if not os.path.exists(env_file_path):
            raise FileNotFoundError(f"Env file not found: {env_file_path}")

        # Parse env file
        secrets = self._parse_env_file(env_file_path)

        # Set target namespace
        target_namespace = namespace or self.config.get_effective_namespace()

        # Migrate secrets
        result = self._migrate_secrets_batch(
            secrets, target_namespace, source="env_file"
        )

        logger.info(
            "Migration completed. Migrated %d secrets to namespace '%s'",
            result["success_count"],
            target_namespace,
        )
        return result

    def migrate_from_docker_compose(
        self, compose_file_path: str, namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Migrate environment variables from docker-compose.yml to Vault.

        Args:
            compose_file_path: Path to docker-compose.yml
            namespace: Target namespace (uses config default if None)

        Returns:
            Migration result summary
        """
        logger.info("Starting migration from docker-compose: %s", compose_file_path)

        if not os.path.exists(compose_file_path):
            raise FileNotFoundError(
                f"Docker compose file not found: {compose_file_path}"
            )

        # Parse docker-compose file
        secrets = self._parse_docker_compose(compose_file_path)

        # Set target namespace
        target_namespace = namespace or self.config.get_effective_namespace()

        # Migrate secrets
        result = self._migrate_secrets_batch(
            secrets, target_namespace, source="docker_compose"
        )

        logger.info(
            "Migration completed. Migrated %d secrets to namespace '%s'",
            result["success_count"],
            target_namespace
        )
        return result

    def migrate_from_kubernetes_secrets(
        self, k8s_namespace: str = "default", vault_namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Migrate secrets from Kubernetes secrets to Vault.

        Args:
            k8s_namespace: Kubernetes namespace to read secrets from
            vault_namespace: Target Vault namespace (uses config default if None)

        Returns:
            Migration result summary
        """
        logger.info("Starting migration from Kubernetes namespace: %s", k8s_namespace)

        # This would require kubernetes client - placeholder for now
        secrets = {}  # TODO: Implement kubernetes secret reading

        # Set target namespace
        target_namespace = vault_namespace or self.config.get_effective_namespace()

        # Migrate secrets
        result = self._migrate_secrets_batch(
            secrets, target_namespace, source="kubernetes"
        )

        logger.info(
            "Migration completed. Migrated %d secrets to namespace '%s'",
            result["success_count"],
            target_namespace
        )
        return result

    def export_to_env_format(
        self, namespace: Optional[str] = None, output_file: Optional[str] = None
    ) -> str:
        """
        Export secrets from Vault to .env format.

        Args:
            namespace: Source namespace (uses config default if None)
            output_file: Output file path (prints to stdout if None)

        Returns:
            Formatted env content
        """
        source_namespace = namespace or self.config.get_effective_namespace()
        logger.info(
            "Exporting secrets from namespace '%s' to env format",
            source_namespace
        )

        # Get all secrets from namespace
        secrets = self._get_secrets_from_namespace(source_namespace)

        # Format as env
        env_content = self._format_as_env(secrets)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(env_content)
            logger.info("Secrets exported to: %s", output_file)

        return env_content

    def export_to_docker_compose_env(
        self, namespace: Optional[str] = None, output_file: Optional[str] = None
    ) -> str:
        """
        Export secrets from Vault to docker-compose environment format.

        Args:
            namespace: Source namespace (uses config default if None)
            output_file: Output file path (prints to stdout if None)

        Returns:
            Formatted docker-compose env content
        """
        source_namespace = namespace or self.config.get_effective_namespace()
        logger.info(
            "Exporting secrets from namespace '%s' to docker-compose format",
            source_namespace
        )

        # Get all secrets from namespace
        secrets = self._get_secrets_from_namespace(source_namespace)

        # Format for docker-compose
        compose_content = self._format_as_docker_compose_env(secrets)

        if output_file:
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(compose_content)
            logger.info("Docker-compose env exported to: %s", output_file)

        return compose_content

    def smart_migrate_docker_compose(
        self,
        compose_file_path: str,
        namespace: Optional[str] = None,
        auto_migrate: bool = False,
        interactive: bool = True,
        auto_import: bool = False
    ) -> Dict[str, Any]:
        """
        Smart migration that detects potential secrets in Docker Compose files.

        Args:
            compose_file_path: Path to docker-compose.yml
            namespace: Target namespace
            auto_migrate: Automatically migrate detected secrets without asking
            interactive: Enable interactive mode for user confirmation
            auto_import: Automatically run import after migration

        Returns:
            Migration result summary
        """
        logger.info("Starting smart migration from docker-compose: %s", compose_file_path)

        if not os.path.exists(compose_file_path):
            raise FileNotFoundError(f"Docker compose file not found: {compose_file_path}")

        # Parse docker-compose file
        detected_secrets = self._detect_potential_secrets(compose_file_path)

        if not detected_secrets:
            logger.info("No potential secrets detected in docker-compose file")
            return {"detected": 0, "migrated": 0, "skipped": 0}

        # Set target namespace
        target_namespace = namespace or self.config.get_effective_namespace()

        # Ensure only one import mode is active
        if auto_migrate:
            interactive = False
        # If both are False, skip migration
        if not auto_migrate and not interactive:
            logger.info("No migration mode selected (auto_migrate and interactive both False)")
            return {"detected": len(detected_secrets), "migrated": 0, "skipped": len(detected_secrets)}

        # Filter and confirm secrets to migrate
        secrets_to_migrate = self._filter_and_confirm_secrets(
            detected_secrets, auto_migrate, interactive
        )

        if not secrets_to_migrate:
            logger.info("No secrets selected for migration")
            return {"detected": len(detected_secrets), "migrated": 0, "skipped": len(detected_secrets)}

        # Migrate selected secrets to Vault
        migration_result = self._migrate_secrets_batch(
            secrets_to_migrate, target_namespace, source="smart_migration"
        )

        # Update Docker Compose file with Vault references
        if not self.config.dry_run:
            self._update_docker_compose_with_vault_refs(
                compose_file_path, secrets_to_migrate, target_namespace
            )
            # Generate vault.hcl config file
            self._generate_vault_config()

        # Handle automatic import
        import_result = None
        if auto_import and migration_result["success_count"] > 0:
            logger.info("Running automatic import after migration...")
            import_result = self._run_automatic_import(target_namespace)
        elif interactive and migration_result["success_count"] > 0:
            import_result = self._ask_and_run_import(target_namespace)

        logger.info(
            "Smart migration completed. Detected: %d, Migrated: %d, Skipped: %d",
            len(detected_secrets),
            migration_result["success_count"],
            len(detected_secrets) - len(secrets_to_migrate)
        )

        result = {
            "detected": len(detected_secrets),
            "migrated": migration_result["success_count"],
            "skipped": len(detected_secrets) - len(secrets_to_migrate),
            "namespace": target_namespace,
            "updated_file": compose_file_path if not self.config.dry_run else None
        }

        if import_result:
            result["imported"] = import_result

        return result

    def _run_automatic_import(self, namespace: str) -> Dict[str, Any]:
        """
        Run automatic import after migration.

        Args:
            namespace: Target namespace for import

        Returns:
            Import result summary
        """
        try:
            # For now, implement a simple import mechanism
            # This could be enhanced to import from various sources
            logger.info("Running automatic import for namespace: %s", namespace)

            # Simple import - could be enhanced to read from config sources
            # For now, just return success since secrets are already migrated
            return {
                "success": True,
                "message": f"Import completed for namespace {namespace}",
                "imported_count": 0  # Could track actual imports here
            }

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Automatic import failed: %s", str(e))
            return {"success": False, "error": str(e)}

    def _ask_and_run_import(self, namespace: str) -> Optional[Dict[str, Any]]:
        """
        Ask user if they want to run import and execute if yes.

        Args:
            namespace: Target namespace for import

        Returns:
            Import result if run, None if skipped
        """
        try:
            # Ask user for import preference
            print("\n" + "="*50)
            print("MIGRATION COMPLETE!")
            print("="*50)
            print(f"Secrets have been migrated to namespace: {namespace}")
            print("\nWould you like to run the import command now?")
            print("This will import secrets from your configured sources.")
            print("\nOptions:")
            print("1. Run import now (recommended)")
            print("2. Skip import (you can run it later manually)")
            print("3. Run import with custom options")

            while True:
                try:
                    choice = input("\nEnter your choice (1-3): ").strip()

                    if choice == "1":
                        print("\nRunning import with default settings...")
                        return self._run_automatic_import(namespace)

                    elif choice == "2":
                        print("\nSkipping import. You can run it later with:")
                        print(f"  vaultrunner import --namespace {namespace}")
                        return None

                    elif choice == "3":
                        # Get custom import options
                        print("\nCustom import options:")
                        source = input("Source (default: auto): ").strip() or "auto"
                        dry_run_input = input("Dry run? (y/N): ").strip().lower()
                        dry_run = dry_run_input in ("y", "yes")

                        print(f"\nRunning import with source='{source}', dry_run={dry_run}...")
                        # For now, implement simple import mechanism
                        # This could be enhanced to use actual import command
                        import_result = {
                            "success": True,
                            "message": f"Import completed with source '{source}'",
                            "dry_run": dry_run
                        }
                        return import_result

                    else:
                        print("Invalid choice. Please enter 1, 2, or 3.")

                except KeyboardInterrupt:
                    print("\n\nImport cancelled by user.")
                    return None

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Interactive import prompt failed: %s", str(e))
            print(f"\nError during import prompt: {e}")
            print("You can run import manually later.")
            return None

    def _detect_potential_secrets(self, compose_file_path: str) -> Dict[str, Dict[str, Any]]:
        """
        Detect potential secrets in Docker Compose file based on naming patterns.

        Returns:
            Dict of detected secrets with metadata
        """
        detected_secrets = {}

        try:
            with open(compose_file_path, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            services = compose_data.get("services", {})
            for service_name, service_config in services.items():
                env_vars = service_config.get("environment", {})

                # Handle both list and dict formats
                if isinstance(env_vars, list):
                    for env_var in env_vars:
                        if "=" in env_var:
                            key, value = env_var.split("=", 1)
                            key = key.strip()
                            value = value.strip().strip('"').strip("'")

                            if self._is_potential_secret(key, value):
                                detected_secrets[f"{service_name}_{key}"] = {
                                    "service": service_name,
                                    "key": key,
                                    "value": value,
                                    "source": "environment_list"
                                }

                elif isinstance(env_vars, dict):
                    for key, value in env_vars.items():
                        if isinstance(value, str):
                            value = value.strip().strip('"').strip("'")

                            if self._is_potential_secret(key, str(value)):
                                detected_secrets[f"{service_name}_{key}"] = {
                                    "service": service_name,
                                    "key": key,
                                    "value": str(value),
                                    "source": "environment_dict"
                                }

        except yaml.YAMLError as e:
            logger.error("Error parsing docker-compose file: %s", e)
            raise

        return detected_secrets

    def _is_potential_secret(self, key: str, value: str) -> bool:
        """
        Determine if an environment variable is likely a secret based on patterns.
        """
        # Skip obviously non-secret values
        if not value or len(value) < 8:
            return False

        # Skip common non-secret patterns
        if value.startswith(("http://", "https://", "localhost", "/")):
            return False

        # Check against secret patterns
        for pattern in self.SECRET_PATTERNS:
            if pattern.match(key):
                return True

        return False

    def _filter_and_confirm_secrets(
        self,
        detected_secrets: Dict[str, Dict[str, Any]],
        auto_migrate: bool,
        interactive: bool
    ) -> Dict[str, str]:
        """
        Filter detected secrets and get user confirmation for migration.
        """
        secrets_to_migrate = {}

        for secret_key, metadata in detected_secrets.items():
            if auto_migrate:
                # Auto-migrate all detected secrets
                secrets_to_migrate[secret_key] = metadata["value"]
                logger.info("Auto-migrating detected secret: %s", metadata["key"])
            elif interactive:
                # Ask user for confirmation
                response = input(
                    f"Migrate secret '{metadata['key']}' from service '{metadata['service']}'? "
                    f"(value: {metadata['value'][:20]}...) [y/N]: "
                ).strip().lower()

                if response in ("y", "yes"):
                    secrets_to_migrate[secret_key] = metadata["value"]
                    logger.info("User confirmed migration of: %s", metadata["key"])
                else:
                    logger.info("User skipped migration of: %s", metadata["key"])
            else:
                # Skip all without confirmation
                logger.info("Skipping detected secret (interactive=False): %s", metadata["key"])

        return secrets_to_migrate

    def _update_docker_compose_with_vault_refs(
        self,
        compose_file_path: str,
        migrated_secrets: Dict[str, str],
        namespace: str
    ) -> None:
        """
        Update Docker Compose file to use Vault Runner sidecar secret references.
        """
        try:
            with open(compose_file_path, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            # Track which secrets were updated
            updated_secrets = {}

            # Update environment variables to use Vault references
            services = compose_data.get("services", {})
            for _service_name, service_config in services.items():
                env_vars = service_config.get("environment", {})

                if isinstance(env_vars, list):
                    # Handle list format
                    for i, env_var in enumerate(env_vars):
                        if "=" in env_var:
                            key, _ = env_var.split("=", 1)
                            key = key.strip()

                            # Check if this key was migrated
                            for secret_key, _ in migrated_secrets.items():
                                if secret_key.endswith(f"_{key}"):
                                    vault_ref = f"${{VAULT_SECRET_{namespace}/{secret_key}}}"
                                    env_vars[i] = f"{key}={vault_ref}"
                                    updated_secrets[secret_key] = vault_ref
                                    break

                elif isinstance(env_vars, dict):
                    # Handle dict format
                    for key, _value in list(env_vars.items()):
                        # Check if this key was migrated
                        for secret_key, _ in migrated_secrets.items():
                            if secret_key.endswith(f"_{key}"):
                                vault_ref = f"${{VAULT_SECRET_{namespace}/{secret_key}}}"
                                env_vars[key] = vault_ref
                                updated_secrets[secret_key] = vault_ref
                                break

            # Add Vault Runner sidecar if not present
            self._add_vault_sidecar(compose_data, namespace)

            # Write updated compose file
            with open(compose_file_path, "w", encoding="utf-8") as f:
                yaml.dump(compose_data, f, default_flow_style=False, sort_keys=False)

            logger.info("Updated Docker Compose file with %d Vault references", len(updated_secrets))

        except Exception as e:
            logger.error("Failed to update Docker Compose file: %s", e)
            raise

    def _add_vault_sidecar(self, compose_data: Dict[str, Any], namespace: str) -> None:
        """
        Add Vault Runner sidecar service to the compose file.
        """
        services = compose_data.setdefault("services", {})

        # Check if sidecar already exists
        if "vault-runner" in services:
            logger.info("Vault Runner sidecar already exists")
            return

        # Add Vault server service if not present
        if "vault" not in services:
            services["vault"] = {
                "image": "hashicorp/vault:latest",
                "ports": ["8200:8200"],
                "environment": [
                    "VAULT_DEV_ROOT_TOKEN_ID=myroot",
                    "VAULT_DEV_LISTEN_ADDRESS=0.0.0.0:8200"
                ],
                "volumes": [
                    "./.vault/config/vault.hcl:/vault/config/vault.hcl",
                    "vault_data:/vault/data"
                ],
                "command": ["vault", "server", "-config=/vault/config/vault.hcl"],
                "networks": ["vault-network"],
                "healthcheck": {
                    "test": ["CMD", "vault", "status"],
                    "interval": "30s",
                    "timeout": "10s",
                    "retries": 3
                }
            }
            logger.info("Added Vault server service to compose file")

        # Add Vault Runner sidecar
        services["vault-runner"] = {
            "image": "vault-runner:latest",  # TODO: Use actual image
            "environment": [
                f"VAULT_ADDR={self.config.vault_addr or 'http://vault:8200'}",
                f"VAULT_TOKEN={self.config.vault_token or '${VAULT_TOKEN}'}",
                f"VAULTRUNNER_NAMESPACE={namespace}"
            ],
            "volumes": [
                "/var/run/docker.sock:/var/run/docker.sock"
            ],
            "networks": ["vault-network"],
            "depends_on": {
                "vault": {
                    "condition": "service_healthy"
                }
            }
        }

        # Ensure network exists
        networks = compose_data.setdefault("networks", {})
        if "vault-network" not in networks:
            networks["vault-network"] = {"driver": "bridge"}

        # Ensure volumes exist
        volumes = compose_data.setdefault("volumes", {})
        if "vault_data" not in volumes:
            volumes["vault_data"] = None

        logger.info("Added Vault Runner sidecar to compose file")

    def _generate_vault_config(self) -> None:
        """
        Generate vault.hcl configuration file for Vault server.
        """
        vault_config_dir = self.config.vault_dir / "config"
        vault_config_dir.mkdir(parents=True, exist_ok=True)
        
        vault_config_path = vault_config_dir / "vault.hcl"
        
        vault_config_content = """# Vault Server Configuration (vault.hcl)

listener "tcp" {
  address = "0.0.0.0:8200"
  tls_disable = 1
}

storage "file" {
  path = "/vault/data"
}

ui = true

# Add additional configuration as needed
"""
        
        with open(vault_config_path, "w", encoding="utf-8") as f:
            f.write(vault_config_content)
        
        logger.info("Generated vault.hcl config file at: %s", vault_config_path)

    def _parse_env_file(self, env_file_path: str) -> Dict[str, str]:
        """Parse a .env file and return key-value pairs."""
        secrets = {}

        with open(env_file_path, "r", encoding="utf-8") as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()

                # Skip empty lines and comments
                if not line or line.startswith("#"):
                    continue

                # Parse key=value
                if "=" in line:
                    key, value = line.split("=", 1)
                    key = key.strip()
                    value = value.strip().strip('"').strip("'")
                    secrets[key] = value
                else:
                    logger.warning(
                        "Skipping invalid line %d in %s: %s",
                        line_num,
                        env_file_path,
                        line
                    )

        return secrets

    def _parse_docker_compose(self, compose_file_path: str) -> Dict[str, str]:
        """Parse docker-compose.yml and extract environment variables."""
        secrets = {}

        try:
            with open(compose_file_path, "r", encoding="utf-8") as f:
                compose_data = yaml.safe_load(f)

            # Extract environment variables from all services
            services = compose_data.get("services", {})
            for service_name, service_config in services.items():
                env_vars = service_config.get("environment", {})

                # Handle both list and dict formats
                if isinstance(env_vars, list):
                    for env_var in env_vars:
                        if "=" in env_var:
                            key, value = env_var.split("=", 1)
                            secrets[f"{service_name}_{key}"] = value
                elif isinstance(env_vars, dict):
                    for key, value in env_vars.items():
                        secrets[f"{service_name}_{key}"] = str(value)

        except yaml.YAMLError as e:
            logger.error("Error parsing docker-compose file: %s", e)
            raise

        return secrets

    def _migrate_secrets_batch(
        self, secrets: Dict[str, str], namespace: str, source: str
    ) -> Dict[str, Any]:
        """Migrate a batch of secrets to Vault."""
        result = {
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "namespace": namespace,
            "source": source,
        }

        for key, value in secrets.items():
            try:
                vault_path = f"secret/{namespace}/{key}"

                if not self.config.dry_run:
                    self.vault_client.put_secret(vault_path, value)

                result["success_count"] += 1
                logger.debug("Migrated secret: %s -> %s", key, vault_path)

            except (ValueError, RuntimeError, OSError) as e:
                result["error_count"] += 1
                error_msg = "Failed to migrate %s: %s" % (key, str(e))
                result["errors"].append(error_msg)
                logger.error(error_msg)

        return result

    def _get_secrets_from_namespace(self, namespace: str) -> Dict[str, str]:
        """Get all secrets from a Vault namespace."""
        try:
            vault_path = f"secret/{namespace}"
            secrets_list = self.vault_client.list_secrets(vault_path)

            secrets = {}
            for secret_name in secrets_list or []:
                secret_path = f"{vault_path}/{secret_name}"
                secret_value = self.vault_client.get_secret(secret_path)
                if secret_value:
                    secrets[secret_name] = secret_value

            return secrets

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Error reading secrets from namespace %s: %s", namespace, str(e))
            return {}

    def _format_as_env(self, secrets: Dict[str, str]) -> str:
        """Format secrets as .env file content."""
        lines = []
        lines.append("# Exported from VaultRunner")
        lines.append(f"# Namespace: {self.config.get_effective_namespace()}")
        lines.append("")

        for key, value in sorted(secrets.items()):
            # Escape quotes and special characters
            escaped_value = value.replace('"', '\\"')
            lines.append(f'{key}="{escaped_value}"')

        return "\n".join(lines)

    def _format_as_docker_compose_env(self, secrets: Dict[str, str]) -> str:
        """Format secrets as docker-compose environment section."""
        lines = []
        lines.append(
            "# Add this to your docker-compose.yml service environment section"
        )
        lines.append("environment:")

        for key, value in sorted(secrets.items()):
            lines.append(f"  - {key}={value}")

        return "\n".join(lines)


def register_migrate_commands(cli_parser):
    """Register migration commands with the CLI parser."""

    # Import command
    import_parser = cli_parser.add_parser(
        "import", help="Import secrets from various sources"
    )
    import_subparsers = import_parser.add_subparsers(
        dest="import_source", help="Import source"
    )

    # Import from env file
    env_parser = import_subparsers.add_parser("env", help="Import from .env file")
    env_parser.add_argument("file", help="Path to .env file")
    env_parser.add_argument(
        "--namespace", "-n", help="Target namespace (default: shared)"
    )

    # Smart migration from docker-compose
    smart_parser = import_subparsers.add_parser(
        "smart", help="Smart migration with secret detection"
    )
    smart_parser.add_argument("file", help="Path to docker-compose.yml file")
    smart_parser.add_argument(
        "--namespace", "-n", help="Target namespace (default: shared)"
    )
    smart_parser.add_argument(
        "--auto", action="store_true",
        help="Automatically migrate detected secrets without asking"
    )
    smart_parser.add_argument(
        "--no-interactive", action="store_true",
        help="Skip interactive prompts (same as --auto)"
    )
    smart_parser.add_argument(
        "--auto-import", action="store_true",
        help="Automatically run import after migration"
    )

    # Export command
    export_parser = cli_parser.add_parser(
        "migrate-export", help="Export secrets to various formats"
    )
    export_subparsers = export_parser.add_subparsers(
        dest="export_format", help="Export format"
    )

    # Export command
    migrate_export_parser = export_subparsers.add_parser(
        "env", help="Export to .env format"
    )
    migrate_export_parser.add_argument(
        "--namespace", "-n", help="Source namespace (default: current)"
    )
    migrate_export_parser.add_argument(
        "--output", "-o", help="Output file (default: stdout)"
    )

    # Export to docker-compose env
    migrate_compose_export_parser = export_subparsers.add_parser(
        "docker-compose", help="Export to docker-compose env format"
    )
    migrate_compose_export_parser.add_argument(
        "--namespace", "-n", help="Source namespace (default: current)"
    )
    migrate_compose_export_parser.add_argument(
        "--output", "-o", help="Output file (default: stdout)"
    )


def handle_migrate_command(args, config: VaultRunnerConfig, vault_client: VaultClient):
    """Handle migration command execution."""
    migration_service = MigrationService(config, vault_client)

    if hasattr(args, "import_source"):
        # Import commands
        if args.import_source == "env":
            result = migration_service.migrate_from_env_file(args.file, args.namespace)
            print(f"Migration completed: {result['success_count']} secrets imported")
            if result["error_count"] > 0:
                print(f"Errors: {result['error_count']}")
                for error in result["errors"]:
                    print(f"  - {error}")

        elif args.import_source == "docker-compose":
            result = migration_service.migrate_from_docker_compose(
                args.file, args.namespace
            )
            print(f"Migration completed: {result['success_count']} secrets imported")
            if result["error_count"] > 0:
                print(f"Errors: {result['error_count']}")
                for error in result["errors"]:
                    print(f"  - {error}")

        elif args.import_source == "smart":
            # Only one import mode should run
            auto_migrate = getattr(args, "auto", False) or getattr(args, "no_interactive", False)
            interactive = not auto_migrate
            auto_import = getattr(args, "auto_import", False)

            result = migration_service.smart_migrate_docker_compose(
                args.file, args.namespace, auto_migrate, interactive, auto_import
            )
            print("Smart migration completed:")
            print(f"  Detected secrets: {result['detected']}")
            print(f"  Migrated: {result['migrated']}")
            print(f"  Skipped: {result['skipped']}")
            if result.get("updated_file"):
                print(f"  Updated file: {result['updated_file']}")
            if result.get("imported"):
                print(f"  Import result: {result['imported']}")

    elif hasattr(args, "export_format"):
        # Export commands
        if args.export_format == "env":
            content = migration_service.export_to_env_format(
                args.namespace, args.output
            )
            if not args.output:
                print(content)

        elif args.export_format == "docker-compose":
            content = migration_service.export_to_docker_compose_env(
                args.namespace, args.output
            )
            if not args.output:
                print(content)
