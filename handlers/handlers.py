# handlers.py - FREE version

from aiogram import Bot, types
from aiogram.filters.command import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, Message

from config import PLATFORM_IDENTIFIERS, extract_url
from handlers.social_media.video_processor import detect_platform_and_process
from utils.user_management import (
    check_channel_subscription,
    increment_download_count,
)
from utils.common_utils import ensure_user_exists, handle_errors
from utils.rate_limiter import rate_limiter


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


async def send_welcome(message: Message, state: FSMContext):
    # Ensure user exists in database
    ensure_user_exists(message)
    welcome_text = (
        "👋 Hi!\n\n"
        "I download videos from Instagram, TikTok, YouTube, Pinterest, "
        "Facebook, Twitter, Reddit and Vimeo.\n\n"
        "📎 Just send a link!"
    )

    await message.answer(welcome_text)


@handle_errors("⚠️ Something went wrong. Try again.")
async def process_video_link(message: Message, state: FSMContext):
    # Ensure user exists in database
    user = ensure_user_exists(message)
    user_id = user['user_id']

    # Extract and validate URL
    url = extract_url(message.text)
    if not url:
        await message.answer("🔗 Please send a valid link")
        return

    # Rate limiting
    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_allowed(user_id)
        await message.answer(f"⏳ Too fast! Wait {wait}s before next download")
        return

    # Check channel subscription (always returns True in FREE version)
    if not await check_channel_subscription(user_id, message.bot):
        return

    # Send processing message
    progress_msg = await message.answer("⬇️ Starting download...")

    # Detect platform and process video
    platform_detected = await detect_platform_and_process(
        message, message.bot, url, progress_msg
    )

    if not platform_detected:
        # Platform not supported
        supported_platforms = ', '.join(sorted(set(PLATFORM_IDENTIFIERS.values())))
        await progress_msg.edit_text(
            f"🚫 Platform not supported\n\nSupported: {supported_platforms}"
        )
        return

    # Increment download counter
    increment_download_count(user_id)


def register_handlers(dp):
    from aiogram.filters import Command
    from aiogram import F

    # Commands
    dp.message.register(send_welcome, Command("start"))

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
    'register_handlers'
]
