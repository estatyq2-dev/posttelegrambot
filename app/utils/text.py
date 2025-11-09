"""Text processing utilities."""

import re
from typing import Optional


def clean_text(text: str) -> str:
    """Clean and normalize text."""
    if not text:
        return ""
    
    # Remove excessive whitespace
    text = re.sub(r'\s+', ' ', text)
    
    # Remove control characters
    text = ''.join(char for char in text if char.isprintable() or char in '\n\r\t')
    
    return text.strip()


def truncate_text(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """Truncate text to max length."""
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


def extract_channel_username(text: str) -> Optional[str]:
    """Extract channel username from text (supports @username or t.me/username)."""
    # Match @username
    match = re.search(r'@([a-zA-Z0-9_]{5,})', text)
    if match:
        return match.group(1)
    
    # Match t.me/username or telegram.me/username
    match = re.search(r'(?:t\.me|telegram\.me)/([a-zA-Z0-9_]{5,})', text)
    if match:
        return match.group(1)
    
    return None


def format_interval(minutes: int) -> str:
    """Format interval in human-readable format."""
    if minutes < 60:
        return f"{minutes} хв"
    hours = minutes // 60
    remaining_minutes = minutes % 60
    if remaining_minutes == 0:
        return f"{hours} год"
    return f"{hours} год {remaining_minutes} хв"


def escape_markdown(text: str) -> str:
    """Escape markdown special characters for Telegram."""
    special_chars = ['_', '*', '[', ']', '(', ')', '~', '`', '>', '#', '+', '-', '=', '|', '{', '}', '.', '!']
    for char in special_chars:
        text = text.replace(char, f'\\{char}')
    return text

