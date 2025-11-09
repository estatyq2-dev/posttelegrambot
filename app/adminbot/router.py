"""Admin bot router with all handlers."""

from typing import Optional

from aiogram import Router, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery
from loguru import logger

from app.adminbot import keyboards as kb
from app.adminbot.states import (
    AddChannelStates,
    AddSourceStates,
    BindingStates,
)
from app.db.models import User, SourceType
from app.db.repo import Repository
from app.utils.text import extract_channel_username, format_interval, truncate_text
from app.utils.time import format_datetime, parse_interval

# Create router
router = Router(name="adminbot")


# ==================== Start and Main Menu ====================


@router.message(Command("start"))
async def cmd_start(message: Message, current_user: User):
    """Handle /start command."""
    await message.answer(
        f"👋 Вітаю, {current_user.first_name or 'користувач'}!\n\n"
        "Я бот для автоматичного репостингу та переписування новин.\n\n"
        "🔹 Додайте свої канали\n"
        "🔹 Додайте джерела новин\n"
        "🔹 Створіть зв'язки між ними\n"
        "🔹 Налаштуйте інтервал публікацій\n\n"
        "Готово! Бот автоматично парситиме, переписуватиме через GPT "
        "та публікуватиме контент у ваші канали.",
        reply_markup=kb.main_menu_keyboard(),
    )


@router.callback_query(F.data == "menu:main")
async def menu_main(callback: CallbackQuery):
    """Show main menu."""
    await callback.message.edit_text(
        "📋 Головне меню\n\n"
        "Виберіть розділ:",
        reply_markup=kb.main_menu_keyboard(),
    )
    await callback.answer()


@router.callback_query(F.data == "menu:help")
async def menu_help(callback: CallbackQuery):
    """Show help information."""
    help_text = """
ℹ️ **Довідка**

**Як користуватися ботом:**

1️⃣ **Додайте канал**
   • Переслати будь-яке повідомлення з каналу
   • Бот має бути адміном каналу

2️⃣ **Додайте джерело**
   • Telegram-канал: @username або посилання
   • RSS: URL стрічки
   • Сайт: URL сайту

3️⃣ **Створіть зв'язок**
   • Оберіть джерело та канал
   • Контент з джерела буде публікуватися в канал

4️⃣ **Налаштуйте інтервал**
   • За замовчуванням 60 хвилин
   • Можна змінити для кожного каналу

**Інтервали:**
• `30m` - 30 хвилин
• `1h` - 1 година
• `2h30m` - 2 години 30 хвилин

**Підтримка:** @support_username
"""
    await callback.message.edit_text(
        help_text,
        reply_markup=kb.cancel_keyboard("menu:main"),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==================== Channels ====================


@router.callback_query(F.data == "menu:channels")
async def menu_channels(callback: CallbackQuery):
    """Show channels menu."""
    await callback.message.edit_text(
        "📢 **Мої канали**\n\n"
        "Керуйте своїми каналами для публікацій.",
        reply_markup=kb.channels_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "channel:add")
async def channel_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a channel."""
    await callback.message.edit_text(
        "➕ **Додавання каналу**\n\n"
        "Переслати мені будь-яке повідомлення з каналу, де бот є адміністратором.\n\n"
        "💡 Щоб додати бота як адміна:\n"
        "1. Відкрийте канал\n"
        "2. Налаштування → Адміністратори\n"
        "3. Додати адміністратора → знайдіть цього бота\n"
        "4. Дайте права на публікацію повідомлень",
        reply_markup=kb.cancel_keyboard("menu:channels"),
        parse_mode="Markdown",
    )
    await state.set_state(AddChannelStates.waiting_for_forward)
    await callback.answer()


@router.message(AddChannelStates.waiting_for_forward, F.forward_from_chat)
async def channel_add_process(
    message: Message, state: FSMContext, current_user: User, repo: Repository
):
    """Process forwarded message to add channel."""
    chat = message.forward_from_chat
    
    if chat.type not in ["channel", "supergroup"]:
        await message.answer(
            "❌ Це не канал. Будь ласка, переслати повідомлення з каналу.",
            reply_markup=kb.cancel_keyboard("menu:channels"),
        )
        return
    
    try:
        # Check if bot has admin rights
        bot_member = await message.bot.get_chat_member(chat.id, message.bot.id)
        if bot_member.status not in ["administrator", "creator"]:
            await message.answer(
                "❌ Бот не є адміністратором цього каналу.\n\n"
                "Додайте бота як адміна з правами публікації повідомлень.",
                reply_markup=kb.cancel_keyboard("menu:channels"),
            )
            return
        
        # Check if channel already exists
        existing_channels = await repo.get_channels(current_user.id)
        if any(ch.telegram_id == chat.id for ch in existing_channels):
            await message.answer(
                "ℹ️ Цей канал уже додано.",
                reply_markup=kb.channels_menu_keyboard(),
            )
            await state.clear()
            return
        
        # Create channel
        channel = await repo.create_channel(
            owner_user_id=current_user.id,
            telegram_id=chat.id,
            title=chat.title or "Без назви",
            username=chat.username,
        )
        
        await message.answer(
            f"✅ Канал **{channel.title}** успішно додано!\n\n"
            f"📊 ID: `{channel.id}`\n"
            f"⏱ Інтервал: {format_interval(channel.publish_interval_minutes)}\n"
            f"🔄 Статус: {'Увімкнено' if channel.is_active else 'Вимкнено'}\n\n"
            "Тепер додайте джерела та створіть зв'язки.",
            reply_markup=kb.channels_menu_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error adding channel: {e}", exc_info=True)
        await message.answer(
            f"❌ Помилка при додаванні каналу: {str(e)}",
            reply_markup=kb.channels_menu_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data == "channel:list")
async def channel_list(callback: CallbackQuery, current_user: User, repo: Repository):
    """List all user channels."""
    channels = await repo.get_channels(current_user.id)
    
    if not channels:
        await callback.message.edit_text(
            "📢 У вас ще немає каналів.\n\n"
            "Додайте перший канал, щоб почати!",
            reply_markup=kb.channels_menu_keyboard(),
        )
    else:
        await callback.message.edit_text(
            f"📢 **Ваші канали** ({len(channels)}):\n\n"
            "Оберіть канал для перегляду:",
            reply_markup=kb.channel_list_keyboard(channels),
            parse_mode="Markdown",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("channel:view:"))
async def channel_view(callback: CallbackQuery, current_user: User, repo: Repository):
    """View channel details."""
    channel_id = int(callback.data.split(":")[2])
    channel = await repo.get_channel(channel_id, current_user.id)
    
    if not channel:
        await callback.answer("❌ Канал не знайдено", show_alert=True)
        return
    
    # Get bindings count
    bindings = await repo.get_bindings_for_channel(channel_id)
    
    status = "✅ Увімкнено" if channel.is_active else "⏸️ Вимкнено"
    last_pub = format_datetime(channel.last_published_at) if channel.last_published_at else "Ніколи"
    
    text = f"""
📢 **{channel.title}**

📊 ID: `{channel.id}`
🆔 Telegram ID: `{channel.telegram_id}`
👤 Username: @{channel.username or 'немає'}

🔄 Статус: {status}
⏱ Інтервал: {format_interval(channel.publish_interval_minutes)}
📅 Остання публікація: {last_pub}

🔗 Зв'язків з джерелами: {len(bindings)}
🌐 Мова: {channel.language or 'авто'}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.channel_detail_keyboard(channel),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("channel:toggle:"))
async def channel_toggle(callback: CallbackQuery, current_user: User, repo: Repository):
    """Toggle channel active status."""
    channel_id = int(callback.data.split(":")[2])
    channel = await repo.get_channel(channel_id, current_user.id)
    
    if not channel:
        await callback.answer("❌ Канал не знайдено", show_alert=True)
        return
    
    # Toggle status
    new_status = not channel.is_active
    await repo.update_channel(channel_id, current_user.id, is_active=new_status)
    
    status_text = "увімкнено ✅" if new_status else "вимкнено ⏸️"
    await callback.answer(f"Канал {status_text}")
    
    # Refresh view
    await channel_view(callback, current_user, repo)


@router.callback_query(F.data.startswith("channel:delete:"))
async def channel_delete(callback: CallbackQuery, current_user: User, repo: Repository):
    """Delete a channel."""
    channel_id = int(callback.data.split(":")[2])
    channel = await repo.get_channel(channel_id, current_user.id)
    
    if not channel:
        await callback.answer("❌ Канал не знайдено", show_alert=True)
        return
    
    await repo.delete_channel(channel_id, current_user.id)
    
    await callback.message.edit_text(
        f"🗑️ Канал **{channel.title}** видалено.",
        reply_markup=kb.channels_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==================== Sources ====================


@router.callback_query(F.data == "menu:sources")
async def menu_sources(callback: CallbackQuery):
    """Show sources menu."""
    await callback.message.edit_text(
        "📰 **Мої джерела**\n\n"
        "Керуйте джерелами новин.",
        reply_markup=kb.sources_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "source:add")
async def source_add_start(callback: CallbackQuery, state: FSMContext):
    """Start adding a source."""
    await callback.message.edit_text(
        "➕ **Додавання джерела**\n\n"
        "Оберіть тип джерела:",
        reply_markup=kb.source_type_keyboard(),
        parse_mode="Markdown",
    )
    await state.set_state(AddSourceStates.waiting_for_type)
    await callback.answer()


@router.callback_query(
    AddSourceStates.waiting_for_type, F.data.startswith("source_type:")
)
async def source_add_type(callback: CallbackQuery, state: FSMContext):
    """Process source type selection."""
    source_type = callback.data.split(":")[1]
    await state.update_data(source_type=source_type)
    
    if source_type == "telegram":
        prompt_text = (
            "📱 **Telegram-канал**\n\n"
            "Введіть username каналу (наприклад, @channel або t.me/channel):"
        )
        next_state = AddSourceStates.waiting_for_handle
    else:
        prompt_text = (
            f"🌐 **{source_type.upper()}**\n\n"
            f"Введіть URL {'RSS-стрічки' if source_type == 'rss' else 'сайту'}:"
        )
        next_state = AddSourceStates.waiting_for_url
    
    await callback.message.edit_text(
        prompt_text,
        reply_markup=kb.cancel_keyboard("menu:sources"),
        parse_mode="Markdown",
    )
    await state.set_state(next_state)
    await callback.answer()


@router.message(AddSourceStates.waiting_for_handle)
async def source_add_handle(
    message: Message, state: FSMContext, current_user: User, repo: Repository
):
    """Process Telegram channel handle."""
    handle = extract_channel_username(message.text)
    
    if not handle:
        await message.answer(
            "❌ Неправильний формат. Введіть @username або посилання t.me/channel",
            reply_markup=kb.cancel_keyboard("menu:sources"),
        )
        return
    
    try:
        # Create source
        source = await repo.create_source(
            owner_user_id=current_user.id,
            source_type=SourceType.TELEGRAM,
            handle=handle,
            title=f"@{handle}",
        )
        
        await message.answer(
            f"✅ Telegram-джерело **@{handle}** додано!\n\n"
            f"📊 ID: `{source.id}`\n"
            f"⏱ Інтервал перевірки: {format_interval(source.check_interval_minutes)}\n"
            f"🔄 Статус: {'Увімкнено' if source.is_active else 'Вимкнено'}\n\n"
            "Тепер створіть зв'язок з каналом для публікації.",
            reply_markup=kb.sources_menu_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error adding source: {e}", exc_info=True)
        await message.answer(
            f"❌ Помилка: {str(e)}",
            reply_markup=kb.sources_menu_keyboard(),
        )
        await state.clear()


@router.message(AddSourceStates.waiting_for_url)
async def source_add_url(
    message: Message, state: FSMContext, current_user: User, repo: Repository
):
    """Process RSS/Website URL."""
    url = message.text.strip()
    data = await state.get_data()
    source_type_str = data.get("source_type", "rss")
    
    if not url.startswith(("http://", "https://")):
        await message.answer(
            "❌ URL має починатися з http:// або https://",
            reply_markup=kb.cancel_keyboard("menu:sources"),
        )
        return
    
    try:
        source_type = SourceType.RSS if source_type_str == "rss" else SourceType.WEBSITE
        
        # Create source
        source = await repo.create_source(
            owner_user_id=current_user.id,
            source_type=source_type,
            url=url,
            title=truncate_text(url, 50),
        )
        
        type_emoji = "📡" if source_type == SourceType.RSS else "🌐"
        await message.answer(
            f"✅ {type_emoji} Джерело додано!\n\n"
            f"📊 ID: `{source.id}`\n"
            f"🔗 URL: {truncate_text(url, 40)}\n"
            f"⏱ Інтервал: {format_interval(source.check_interval_minutes)}\n\n"
            "Створіть зв'язок з каналом для публікації.",
            reply_markup=kb.sources_menu_keyboard(),
            parse_mode="Markdown",
        )
        await state.clear()
        
    except Exception as e:
        logger.error(f"Error adding source: {e}", exc_info=True)
        await message.answer(
            f"❌ Помилка: {str(e)}",
            reply_markup=kb.sources_menu_keyboard(),
        )
        await state.clear()


@router.callback_query(F.data == "source:list")
async def source_list(callback: CallbackQuery, current_user: User, repo: Repository):
    """List all user sources."""
    sources = await repo.get_sources(current_user.id)
    
    if not sources:
        await callback.message.edit_text(
            "📰 У вас ще немає джерел.\n\n"
            "Додайте перше джерело!",
            reply_markup=kb.sources_menu_keyboard(),
        )
    else:
        await callback.message.edit_text(
            f"📰 **Ваші джерела** ({len(sources)}):\n\n"
            "Оберіть джерело:",
            reply_markup=kb.source_list_keyboard(sources),
            parse_mode="Markdown",
        )
    
    await callback.answer()


@router.callback_query(F.data.startswith("source:view:"))
async def source_view(callback: CallbackQuery, current_user: User, repo: Repository):
    """View source details."""
    source_id = int(callback.data.split(":")[2])
    source = await repo.get_source(source_id, current_user.id)
    
    if not source:
        await callback.answer("❌ Джерело не знайдено", show_alert=True)
        return
    
    bindings = await repo.get_bindings_for_source(source_id)
    
    status = "✅ Увімкнено" if source.is_active else "⏸️ Вимкнено"
    type_emoji = {"telegram": "📱", "rss": "📡", "website": "🌐"}.get(
        source.source_type.value, "📄"
    )
    
    text = f"""
{type_emoji} **{source.title or 'Без назви'}**

📊 ID: `{source.id}`
📍 Тип: {source.source_type.value}
{'👤 Handle: @' + source.handle if source.handle else '🔗 URL: ' + truncate_text(source.url or '', 40)}

🔄 Статус: {status}
⏱ Інтервал перевірки: {format_interval(source.check_interval_minutes)}
📅 Остання перевірка: {format_datetime(source.last_checked_at)}

🔗 Зв'язків з каналами: {len(bindings)}
"""
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.source_detail_keyboard(source),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data.startswith("source:toggle:"))
async def source_toggle(callback: CallbackQuery, current_user: User, repo: Repository):
    """Toggle source active status."""
    source_id = int(callback.data.split(":")[2])
    source = await repo.get_source(source_id, current_user.id)
    
    if not source:
        await callback.answer("❌ Джерело не знайдено", show_alert=True)
        return
    
    new_status = not source.is_active
    await repo.update_source(source_id, current_user.id, is_active=new_status)
    
    status_text = "увімкнено ✅" if new_status else "вимкнено ⏸️"
    await callback.answer(f"Джерело {status_text}")
    
    await source_view(callback, current_user, repo)


@router.callback_query(F.data.startswith("source:delete:"))
async def source_delete(callback: CallbackQuery, current_user: User, repo: Repository):
    """Delete a source."""
    source_id = int(callback.data.split(":")[2])
    source = await repo.get_source(source_id, current_user.id)
    
    if not source:
        await callback.answer("❌ Джерело не знайдено", show_alert=True)
        return
    
    await repo.delete_source(source_id, current_user.id)
    
    await callback.message.edit_text(
        f"🗑️ Джерело **{source.title or 'Без назви'}** видалено.",
        reply_markup=kb.sources_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==================== Bindings ====================


@router.callback_query(F.data == "menu:bindings")
async def menu_bindings(callback: CallbackQuery):
    """Show bindings menu."""
    await callback.message.edit_text(
        "🔗 **Зв'язки**\n\n"
        "Керуйте зв'язками між джерелами та каналами.",
        reply_markup=kb.bindings_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


@router.callback_query(F.data == "binding:add")
async def binding_add_start(
    callback: CallbackQuery, state: FSMContext, current_user: User, repo: Repository
):
    """Start creating a binding."""
    sources = await repo.get_sources(current_user.id, is_active=True)
    
    if not sources:
        await callback.answer(
            "❌ Спочатку додайте активне джерело",
            show_alert=True
        )
        return
    
    await callback.message.edit_text(
        "🔗 **Створення зв'язку**\n\n"
        "Оберіть джерело:",
        reply_markup=kb.source_list_keyboard(sources),
        parse_mode="Markdown",
    )
    await state.set_state(BindingStates.selecting_source)
    await callback.answer()


@router.callback_query(F.data == "binding:list")
async def binding_list(callback: CallbackQuery, current_user: User, repo: Repository):
    """List all bindings."""
    channels = await repo.get_channels(current_user.id)
    
    if not channels:
        await callback.answer("❌ Немає каналів", show_alert=True)
        return
    
    text = "🔗 **Ваші зв'язки:**\n\n"
    
    for channel in channels:
        bindings = await repo.get_bindings_for_channel(channel.id)
        text += f"📢 **{channel.title}**\n"
        
        if bindings:
            for binding in bindings:
                source = binding.source
                status = "✅" if binding.is_active and source.is_active else "⏸️"
                text += f"  {status} ← {source.title or source.handle or 'Без назви'}\n"
        else:
            text += "  _Немає джерел_\n"
        
        text += "\n"
    
    await callback.message.edit_text(
        text,
        reply_markup=kb.bindings_menu_keyboard(),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==================== Settings ====================


@router.callback_query(F.data == "menu:settings")
async def menu_settings(callback: CallbackQuery, current_user: User):
    """Show settings menu."""
    text = f"""
⚙️ **Налаштування**

👤 Користувач: {current_user.first_name or 'Без імені'}
🆔 Telegram ID: `{current_user.telegram_id}`
📅 Реєстрація: {format_datetime(current_user.created_at)}

Додаткові налаштування будуть додані незабаром.
"""
    await callback.message.edit_text(
        text,
        reply_markup=kb.cancel_keyboard("menu:main"),
        parse_mode="Markdown",
    )
    await callback.answer()


# ==================== Cancel Handler ====================


@router.callback_query(F.data == "cancel")
@router.callback_query(StateFilter("*"), F.data == "cancel")
async def cancel_handler(callback: CallbackQuery, state: FSMContext):
    """Cancel current operation and return to main menu."""
    await state.clear()
    await callback.message.edit_text(
        "❌ Операцію скасовано.",
        reply_markup=kb.main_menu_keyboard(),
    )
    await callback.answer()

