"""
Secure Vault Commands

Provides secure vault initialization, key management, and export functionality.
"""

import getpass
from ..utils.logging import get_logger
from ..security.key_manager import SecureKeyManager
from ..models.config import VaultRunnerConfig

logger = get_logger(__name__)


def register_secure_commands(cli_parser):
    """Register secure vault commands with the CLI parser."""

    # Secure vault command
    secure_parser = cli_parser.add_parser(
        "secure", help="Secure vault key management and initialization"
    )
    secure_subparsers = secure_parser.add_subparsers(
        dest="secure_command", help="Secure vault commands"
    )

    # Initialize secure vault
    init_parser = secure_subparsers.add_parser(
        "init", help="Initialize secure vault with encrypted keys"
    )
    init_parser.add_argument(
        "--password", help="Password for key encryption (prompt if not provided)"
    )
    init_parser.add_argument(
        "--export-key", action="store_true",
        help="Export the generated vault key to stdout"
    )

    # Export vault key
    export_parser = secure_subparsers.add_parser(
        "export", help="Export vault key after password verification"
    )
    export_parser.add_argument(
        "--password", help="Password for key decryption (prompt if not provided)"
    )

    # Change password
    change_parser = secure_subparsers.add_parser(
        "change-password", help="Change the password for vault key encryption"
    )
    change_parser.add_argument(
        "--old-password", help="Current password (prompt if not provided)"
    )
    change_parser.add_argument(
        "--new-password", help="New password (prompt if not provided)"
    )


class SecureVaultCommand:
    """Secure vault command handler."""

    def __init__(self, config: VaultRunnerConfig):
        self.config = config
        self.key_manager = SecureKeyManager(config.vault_dir)

    def execute(self, args):
        """Execute secure vault command."""
        command = getattr(args, "secure_command", None)

        if command == "init":
            return self._init_secure_vault(args)
        elif command == "export":
            return self._export_vault_key(args)
        elif command == "change-password":
            return self._change_password(args)
        else:
            print("Secure vault commands:")
            print("  init           - Initialize secure vault with encrypted keys")
            print("  export         - Export vault key after password verification")
            print("  change-password - Change the password for vault key encryption")
            return 0

    def _init_secure_vault(self, args) -> int:
        """Initialize secure vault with encrypted keys."""
        try:
            # Get password
            password = args.password
            if not password:
                password = self._prompt_password("Enter password for vault key encryption")
                confirm_password = self._prompt_password("Confirm password")
                if password != confirm_password:
                    print("Passwords do not match!")
                    return 1

            # Initialize secure vault
            result = self.key_manager.initialize_secure_vault(password)

            print("🔐 Secure Vault initialized successfully!")
            print(f"📄 SSL Certificate: {result['ssl_certificate']}")
            print(f"🔑 SSL Private Key: {result['ssl_private_key']}")

            if args.export_key:
                print(f"🗝️  Vault Root Key: {result['vault_key']}")
                print("⚠️  WARNING: Store this key securely! It will not be shown again.")
            else:
                print("💡 Use 'vaultrunner secure export' to retrieve the vault key later")

            print("\nNext steps:")
            print("1. Start Vault with: vaultrunner vault deploy --dev")
            print("2. Set VAULT_TOKEN environment variable")
            print("3. Use VaultRunner commands as usual")

            return 0

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to initialize secure vault: %s", e)
            return 1

    def _export_vault_key(self, args) -> int:
        """Export vault key after password verification."""
        try:
            # Get password
            password = args.password
            if not password:
                password = self._prompt_password("Enter password to decrypt vault key")

            # Export key
            vault_key = self.key_manager.export_vault_key(password)

            if vault_key:
                print(f"🗝️  Vault Root Key: {vault_key}")
                print("⚠️  WARNING: Keep this key secure!")
                return 0
            else:
                print("❌ Failed to decrypt vault key. Incorrect password?")
                return 1

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to export vault key: %s", e)
            return 1

    def _change_password(self, args) -> int:
        """Change the password for vault key encryption."""
        try:
            # Get old password
            old_password = args.old_password
            if not old_password:
                old_password = self._prompt_password("Enter current password")

            # Get new password
            new_password = args.new_password
            if not new_password:
                new_password = self._prompt_password("Enter new password")
                confirm_password = self._prompt_password("Confirm new password")
                if new_password != confirm_password:
                    print("New passwords do not match!")
                    return 1

            # Load current encrypted key
            key_data = self.key_manager.load_encrypted_key()
            if not key_data:
                print("❌ No encrypted key found. Run 'vaultrunner secure init' first.")
                return 1

            # Decrypt with old password
            vault_key = self.key_manager.decrypt_vault_key(key_data["encrypted_key"], old_password)

            # Encrypt with new password
            new_encrypted_key = self.key_manager.encrypt_vault_key(vault_key, new_password)

            # Update stored key
            key_data["encrypted_key"] = new_encrypted_key
            self.key_manager.store_encrypted_key(new_encrypted_key, key_data["metadata"])

            print("✅ Password changed successfully!")
            return 0

        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to change password: %s", e)
            return 1

    def _prompt_password(self, prompt: str) -> str:
        """Prompt user for password securely."""
        return getpass.getpass(f"{prompt}: ")