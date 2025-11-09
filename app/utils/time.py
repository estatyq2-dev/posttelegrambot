"""Time utilities."""

from datetime import datetime, timedelta
from typing import Optional

import pytz

from app.config import get_settings


def now_tz() -> datetime:
    """Get current time in configured timezone."""
    settings = get_settings()
    tz = pytz.timezone(settings.timezone)
    return datetime.now(tz)


def to_utc(dt: datetime) -> datetime:
    """Convert datetime to UTC."""
    if dt.tzinfo is None:
        # Assume it's in the configured timezone
        settings = get_settings()
        tz = pytz.timezone(settings.timezone)
        dt = tz.localize(dt)
    return dt.astimezone(pytz.UTC)


def from_utc(dt: datetime) -> datetime:
    """Convert UTC datetime to configured timezone."""
    settings = get_settings()
    tz = pytz.timezone(settings.timezone)
    if dt.tzinfo is None:
        dt = pytz.UTC.localize(dt)
    return dt.astimezone(tz)


def format_datetime(dt: Optional[datetime], fmt: str = "%Y-%m-%d %H:%M") -> str:
    """Format datetime to string."""
    if dt is None:
        return "Ніколи"
    dt_local = from_utc(dt) if dt.tzinfo else dt
    return dt_local.strftime(fmt)


def parse_interval(text: str) -> Optional[int]:
    """Parse interval text to minutes (e.g., '1h', '30m', '2h30m')."""
    text = text.lower().strip()
    
    # Try to parse as pure number (minutes)
    if text.isdigit():
        return int(text)
    
    # Parse format like "1h", "30m", "2h30m"
    hours = 0
    minutes = 0
    
    import re
    hours_match = re.search(r'(\d+)h', text)
    minutes_match = re.search(r'(\d+)m', text)
    
    if hours_match:
        hours = int(hours_match.group(1))
    if minutes_match:
        minutes = int(minutes_match.group(1))
    
    total_minutes = hours * 60 + minutes
    return total_minutes if total_minutes > 0 else None

