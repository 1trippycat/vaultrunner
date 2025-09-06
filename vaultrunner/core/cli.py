"""
CLI Module - Command Line Interface

Handles command line parsing and routing to appropriate modules.
Implements security-first design with input validation.
"""

import sys
import argparse
from typing import List, Optional

from ..core.init import VaultRunnerApp
from ..utils.logging import get_logger
from ..security.input_validation import validate_args

logger = get_logger(__name__)


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser with all subcommands."""
    parser = argparse.ArgumentParser(
        prog="vaultrunner",
        description="HashiCorp Vault Docker Integration Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  vaultrunner secrets add myapp/database/password
  vaultrunner templates create myapp/database/password
  vaultrunner docker upgrade docker-compose.yml
  vaultrunner vault deploy
  vaultrunner export docker-compose.yml

For more help on a specific command, use:
  vaultrunner <command> --help
        """,
    )

    parser.add_argument("--version", action="version", version="VaultRunner 1.0.0")

    parser.add_argument(
        "--docker", action="store_true", help="Enable Docker-specific optimizations"
    )

    parser.add_argument(
        "--config", type=str, help="Configuration file path (default: .vaultrunner.yml)"
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be done without executing",
    )

    parser.add_argument(
        "--log-level",
        choices=["debug", "info", "warning", "error"],
        default="info",
        help="Set logging level",
    )

    # Create subparsers
    subparsers = parser.add_subparsers(
        dest="command", help="Available commands", metavar="<command>"
    )

        # Import and register subcommand parsers
    from ..commands.secrets import register_secrets_parser
    from ..commands.templates import register_templates_parser
    from ..commands.docker import register_docker_parser
    from ..commands.vault import register_vault_parser
    from ..commands.export import register_export_parser
    from ..commands.bulk import register_bulk_commands
    from ..commands.deploy import register_deploy_parser
    from ..commands.migrate import register_migrate_commands
    from ..commands.secure import register_secure_commands
    from ..commands.backup import register_backup_commands
    from ..commands.mcp import register_mcp_parser

    register_secrets_parser(subparsers)
    register_templates_parser(subparsers)
    register_docker_parser(subparsers)
    register_vault_parser(subparsers)
    register_export_parser(subparsers)
    register_bulk_commands(subparsers)
    register_deploy_parser(subparsers)
    register_migrate_commands(subparsers)
    register_secure_commands(subparsers)
    register_backup_commands(subparsers)
    register_mcp_parser(subparsers)

    return parser


def main(argv: Optional[List[str]] = None) -> int:
    """Main entry point for VaultRunner CLI."""
    if argv is None:
        argv = sys.argv[1:]

    args = None
    try:
        # Parse arguments
        parser = create_parser()
        args = parser.parse_args(argv)

        # Validate arguments for security
        validate_args(args)

        # Show help if no command specified
        if not args.command:
            parser.print_help()
            return 0

        # Initialize VaultRunner application
        app = VaultRunnerApp(args)

        # Route to appropriate command handler
        return app.execute_command(args)

    except KeyboardInterrupt:
        logger.info("Operation cancelled by user")
        return 130
    except (ValueError, RuntimeError, OSError) as e:
        logger.error("Unexpected error: %s", e)
        if args and hasattr(args, "log_level") and args.log_level == "debug":
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
