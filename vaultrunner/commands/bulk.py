"""
Bulk Operations Command

Handles bulk secret operations with namespace support.
Simplified implementation for Docker/ENV users.
"""

import json
from typing import Dict, List, Optional, Any
from ..models.config import VaultRunnerConfig
from ..vault.client import VaultClient
from ..utils.logging import get_logger

logger = get_logger(__name__)


class BulkOperations:
    """Service for bulk secret operations."""

    def __init__(self, config: VaultRunnerConfig, vault_client: VaultClient):
        self.config = config
        self.vault_client = vault_client

    def set_multiple_secrets(
        self, secrets: Dict[str, str], namespace: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Set multiple secrets at once.

        Args:
            secrets: Dictionary of key-value pairs to set
            namespace: Target namespace (uses config default if None)

        Returns:
            Operation result summary
        """
        target_namespace = namespace or self.config.get_effective_namespace()
        logger.info(
            "Setting %d secrets in namespace '%s'", len(secrets), target_namespace
        )

        result = {
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "namespace": target_namespace,
        }

        for key, value in secrets.items():
            try:
                secret_path = f"{target_namespace}/{key}"
                if namespace:
                    secret_path = f"{namespace}/{key}"

                if not self.config.dry_run:
                    self.vault_client.put_secret(secret_path, value)

                result["success_count"] += 1
                logger.debug("Set secret: %s", key)

            except Exception as e:
                result["error_count"] += 1
                error_msg = f"Failed to set {key}: {str(e)}"
                result["errors"].append(error_msg)
                logger.error("Failed to set secret %s: %s", key, str(e))

        return result

    def get_multiple_secrets(
        self, secret_names: List[str], namespace: Optional[str] = None
    ) -> Dict[str, str]:
        """
        Get multiple secrets at once.

        Args:
            secret_names: List of secret names to retrieve
            namespace: Source namespace (uses config default if None)

        Returns:
            Dictionary of secret names to values
        """
        source_namespace = namespace or self.config.get_effective_namespace()
        logger.info(
            "Getting %d secrets from namespace '%s'",
            len(secret_names),
            source_namespace,
        )

        secrets = {}

        for secret_name in secret_names:
            try:
                secret_path = f"{source_namespace}/{secret_name}"
                secret_value = self.vault_client.get_secret(secret_path)

                if secret_value:
                    secrets[secret_name] = secret_value
                else:
                    logger.warning("Secret not found or empty: %s", secret_name)

            except Exception as e:
                logger.error("Failed to get secret %s: %s", secret_name, str(e))

        return secrets

    def list_namespaces(self) -> List[str]:
        """
        List all available namespaces.

        Returns:
            List of namespace names
        """
        try:
            result = self.vault_client.list_secrets("")
            return result or []
        except Exception as e:
            logger.error("Failed to list namespaces: %s", str(e))
            return []

    def list_secrets_in_namespace(self, namespace: Optional[str] = None) -> List[str]:
        """
        List all secrets in a namespace.

        Args:
            namespace: Namespace to list (uses config default if None)

        Returns:
            List of secret names
        """
        target_namespace = namespace or self.config.get_effective_namespace()

        try:
            vault_path = f"{target_namespace}"
            result = self.vault_client.list_secrets(vault_path)
            return result or []
        except Exception as e:
            logger.error(
                "Failed to list secrets in namespace %s: %s", target_namespace, str(e)
            )
            return []

    def copy_namespace(
        self, source_namespace: str, target_namespace: str
    ) -> Dict[str, Any]:
        """
        Copy all secrets from one namespace to another.

        Args:
            source_namespace: Source namespace
            target_namespace: Target namespace

        Returns:
            Operation result summary
        """
        logger.info(
            "Copying secrets from '%s' to '%s'", source_namespace, target_namespace
        )

        # Get all secrets from source namespace
        secret_names = self.list_secrets_in_namespace(source_namespace)
        secrets = self.get_multiple_secrets(secret_names, source_namespace)

        # Set secrets in target namespace
        return self.set_multiple_secrets(secrets, target_namespace)

    def delete_namespace(self, namespace: str, confirm: bool = False) -> Dict[str, Any]:
        """
        Delete all secrets in a namespace.

        Args:
            namespace: Namespace to delete
            confirm: Confirmation flag

        Returns:
            Operation result summary
        """
        if not confirm:
            raise ValueError("Namespace deletion requires explicit confirmation")

        if namespace == self.config.default_namespace:
            raise ValueError("Cannot delete the default shared namespace")

        logger.info("Deleting all secrets in namespace '%s'", namespace)

        result = {
            "success_count": 0,
            "error_count": 0,
            "errors": [],
            "namespace": namespace,
        }

        # Get all secrets in namespace
        secret_names = self.list_secrets_in_namespace(namespace)

        for secret_name in secret_names:
            try:
                vault_path = f"secret/{namespace}/{secret_name}"

                if not self.config.dry_run:
                    self.vault_client.delete_secret(vault_path)

                result["success_count"] += 1
                logger.debug("Deleted secret: %s", secret_name)

            except Exception as e:
                result["error_count"] += 1
                error_msg = f"Failed to delete {secret_name}: {str(e)}"
                result["errors"].append(error_msg)
                logger.error("Failed to delete secret %s: %s", secret_name, str(e))

        return result


def register_bulk_commands(cli_parser):
    """Register bulk operation commands with the CLI parser."""

    # Namespace commands
    namespace_parser = cli_parser.add_parser("namespace", help="Namespace operations")
    namespace_subparsers = namespace_parser.add_subparsers(
        dest="namespace_action", help="Namespace action"
    )

    # List namespaces
    namespace_subparsers.add_parser("list", help="List all namespaces")

    # List secrets in namespace
    list_secrets_parser = namespace_subparsers.add_parser(
        "secrets", help="List secrets in namespace"
    )
    list_secrets_parser.add_argument(
        "--namespace", "-n", help="Namespace to list (default: current)"
    )

    # Copy namespace
    copy_parser = namespace_subparsers.add_parser(
        "copy", help="Copy all secrets from one namespace to another"
    )
    copy_parser.add_argument("source", help="Source namespace")
    copy_parser.add_argument("target", help="Target namespace")

    # Delete namespace
    delete_parser = namespace_subparsers.add_parser(
        "delete", help="Delete all secrets in a namespace"
    )
    delete_parser.add_argument("namespace", help="Namespace to delete")
    delete_parser.add_argument(
        "--confirm", action="store_true", help="Confirm deletion"
    )

    # Bulk set command
    bulk_set_parser = cli_parser.add_parser(
        "bulk-set", help="Set multiple secrets from JSON"
    )
    bulk_set_parser.add_argument(
        "secrets_json", help="JSON string or file with secrets"
    )
    bulk_set_parser.add_argument(
        "--namespace", "-n", help="Target namespace (default: current)"
    )
    bulk_set_parser.add_argument(
        "--from-file",
        "-f",
        action="store_true",
        help="Read from file instead of command line",
    )

    # Bulk get command
    bulk_get_parser = cli_parser.add_parser("bulk-get", help="Get multiple secrets")
    bulk_get_parser.add_argument(
        "secret_names", nargs="+", help="Secret names to retrieve"
    )
    bulk_get_parser.add_argument(
        "--namespace", "-n", help="Source namespace (default: current)"
    )
    bulk_get_parser.add_argument(
        "--format", choices=["json", "env"], default="json", help="Output format"
    )


def handle_bulk_command(args, config: VaultRunnerConfig, vault_client: VaultClient):
    """Handle bulk operation command execution."""
    bulk_ops = BulkOperations(config, vault_client)

    if hasattr(args, "namespace_action"):
        # Namespace commands
        if args.namespace_action == "list":
            namespaces = bulk_ops.list_namespaces()
            print("Available namespaces:")
            for namespace in namespaces:
                marker = (
                    " (current)"
                    if namespace == config.get_effective_namespace()
                    else ""
                )
                shared_marker = (
                    " (shared)" if namespace == config.default_namespace else ""
                )
                print(f"  - {namespace}{marker}{shared_marker}")

        elif args.namespace_action == "secrets":
            secrets = bulk_ops.list_secrets_in_namespace(args.namespace)
            namespace = args.namespace or config.get_effective_namespace()
            print(f"Secrets in namespace '{namespace}':")
            for secret in secrets:
                print(f"  - {secret}")

        elif args.namespace_action == "copy":
            result = bulk_ops.copy_namespace(args.source, args.target)
            print(
                f"Copied {result['success_count']} secrets from '{args.source}' to '{args.target}'"
            )
            if result["error_count"] > 0:
                print(f"Errors: {result['error_count']}")

        elif args.namespace_action == "delete":
            result = bulk_ops.delete_namespace(args.namespace, args.confirm)
            print(
                f"Deleted {result['success_count']} secrets from namespace '{args.namespace}'"
            )
            if result["error_count"] > 0:
                print(f"Errors: {result['error_count']}")

    elif hasattr(args, "secrets_json"):
        # Bulk set command
        if args.from_file:
            with open(args.secrets_json, "r", encoding="utf-8") as f:
                secrets_data = json.load(f)
        else:
            secrets_data = json.loads(args.secrets_json)

        result = bulk_ops.set_multiple_secrets(secrets_data, args.namespace)
        print(f"Set {result['success_count']} secrets")
        if result["error_count"] > 0:
            print(f"Errors: {result['error_count']}")

    elif hasattr(args, "secret_names"):
        # Bulk get command
        secrets = bulk_ops.get_multiple_secrets(args.secret_names, args.namespace)

        if args.format == "json":
            print(json.dumps(secrets, indent=2))
        elif args.format == "env":
            for key, value in secrets.items():
                print(f'{key}="{value}"')
