"""Rewriting tasks."""

from datetime import datetime

from loguru import logger

from app.db.base import get_session
from app.db.models import PostStatus, RawMessage
from app.db.repo import Repository
from app.llm.rewrite import rewrite_post
from app.processing.moderation import moderate_content


async def rewrite_message_task(raw_message_id: int, owner_user_id: int):
    """Task to rewrite a raw message and create posts.
    
    Args:
        raw_message_id: Raw message ID to process
        owner_user_id: Owner user ID for isolation
    """
    logger.info(f"Starting rewrite task for message {raw_message_id}")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get raw message
            raw_message = await repo.get_raw_message(raw_message_id, owner_user_id)
            
            if not raw_message:
                logger.error(f"Raw message {raw_message_id} not found")
                return
            
            if raw_message.is_processed:
                logger.debug(f"Message {raw_message_id} already processed")
                return
            
            # Moderate content
            is_ok, reason = moderate_content(raw_message.text or "")
            if not is_ok:
                logger.warning(
                    f"Message {raw_message_id} failed moderation: {reason}"
                )
                await repo.mark_message_processed(raw_message_id, owner_user_id)
                return
            
            # Get bindings for this source to determine target channels
            bindings = await repo.get_bindings_for_source(raw_message.source_id)
            
            if not bindings:
                logger.debug(f"No bindings for source {raw_message.source_id}")
                await repo.mark_message_processed(raw_message_id, owner_user_id)
                return
            
            # Process for each channel
            for binding in bindings:
                if not binding.is_active:
                    continue
                
                channel = binding.channel
                if not channel.is_active:
                    continue
                
                try:
                    # Rewrite text for this channel
                    rewritten = await rewrite_post(
                        raw_text=raw_message.text or "",
                        channel_language=channel.language,
                        channel_style=channel.style_prompt,
                    )
                    
                    if not rewritten:
                        logger.error(
                            f"Failed to rewrite message {raw_message_id} "
                            f"for channel {channel.id}"
                        )
                        continue
                    
                    # Create post
                    post = await repo.create_post(
                        owner_user_id=owner_user_id,
                        channel_id=channel.id,
                        text=rewritten,
                        raw_message_id=raw_message_id,
                        media_paths=raw_message.media_paths,
                        status=PostStatus.READY,
                    )
                    
                    logger.info(
                        f"Created post {post.id} for channel {channel.id} "
                        f"from message {raw_message_id}"
                    )
                    
                except Exception as e:
                    logger.error(
                        f"Error creating post for channel {channel.id}: {e}",
                        exc_info=True
                    )
            
            # Mark message as processed
            await repo.mark_message_processed(raw_message_id, owner_user_id)
            logger.info(f"Completed rewrite task for message {raw_message_id}")
            
        except Exception as e:
            logger.error(
                f"Error in rewrite task for message {raw_message_id}: {e}",
                exc_info=True
            )


async def rewrite_all_pending_task():
    """Task to rewrite all unprocessed messages.
    
    This can be scheduled periodically.
    """
    logger.info("Starting rewrite for all pending messages")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get all unprocessed messages (across all users)
            from sqlalchemy import select
            from app.db.models import RawMessage
            
            stmt = (
                select(RawMessage)
                .where(RawMessage.is_processed == False)
                .order_by(RawMessage.created_at.asc())
                .limit(100)  # Process in batches
            )
            result = await session.execute(stmt)
            messages = result.scalars().all()
            
            logger.info(f"Found {len(messages)} pending messages to rewrite")
            
            for message in messages:
                try:
                    await rewrite_message_task(message.id, message.owner_user_id)
                except Exception as e:
                    logger.error(
                        f"Error rewriting message {message.id}: {e}",
                        exc_info=True
                    )
            
            logger.info("Completed rewrite for pending messages")
            
        except Exception as e:
            logger.error(f"Error in rewrite_all_pending_task: {e}", exc_info=True)

