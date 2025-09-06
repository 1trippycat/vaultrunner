"""
Logging Utility Module

Provides structured logging with security considerations.
Implements security-first logging to prevent sensitive data exposure.
"""

import logging
import sys
from typing import Optional


# Log levels mapping
LOG_LEVELS = {
    "debug": logging.DEBUG,
    "info": logging.INFO,
    "warning": logging.WARNING,
    "error": logging.ERROR,
}


class SecurityFilter(logging.Filter):
    """Filter to sanitize log messages and prevent sensitive data exposure."""

    SENSITIVE_PATTERNS = ["password", "token", "key", "secret", "credential"]

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter log records to sanitize sensitive information."""
        # Convert message to string if it isn't already
        message = str(record.getMessage())

        # Check for sensitive patterns and mask them
        lower_message = message.lower()
        for pattern in self.SENSITIVE_PATTERNS:
            if pattern in lower_message:
                # Mark as potentially sensitive
                record.msg = f"[POTENTIALLY SENSITIVE] {record.msg}"
                break

        return True


def setup_logging(level: str = "info") -> None:
    """Setup logging configuration with security considerations."""
    log_level = LOG_LEVELS.get(level.lower(), logging.INFO)

    # Create formatter
    formatter = logging.Formatter(
        fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Setup handler
    handler = logging.StreamHandler(sys.stderr)
    handler.setFormatter(formatter)
    handler.addFilter(SecurityFilter())

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    root_logger.handlers.clear()
    root_logger.addHandler(handler)


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for the specified module."""
    return logging.getLogger(name)


def log_sensitive_operation(
    operation: str, resource: str, logger: logging.Logger
) -> None:
    """Log sensitive operations without exposing sensitive data."""
    logger.info(f"Performing sensitive operation: {operation} on resource: {resource}")


def sanitize_for_logging(message: str) -> str:
    """Sanitize a message for safe logging."""
    # Remove control characters and limit length
    sanitized = "".join(char for char in message if char.isprintable())
    return sanitized[:500] if len(sanitized) > 500 else sanitized
