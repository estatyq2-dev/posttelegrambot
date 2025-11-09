"""Media storage utilities."""

from pathlib import Path
from typing import Optional

from loguru import logger

from app.config import get_settings


def get_media_path(filename: str) -> Path:
    """Get full path for media file."""
    settings = get_settings()
    media_dir = settings.media_storage_dir
    media_dir.mkdir(parents=True, exist_ok=True)
    return media_dir / filename


def media_exists(path: str) -> bool:
    """Check if media file exists."""
    return Path(path).exists()


def delete_media(path: str) -> bool:
    """Delete media file."""
    try:
        Path(path).unlink(missing_ok=True)
        return True
    except Exception as e:
        logger.error(f"Error deleting media {path}: {e}")
        return False

