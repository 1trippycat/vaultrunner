"""
Backup and Restore Commands

Provides encrypted backup and restore functionality for Vault secrets.
"""

import os
import json
import base64
from pathlib import Path
from datetime import datetime
from ..utils.logging import get_logger
from ..security.key_manager import SecureKeyManager
from ..models.config import VaultRunnerConfig
from ..vault.client import VaultClient

logger = get_logger(__name__)


def register_backup_commands(cli_parser):
    """Register backup and restore commands with the CLI parser."""

    # Backup command
    backup_parser = cli_parser.add_parser(
        "backup", help="Create encrypted backup of vault secrets"
    )
    backup_parser.add_argument(
        "--output", "-o", help="Output file path (default: auto-generated)"
    )
    backup_parser.add_argument(
        "--namespace", "-n", help="Namespace to backup (default: all)"
    )
    backup_parser.add_argument(
        "--password", help="Password for backup encryption (prompt if not provided)"
    )

    # Restore command
    restore_parser = cli_parser.add_parser(
        "restore", help="Restore secrets from encrypted backup"
    )
    restore_parser.add_argument(
        "backup_file", help="Path to encrypted backup file"
    )
    restore_parser.add_argument(
        "--password", help="Password for backup decryption (prompt if not provided)"
    )
    restore_parser.add_argument(
        "--dry-run", action="store_true", help="Show what would be restored without doing it"
    )

    # Cron setup command
    cron_parser = cli_parser.add_parser(
        "cron-setup", help="Set up automated nightly backups"
    )
    cron_parser.add_argument(
        "--backup-dir", help="Directory to store backups (default: .vault/backups)"
    )
    cron_parser.add_argument(
        "--password", help="Password for backup encryption (prompt if not provided)"
    )
    cron_parser.add_argument(
        "--schedule", help="Cron schedule (default: '0 2 * * *' - daily at 2 AM)"
    )


class BackupRestoreCommand:
    """Backup and restore command handler."""

    def __init__(self, config: VaultRunnerConfig):
        self.config = config
        self.key_manager = SecureKeyManager(config.vault_dir)
        self.vault_client = VaultClient(config)

    def execute(self, args):
        """Execute backup/restore command."""
        command = getattr(args, "command", None)

        if command == "backup":
            return self._create_backup(args)
        elif command == "restore":
            return self._restore_backup(args)
        elif command == "cron-setup":
            return self._setup_cron(args)
        else:
            print("Backup and restore commands:")
            print("  backup     - Create encrypted backup of vault secrets")
            print("  restore    - Restore secrets from encrypted backup")
            print("  cron-setup - Set up automated nightly backups")
            return 0

    def _create_backup(self, args) -> int:
        """Create encrypted backup of vault secrets."""
        try:
            # Get password
            password = args.password
            if not password:
                import getpass
                password = getpass.getpass("Enter password for backup encryption: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("❌ Passwords do not match!")
                    return 1

            # Determine output file
            if args.output:
                output_file = Path(args.output)
            else:
                timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
                output_file = Path(f".vault/backups/vault_backup_{timestamp}.enc")

            output_file.parent.mkdir(parents=True, exist_ok=True)

            # Get secrets to backup
            namespace = args.namespace or "shared"
            secrets = self._get_all_secrets(namespace)

            if not secrets:
                print(f"⚠️  No secrets found in namespace '{namespace}'")
                return 1

            # Create backup data
            backup_data = {
                "metadata": {
                    "created_at": datetime.now().isoformat(),
                    "namespace": namespace,
                    "secret_count": len(secrets),
                    "version": "1.0"
                },
                "secrets": secrets
            }

            # Encrypt backup
            json_data = json.dumps(backup_data, indent=2)
            encrypted_data = self.key_manager.encrypt_vault_key(json_data, password)

            # Save encrypted backup
            with open(output_file, "w", encoding="utf-8") as f:
                f.write(encrypted_data)

            print(f"✅ Backup created successfully!")
            print(f"📁 File: {output_file}")
            print(f"🔐 Secrets backed up: {len(secrets)}")
            print(f"📦 Namespace: {namespace}")

            return 0

        except Exception as e:
            logger.error("Failed to create backup: %s", e)
            print(f"❌ Failed to create backup: {e}")
            return 1

    def _restore_backup(self, args) -> int:
        """Restore secrets from encrypted backup."""
        try:
            backup_file = Path(args.backup_file)
            if not backup_file.exists():
                print(f"❌ Backup file not found: {backup_file}")
                return 1

            # Get password
            password = args.password
            if not password:
                import getpass
                password = getpass.getpass("Enter password for backup decryption: ")

            # Read encrypted backup
            with open(backup_file, "r", encoding="utf-8") as f:
                encrypted_data = f.read()

            # Decrypt backup
            json_data = self.key_manager.decrypt_vault_key(encrypted_data, password)
            backup_data = json.loads(json_data)

            print(f"📦 Restoring backup from {backup_file}")
            print(f"📅 Created: {backup_data['metadata']['created_at']}")
            print(f"🔐 Secrets: {backup_data['metadata']['secret_count']}")
            print(f"🏷️  Namespace: {backup_data['metadata']['namespace']}")

            if args.dry_run:
                print("\n📋 Secrets that would be restored:")
                for path, value in backup_data["secrets"].items():
                    print(f"  • {path}")
                print("\n💡 Use --dry-run=false to actually restore")
                return 0

            # Restore secrets
            restored_count = 0
            for path, value in backup_data["secrets"].items():
                try:
                    if not self.config.dry_run:
                        self.vault_client.put_secret(path, value)
                    restored_count += 1
                    print(f"✅ Restored: {path}")
                except Exception as e:
                    print(f"❌ Failed to restore {path}: {e}")

            print(f"\n✅ Restore completed! Restored {restored_count} secrets.")
            return 0

        except Exception as e:
            logger.error("Failed to restore backup: %s", e)
            print(f"❌ Failed to restore backup: {e}")
            return 1

    def _setup_cron(self, args) -> int:
        """Set up automated nightly backups."""
        try:
            # Get password
            password = args.password
            if not password:
                import getpass
                password = getpass.getpass("Enter password for automated backups: ")
                confirm = getpass.getpass("Confirm password: ")
                if password != confirm:
                    print("❌ Passwords do not match!")
                    return 1

            backup_dir = args.backup_dir or ".vault/backups"
            schedule = args.schedule or "0 2 * * *"

            # Create backup script
            script_content = f"""#!/bin/bash
# VaultRunner Automated Backup Script
# Generated on {datetime.now().isoformat()}

export PYTHONPATH={Path.cwd()}/src
cd {Path.cwd()}

# Run backup
/home/tipsykat/dev/core/vaultrunner/.venv/bin/python src/vaultrunner/main.py backup \\
    --output {backup_dir}/vault_backup_$(date +%Y%m%d_%H%M%S).enc \\
    --password {password!r} \\
    --namespace shared

echo "Backup completed at $(date)"
"""

            script_path = Path(".vault/scripts/backup.sh")
            script_path.parent.mkdir(parents=True, exist_ok=True)

            with open(script_path, "w", encoding="utf-8") as f:
                f.write(script_content)

            # Make script executable
            script_path.chmod(0o755)

            # Create cron job
            cron_content = f"{schedule} {script_path} >> {backup_dir}/backup.log 2>&1\n"

            print("🔧 To set up the cron job, run:")
            print(f"echo '{cron_content.strip()}' | crontab -")
            print("\n📋 Cron job details:")
            print(f"   Schedule: {schedule}")
            print(f"   Script: {script_path}")
            print(f"   Backup dir: {backup_dir}")
            print("\n✅ Automated backup setup complete!")

            return 0

        except Exception as e:
            logger.error("Failed to setup cron: %s", e)
            print(f"❌ Failed to setup automated backup: {e}")
            return 1

    def _get_all_secrets(self, namespace: str) -> dict:
        """Get all secrets from a namespace recursively."""
        secrets = {}

        def _collect_secrets(path: str):
            """Recursively collect secrets from a path."""
            try:
                items = self.vault_client.list_secrets(path)
                if items:
                    for item in items:
                        item_path = f"{path}/{item}" if path else item
                        # Check if this is a secret (has data) or a folder
                        try:
                            value = self.vault_client.get_secret(item_path)
                            if value is not None:
                                secrets[item_path] = value
                            else:
                                # It's a folder, recurse
                                _collect_secrets(item_path)
                        except:
                            # If we can't get it as a secret, try as a folder
                            _collect_secrets(item_path)
            except Exception as e:
                logger.debug("Failed to list path %s: %s", path, e)

        _collect_secrets(namespace)
        return secrets