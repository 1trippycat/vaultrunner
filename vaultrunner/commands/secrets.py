"""
Secrets Command Module

Handles all secret management operations with Vault.
Implements security-first secret handling.
"""

from argparse import ArgumentParser, Namespace
from typing import Any

from ..models.config import VaultRunnerConfig
from ..utils.logging import get_logger
from ..vault.client import VaultClient
from ..security.input_validation import validate_secret_name, validate_secret_content

logger = get_logger(__name__)


def register_secrets_parser(subparsers: Any) -> None:
    """Register secrets subcommand parser."""
    parser = subparsers.add_parser(
        "secrets",
        help="Manage secrets in HashiCorp Vault",
        description="Add, retrieve, list, and delete secrets in Vault",
    )

    secrets_subparsers = parser.add_subparsers(
        dest="secrets_command", help="Secrets operations"
    )

    # Add secret command
    add_parser = secrets_subparsers.add_parser("add", help="Add or update a secret")
    add_parser.add_argument("path", help="Secret path")
    add_parser.add_argument(
        "value", nargs="?", help="Secret value (prompt if not provided)"
    )
    add_parser.add_argument(
        "--namespace", "-n", help="Secret namespace (default: shared)"
    )
    add_parser.add_argument("--vault-addr", help="Override Vault server address")

    # Get secret command
    get_parser = secrets_subparsers.add_parser("get", help="Retrieve a secret value")
    get_parser.add_argument("path", help="Secret path")
    get_parser.add_argument(
        "--namespace", "-n", help="Secret namespace (default: shared)"
    )
    get_parser.add_argument("--vault-addr", help="Override Vault server address")

    # List secrets command
    list_parser = secrets_subparsers.add_parser("list", help="List secrets")
    list_parser.add_argument("path", nargs="?", help="Secret path prefix")
    list_parser.add_argument(
        "--namespace", "-n", help="Secret namespace (default: shared)"
    )
    list_parser.add_argument("--vault-addr", help="Override Vault server address")

    # Delete secret command
    delete_parser = secrets_subparsers.add_parser("delete", help="Delete a secret")
    delete_parser.add_argument("path", help="Secret path")
    delete_parser.add_argument(
        "--namespace", "-n", help="Secret namespace (default: shared)"
    )
    delete_parser.add_argument(
        "--force", "-f", action="store_true", help="Force deletion without confirmation"
    )
    delete_parser.add_argument("--vault-addr", help="Override Vault server address")


class SecretsCommand:
    """Secrets command handler."""

    def __init__(self, config: VaultRunnerConfig):
        """Initialize secrets command."""
        self.config = config
        self.vault_client = VaultClient(config)

    def execute(self, args: Namespace) -> int:
        """Execute secrets command."""
        try:
            if args.secrets_command == "add":
                return self._add_secret(args)
            elif args.secrets_command == "get":
                return self._get_secret(args)
            elif args.secrets_command == "list":
                return self._list_secrets(args)
            elif args.secrets_command == "delete":
                return self._delete_secret(args)
            else:
                logger.error("No secrets subcommand specified")
                return 1

        except Exception as e:
            logger.error(f"Secrets command failed: {e}")
            return 1

    def _add_secret(self, args: Namespace) -> int:
        """Add or update a secret."""
        # Validate secret path
        validate_secret_name(args.path)

        # Get secret value
        secret_value = args.value
        if not secret_value:
            import getpass

            secret_value = getpass.getpass(f"Enter secret value for '{args.path}': ")

        # Validate secret content
        validate_secret_content(secret_value, args.path)

        # Override Vault address if provided
        if args.vault_addr:
            self.config.vault_addr = args.vault_addr

        # Construct secret path with namespace
        namespace = (
            getattr(args, "namespace", None) or self.config.get_effective_namespace()
        )
        secret_path = f"{namespace}/{args.path}"

        # Add secret
        if self.config.dry_run:
            logger.info(
                "[DRY RUN] Would add secret: %s in namespace %s", args.path, namespace
            )
            return 0

        success = self.vault_client.put_secret(secret_path, secret_value)
        if success:
            logger.info(
                "Secret added successfully: %s in namespace %s", args.path, namespace
            )
            return 0
        else:
            logger.error("Failed to add secret: %s", args.path)
            return 1

    def _get_secret(self, args: Namespace) -> int:
        """Get a secret value."""
        # Validate secret path
        validate_secret_name(args.path)

        # Override Vault address if provided
        if args.vault_addr:
            self.config.vault_addr = args.vault_addr

        # Construct secret path with namespace
        namespace = (
            getattr(args, "namespace", None) or self.config.get_effective_namespace()
        )
        secret_path = f"{namespace}/{args.path}"

        # Get secret
        secret_value = self.vault_client.get_secret(secret_path)
        if secret_value is not None:
            print(secret_value)
            return 0
        else:
            logger.error(
                "Secret not found or access denied: %s in namespace %s",
                args.path,
                namespace,
            )
            return 1

    def _list_secrets(self, args: Namespace) -> int:
        """List secrets."""
        # Validate secret path if provided
        if args.path:
            validate_secret_name(args.path)

        # Override Vault address if provided
        if args.vault_addr:
            self.config.vault_addr = args.vault_addr

        # List secrets
        secrets = self.vault_client.list_secrets(args.path)
        if secrets is not None:
            if secrets:
                for secret in secrets:
                    print(secret)
            else:
                logger.info("No secrets found")
            return 0
        else:
            logger.error("Failed to list secrets")
            return 1

    def _delete_secret(self, args: Namespace) -> int:
        """Delete a secret."""
        # Validate secret path
        validate_secret_name(args.path)

        # Confirm deletion unless force is used
        if not args.force and not self.config.dry_run:
            response = input(f"Delete secret '{args.path}'? (y/N): ")
            if response.lower() != "y":
                logger.info("Deletion cancelled")
                return 0

        # Override Vault address if provided
        if args.vault_addr:
            self.config.vault_addr = args.vault_addr

        # Delete secret
        if self.config.dry_run:
            logger.info(f"[DRY RUN] Would delete secret: {args.path}")
            return 0

        success = self.vault_client.delete_secret(args.path)
        if success:
            logger.info(f"Secret deleted successfully: {args.path}")
            return 0
        else:
            logger.error(f"Failed to delete secret: {args.path}")
            return 1
