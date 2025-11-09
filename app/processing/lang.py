"""Language detection."""

from typing import Optional

from langdetect import detect, LangDetectException
from loguru import logger


def detect_language(text: str) -> Optional[str]:
    """Detect language of text.
    
    Returns:
        Language code (uk, en, ru, etc.) or None
    """
    if not text or len(text.strip()) < 10:
        return None
    
    try:
        lang = detect(text)
        return lang
    except LangDetectException as e:
        logger.debug(f"Language detection failed: {e}")
        return None

