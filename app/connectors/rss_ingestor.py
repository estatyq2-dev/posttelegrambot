"""RSS feed ingestion."""

from datetime import datetime
from typing import Optional
import hashlib

import aiohttp
import feedparser
from loguru import logger

from app.connectors.html_clean import extract_text_from_html
from app.db.repo import Repository
from app.db.models import Source
from app.utils.hash import compute_content_hash


async def fetch_rss_feed(url: str) -> Optional[feedparser.FeedParserDict]:
    """Fetch and parse RSS feed."""
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(url, timeout=aiohttp.ClientTimeout(total=30)) as response:
                if response.status != 200:
                    logger.error(f"RSS feed error: {response.status} for {url}")
                    return None
                
                content = await response.text()
                feed = feedparser.parse(content)
                
                if feed.bozo:
                    logger.warning(f"RSS feed parse warning for {url}: {feed.bozo_exception}")
                
                return feed
                
    except aiohttp.ClientError as e:
        logger.error(f"HTTP error fetching RSS {url}: {e}")
        return None
    except Exception as e:
        logger.error(f"Error fetching RSS {url}: {e}", exc_info=True)
        return None


async def ingest_rss_source(source: Source, repo: Repository) -> int:
    """Ingest messages from RSS feed.
    
    Returns:
        Number of new messages ingested
    """
    if not source.url:
        logger.error(f"RSS source {source.id} has no URL")
        return 0
    
    logger.info(f"Ingesting RSS source {source.id}: {source.url}")
    
    feed = await fetch_rss_feed(source.url)
    if not feed or not hasattr(feed, "entries"):
        logger.error(f"Failed to fetch RSS feed for source {source.id}")
        return 0
    
    new_count = 0
    
    for entry in feed.entries:
        try:
            # Extract content
            text = ""
            if hasattr(entry, "summary"):
                text = extract_text_from_html(entry.summary)
            elif hasattr(entry, "description"):
                text = extract_text_from_html(entry.description)
            
            if hasattr(entry, "content"):
                for content in entry.content:
                    text += "\n\n" + extract_text_from_html(content.value)
            
            if not text.strip():
                continue
            
            # Add title
            if hasattr(entry, "title"):
                text = f"{entry.title}\n\n{text}"
            
            # Add link
            link = entry.get("link", "")
            if link:
                text += f"\n\n🔗 {link}"
            
            # Get published date
            published_at = None
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published_at = datetime(*entry.published_parsed[:6])
            
            # Use entry ID or link as external_id
            external_id = entry.get("id") or entry.get("link") or compute_content_hash(text)
            
            # Check if already exists
            exists = await repo.check_message_exists(
                source_id=source.id,
                external_id=external_id,
                owner_user_id=source.owner_user_id,
            )
            
            if exists:
                continue
            
            # Create raw message
            content_hash = compute_content_hash(text)
            
            await repo.create_raw_message(
                owner_user_id=source.owner_user_id,
                source_id=source.id,
                external_id=external_id,
                text=text,
                content_hash=content_hash,
                published_at_source=published_at,
            )
            
            new_count += 1
            logger.debug(f"Ingested RSS entry: {entry.get('title', 'No title')}")
            
        except Exception as e:
            logger.error(f"Error processing RSS entry: {e}", exc_info=True)
            continue
    
    # Update source last_checked_at
    await repo.update_source(
        source.id,
        source.owner_user_id,
        last_checked_at=datetime.utcnow(),
    )
    
    logger.info(f"RSS ingestion complete for source {source.id}: {new_count} new messages")
    return new_count

