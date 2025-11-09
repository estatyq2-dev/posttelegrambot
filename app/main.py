"""Main application entry point."""

import asyncio
import signal
from contextlib import asynccontextmanager

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage
from loguru import logger

from app.adminbot.access import EnsureUserMiddleware
from app.adminbot.router import router as admin_router
from app.config import get_settings
from app.connectors.telegram_ingestor import start_telethon_client, stop_telethon_client
from app.db.base import close_db
from app.logging_conf import setup_logging
from app.publisher.scheduler import init_scheduler, shutdown_scheduler


# Global objects
bot: Bot = None
dp: Dispatcher = None


async def on_startup():
    """Execute on application startup."""
    logger.info("Starting News Relay Bot...")
    
    settings = get_settings()
    
    # Initialize Telethon client for reading channels
    try:
        await start_telethon_client()
        logger.info("Telethon client started")
    except Exception as e:
        logger.error(f"Failed to start Telethon client: {e}", exc_info=True)
        logger.warning("Bot will work without Telegram source ingestion")
    
    # Initialize publisher scheduler
    try:
        await init_scheduler()
        logger.info("Publisher scheduler started")
    except Exception as e:
        logger.error(f"Failed to start publisher scheduler: {e}", exc_info=True)
    
    logger.info("News Relay Bot started successfully")


async def on_shutdown():
    """Execute on application shutdown."""
    logger.info("Shutting down News Relay Bot...")
    
    # Shutdown publisher scheduler
    try:
        await shutdown_scheduler()
    except Exception as e:
        logger.error(f"Error shutting down scheduler: {e}")
    
    # Stop Telethon client
    try:
        await stop_telethon_client()
    except Exception as e:
        logger.error(f"Error stopping Telethon: {e}")
    
    # Close database connections
    try:
        await close_db()
    except Exception as e:
        logger.error(f"Error closing database: {e}")
    
    # Close bot session
    if bot:
        await bot.session.close()
    
    logger.info("News Relay Bot shut down")


async def main():
    """Main application function."""
    global bot, dp
    
    # Setup logging
    setup_logging()
    
    # Get settings
    settings = get_settings()
    
    # Create bot and dispatcher
    bot = Bot(token=settings.tg_bot_token)
    dp = Dispatcher(storage=MemoryStorage())
    
    # Register middleware
    dp.message.middleware(EnsureUserMiddleware())
    dp.callback_query.middleware(EnsureUserMiddleware())
    
    # Register routers
    dp.include_router(admin_router)
    
    # Startup
    await on_startup()
    
    # Start polling
    logger.info("Starting bot polling...")
    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    except Exception as e:
        logger.error(f"Error during polling: {e}", exc_info=True)
    finally:
        await on_shutdown()


def signal_handler(signum, frame):
    """Handle shutdown signals."""
    logger.info(f"Received signal {signum}, shutting down...")
    raise KeyboardInterrupt


if __name__ == "__main__":
    # Setup signal handlers
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        exit(1)

