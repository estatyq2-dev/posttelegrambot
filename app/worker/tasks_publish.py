"""Publishing tasks."""

from loguru import logger

from app.db.base import get_session
from app.db.repo import Repository
from app.publisher.scheduler import run_channel_tick


async def publish_channel_task(channel_id: int):
    """Task to publish next post for a channel.
    
    Args:
        channel_id: Channel ID to publish to
    """
    logger.info(f"Starting publish task for channel {channel_id}")
    
    try:
        await run_channel_tick(channel_id)
        logger.info(f"Completed publish task for channel {channel_id}")
    except Exception as e:
        logger.error(
            f"Error in publish task for channel {channel_id}: {e}",
            exc_info=True
        )


async def publish_all_ready_task():
    """Task to publish ready posts across all channels.
    
    This is an alternative to scheduler-based publishing.
    """
    logger.info("Starting publish for all ready posts")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get all active channels
            from sqlalchemy import select
            from app.db.models import Channel
            
            stmt = select(Channel).where(Channel.is_active == True)
            result = await session.execute(stmt)
            channels = result.scalars().all()
            
            logger.info(f"Found {len(channels)} active channels")
            
            for channel in channels:
                try:
                    await publish_channel_task(channel.id)
                except Exception as e:
                    logger.error(
                        f"Error publishing to channel {channel.id}: {e}",
                        exc_info=True
                    )
            
            logger.info("Completed publish for all channels")
            
        except Exception as e:
            logger.error(f"Error in publish_all_ready_task: {e}", exc_info=True)

