"""Hashing utilities for content deduplication."""

import hashlib
from typing import Optional


def compute_content_hash(text: Optional[str], media_urls: Optional[str] = None) -> str:
    """Compute hash of content for deduplication."""
    content = f"{text or ''}{media_urls or ''}"
    return hashlib.sha256(content.encode('utf-8')).hexdigest()


def compute_text_hash(text: str) -> str:
    """Compute hash of text only."""
    return hashlib.sha256(text.encode('utf-8')).hexdigest()

