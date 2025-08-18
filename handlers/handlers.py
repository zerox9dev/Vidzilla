# handlers.py - FREE version

from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PLATFORM_IDENTIFIERS
from handlers.social_media.video_processor import detect_platform_and_process
from utils.user_management import (
    check_channel_subscription,
    create_user,
    get_user,
    increment_download_count,
    update_user,
)


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


async def send_welcome(message: Message, state: FSMContext):
    """Send welcome message - FREE version"""
    user_id = message.from_user.id
    username = message.from_user.username
    language_code = message.from_user.language_code

    # Get or create user
    user = get_user(user_id)
    if not user:
        create_user(user_id, username, language_code)
    else:
        update_user(user_id, username, language_code)

    welcome_text = f"🎬 **Vidzilla**\n\nSend video link 👇"

    await message.answer(welcome_text, parse_mode="Markdown")


async def process_video_link(message: Message, state: FSMContext):
    """Process video link - FREE version"""
    user_id = message.from_user.id
    url = message.text.strip()

    # Check if user exists, create if not
    user = get_user(user_id)
    if not user:
        create_user(user_id, message.from_user.username, message.from_user.language_code)

    # Check channel subscription (always returns True in FREE version)
    if not await check_channel_subscription(user_id, message.bot):
        return

    # Send processing message
    progress_msg = await message.answer("⏳ Loading...")

    try:
        # Detect platform and process video
        platform_detected = await detect_platform_and_process(
            message, message.bot, url, progress_msg
        )

        if not platform_detected:
            # Platform not supported
            supported_platforms = ', '.join(set(PLATFORM_IDENTIFIERS.values()))
            await progress_msg.edit_text(
                f"❌ Platform not supported\n\n✅ {supported_platforms}",
                parse_mode="Markdown"
            )
            return

        # Increment download counter
        increment_download_count(user_id)

    except Exception as e:
        error_message = "❌ Error\n💡 Try another link"
        await progress_msg.edit_text(error_message, parse_mode="Markdown")
        print(f"Error processing video: {e}")


async def handle_help_command(message: Message):
    """Handle /help command"""
    help_text = "📱 YouTube, Instagram, TikTok, Facebook, Twitter, Pinterest, Reddit, Vimeo\n\n💡 Just send a link"

    await message.answer(help_text, parse_mode="Markdown")


async def handle_about_command(message: Message):
    """Handle /about command"""
    about_text = "🎬 **Vidzilla**\n\n✨ 8 platforms\n🚀 Fast & Free"

    await message.answer(about_text, parse_mode="Markdown")


def register_handlers(dp):
    """Register all main bot handlers with the dispatcher"""
    from aiogram.filters import Command
    from aiogram import F

    # Commands
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(handle_help_command, Command("help"))
    dp.message.register(handle_about_command, Command("about"))

    # Video link processing (any message that contains URLs)
    dp.message.register(process_video_link, F.text.regexp(r'https?://'))

    # Fallback for other messages
    dp.message.register(send_welcome)

    print("Main handlers registered")


# Export functions for main router
__all__ = [
    'DownloadVideo',
    'send_welcome',
    'process_video_link',
    'handle_help_command',
    'handle_about_command',
    'register_handlers'
]
