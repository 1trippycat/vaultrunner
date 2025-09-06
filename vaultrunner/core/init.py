"""
VaultRunner Application Initialization

Handles environment setup, configuration loading, and security validation.
Implements security-first design principles.
"""

import os
import sys
from pathlib import Path
from typing import Any, Dict
from argparse import Namespace

from ..config.config_loader import ConfigLoader
from ..utils.logging import setup_logging, get_logger
from ..security.environment import validate_environment
from ..models.config import VaultRunnerConfig

logger = get_logger(__name__)


class VaultRunnerApp:
    """Main VaultRunner application class."""

    def __init__(self, args: Namespace):
        """Initialize VaultRunner application."""
        self.args = args
        self.config: VaultRunnerConfig = None
        self.vault_dir = Path(".vault")

        # Setup logging first
        setup_logging(args.log_level)
        logger.info("Initializing VaultRunner v1.0.0")

        # Validate environment
        self._validate_environment()

        # Load configuration
        self._load_configuration()

        # Initialize vault directory
        self._init_vault_directory()

        logger.info("VaultRunner initialization complete")

    def _validate_environment(self) -> None:
        """Validate execution environment for security."""
        logger.debug("Validating execution environment")
        validate_environment()
        logger.debug("Environment validation complete")

    def _load_configuration(self) -> None:
        """Load and validate configuration."""
        logger.debug("Loading configuration")

        config_file = self.args.config or ".vaultrunner.yml"
        config_loader = ConfigLoader(config_file)
        self.config = config_loader.load()

        # Override with command line arguments
        if self.args.dry_run:
            self.config.dry_run = True
        if self.args.log_level:
            self.config.log_level = self.args.log_level

        logger.debug("Configuration loaded successfully")

    def _init_vault_directory(self) -> None:
        """Initialize vault directory if it doesn't exist."""
        if not self.vault_dir.exists():
            logger.info(f"Creating vault directory: {self.vault_dir}")
            self.vault_dir.mkdir(mode=0o700, exist_ok=True)

    def execute_command(self, args: Namespace) -> int:
        """Execute the specified command."""
        logger.debug(f"Executing command: {args.command}")

        try:
            # Import command handlers
            from ..commands.secrets import SecretsCommand
            from ..commands.templates import TemplatesCommand
            from ..commands.docker import DockerCommand
            from ..commands.vault import VaultCommand
            from ..commands.export import ExportCommand
            from ..commands.deploy import DeployCommand
            from ..commands.secure import SecureVaultCommand
            from ..commands.backup import BackupRestoreCommand
            from ..commands.migrate import handle_migrate_command
            from ..commands.bulk import handle_bulk_command
            from ..vault.client import VaultClient

            # Route to appropriate command
            if args.command == "secrets":
                command = SecretsCommand(self.config)
                return command.execute(args)
            elif args.command == "templates":
                command = TemplatesCommand(self.config)
                return command.execute(args)
            elif args.command == "docker":
                command = DockerCommand(self.config)
                return command.execute(args)
            elif args.command == "vault":
                command = VaultCommand(self.config)
                return command.execute(args)
            elif args.command == "export":
                command = ExportCommand(self.config)
                return command.execute(args)
            elif args.command == "deploy":
                command = DeployCommand(self.config)
                return command.execute(args)
            elif args.command == "secure":
                command = SecureVaultCommand(self.config)
                return command.execute(args)
            elif args.command == "backup":
                command = BackupRestoreCommand(self.config)
                return command.execute(args)
            elif args.command == "mcp-server":
                from ..commands.mcp import run_mcp_server
                return run_mcp_server(args)
            elif args.command == "import":
                vault_client = VaultClient(self.config)
                handle_migrate_command(args, self.config, vault_client)
                return 0
            elif args.command in ["namespace", "bulk-set", "bulk-get"]:
                vault_client = VaultClient(self.config)
                handle_bulk_command(args, self.config, vault_client)
                return 0
            else:
                logger.error("Unknown command: %s", args.command)
                return 1

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Command execution failed: %s", e)
            if self.config.log_level == "debug":
                import traceback

                traceback.print_exc()
            return 1
