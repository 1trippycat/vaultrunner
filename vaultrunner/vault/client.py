"""
Vault Client Module

Handles all interactions with HashiCorp Vault.
Implements security-first Vault operations with automatic key decryption.
"""

import os
import subprocess
import getpass
from typing import Optional, List
from ..utils.logging import get_logger
from ..security.key_manager import SecureKeyManager

logger = get_logger(__name__)


class VaultClient:
    """Vault client with security-first operations."""

    def __init__(self, config):
        """Initialize Vault client."""
        self.config = config
        self.key_manager = SecureKeyManager(config.vault_dir)
        self._setup_environment()

    def _setup_environment(self):
        """Setup Vault environment variables."""
        if self.config.vault_addr:
            os.environ["VAULT_ADDR"] = self.config.vault_addr

        # Always check for encrypted key and prompt for password on secret operations
        self._ensure_vault_token()

        if self.config.vault_token:
            os.environ["VAULT_TOKEN"] = self.config.vault_token
        if self.config.vault_namespace:
            os.environ["VAULT_NAMESPACE"] = self.config.vault_namespace

    def _ensure_vault_token(self):
        """Ensure we have a valid vault token, prompting for password if needed."""
        # If we already have a token from config, use it
        if self.config.vault_token:
            return

        # Check if we have an encrypted vault token
        key_data = self.key_manager.load_encrypted_key()
        if key_data:
            logger.info("Encrypted vault key found, prompting for password...")
            password = self._prompt_password("Enter password to unlock vault key")
            vault_key = self.key_manager.decrypt_vault_key(key_data["encrypted_key"], password)
            if vault_key:
                self.config.vault_token = vault_key
                logger.info("Vault key decrypted successfully")
            else:
                logger.error("Failed to decrypt vault key")
                raise ValueError("Invalid password or corrupted key")

    def _prompt_password(self, prompt: str) -> str:
        """Prompt user for password securely."""
        return getpass.getpass(f"{prompt}: ")

    def put_secret(self, path: str, value: str) -> bool:
        """Put a secret in Vault."""
        try:
            cmd = ["vault", "kv", "put", f"secret/{path}", f"value={value}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.returncode == 0
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to put secret: %s", e)
            return False

    def get_secret(self, path: str) -> Optional[str]:
        """Get a secret from Vault."""
        try:
            cmd = ["vault", "kv", "get", "-field=value", f"secret/{path}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip()
            return None
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to get secret: %s", e)
            return None

    def list_secrets(self, path: Optional[str] = None) -> Optional[List[str]]:
        """List secrets from Vault."""
        try:
            vault_path = "secret/" + (path if path else "")
            cmd = ["vault", "kv", "list", vault_path]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            if result.returncode == 0:
                return result.stdout.strip().split("\n")[2:]  # Skip header
            return None
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to list secrets: %s", e)
            return None

    def delete_secret(self, path: str) -> bool:
        """Delete a secret from Vault."""
        try:
            cmd = ["vault", "kv", "delete", f"secret/{path}"]
            result = subprocess.run(cmd, capture_output=True, text=True, check=False)
            return result.returncode == 0
        except (ValueError, RuntimeError, OSError) as e:
            logger.error("Failed to delete secret: %s", e)
            return False
