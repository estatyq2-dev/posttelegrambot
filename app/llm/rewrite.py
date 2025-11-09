"""Text rewriting logic."""

from typing import Optional

from loguru import logger

from app.llm.client import get_llm_client
from app.llm.prompts import build_system_prompt, build_user_prompt
from app.utils.text import clean_text


async def rewrite_text(
    text: str,
    style: str = "neutral",
    language: Optional[str] = None,
    custom_prompt: Optional[str] = None,
    temperature: float = 0.7,
) -> Optional[str]:
    """Rewrite text using LLM.
    
    Args:
        text: Original text to rewrite
        style: Writing style (neutral, formal, casual, brief)
        language: Target language (uk, en, ru)
        custom_prompt: Additional custom instructions
        temperature: LLM temperature (0.0-1.0)
    
    Returns:
        Rewritten text or None if failed
    """
    if not text or not text.strip():
        logger.warning("Empty text provided for rewriting")
        return None
    
    # Clean text
    text = clean_text(text)
    
    # Build prompts
    system_prompt = build_system_prompt(
        style=style,
        language=language,
        custom_prompt=custom_prompt,
    )
    user_prompt = build_user_prompt(text)
    
    # Get LLM client and rewrite
    client = get_llm_client()
    
    try:
        rewritten = await client.rewrite_text(
            text=user_prompt,
            system_prompt=system_prompt,
            temperature=temperature,
        )
        
        if rewritten:
            # Clean result
            rewritten = clean_text(rewritten)
            return rewritten
        
        logger.error("LLM returned empty result")
        return None
        
    except Exception as e:
        logger.error(f"Error during text rewriting: {e}", exc_info=True)
        return None


async def rewrite_post(
    raw_text: str,
    channel_language: Optional[str] = None,
    channel_style: Optional[str] = None,
) -> Optional[str]:
    """Rewrite a post for a specific channel.
    
    Args:
        raw_text: Original raw text
        channel_language: Target language for the channel
        channel_style: Custom style prompt for the channel
    
    Returns:
        Rewritten text ready for publishing or None
    """
    return await rewrite_text(
        text=raw_text,
        style="neutral",
        language=channel_language,
        custom_prompt=channel_style,
        temperature=0.7,
    )

