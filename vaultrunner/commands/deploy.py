"""
Deployment Command Module

Handles deployment operations with namespace support for secure secret injection.
"""

from argparse import ArgumentParser, Namespace
from typing import Any

from ..models.config import VaultRunnerConfig
from ..utils.logging import get_logger
from ..vault.client import VaultClient

logger = get_logger(__name__)


def register_deploy_parser(subparsers: Any) -> None:
    """Register deploy subcommand parser."""
    parser = subparsers.add_parser(
        "deploy",
        help="Deploy applications with Vault secret injection",
        description="Deploy Docker Compose applications with automatic secret injection from Vault namespaces",
    )

    parser.add_argument(
        "--namespace", "-n",
        help="Secret namespace to use for deployment (default: shared)"
    )
    parser.add_argument(
        "--compose-file", "-f",
        default="docker-compose.yml",
        help="Docker Compose file to deploy (default: docker-compose.yml)"
    )
    parser.add_argument(
        "--vault-addr",
        help="Override Vault server address"
    )
    parser.add_argument(
        "--env-file",
        help="Environment file to load additional variables"
    )
    parser.add_argument(
        "--services",
        help="Comma-separated list of specific services to deploy"
    )
    parser.add_argument(
        "--network",
        help="Docker network to use for deployment"
    )
    parser.add_argument(
        "--auto-networks",
        action="store_true",
        help="Automatically detect and create networks"
    )
    parser.add_argument(
        "--sidecar",
        action="store_true",
        help="Deploy with VaultRunner sidecar for secret injection"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show deployment plan without executing"
    )


class DeployCommand:
    """Deploy command handler."""

    def __init__(self, config: VaultRunnerConfig):
        """Initialize deploy command."""
        self.config = config
        self.vault_client = VaultClient(config)

    def execute(self, args: Namespace) -> int:
        """Execute deploy command."""
        try:
            return self._deploy(args)
        except (ValueError, FileNotFoundError, ConnectionError) as e:
            logger.error("Deploy command failed: %s", e)
            return 1

    def _deploy(self, args: Namespace) -> int:
        """Deploy application with Vault integration."""
        # Get namespace
        namespace = (
            getattr(args, "namespace", None) or
            self.config.get_effective_namespace()
        )

        logger.info("Deploying with namespace: %s", namespace)

        # Override Vault address if provided
        if args.vault_addr:
            self.config.vault_addr = args.vault_addr

        # Validate namespace exists and has secrets
        secrets = self.vault_client.list_secrets()
        if not secrets:
            logger.warning("No secrets found in namespace: %s", namespace)
            logger.info("You can add secrets with: vaultrunner secrets add <path> <value> --namespace %s", namespace)
            return 1

        # Check if compose file exists
        import os
        if not os.path.exists(args.compose_file):
            logger.error("Compose file not found: %s", args.compose_file)
            return 1

        # Dry run mode
        if args.dry_run:
            return self._dry_run(args, namespace, secrets)

        # Perform deployment
        return self._perform_deployment(args, namespace, secrets)

    def _dry_run(self, args: Namespace, namespace: str, secrets: list) -> int:
        """Show deployment plan without executing."""
        logger.info("🔍 DRY RUN - Deployment Plan:")
        logger.info("  📁 Compose file: %s", args.compose_file)
        logger.info("  📦 Namespace: %s", namespace)
        logger.info("  🔐 Secrets found: %d", len(secrets))

        if args.services:
            logger.info("  🐳 Services: %s", args.services)

        if args.sidecar:
            logger.info("  🔗 Sidecar: VaultRunner sidecar will be deployed")

        if args.network:
            logger.info("  🌐 Network: %s", args.network)

        logger.info("\n📋 Secrets that will be injected:")
        for secret in secrets[:10]:  # Show first 10
            logger.info("  • %s", secret)

        if len(secrets) > 10:
            logger.info("  ... and %d more", len(secrets) - 10)

        logger.info("\n✅ Dry run complete - no changes made")
        return 0

    def _perform_deployment(self, args: Namespace, namespace: str, secrets: list) -> int:
        """Perform the actual deployment."""
        import subprocess
        import os

        logger.info("🚀 Deploying %s with namespace %s", args.compose_file, namespace)

        # Build docker compose command
        cmd = ["docker", "compose", "-f", args.compose_file]

        # Add specific services if provided
        if args.services:
            services = args.services.split(",")
            cmd.extend(["up", "-d"] + services)
        else:
            cmd.extend(["up", "-d"])

        # Set environment variables for Vault access
        env = os.environ.copy()
        env.update({
            "VAULT_ADDR": self.config.vault_addr,
            "VAULT_TOKEN": self.config.vault_token or "",
            "VAULTRUNNER_NAMESPACE": namespace,
        })

        # Add environment file if provided
        if args.env_file:
            if os.path.exists(args.env_file):
                cmd.extend(["--env-file", args.env_file])
                logger.info("📄 Using environment file: %s", args.env_file)
            else:
                logger.warning("Environment file not found: %s", args.env_file)

        logger.info("🔧 Executing: %s", ' '.join(cmd))

        try:
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                cwd=os.getcwd(),
                check=False
            )

            if result.returncode == 0:
                logger.info("✅ Deployment successful!")
                logger.info("🔍 Check logs: docker compose -f %s logs", args.compose_file)
                logger.info("📊 Check status: docker compose -f %s ps", args.compose_file)

                # Show secret injection verification
                self._verify_secret_injection(args, namespace)

                return 0
            else:
                logger.error("❌ Deployment failed!")
                logger.error(f"STDOUT: {result.stdout}")
                logger.error("STDERR: %s", result.stderr)
                return 1

        except (subprocess.SubprocessError, OSError) as e:
            logger.error("Deployment execution failed: %s", e)
            return 1

    def _verify_secret_injection(self, args: Namespace, namespace: str) -> None:
        """Verify that secrets are being injected properly."""
        logger.info("\n🔍 Secret Injection Verification:")
        logger.info("  📋 To verify secrets are injected, run:")
        logger.info("    docker compose -f %s logs | grep -i vault", args.compose_file)
        logger.info("  🧪 Or check environment variables in a container:")
        logger.info("    docker compose -f %s exec <service> env | grep -E '(VAULT|SECRET)'", args.compose_file)
        logger.info("  📊 Current namespace: %s", namespace)