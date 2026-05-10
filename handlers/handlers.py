# handlers.py - FREE version

from aiogram import F
from aiogram.filters import Command
from aiogram.types import Message

from config import PLATFORM_IDENTIFIERS, extract_url
from handlers.social_media.video_processor import detect_platform_and_process
from utils.user_management import (
    check_channel_subscription,
    increment_download_count,
)
from utils.common_utils import ensure_user_exists, handle_errors
from utils.rate_limiter import rate_limiter
from utils.ads import WELCOME_AD, PERIODIC_AD, should_show_periodic_ad


async def send_welcome(message: Message):
    ensure_user_exists(message)
    welcome_text = (
        "👋 Hi!\n\n"
        "I download videos from Instagram, TikTok, YouTube, Pinterest, "
        "Facebook, Twitter, Reddit and Vimeo.\n\n"
        "📎 Just send a link!"
        + WELCOME_AD
    )
    await message.answer(welcome_text, disable_web_page_preview=True)


async def send_hint(message: Message):
    await message.answer("🔗 Send me a video link to download")


@handle_errors("⚠️ Something went wrong. Try again.")
async def process_video_link(message: Message):
    user = ensure_user_exists(message)
    user_id = user['user_id']

    url = extract_url(message.text)
    if not url:
        await message.answer("🔗 Please send a valid link")
        return

    if not rate_limiter.is_allowed(user_id):
        wait = rate_limiter.seconds_until_allowed(user_id)
        await message.answer(f"⏳ Too fast! Wait {wait}s before next download")
        return

    if not await check_channel_subscription(user_id, message.bot):
        return

    progress_msg = await message.answer("⬇️ Starting download...")

    platform_detected = await detect_platform_and_process(
        message, message.bot, url, progress_msg
    )

    if not platform_detected:
        supported_platforms = ', '.join(sorted(set(PLATFORM_IDENTIFIERS.values())))
        await progress_msg.edit_text(
            f"🚫 Platform not supported\n\nSupported: {supported_platforms}"
        )
        return

    new_count = increment_download_count(user_id)

    if should_show_periodic_ad(new_count):
        await message.answer(PERIODIC_AD, disable_web_page_preview=True)


def register_handlers(dp):
    dp.message.register(send_welcome, Command("start"))
    dp.message.register(process_video_link, F.text.regexp(r'https?://'))
    dp.message.register(send_hint)
    print("Main handlers registered")


__all__ = [
    'send_welcome',
    'send_hint',
    'process_video_link',
    'register_handlers',
]
