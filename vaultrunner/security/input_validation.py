"""
Input Validation Module

Implements security-first input validation and sanitization.
Prevents injection attacks and validates all user inputs.
"""

import re
import os
from pathlib import Path
from typing import Any
from argparse import Namespace
from urllib.parse import urlparse

from ..utils.logging import get_logger

logger = get_logger(__name__)


class ValidationError(Exception):
    """Custom exception for validation errors."""

    pass


def validate_secret_name(secret_name: str) -> None:
    """Validate secret name format for security."""
    if not secret_name:
        raise ValidationError("Secret name cannot be empty")

    # Validate format: alphanumeric, hyphens, underscores, forward slashes only
    if not re.match(r"^[a-zA-Z0-9/_-]+$", secret_name):
        raise ValidationError(
            f"Invalid secret name format: {secret_name}. "
            "Secret names must contain only alphanumeric characters, hyphens, underscores, and forward slashes"
        )

    # Check length limits
    if len(secret_name) > 255:
        raise ValidationError(
            f"Secret name too long (max 255 characters): {secret_name}"
        )


def validate_file_path(file_path: str, context: str = "file") -> None:
    """Validate file path for security."""
    if not file_path:
        raise ValidationError(f"{context.capitalize()} path cannot be empty")

    # Prevent path traversal attacks
    if ".." in file_path:
        raise ValidationError(f"Path traversal not allowed: {file_path}")

    # Ensure path is within current directory or subdirectories
    try:
        resolved_path = Path(file_path).resolve()
        current_dir = Path.cwd().resolve()

        # Check if resolved path is under current directory
        try:
            resolved_path.relative_to(current_dir)
        except ValueError:
            raise ValidationError(
                f"Path outside working directory not allowed: {file_path}"
            )

    except Exception as e:
        raise ValidationError(f"Invalid file path: {file_path} - {e}")


def validate_vault_url(vault_url: str) -> None:
    """Validate Vault server URL."""
    if not vault_url:
        raise ValidationError("Vault URL cannot be empty")

    try:
        parsed = urlparse(vault_url)

        # Check scheme
        if parsed.scheme not in ["http", "https"]:
            raise ValidationError(
                f"Invalid URL scheme: {parsed.scheme}. Must be http or https"
            )

        # Check hostname
        if not parsed.hostname:
            raise ValidationError("URL must include a hostname")

        # Warn about non-HTTPS in production
        if parsed.scheme == "http" and os.getenv("VAULTRUNNER_ENV") != "development":
            logger.warning("Using HTTP instead of HTTPS for Vault connection")
            logger.warning("This is insecure for production environments")

    except Exception as e:
        raise ValidationError(f"Invalid Vault URL format: {vault_url} - {e}")


def validate_docker_file(docker_file: str) -> None:
    """Validate Docker file format and existence."""
    # Validate file path first
    validate_file_path(docker_file, "Docker file")

    file_path = Path(docker_file)

    # Check if file exists
    if not file_path.exists():
        raise ValidationError(f"Docker file not found: {docker_file}")

    # Check file extension
    valid_extensions = [".yml", ".yaml"]
    valid_names = ["Dockerfile", "docker-compose.yml", "docker-compose.yaml"]

    if file_path.suffix not in valid_extensions and file_path.name not in valid_names:
        raise ValidationError(f"Unsupported Docker file format: {docker_file}")


def sanitize_env_value(value: str) -> str:
    """Sanitize environment variable value."""
    # Remove control characters and non-printable characters
    return "".join(char for char in value if char.isprintable())


def validate_args(args: Namespace) -> None:
    """Validate command line arguments for security."""
    # Validate config file path if provided
    if hasattr(args, "config") and args.config:
        validate_file_path(args.config, "config file")

    # Validate log level
    if hasattr(args, "log_level") and args.log_level:
        valid_levels = ["debug", "info", "warning", "error"]
        if args.log_level not in valid_levels:
            raise ValidationError(f"Invalid log level: {args.log_level}")


def validate_secret_content(secret_value: str, secret_path: str) -> None:
    """Validate secret content for security issues."""
    if not secret_value:
        raise ValidationError("Secret value cannot be empty")

    # Check for common security issues
    lower_value = secret_value.lower()

    # Check for potential credential patterns
    dangerous_patterns = [
        r'(password|secret|key|token)\s*=\s*["\']?\s*["\']?',
        r"(drop|select|insert|update|delete)\s+",
    ]

    for pattern in dangerous_patterns:
        if re.search(pattern, lower_value):
            logger.warning(
                f"Secret value contains potentially dangerous patterns: {secret_path}"
            )

    # Check minimum length for passwords
    if len(secret_value) < 8:
        logger.warning(f"Secret value is shorter than 8 characters: {secret_path}")


def is_safe_filename(filename: str) -> bool:
    """Check if filename is safe (no directory traversal, etc.)."""
    if not filename:
        return False

    # Check for dangerous characters
    dangerous_chars = ["..", "/", "\\", "\0"]
    return not any(char in filename for char in dangerous_chars)
