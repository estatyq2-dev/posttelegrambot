"""Middleware for user authentication and isolation."""

from typing import Any, Awaitable, Callable, Dict

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, User as TgUser, Message, CallbackQuery
from loguru import logger

from app.db.base import get_session
from app.db.repo import Repository


class EnsureUserMiddleware(BaseMiddleware):
    """Middleware to ensure user exists in database and add to context."""

    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any],
    ) -> Any:
        """Process update and ensure user exists."""
        # Get Telegram user from event
        tg_user: TgUser | None = None
        
        if isinstance(event, Message):
            tg_user = event.from_user
        elif isinstance(event, CallbackQuery):
            tg_user = event.from_user
        
        if tg_user is None or tg_user.is_bot:
            # Skip for bots or if user not found
            return await handler(event, data)
        
        # Get or create user in database
        async with get_session() as session:
            repo = Repository(session)
            
            try:
                user = await repo.get_or_create_user(
                    telegram_id=tg_user.id,
                    username=tg_user.username,
                    first_name=tg_user.first_name,
                    last_name=tg_user.last_name,
                )
                
                # Add user and repository to context
                data["current_user"] = user
                data["repo"] = repo
                
                logger.debug(
                    f"User {user.telegram_id} ({user.username or 'no username'}) "
                    f"authenticated, user_id={user.id}"
                )
                
                # Call handler with updated context
                return await handler(event, data)
                
            except Exception as e:
                logger.error(f"Error in EnsureUserMiddleware: {e}", exc_info=True)
                raise

