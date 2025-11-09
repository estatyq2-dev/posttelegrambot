"""Logging configuration using loguru."""

import sys
from pathlib import Path

from loguru import logger

from app.config import get_settings


def setup_logging():
    """Configure loguru logger."""
    settings = get_settings()

    # Remove default handler
    logger.remove()

    # Console handler with colors
    logger.add(
        sys.stdout,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        level=settings.log_level,
        colorize=True,
    )

    # File handler for all logs
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    logger.add(
        log_dir / "news_relay_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="00:00",  # Rotate at midnight
        retention="30 days",
        compression="zip",
    )

    # Separate file for errors
    logger.add(
        log_dir / "errors_{time:YYYY-MM-DD}.log",
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="ERROR",
        rotation="00:00",
        retention="90 days",
        compression="zip",
    )

    logger.info(f"Logging initialized with level: {settings.log_level}")


def get_logger(name: str):
    """Get a logger instance with the given name."""
    return logger.bind(name=name)

