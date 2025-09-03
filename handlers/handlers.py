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
    increment_download_count,
)
from utils.common_utils import ensure_user_exists, handle_errors


class DownloadVideo(StatesGroup):
    waiting_for_link = State()


async def send_welcome(message: Message, state: FSMContext):
    # Ensure user exists in database
    ensure_user_exists(message)
    welcome_text = "👋 Hi!\n\n📥 I help you download videos and photos from Instagram, TikTok, YouTube and Pinterest —\nwithout watermarks and in the best quality!\n\n📎 Just send a link — and get video in a couple of seconds!"

    await message.answer(welcome_text, parse_mode="Markdown")


@handle_errors("Error\nTry another link")
async def process_video_link(message: Message, state: FSMContext):
    # Ensure user exists in database
    user = ensure_user_exists(message)
    user_id = user['user_id']
    url = message.text.strip()

    # Check channel subscription (always returns True in FREE version)
    if not await check_channel_subscription(user_id, message.bot):
        return

    # Send processing message
    progress_msg = await message.answer("Loading...")

    # Detect platform and process video
    platform_detected = await detect_platform_and_process(
        message, message.bot, url, progress_msg
    )

    if not platform_detected:
        # Platform not supported
        supported_platforms = ', '.join(set(PLATFORM_IDENTIFIERS.values()))
        await progress_msg.edit_text(
            f"Platform not supported\n\n{supported_platforms}",
            parse_mode="Markdown"
        )
        return

    # Increment download counter
    increment_download_count(user_id)



async def handle_about_command(message: Message):
    about_text = "Vidzilla\n\n8 platforms\nFast & Free\n\n- YouTube\n- Instagram\n- TikTok\n- Facebook\n- Twitter\n- Pinterest\n- Reddit\n- Vimeo"

    await message.answer(about_text, parse_mode="Markdown")


def register_handlers(dp):
    from aiogram.filters import Command
    from aiogram import F

    # Commands
    dp.message.register(send_welcome, Command("start"))
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
    'handle_about_command',
    'register_handlers'
]
