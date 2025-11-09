"""Background task queue management using APScheduler.

Note: This implementation uses APScheduler instead of RQ/Celery for simplicity.
For production with high load, consider migrating to Celery or RQ.
"""

import asyncio
from typing import Optional

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.interval import IntervalTrigger
from loguru import logger

from app.config import get_settings
from app.connectors.telegram_ingestor import start_telethon_client, stop_telethon_client
from app.logging_conf import setup_logging
from app.worker.tasks_ingest import ingest_all_sources_task
from app.worker.tasks_rewrite import rewrite_all_pending_task


# Global worker scheduler
_worker_scheduler: Optional[AsyncIOScheduler] = None


def get_worker_scheduler() -> AsyncIOScheduler:
    """Get or create worker scheduler."""
    global _worker_scheduler
    if _worker_scheduler is None:
        _worker_scheduler = AsyncIOScheduler()
    return _worker_scheduler


async def init_worker():
    """Initialize worker with periodic tasks."""
    logger.info("Initializing background worker...")
    
    # Start Telethon client
    try:
        await start_telethon_client()
    except Exception as e:
        logger.error(f"Failed to start Telethon client: {e}", exc_info=True)
    
    scheduler = get_worker_scheduler()
    
    # Schedule periodic ingestion (every 10 minutes)
    scheduler.add_job(
        ingest_all_sources_task,
        trigger=IntervalTrigger(minutes=10),
        id="ingest_all_sources",
        name="Ingest all sources",
        replace_existing=True,
    )
    
    # Schedule periodic rewriting (every 2 minutes)
    scheduler.add_job(
        rewrite_all_pending_task,
        trigger=IntervalTrigger(minutes=2),
        id="rewrite_all_pending",
        name="Rewrite all pending messages",
        replace_existing=True,
    )
    
    # Start scheduler
    if not scheduler.running:
        scheduler.start()
        logger.info("Worker scheduler started")
    
    logger.info("Background worker initialized")


async def shutdown_worker():
    """Shutdown worker."""
    logger.info("Shutting down background worker...")
    
    scheduler = get_worker_scheduler()
    
    if scheduler.running:
        scheduler.shutdown()
        logger.info("Worker scheduler shut down")
    
    # Stop Telethon client
    try:
        await stop_telethon_client()
    except Exception as e:
        logger.error(f"Error stopping Telethon client: {e}")
    
    logger.info("Background worker shut down")


async def run_worker():
    """Run worker as standalone process."""
    setup_logging()
    logger.info("Starting background worker process...")
    
    try:
        await init_worker()
        
        # Keep running
        while True:
            await asyncio.sleep(60)
            
    except KeyboardInterrupt:
        logger.info("Received shutdown signal")
    except Exception as e:
        logger.error(f"Worker error: {e}", exc_info=True)
    finally:
        await shutdown_worker()


if __name__ == "__main__":
    # Run worker as standalone process
    asyncio.run(run_worker())

