"""
Environment Validation Module

Validates the execution environment for security and required dependencies.
"""

import os
import shutil
from pathlib import Path
from typing import List

from ..utils.logging import get_logger

logger = get_logger(__name__)


class EnvironmentError(Exception):
    """Custom exception for environment validation errors."""

    pass


def validate_environment() -> None:
    """Validate execution environment for security and requirements."""
    logger.debug("Validating execution environment")

    # Check required tools
    _check_required_tools()

    # Validate current directory permissions
    _check_directory_permissions()

    # Check Python version
    _check_python_version()

    logger.debug("Environment validation complete")


def _check_required_tools() -> None:
    """Check that required external tools are available."""
    required_tools = ["docker", "jq"]
    optional_tools = ["yq", "kubectl"]

    missing_required = []
    missing_optional = []

    for tool in required_tools:
        if not shutil.which(tool):
            missing_required.append(tool)

    for tool in optional_tools:
        if not shutil.which(tool):
            missing_optional.append(tool)

    if missing_required:
        raise EnvironmentError(
            f"Required tools not found in PATH: {', '.join(missing_required)}"
        )

    if missing_optional:
        logger.warning(f"Optional tools not found: {', '.join(missing_optional)}")


def _check_directory_permissions() -> None:
    """Validate current directory permissions."""
    current_dir = Path.cwd()

    # Check if directory is writable
    if not os.access(current_dir, os.W_OK):
        raise EnvironmentError("Current directory is not writable")

    # Check if we can create subdirectories
    test_dir = current_dir / ".vaultrunner_test"
    try:
        test_dir.mkdir(exist_ok=True)
        test_dir.rmdir()
    except Exception as e:
        raise EnvironmentError(f"Cannot create subdirectories: {e}")


def _check_python_version() -> None:
    """Check Python version compatibility."""
    import sys

    if sys.version_info < (3, 8):
        raise EnvironmentError(
            f"Python 3.8+ required, found {sys.version_info.major}.{sys.version_info.minor}"
        )


def get_vault_binary_path() -> str:
    """Get path to Vault binary, if available."""
    vault_path = shutil.which("vault")
    if not vault_path:
        logger.warning("Vault CLI not found in PATH")
        return ""
    return vault_path


def check_docker_daemon() -> bool:
    """Check if Docker daemon is running."""
    try:
        import subprocess

        result = subprocess.run(
            ["docker", "info"], capture_output=True, text=True, timeout=10
        )
        return result.returncode == 0
    except Exception:
        return False


def is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    try:
        # Check for Docker-specific files
        if Path("/.dockerenv").exists():
            return True

        # Check cgroup for Docker
        with open("/proc/1/cgroup", "r") as f:
            content = f.read()
            return "docker" in content or "containerd" in content
    except Exception:
        return False


def get_environment_info() -> dict:
    """Get information about the current environment."""
    import sys
    import platform

    return {
        "python_version": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "platform": platform.platform(),
        "architecture": platform.architecture()[0],
        "cwd": str(Path.cwd()),
        "vault_available": bool(get_vault_binary_path()),
        "docker_available": bool(shutil.which("docker")),
        "docker_running": check_docker_daemon(),
        "running_in_docker": is_running_in_docker(),
        "environment": os.getenv("VAULTRUNNER_ENV", "production"),
    }
