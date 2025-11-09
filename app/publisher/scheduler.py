"""Publishing scheduler using APScheduler."""

from datetime import datetime, timedelta
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.config import get_settings
from app.db.base import get_session
from app.db.models import Channel, PostStatus
from app.db.repo import Repository
from app.publisher.telegram_bot import publish_post


# Global scheduler instance
_scheduler: Optional[AsyncIOScheduler] = None


def get_scheduler() -> AsyncIOScheduler:
    """Get or create scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = AsyncIOScheduler()
    return _scheduler


async def run_channel_tick(channel_id: int):
    """Execute publishing tick for a channel.
    
    This function:
    1. Gets next ready post for channel
    2. Publishes it
    3. Updates post status
    """
    logger.debug(f"Running tick for channel {channel_id}")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get channel
            # Note: We need owner_user_id, but scheduler doesn't have it
            # We'll need to fetch channel first to get owner
            from sqlalchemy import select
            from app.db.models import Channel
            
            stmt = select(Channel).where(Channel.id == channel_id)
            result = await session.execute(stmt)
            channel = result.scalar_one_or_none()
            
            if not channel:
                logger.error(f"Channel {channel_id} not found")
                return
            
            if not channel.is_active:
                logger.debug(f"Channel {channel_id} is inactive, skipping")
                return
            
            # Get next post
            post = await repo.get_next_post_for_channel(channel_id)
            
            if not post:
                logger.debug(f"No ready posts for channel {channel_id}")
                return
            
            # Publish
            logger.info(f"Publishing post {post.id} to channel {channel_id}")
            success, error = await publish_post(post, channel.telegram_id)
            
            if success:
                # Mark as published
                await repo.update_post(
                    post.id,
                    post.owner_user_id,
                    status=PostStatus.PUBLISHED,
                    published_at=datetime.utcnow(),
                )
                
                # Update channel last_published_at
                await repo.update_channel(
                    channel_id,
                    channel.owner_user_id,
                    last_published_at=datetime.utcnow(),
                )
                
                logger.info(f"Post {post.id} published successfully")
            else:
                # Mark as failed
                await repo.update_post(
                    post.id,
                    post.owner_user_id,
                    status=PostStatus.FAILED,
                    error_message=error or "Unknown error",
                    retry_count=post.retry_count + 1,
                )
                
                logger.error(f"Failed to publish post {post.id}: {error}")
        
        except Exception as e:
            logger.error(f"Error in channel tick {channel_id}: {e}", exc_info=True)


async def schedule_channel(channel: Channel):
    """Add channel to scheduler."""
    scheduler = get_scheduler()
    
    job_id = f"channel_{channel.id}"
    
    # Remove existing job if any
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
    
    # Add new job
    scheduler.add_job(
        run_channel_tick,
        trigger=IntervalTrigger(minutes=channel.publish_interval_minutes),
        args=[channel.id],
        id=job_id,
        name=f"Channel {channel.title} ({channel.id})",
        replace_existing=True,
    )
    
    logger.info(
        f"Scheduled channel {channel.id} with interval "
        f"{channel.publish_interval_minutes} minutes"
    )


async def unschedule_channel(channel_id: int):
    """Remove channel from scheduler."""
    scheduler = get_scheduler()
    job_id = f"channel_{channel_id}"
    
    if scheduler.get_job(job_id):
        scheduler.remove_job(job_id)
        logger.info(f"Unscheduled channel {channel_id}")


async def init_scheduler():
    """Initialize scheduler with all active channels."""
    logger.info("Initializing publisher scheduler...")
    
    async with get_session() as session:
        repo = Repository(session)
        
        # This is a simplified version - in production, iterate over all users
        # For now, we'll add a separate function to register channels
        pass
    
    scheduler = get_scheduler()
    
    if not scheduler.running:
        scheduler.start()
        logger.info("Scheduler started")


async def shutdown_scheduler():
    """Shutdown scheduler."""
    scheduler = get_scheduler()
    
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Scheduler shut down")


async def refresh_channel_schedule(channel: Channel):
    """Refresh schedule for a channel (reschedule with new settings)."""
    if channel.is_active:
        await schedule_channel(channel)
    else:
        await unschedule_channel(channel.id)

