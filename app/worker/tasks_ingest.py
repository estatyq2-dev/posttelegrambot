"""Ingestion tasks."""

from loguru import logger

from app.connectors.telegram_ingestor import ingest_telegram_source
from app.connectors.rss_ingestor import ingest_rss_source
from app.db.base import get_session
from app.db.models import Source, SourceType
from app.db.repo import Repository


async def ingest_source_task(source_id: int, owner_user_id: int):
    """Task to ingest content from a source.
    
    Args:
        source_id: Source ID to ingest
        owner_user_id: Owner user ID for isolation
    """
    logger.info(f"Starting ingestion task for source {source_id}")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get source
            source = await repo.get_source(source_id, owner_user_id)
            
            if not source:
                logger.error(f"Source {source_id} not found for user {owner_user_id}")
                return
            
            if not source.is_active:
                logger.debug(f"Source {source_id} is inactive, skipping")
                return
            
            # Ingest based on type
            new_count = 0
            
            if source.source_type == SourceType.TELEGRAM:
                new_count = await ingest_telegram_source(source, repo)
            elif source.source_type == SourceType.RSS:
                new_count = await ingest_rss_source(source, repo)
            elif source.source_type == SourceType.WEBSITE:
                # Website ingestion not implemented yet
                logger.warning("Website ingestion not yet implemented")
            
            logger.info(
                f"Ingestion task completed for source {source_id}: {new_count} new messages"
            )
            
        except Exception as e:
            logger.error(f"Error in ingestion task for source {source_id}: {e}", exc_info=True)


async def ingest_all_sources_task():
    """Task to ingest all active sources.
    
    This can be scheduled periodically.
    """
    logger.info("Starting ingestion for all active sources")
    
    async with get_session() as session:
        repo = Repository(session)
        
        try:
            # Get all active sources (across all users)
            from sqlalchemy import select
            from app.db.models import Source
            
            stmt = select(Source).where(Source.is_active == True)
            result = await session.execute(stmt)
            sources = result.scalars().all()
            
            logger.info(f"Found {len(sources)} active sources to ingest")
            
            for source in sources:
                try:
                    await ingest_source_task(source.id, source.owner_user_id)
                except Exception as e:
                    logger.error(
                        f"Error ingesting source {source.id}: {e}",
                        exc_info=True
                    )
            
            logger.info("Completed ingestion for all sources")
            
        except Exception as e:
            logger.error(f"Error in ingest_all_sources_task: {e}", exc_info=True)

