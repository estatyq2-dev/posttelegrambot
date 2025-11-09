"""SQLAlchemy database models."""

from datetime import datetime
from enum import Enum as PyEnum
from typing import Optional

from sqlalchemy import (
    BigInteger,
    Boolean,
    DateTime,
    Enum,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.sql import func

from app.db.base import Base


class SourceType(str, PyEnum):
    """Type of content source."""

    TELEGRAM = "telegram"
    RSS = "rss"
    WEBSITE = "website"


class PostStatus(str, PyEnum):
    """Status of a post in the publishing pipeline."""

    RAW = "raw"  # Just ingested, not processed
    PROCESSING = "processing"  # Being rewritten
    READY = "ready"  # Ready to publish
    PUBLISHED = "published"  # Successfully published
    FAILED = "failed"  # Publishing failed
    SKIPPED = "skipped"  # Skipped (duplicate, moderation, etc.)


class User(Base):
    """Telegram user who owns channels and sources."""

    __tablename__ = "users"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, unique=True, index=True, nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    first_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    last_name: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    channels: Mapped[list["Channel"]] = relationship(
        "Channel", back_populates="owner", cascade="all, delete-orphan"
    )
    sources: Mapped[list["Source"]] = relationship(
        "Source", back_populates="owner", cascade="all, delete-orphan"
    )
    raw_messages: Mapped[list["RawMessage"]] = relationship(
        "RawMessage", back_populates="owner", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="owner", cascade="all, delete-orphan"
    )


class Channel(Base):
    """Telegram channel where bot publishes content."""

    __tablename__ = "channels"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    telegram_id: Mapped[int] = mapped_column(BigInteger, nullable=False)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    username: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Publishing settings
    publish_interval_minutes: Mapped[int] = mapped_column(Integer, default=60, nullable=False)
    last_published_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    
    # Style settings
    language: Mapped[Optional[str]] = mapped_column(String(10), nullable=True)  # uk, en, etc.
    style_prompt: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="channels")
    bindings: Mapped[list["Binding"]] = relationship(
        "Binding", back_populates="channel", cascade="all, delete-orphan"
    )
    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="channel", cascade="all, delete-orphan"
    )

    __table_args__ = (
        UniqueConstraint("owner_user_id", "telegram_id", name="uq_user_channel"),
        Index("ix_channels_owner_active", "owner_user_id", "is_active"),
    )


class Source(Base):
    """Content source (Telegram channel, RSS feed, or website)."""

    __tablename__ = "sources"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_type: Mapped[SourceType] = mapped_column(Enum(SourceType), nullable=False)
    
    # Source identification
    handle: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # @channel or URL
    telegram_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    url: Mapped[Optional[str]] = mapped_column(String(1024), nullable=True)
    
    title: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    # Ingestion settings
    check_interval_minutes: Mapped[int] = mapped_column(Integer, default=30, nullable=False)
    last_checked_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    last_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="sources")
    bindings: Mapped[list["Binding"]] = relationship(
        "Binding", back_populates="source", cascade="all, delete-orphan"
    )
    raw_messages: Mapped[list["RawMessage"]] = relationship(
        "RawMessage", back_populates="source", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_sources_owner_active", "owner_user_id", "is_active"),
        Index("ix_sources_type", "source_type"),
    )


class Binding(Base):
    """Binding between a source and a channel (many-to-many relationship)."""

    __tablename__ = "bindings"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )

    # Relationships
    source: Mapped["Source"] = relationship("Source", back_populates="bindings")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="bindings")

    __table_args__ = (
        UniqueConstraint("source_id", "channel_id", name="uq_source_channel"),
    )


class RawMessage(Base):
    """Raw message ingested from a source."""

    __tablename__ = "raw_messages"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    source_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("sources.id", ondelete="CASCADE"), nullable=False, index=True
    )
    
    # Message content
    external_id: Mapped[Optional[str]] = mapped_column(String(255), nullable=True)  # Message ID from source
    text: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    media_urls: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of URLs
    media_paths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array of local paths
    
    # Content hash for deduplication
    content_hash: Mapped[Optional[str]] = mapped_column(String(64), nullable=True, index=True)
    
    # Processing
    is_processed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    processed_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    published_at_source: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True), nullable=True
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False, index=True
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="raw_messages")
    source: Mapped["Source"] = relationship("Source", back_populates="raw_messages")
    posts: Mapped[list["Post"]] = relationship(
        "Post", back_populates="raw_message", cascade="all, delete-orphan"
    )

    __table_args__ = (
        Index("ix_raw_messages_source_external", "source_id", "external_id"),
        Index("ix_raw_messages_processed", "is_processed", "created_at"),
    )


class Post(Base):
    """Processed post ready for publishing."""

    __tablename__ = "posts"

    id: Mapped[int] = mapped_column(BigInteger, primary_key=True, index=True)
    owner_user_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    channel_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("channels.id", ondelete="CASCADE"), nullable=False, index=True
    )
    raw_message_id: Mapped[Optional[int]] = mapped_column(
        BigInteger, ForeignKey("raw_messages.id", ondelete="SET NULL"), nullable=True, index=True
    )
    
    # Post content
    text: Mapped[str] = mapped_column(Text, nullable=False)
    media_paths: Mapped[Optional[str]] = mapped_column(Text, nullable=True)  # JSON array
    
    # Publishing status
    status: Mapped[PostStatus] = mapped_column(
        Enum(PostStatus), default=PostStatus.READY, nullable=False, index=True
    )
    
    # Telegram message ID after publishing
    telegram_message_id: Mapped[Optional[int]] = mapped_column(BigInteger, nullable=True)
    
    # Error handling
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)
    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    
    # Timestamps
    scheduled_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    published_at: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now(), nullable=False
    )

    # Relationships
    owner: Mapped["User"] = relationship("User", back_populates="posts")
    channel: Mapped["Channel"] = relationship("Channel", back_populates="posts")
    raw_message: Mapped[Optional["RawMessage"]] = relationship(
        "RawMessage", back_populates="posts"
    )

    __table_args__ = (
        Index("ix_posts_channel_status", "channel_id", "status"),
        Index("ix_posts_status_created", "status", "created_at"),
    )

