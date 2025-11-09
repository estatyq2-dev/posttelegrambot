"""Telegram bot for publishing posts."""

import json
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from loguru import logger

from app.config import get_settings
from app.db.models import Post
from app.media.telegram_upload import upload_media_group, upload_single_photo
from app.publisher.formatter import format_post


# Global bot instance for publishing
_publish_bot: Optional[Bot] = None


def get_publish_bot() -> Bot:
    """Get or create bot instance for publishing."""
    global _publish_bot
    if _publish_bot is None:
        settings = get_settings()
        _publish_bot = Bot(token=settings.tg_bot_token)
    return _publish_bot


async def publish_post(post: Post, channel_telegram_id: int) -> tuple[bool, Optional[str]]:
    """Publish a post to Telegram channel.
    
    Args:
        post: Post object to publish
        channel_telegram_id: Telegram ID of target channel
    
    Returns:
        (success, error_message) tuple
    """
    bot = get_publish_bot()
    
    try:
        # Format text
        text = format_post(post.text)
        
        # Parse media paths
        media_paths = []
        if post.media_paths:
            try:
                media_paths = json.loads(post.media_paths)
            except json.JSONDecodeError:
                logger.warning(f"Failed to parse media_paths for post {post.id}")
        
        # Publish
        message_id = None
        
        if media_paths:
            # Publish with media
            if len(media_paths) == 1:
                # Single photo
                message_id = await upload_single_photo(
                    bot=bot,
                    chat_id=channel_telegram_id,
                    photo_path=media_paths[0],
                    caption=text,
                )
            else:
                # Media group
                message_ids = await upload_media_group(
                    bot=bot,
                    chat_id=channel_telegram_id,
                    media_paths=media_paths,
                    caption=text,
                )
                if message_ids:
                    message_id = message_ids[0]  # Store first message ID
        else:
            # Text only
            message = await bot.send_message(
                chat_id=channel_telegram_id,
                text=text,
            )
            message_id = message.message_id
        
        if message_id:
            logger.info(
                f"Post {post.id} published to channel {channel_telegram_id}, "
                f"message_id={message_id}"
            )
            return True, None
        else:
            error = "Failed to get message_id after publishing"
            logger.error(error)
            return False, error
        
    except TelegramAPIError as e:
        error = f"Telegram API error: {e}"
        logger.error(error)
        return False, error
    except Exception as e:
        error = f"Unexpected error: {e}"
        logger.error(error, exc_info=True)
        return False, error

