"""Post formatting utilities."""

from app.processing.normalize import normalize_text, truncate_to_limit


def format_post(text: str, max_length: int = 4096) -> str:
    """Format post text for publishing."""
    # Normalize
    text = normalize_text(text)
    
    # Truncate if needed
    text = truncate_to_limit(text, max_length)
    
    return text

