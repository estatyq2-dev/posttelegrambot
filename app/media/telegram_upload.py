"""Telegram media upload helpers."""

import json
from pathlib import Path
from typing import Optional

from aiogram import Bot
from aiogram.types import InputMediaPhoto, InputMediaVideo, InputMediaDocument, FSInputFile
from loguru import logger


async def upload_media_group(
    bot: Bot,
    chat_id: int,
    media_paths: list[str],
    caption: Optional[str] = None,
) -> Optional[list[int]]:
    """Upload media group to Telegram.
    
    Returns:
        List of message IDs or None if failed
    """
    if not media_paths:
        return None
    
    try:
        media_group = []
        
        for i, path in enumerate(media_paths[:10]):  # Telegram limit: 10 media per group
            if not Path(path).exists():
                logger.warning(f"Media file not found: {path}")
                continue
            
            file = FSInputFile(path)
            
            # Determine media type by extension
            ext = Path(path).suffix.lower()
            
            # Add caption only to first media
            item_caption = caption if i == 0 else None
            
            if ext in ['.jpg', '.jpeg', '.png', '.webp']:
                media_group.append(InputMediaPhoto(media=file, caption=item_caption))
            elif ext in ['.mp4', '.mov', '.avi']:
                media_group.append(InputMediaVideo(media=file, caption=item_caption))
            else:
                media_group.append(InputMediaDocument(media=file, caption=item_caption))
        
        if not media_group:
            return None
        
        messages = await bot.send_media_group(chat_id=chat_id, media=media_group)
        return [msg.message_id for msg in messages]
        
    except Exception as e:
        logger.error(f"Error uploading media group: {e}", exc_info=True)
        return None


async def upload_single_photo(
    bot: Bot,
    chat_id: int,
    photo_path: str,
    caption: Optional[str] = None,
) -> Optional[int]:
    """Upload single photo to Telegram.
    
    Returns:
        Message ID or None if failed
    """
    try:
        if not Path(photo_path).exists():
            logger.warning(f"Photo file not found: {photo_path}")
            return None
        
        photo = FSInputFile(photo_path)
        message = await bot.send_photo(
            chat_id=chat_id,
            photo=photo,
            caption=caption,
        )
        
        return message.message_id
        
    except Exception as e:
        logger.error(f"Error uploading photo: {e}", exc_info=True)
        return None

