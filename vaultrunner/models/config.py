"""
Configuration Model

Defines the configuration data structures for VaultRunner.
Implements security-first configuration with validation.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any
from pathlib import Path


@dataclass
class VaultRunnerConfig:
    """VaultRunner configuration model."""

    # Vault connection settings
    vault_addr: Optional[str] = None
    vault_token: Optional[str] = None
    vault_namespace: Optional[str] = None

    # Authentication settings
    auth_method: str = "token"

    # Application settings
    dry_run: bool = False
    log_level: str = "info"

    # Secret namespace settings
    secret_namespace: Optional[str] = None  # If None, uses 'shared' namespace
    default_namespace: str = "shared"

    # Migration and compatibility settings
    env_file_path: Optional[str] = None
    docker_secrets_path: Optional[str] = None
    export_format: str = "env"  # env, yaml, json

    # Docker settings
    docker_compose_file: str = "docker-compose.yml"

    # Kubernetes settings
    kubernetes_namespace: str = "default"

    # Vault directory settings
    vault_dir: Path = field(default_factory=lambda: Path(".vault"))

    # Development workflow settings
    environment: str = "development"  # development, staging, production
    auto_backup: bool = True
    backup_retention_days: int = 30

    # Additional configuration
    config_file: Optional[str] = None
    backup_enabled: bool = True

    def __post_init__(self):
        """Post-initialization validation."""
        # Validate log level
        if self.log_level not in ["debug", "info", "warning", "error"]:
            raise ValueError(f"Invalid log level: {self.log_level}")

        # Validate auth method
        valid_auth_methods = ["token", "userpass", "ldap", "github"]
        if self.auth_method not in valid_auth_methods:
            raise ValueError(f"Invalid auth method: {self.auth_method}")

        # Validate export format
        valid_export_formats = ["env", "yaml", "json", "docker-compose"]
        if self.export_format not in valid_export_formats:
            raise ValueError(f"Invalid export format: {self.export_format}")

        # Validate environment
        valid_environments = ["development", "staging", "production"]
        if self.environment not in valid_environments:
            raise ValueError(f"Invalid environment: {self.environment}")

        # Ensure vault_dir is a Path object
        if isinstance(self.vault_dir, str):
            self.vault_dir = Path(self.vault_dir)

    def get_effective_namespace(self) -> str:
        """Get the effective namespace for secrets."""
        return self.secret_namespace or self.default_namespace

    def get_vault_path(self, secret_name: str) -> str:
        """Get the full Vault path for a secret."""
        namespace = self.get_effective_namespace()
        return f"secret/{namespace}/{secret_name}"

    def is_shared_namespace(self) -> bool:
        """Check if using the shared namespace."""
        return self.get_effective_namespace() == self.default_namespace

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        result = {}
        for key, value in self.__dict__.items():
            if isinstance(value, Path):
                result[key] = str(value)
            else:
                result[key] = value
        return result

    def is_vault_configured(self) -> bool:
        """Check if Vault is properly configured."""
        return bool(self.vault_addr and self.vault_token)

    def get_vault_url(self) -> Optional[str]:
        """Get the Vault server URL."""
        return self.vault_addr

    def mask_sensitive_config(self) -> Dict[str, Any]:
        """Get configuration with sensitive values masked."""
        config_dict = self.to_dict()

        # Mask sensitive values
        if config_dict.get("vault_token"):
            config_dict["vault_token"] = "***masked***"

        return config_dict
