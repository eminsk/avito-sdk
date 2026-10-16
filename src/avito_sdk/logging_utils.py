"""
Logging utilities for avito-sdk.
Provides thread-safe file logging with rotating archives, console output,
and privacy filters to mask mobile proxy credentials and Telegram bot tokens.
"""

from __future__ import annotations

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
import re
from typing import Optional, Union


class PrivacyFilter(logging.Filter):
    """Filter that masks sensitive proxy credentials and tokens in log records."""

    _PROXY_CREDS_RE = re.compile(r'://([^:\s]+):([^@\s]+)@')
    _TG_TOKEN_RE = re.compile(r'/bot([0-9]{8,12}:[^\s/]+)')

    def filter(self, record: logging.LogRecord) -> bool:
        if isinstance(record.msg, str):
            # Mask user:pass in URLs
            record.msg = self._PROXY_CREDS_RE.sub(r'://***:***@', record.msg)
            # Mask bot tokens in URLs
            record.msg = self._TG_TOKEN_RE.sub(r'/bot***:***', record.msg)
        return True


def setup_logging(
    log_file: Optional[Union[str, Path]] = "storage/logs/avito_bot.log",
    level: int = logging.INFO,
    max_bytes: int = 10 * 1024 * 1024,
    backup_count: int = 5,
    enable_console: bool = True,
) -> logging.Logger:
    """
    Configure root and avito_sdk loggers with rotating file output and privacy filtering.

    Args:
        log_file: Path to destination log file (auto-creates directories).
        level: Logging level (default INFO).
        max_bytes: Max size per log file before rotation (default 10MB).
        backup_count: Number of rotated log archives to keep (default 5).
        enable_console: Whether to attach console StreamHandler.

    Returns:
        Configured avito_sdk logger.
    """
    logger = logging.getLogger("avito_sdk")
    logger.setLevel(level)

    formatter = logging.Formatter(
        "[%(asctime)s] [%(levelname)s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    privacy_filter = PrivacyFilter()

    # Avoid duplicate handlers on re-configuration
    for h in list(logger.handlers):
        if isinstance(h, (RotatingFileHandler, logging.FileHandler)):
            logger.removeHandler(h)

    if log_file:
        p = Path(log_file)
        p.parent.mkdir(parents=True, exist_ok=True)
        file_handler = RotatingFileHandler(
            p,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding="utf-8",
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(formatter)
        file_handler.addFilter(privacy_filter)
        logger.addHandler(file_handler)

    if enable_console and not any(isinstance(h, logging.StreamHandler) and not isinstance(h, RotatingFileHandler) for h in logger.handlers):
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(formatter)
        console_handler.addFilter(privacy_filter)
        logger.addHandler(console_handler)

    return logger
