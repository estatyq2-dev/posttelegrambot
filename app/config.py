"""Application configuration management."""

import os
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings loaded from environment variables."""

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # Telegram Bot Configuration
    tg_bot_token: str = Field(..., description="Telegram Bot API token")
    tg_api_id: int = Field(..., description="Telegram API ID from my.telegram.org")
    tg_api_hash: str = Field(..., description="Telegram API Hash from my.telegram.org")
    tg_session_path: str = Field(
        default=".tg_session/session.session",
        description="Path to Telethon session file"
    )

    # OpenAI / GPT Configuration
    openai_api_key: str = Field(..., description="OpenAI API key")
    openai_base_url: str = Field(
        default="https://api.openai.com/v1",
        description="OpenAI API base URL"
    )
    openai_model: str = Field(default="gpt-4o-mini", description="OpenAI model to use")

    # Database Configuration
    database_url: str = Field(
        ...,
        description="Database connection URL (PostgreSQL)"
    )

    # Redis Configuration
    redis_url: str = Field(default="redis://localhost:6379/0", description="Redis URL")

    # Application Configuration
    timezone: str = Field(default="Europe/Kyiv", description="Application timezone")
    log_level: str = Field(default="INFO", description="Logging level")

    # Worker Configuration
    rq_queue_ingest: str = Field(default="ingest", description="RQ queue name for ingestion")
    rq_queue_rewrite: str = Field(default="rewrite", description="RQ queue name for rewriting")
    rq_queue_publish: str = Field(default="publish", description="RQ queue name for publishing")

    # Publishing Configuration
    default_publish_interval_minutes: int = Field(
        default=60,
        description="Default publishing interval in minutes"
    )
    max_post_length: int = Field(default=4096, description="Maximum post length")

    # Media Storage
    media_storage_path: str = Field(
        default="media_storage",
        description="Path to media storage directory"
    )

    @property
    def media_storage_dir(self) -> Path:
        """Get media storage directory as Path object."""
        return Path(self.media_storage_path)

    @property
    def tg_session_dir(self) -> Path:
        """Get Telegram session directory as Path object."""
        return Path(self.tg_session_path).parent

    def __init__(self, **kwargs):
        """Initialize settings and create necessary directories."""
        super().__init__(**kwargs)
        # Ensure directories exist
        self.media_storage_dir.mkdir(parents=True, exist_ok=True)
        self.tg_session_dir.mkdir(parents=True, exist_ok=True)


# Global settings instance
settings: Optional[Settings] = None


def get_settings() -> Settings:
    """Get or create global settings instance."""
    global settings
    if settings is None:
        settings = Settings()
    return settings

