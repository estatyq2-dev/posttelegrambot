"""Keyboard layouts for admin bot."""

from typing import List, Optional

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from aiogram.utils.keyboard import InlineKeyboardBuilder

from app.db.models import Channel, Source, Binding


def main_menu_keyboard() -> InlineKeyboardMarkup:
    """Create main menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📢 Мої канали", callback_data="menu:channels")
    )
    builder.row(
        InlineKeyboardButton(text="📰 Мої джерела", callback_data="menu:sources")
    )
    builder.row(
        InlineKeyboardButton(text="🔗 Зв'язки", callback_data="menu:bindings")
    )
    builder.row(
        InlineKeyboardButton(text="⚙️ Налаштування", callback_data="menu:settings")
    )
    builder.row(
        InlineKeyboardButton(text="ℹ️ Допомога", callback_data="menu:help")
    )
    return builder.as_markup()


def channels_menu_keyboard() -> InlineKeyboardMarkup:
    """Create channels menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Додати канал", callback_data="channel:add")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мої канали", callback_data="channel:list")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:main")
    )
    return builder.as_markup()


def sources_menu_keyboard() -> InlineKeyboardMarkup:
    """Create sources menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Додати джерело", callback_data="source:add")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мої джерела", callback_data="source:list")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:main")
    )
    return builder.as_markup()


def source_type_keyboard() -> InlineKeyboardMarkup:
    """Create source type selection keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="📱 Telegram-канал", callback_data="source_type:telegram")
    )
    builder.row(
        InlineKeyboardButton(text="📡 RSS-стрічка", callback_data="source_type:rss")
    )
    builder.row(
        InlineKeyboardButton(text="🌐 Веб-сайт", callback_data="source_type:website")
    )
    builder.row(
        InlineKeyboardButton(text="« Скасувати", callback_data="menu:sources")
    )
    return builder.as_markup()


def channel_list_keyboard(channels: List[Channel]) -> InlineKeyboardMarkup:
    """Create keyboard with list of channels."""
    builder = InlineKeyboardBuilder()
    
    for channel in channels:
        status_emoji = "✅" if channel.is_active else "⏸️"
        text = f"{status_emoji} {channel.title}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"channel:view:{channel.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:channels")
    )
    return builder.as_markup()


def channel_detail_keyboard(channel: Channel) -> InlineKeyboardMarkup:
    """Create keyboard for channel details."""
    builder = InlineKeyboardBuilder()
    
    # Toggle active status
    if channel.is_active:
        builder.row(
            InlineKeyboardButton(
                text="⏸️ Вимкнути",
                callback_data=f"channel:toggle:{channel.id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="▶️ Увімкнути",
                callback_data=f"channel:toggle:{channel.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редагувати",
            callback_data=f"channel:edit:{channel.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🧪 Тест-публікація",
            callback_data=f"channel:test:{channel.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Видалити",
            callback_data=f"channel:delete:{channel.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="channel:list")
    )
    return builder.as_markup()


def source_list_keyboard(sources: List[Source]) -> InlineKeyboardMarkup:
    """Create keyboard with list of sources."""
    builder = InlineKeyboardBuilder()
    
    for source in sources:
        status_emoji = "✅" if source.is_active else "⏸️"
        type_emoji = {"telegram": "📱", "rss": "📡", "website": "🌐"}.get(
            source.source_type.value, "📄"
        )
        text = f"{status_emoji} {type_emoji} {source.title or source.handle or 'Без назви'}"
        builder.row(
            InlineKeyboardButton(
                text=text,
                callback_data=f"source:view:{source.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:sources")
    )
    return builder.as_markup()


def source_detail_keyboard(source: Source) -> InlineKeyboardMarkup:
    """Create keyboard for source details."""
    builder = InlineKeyboardBuilder()
    
    # Toggle active status
    if source.is_active:
        builder.row(
            InlineKeyboardButton(
                text="⏸️ Вимкнути",
                callback_data=f"source:toggle:{source.id}"
            )
        )
    else:
        builder.row(
            InlineKeyboardButton(
                text="▶️ Увімкнути",
                callback_data=f"source:toggle:{source.id}"
            )
        )
    
    builder.row(
        InlineKeyboardButton(
            text="✏️ Редагувати",
            callback_data=f"source:edit:{source.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🔄 Оновити зараз",
            callback_data=f"source:refresh:{source.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(
            text="🗑️ Видалити",
            callback_data=f"source:delete:{source.id}"
        )
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="source:list")
    )
    return builder.as_markup()


def bindings_menu_keyboard() -> InlineKeyboardMarkup:
    """Create bindings menu keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="➕ Створити зв'язок", callback_data="binding:add")
    )
    builder.row(
        InlineKeyboardButton(text="📋 Мої зв'язки", callback_data="binding:list")
    )
    builder.row(
        InlineKeyboardButton(text="« Назад", callback_data="menu:main")
    )
    return builder.as_markup()


def confirm_keyboard(callback_yes: str, callback_no: str = "cancel") -> InlineKeyboardMarkup:
    """Create confirmation keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="✅ Так", callback_data=callback_yes),
        InlineKeyboardButton(text="❌ Ні", callback_data=callback_no)
    )
    return builder.as_markup()


def cancel_keyboard(callback_data: str = "cancel") -> InlineKeyboardMarkup:
    """Create cancel keyboard."""
    builder = InlineKeyboardBuilder()
    builder.row(
        InlineKeyboardButton(text="« Скасувати", callback_data=callback_data)
    )
    return builder.as_markup()

