"""Telegram channel ingestion using Telethon."""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from loguru import logger
from telethon import TelegramClient
from telethon.tl.types import Message as TelethonMessage

from app.config import get_settings
from app.db.models import Source
from app.db.repo import Repository
from app.utils.hash import compute_content_hash


# Global Telethon client
_telethon_client: Optional[TelegramClient] = None


def get_telethon_client() -> TelegramClient:
    """Get or create Telethon client."""
    global _telethon_client
    
    if _telethon_client is None:
        settings = get_settings()
        
        session_path = Path(settings.tg_session_path)
        session_path.parent.mkdir(parents=True, exist_ok=True)
        
        _telethon_client = TelegramClient(
            str(session_path),
            settings.tg_api_id,
            settings.tg_api_hash,
        )
    
    return _telethon_client


async def start_telethon_client():
    """Start Telethon client."""
    client = get_telethon_client()
    
    if not client.is_connected():
        await client.start()
        logger.info("Telethon client started")


async def stop_telethon_client():
    """Stop Telethon client."""
    global _telethon_client
    
    if _telethon_client and _telethon_client.is_connected():
        await _telethon_client.disconnect()
        logger.info("Telethon client stopped")


async def download_media(message: TelethonMessage, storage_path: Path) -> Optional[str]:
    """Download media from message and return local path."""
    if not message.media:
        return None
    
    try:
        # Create unique filename
        filename = f"tg_{message.chat_id}_{message.id}_{datetime.utcnow().timestamp()}"
        
        # Download
        path = await message.download_media(file=str(storage_path / filename))
        
        if path:
            logger.debug(f"Downloaded media to {path}")
            return str(path)
        
        return None
        
    except Exception as e:
        logger.error(f"Error downloading media: {e}", exc_info=True)
        return None


async def ingest_telegram_source(source: Source, repo: Repository, limit: int = 50) -> int:
    """Ingest messages from Telegram channel.
    
    Args:
        source: Source object with Telegram handle
        repo: Database repository
        limit: Maximum number of messages to fetch
    
    Returns:
        Number of new messages ingested
    """
    if not source.handle:
        logger.error(f"Telegram source {source.id} has no handle")
        return 0
    
    logger.info(f"Ingesting Telegram source {source.id}: @{source.handle}")
    
    client = get_telethon_client()
    
    try:
        # Ensure client is started
        if not client.is_connected():
            await start_telethon_client()
        
        # Get channel entity
        try:
            entity = await client.get_entity(source.handle)
        except Exception as e:
            logger.error(f"Failed to get Telegram entity @{source.handle}: {e}")
            return 0
        
        # Update source telegram_id if not set
        if not source.telegram_id:
            await repo.update_source(
                source.id,
                source.owner_user_id,
                telegram_id=entity.id,
            )
        
        # Get messages
        messages = []
        async for message in client.iter_messages(entity, limit=limit):
            if isinstance(message, TelethonMessage) and message.text:
                messages.append(message)
        
        new_count = 0
        settings = get_settings()
        media_storage = settings.media_storage_dir
        media_storage.mkdir(parents=True, exist_ok=True)
        
        for message in reversed(messages):  # Process oldest first
            try:
                # Check if already exists
                external_id = str(message.id)
                exists = await repo.check_message_exists(
                    source_id=source.id,
                    external_id=external_id,
                    owner_user_id=source.owner_user_id,
                )
                
                if exists:
                    continue
                
                # Extract text
                text = message.text or ""
                
                # Download media if present
                media_paths = []
                if message.media:
                    media_path = await download_media(message, media_storage)
                    if media_path:
                        media_paths.append(media_path)
                
                # Create raw message
                content_hash = compute_content_hash(text)
                
                await repo.create_raw_message(
                    owner_user_id=source.owner_user_id,
                    source_id=source.id,
                    external_id=external_id,
                    text=text,
                    media_paths=json.dumps(media_paths) if media_paths else None,
                    content_hash=content_hash,
                    published_at_source=message.date,
                )
                
                new_count += 1
                logger.debug(f"Ingested Telegram message {message.id}")
                
            except Exception as e:
                logger.error(f"Error processing Telegram message: {e}", exc_info=True)
                continue
        
        # Update source last_checked_at and last_message_id
        last_message_id = messages[0].id if messages else source.last_message_id
        await repo.update_source(
            source.id,
            source.owner_user_id,
            last_checked_at=datetime.utcnow(),
            last_message_id=last_message_id,
        )
        
        logger.info(
            f"Telegram ingestion complete for source {source.id}: {new_count} new messages"
        )
        return new_count
        
    except Exception as e:
        logger.error(f"Error ingesting Telegram source {source.id}: {e}", exc_info=True)
        return 0

