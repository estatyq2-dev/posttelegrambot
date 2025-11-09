"""Content moderation (placeholder)."""

from typing import Tuple


def moderate_content(text: str) -> Tuple[bool, str]:
    """Moderate content for spam, inappropriate content, etc.
    
    Returns:
        (is_ok, reason) - True if content is OK, False with reason otherwise
    """
    # Placeholder implementation
    # In production, add:
    # - Spam detection
    # - Profanity filtering
    # - Content policy checks
    # - etc.
    
    if not text or len(text.strip()) < 10:
        return False, "Content too short"
    
    return True, ""

