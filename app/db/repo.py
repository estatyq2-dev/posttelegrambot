"""Database repository for CRUD operations."""

from datetime import datetime
from typing import Optional, Sequence

from sqlalchemy import select, update, delete, and_, or_
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.db.models import (
    User,
    Channel,
    Source,
    Binding,
    RawMessage,
    Post,
    SourceType,
    PostStatus,
)


class Repository:
    """Repository for database operations with user isolation."""

    def __init__(self, session: AsyncSession):
        """Initialize repository with database session."""
        self.session = session

    # ==================== User Operations ====================

    async def get_or_create_user(
        self, telegram_id: int, username: Optional[str] = None,
        first_name: Optional[str] = None, last_name: Optional[str] = None
    ) -> User:
        """Get existing user or create new one."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        user = result.scalar_one_or_none()

        if user is None:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name,
            )
            self.session.add(user)
            await self.session.flush()
        else:
            # Update user info if changed
            if username and user.username != username:
                user.username = username
            if first_name and user.first_name != first_name:
                user.first_name = first_name
            if last_name and user.last_name != last_name:
                user.last_name = last_name

        return user

    async def get_user_by_telegram_id(self, telegram_id: int) -> Optional[User]:
        """Get user by Telegram ID."""
        stmt = select(User).where(User.telegram_id == telegram_id)
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    # ==================== Channel Operations ====================

    async def create_channel(
        self,
        owner_user_id: int,
        telegram_id: int,
        title: str,
        username: Optional[str] = None,
        publish_interval_minutes: int = 60,
    ) -> Channel:
        """Create a new channel."""
        channel = Channel(
            owner_user_id=owner_user_id,
            telegram_id=telegram_id,
            title=title,
            username=username,
            publish_interval_minutes=publish_interval_minutes,
        )
        self.session.add(channel)
        await self.session.flush()
        return channel

    async def get_channel(self, channel_id: int, owner_user_id: int) -> Optional[Channel]:
        """Get channel by ID (with user isolation)."""
        stmt = select(Channel).where(
            and_(Channel.id == channel_id, Channel.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_channels(
        self, owner_user_id: int, is_active: Optional[bool] = None
    ) -> Sequence[Channel]:
        """Get all channels for a user."""
        stmt = select(Channel).where(Channel.owner_user_id == owner_user_id)
        if is_active is not None:
            stmt = stmt.where(Channel.is_active == is_active)
        stmt = stmt.order_by(Channel.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_channel(
        self, channel_id: int, owner_user_id: int, **kwargs
    ) -> Optional[Channel]:
        """Update channel fields."""
        channel = await self.get_channel(channel_id, owner_user_id)
        if channel:
            for key, value in kwargs.items():
                if hasattr(channel, key):
                    setattr(channel, key, value)
            await self.session.flush()
        return channel

    async def delete_channel(self, channel_id: int, owner_user_id: int) -> bool:
        """Delete a channel."""
        stmt = delete(Channel).where(
            and_(Channel.id == channel_id, Channel.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ==================== Source Operations ====================

    async def create_source(
        self,
        owner_user_id: int,
        source_type: SourceType,
        handle: Optional[str] = None,
        telegram_id: Optional[int] = None,
        url: Optional[str] = None,
        title: Optional[str] = None,
        check_interval_minutes: int = 30,
    ) -> Source:
        """Create a new source."""
        source = Source(
            owner_user_id=owner_user_id,
            source_type=source_type,
            handle=handle,
            telegram_id=telegram_id,
            url=url,
            title=title,
            check_interval_minutes=check_interval_minutes,
        )
        self.session.add(source)
        await self.session.flush()
        return source

    async def get_source(self, source_id: int, owner_user_id: int) -> Optional[Source]:
        """Get source by ID (with user isolation)."""
        stmt = select(Source).where(
            and_(Source.id == source_id, Source.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_sources(
        self,
        owner_user_id: int,
        source_type: Optional[SourceType] = None,
        is_active: Optional[bool] = None,
    ) -> Sequence[Source]:
        """Get all sources for a user."""
        stmt = select(Source).where(Source.owner_user_id == owner_user_id)
        if source_type:
            stmt = stmt.where(Source.source_type == source_type)
        if is_active is not None:
            stmt = stmt.where(Source.is_active == is_active)
        stmt = stmt.order_by(Source.created_at.desc())
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_source(
        self, source_id: int, owner_user_id: int, **kwargs
    ) -> Optional[Source]:
        """Update source fields."""
        source = await self.get_source(source_id, owner_user_id)
        if source:
            for key, value in kwargs.items():
                if hasattr(source, key):
                    setattr(source, key, value)
            await self.session.flush()
        return source

    async def delete_source(self, source_id: int, owner_user_id: int) -> bool:
        """Delete a source."""
        stmt = delete(Source).where(
            and_(Source.id == source_id, Source.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ==================== Binding Operations ====================

    async def create_binding(self, source_id: int, channel_id: int) -> Binding:
        """Create a binding between source and channel."""
        binding = Binding(source_id=source_id, channel_id=channel_id)
        self.session.add(binding)
        await self.session.flush()
        return binding

    async def get_bindings_for_channel(self, channel_id: int) -> Sequence[Binding]:
        """Get all bindings for a channel."""
        stmt = (
            select(Binding)
            .where(Binding.channel_id == channel_id)
            .options(selectinload(Binding.source))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def get_bindings_for_source(self, source_id: int) -> Sequence[Binding]:
        """Get all bindings for a source."""
        stmt = (
            select(Binding)
            .where(Binding.source_id == source_id)
            .options(selectinload(Binding.channel))
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def delete_binding(self, source_id: int, channel_id: int) -> bool:
        """Delete a binding."""
        stmt = delete(Binding).where(
            and_(Binding.source_id == source_id, Binding.channel_id == channel_id)
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ==================== Raw Message Operations ====================

    async def create_raw_message(
        self,
        owner_user_id: int,
        source_id: int,
        external_id: Optional[str] = None,
        text: Optional[str] = None,
        media_urls: Optional[str] = None,
        media_paths: Optional[str] = None,
        content_hash: Optional[str] = None,
        published_at_source: Optional[datetime] = None,
    ) -> RawMessage:
        """Create a raw message."""
        raw_message = RawMessage(
            owner_user_id=owner_user_id,
            source_id=source_id,
            external_id=external_id,
            text=text,
            media_urls=media_urls,
            media_paths=media_paths,
            content_hash=content_hash,
            published_at_source=published_at_source,
        )
        self.session.add(raw_message)
        await self.session.flush()
        return raw_message

    async def get_raw_message(
        self, message_id: int, owner_user_id: int
    ) -> Optional[RawMessage]:
        """Get raw message by ID."""
        stmt = select(RawMessage).where(
            and_(RawMessage.id == message_id, RawMessage.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_unprocessed_messages(
        self, owner_user_id: int, limit: int = 100
    ) -> Sequence[RawMessage]:
        """Get unprocessed raw messages."""
        stmt = (
            select(RawMessage)
            .where(
                and_(
                    RawMessage.owner_user_id == owner_user_id,
                    RawMessage.is_processed == False,
                )
            )
            .order_by(RawMessage.created_at.asc())
            .limit(limit)
        )
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def check_message_exists(
        self, source_id: int, external_id: str, owner_user_id: int
    ) -> bool:
        """Check if message already exists."""
        stmt = select(RawMessage.id).where(
            and_(
                RawMessage.owner_user_id == owner_user_id,
                RawMessage.source_id == source_id,
                RawMessage.external_id == external_id,
            )
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none() is not None

    async def mark_message_processed(self, message_id: int, owner_user_id: int) -> bool:
        """Mark raw message as processed."""
        stmt = (
            update(RawMessage)
            .where(
                and_(
                    RawMessage.id == message_id,
                    RawMessage.owner_user_id == owner_user_id,
                )
            )
            .values(is_processed=True, processed_at=datetime.utcnow())
        )
        result = await self.session.execute(stmt)
        return result.rowcount > 0

    # ==================== Post Operations ====================

    async def create_post(
        self,
        owner_user_id: int,
        channel_id: int,
        text: str,
        raw_message_id: Optional[int] = None,
        media_paths: Optional[str] = None,
        status: PostStatus = PostStatus.READY,
    ) -> Post:
        """Create a post."""
        post = Post(
            owner_user_id=owner_user_id,
            channel_id=channel_id,
            raw_message_id=raw_message_id,
            text=text,
            media_paths=media_paths,
            status=status,
        )
        self.session.add(post)
        await self.session.flush()
        return post

    async def get_post(self, post_id: int, owner_user_id: int) -> Optional[Post]:
        """Get post by ID."""
        stmt = select(Post).where(
            and_(Post.id == post_id, Post.owner_user_id == owner_user_id)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_next_post_for_channel(self, channel_id: int) -> Optional[Post]:
        """Get next ready post for publishing."""
        stmt = (
            select(Post)
            .where(and_(Post.channel_id == channel_id, Post.status == PostStatus.READY))
            .order_by(Post.created_at.asc())
            .limit(1)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def get_posts(
        self,
        owner_user_id: int,
        channel_id: Optional[int] = None,
        status: Optional[PostStatus] = None,
        limit: int = 100,
    ) -> Sequence[Post]:
        """Get posts with optional filters."""
        stmt = select(Post).where(Post.owner_user_id == owner_user_id)
        if channel_id:
            stmt = stmt.where(Post.channel_id == channel_id)
        if status:
            stmt = stmt.where(Post.status == status)
        stmt = stmt.order_by(Post.created_at.desc()).limit(limit)
        result = await self.session.execute(stmt)
        return result.scalars().all()

    async def update_post(
        self, post_id: int, owner_user_id: int, **kwargs
    ) -> Optional[Post]:
        """Update post fields."""
        post = await self.get_post(post_id, owner_user_id)
        if post:
            for key, value in kwargs.items():
                if hasattr(post, key):
                    setattr(post, key, value)
            await self.session.flush()
        return post

    async def mark_post_published(
        self, post_id: int, telegram_message_id: int
    ) -> Optional[Post]:
        """Mark post as published."""
        stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(
                status=PostStatus.PUBLISHED,
                telegram_message_id=telegram_message_id,
                published_at=datetime.utcnow(),
            )
            .returning(Post)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

    async def mark_post_failed(
        self, post_id: int, error_message: str
    ) -> Optional[Post]:
        """Mark post as failed."""
        stmt = (
            update(Post)
            .where(Post.id == post_id)
            .values(
                status=PostStatus.FAILED,
                error_message=error_message,
                retry_count=Post.retry_count + 1,
            )
            .returning(Post)
        )
        result = await self.session.execute(stmt)
        return result.scalar_one_or_none()

