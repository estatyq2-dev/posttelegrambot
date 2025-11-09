"""Text normalization."""

import re
from app.utils.text import clean_text


def normalize_text(text: str) -> str:
    """Normalize text for processing."""
    if not text:
        return ""
    
    # Clean text
    text = clean_text(text)
    
    # Remove excessive newlines
    text = re.sub(r'\n{3,}', '\n\n', text)
    
    # Remove excessive spaces
    text = re.sub(r' {2,}', ' ', text)
    
    return text.strip()


def truncate_to_limit(text: str, max_length: int = 4096) -> str:
    """Truncate text to Telegram message limit."""
    if len(text) <= max_length:
        return text
    
    # Truncate with ellipsis
    return text[:max_length - 3] + "..."

