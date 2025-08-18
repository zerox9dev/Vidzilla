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

    welcome_text = f"""
🎬 **Welcome to Vidzilla - FREE Version!**

Hi {message.from_user.first_name}! 👋

📱 **What I can do:**
• Download videos from top social platforms
• Support for: YouTube, Instagram, TikTok, Facebook, Twitter, Pinterest, Reddit, Vimeo
• Fast and reliable downloads
• No limits, completely FREE!

🚀 **How to use:**
Just send me a video link from any supported platform and I'll download it for you!

💡 **Supported platforms:**
{', '.join(set(PLATFORM_IDENTIFIERS.values()))}

🆓 **This is the FREE version** - no subscriptions, no payments required!

Ready to download? Send me a video link! 🎥
"""

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
    progress_msg = await message.answer("⏳ Processing your request...")

    try:
        # Detect platform and process video
        platform_detected = await detect_platform_and_process(
            message, message.bot, url, progress_msg
        )

        if not platform_detected:
            # Platform not supported
            supported_platforms = ', '.join(set(PLATFORM_IDENTIFIERS.values()))
            await progress_msg.edit_text(
                f"❌ **Platform not supported**\n\n"
                f"🔗 URL: `{url[:50]}{'...' if len(url) > 50 else ''}`\n\n"
                f"✅ **Supported platforms:**\n{supported_platforms}\n\n"
                f"💡 Please send a link from one of the supported platforms.",
                parse_mode="Markdown"
            )
            return

        # Increment download counter
        increment_download_count(user_id)

    except Exception as e:
        error_message = f"❌ **Error processing video**\n\n💡 Please try again or use a different link."
        await progress_msg.edit_text(error_message, parse_mode="Markdown")
        print(f"Error processing video: {e}")


async def handle_help_command(message: Message):
    """Handle /help command"""
    help_text = """
🆘 **Help - Vidzilla FREE**

🎬 **How to use:**
1️⃣ Send me any video link from supported platforms
2️⃣ Wait for processing (usually 10-30 seconds)
3️⃣ Get your downloaded video!

📱 **Supported platforms:**
• YouTube (youtube.com, youtu.be)
• Instagram (instagram.com)
• TikTok (tiktok.com)
• Facebook (facebook.com, fb.com)
• Twitter/X (twitter.com, x.com)
• Pinterest (pinterest.com, pin.it)
• Reddit (reddit.com)
• Vimeo (vimeo.com)

⚠️ **Important notes:**
• Videos larger than 50MB cannot be sent via Telegram
• Some private or restricted videos may not be downloadable
• Processing time depends on video size and platform

🆓 **This is completely FREE!**
No subscriptions, no payments, no limits!

❓ **Need more help?** Contact admin or try different video links.
"""

    await message.answer(help_text, parse_mode="Markdown")


async def handle_about_command(message: Message):
    """Handle /about command"""
    about_text = """
ℹ️ **About Vidzilla**

🎬 Vidzilla is a free video downloader bot that helps you download videos from popular social media platforms.

🆓 **FREE Version Features:**
• Download from 8 popular platforms
• No download limits
• No subscription required
• Fast and reliable
• Clean, simple interface

🌟 **Other Versions Available:**
• **Stripe Payments Branch:** Premium features with Stripe integration
• **Channel Subscription Branch:** Channel-based access control

🛠️ **Technical Info:**
• Built with Python & aiogram
• Uses yt-dlp for video downloading
• MongoDB for user management
• Deployed with reliability in mind

💝 **Completely Free!**
This version is 100% free with no hidden costs or limitations.

Enjoy downloading! 🎥
"""

    await message.answer(about_text, parse_mode="Markdown")


# Export functions for main router
__all__ = [
    'DownloadVideo',
    'send_welcome',
    'process_video_link',
    'handle_help_command',
    'handle_about_command'
]
