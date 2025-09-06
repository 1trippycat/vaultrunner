"""
Configuration Loader Module

Handles loading and validation of VaultRunner configuration from multiple sources.
Implements security-first configuration management.
"""

import os
import yaml
from pathlib import Path
from typing import Dict, Any, Optional

from ..models.config import VaultRunnerConfig
from ..utils.logging import get_logger
from ..security.input_validation import validate_file_path, ValidationError

logger = get_logger(__name__)


class ConfigLoader:
    """Configuration loader with security validation."""

    def __init__(self, config_file: Optional[str] = None):
        """Initialize configuration loader."""
        self.config_file = config_file or ".vaultrunner.yml"
        self.config_data: Dict[str, Any] = {}

    def load(self) -> VaultRunnerConfig:
        """Load configuration from file and environment variables."""
        logger.debug("Loading configuration")

        # Load from config file if it exists
        if Path(self.config_file).exists():
            self._load_config_file()

        # Override with environment variables
        self._load_env_config()

        # Create configuration object
        config = self._create_config()

        logger.debug("Configuration loaded successfully")
        return config

    def _load_config_file(self) -> None:
        """Load configuration from YAML file."""
        logger.debug(f"Loading configuration from {self.config_file}")

        try:
            # Validate file path
            validate_file_path(self.config_file, "config file")

            with open(self.config_file, "r") as f:
                file_data = yaml.safe_load(f)

            # Extract vaultrunner configuration
            if isinstance(file_data, dict) and "vaultrunner" in file_data:
                self.config_data.update(file_data["vaultrunner"])
            elif isinstance(file_data, dict):
                self.config_data.update(file_data)

        except ValidationError:
            raise
        except Exception as e:
            logger.warning(f"Could not load config file {self.config_file}: {e}")

    def _load_env_config(self) -> None:
        """Load configuration from environment variables."""
        logger.debug("Loading configuration from environment variables")

        # Environment variable mappings
        env_mappings = {
            "VAULT_ADDR": "vault_addr",
            "VAULT_TOKEN": "vault_token",
            "VAULT_NAMESPACE": "vault_namespace",
            "VAULTRUNNER_AUTH_METHOD": "auth_method",
            "VAULTRUNNER_DRY_RUN": "dry_run",
            "VAULTRUNNER_LOG_LEVEL": "log_level",
            "VAULTRUNNER_DOCKER_COMPOSE_FILE": "docker_compose_file",
            "VAULTRUNNER_K8S_NAMESPACE": "kubernetes_namespace",
        }

        for env_var, config_key in env_mappings.items():
            value = os.getenv(env_var)
            if value is not None:
                # Convert boolean strings
                if config_key in ["dry_run"] and value.lower() in ["true", "false"]:
                    self.config_data[config_key] = value.lower() == "true"
                else:
                    self.config_data[config_key] = value

    def _create_config(self) -> VaultRunnerConfig:
        """Create VaultRunnerConfig object from loaded data."""
        try:
            # Create config with validation
            config = VaultRunnerConfig(**self.config_data)

            # Log masked configuration for debugging
            if logger.isEnabledFor(10):  # DEBUG level
                masked_config = config.mask_sensitive_config()
                logger.debug(f"Loaded configuration: {masked_config}")

            return config

        except Exception as e:
            raise ValidationError(f"Invalid configuration: {e}")

    def save_config(
        self, config: VaultRunnerConfig, file_path: Optional[str] = None
    ) -> None:
        """Save configuration to file."""
        output_file = file_path or self.config_file

        # Validate output path
        validate_file_path(output_file, "output config file")

        # Prepare config data (without sensitive values)
        config_data = {
            "vaultrunner": {
                "auth_method": config.auth_method,
                "log_level": config.log_level,
                "docker_compose_file": config.docker_compose_file,
                "kubernetes_namespace": config.kubernetes_namespace,
                "backup_enabled": config.backup_enabled,
            }
        }

        # Add non-sensitive vault settings
        if config.vault_addr:
            config_data["vaultrunner"]["vault_addr"] = config.vault_addr
        if config.vault_namespace:
            config_data["vaultrunner"]["vault_namespace"] = config.vault_namespace

        try:
            with open(output_file, "w") as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)

            logger.info(f"Configuration saved to {output_file}")

        except Exception as e:
            raise ValidationError(f"Could not save configuration: {e}")


def create_default_config() -> str:
    """Create a default configuration file template."""
    default_config = """# VaultRunner Configuration File
# 
# This file contains VaultRunner configuration settings.
# Do not store sensitive values like tokens here - use environment variables instead.

vaultrunner:
  # Vault server settings
  vault_addr: "https://vault.example.com:8200"
  # vault_namespace: "my-namespace"  # Enterprise feature
  
  # Authentication method
  auth_method: "token"  # token, userpass, ldap, github
  
  # Application settings
  log_level: "info"  # debug, info, warning, error
  # dry_run: false
  
  # Docker settings
  docker_compose_file: "docker-compose.yml"
  
  # Kubernetes settings
  kubernetes_namespace: "default"
  
  # Backup settings
  backup_enabled: true

# Security Notes:
# - Use VAULT_TOKEN environment variable for authentication token
# - Use VAULT_ADDR environment variable to override vault_addr
# - Never commit sensitive values to version control
"""
    return default_config
