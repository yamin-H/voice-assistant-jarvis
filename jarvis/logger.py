"""Production logging system for Jarvis Lite.

Outputs structured, timestamped logs to a rotating file in %APPDATA%/JarvisLite/logs/
while keeping the interactive console output clean.
"""

import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path

from jarvis.config import get_data_dir

LOG_DIR = get_data_dir() / "logs"
DEFAULT_LOG_FILE = LOG_DIR / "jarvis.log"


def setup_logging(cfg=None) -> logging.Logger:
    """Initialize rotating file and console logging."""
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    level_name = "INFO"
    max_bytes = 5 * 1024 * 1024  # 5 MB
    backup_count = 3

    if cfg and "logging" in cfg:
        log_cfg = cfg["logging"]
        level_name = log_cfg.get("level", "INFO").upper()
        max_bytes = log_cfg.get("max_mb", 5) * 1024 * 1024
        backup_count = log_cfg.get("backup_count", 3)

    log_level = getattr(logging, level_name, logging.INFO)

    # Root jarvis logger
    logger = logging.getLogger("jarvis")
    logger.setLevel(logging.DEBUG)  # Capture all; handlers filter
    logger.handlers.clear()

    # 1. Rotating File Handler (detailed: time, level, module, line, message)
    file_handler = RotatingFileHandler(
        DEFAULT_LOG_FILE,
        maxBytes=max_bytes,
        backupCount=backup_count,
        encoding="utf-8",
    )
    file_handler.setLevel(log_level)
    file_formatter = logging.Formatter(
        "%(asctime)s [%(levelname)-7s] [%(name)s:%(lineno)d] %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )
    file_handler.setFormatter(file_formatter)
    logger.addHandler(file_handler)

    # 2. Console Handler (warnings and errors only, so interactive UI isn't cluttered)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.WARNING)
    console_formatter = logging.Formatter(
        "\n  [%(levelname)s] %(message)s"
    )
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

    logger.info("=" * 60)
    logger.info("Jarvis Lite session started (Log level: %s)", level_name)
    logger.info("Log file: %s", DEFAULT_LOG_FILE)
    logger.info("=" * 60)

    return logger


def get_logger(name: str | None = None) -> logging.Logger:
    """Return a namespaced logger, e.g. jarvis.agent, jarvis.router."""
    if name:
        return logging.getLogger(f"jarvis.{name}")
    return logging.getLogger("jarvis")