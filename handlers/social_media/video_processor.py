"""
Simplified video processor using yt-dlp with minimal configuration.
Supports top 8 most popular platforms with maximum stability.
"""

import asyncio
import logging
import os
import tempfile
import uuid
from typing import Optional

import yt_dlp
from aiogram.types import FSInputFile

from config import TEMP_DIRECTORY, PLATFORM_IDENTIFIERS
from utils.user_agent_utils import get_random_user_agent

# Set up logging
logger = logging.getLogger(__name__)

# Telegram limits
TELEGRAM_VIDEO_SIZE_LIMIT_MB = 50  # Telegram's video size limit


def get_file_size_mb(file_path: str) -> float:
    """Get file size in megabytes"""
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


class SimpleVideoDownloader:
    """Simplified video downloader using yt-dlp with minimal configuration"""

    def __init__(self):
        self.temp_dir = TEMP_DIRECTORY
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_simple_ytdlp_options(self, output_path: str) -> dict:
        """Get minimal yt-dlp options for maximum compatibility"""
        return {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best/worst',  # Simple format selection
            'writeinfojson': False,
            'writesubtitles': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'http_headers': {'User-Agent': get_random_user_agent()},
            'extract_flat': False,
            'writethumbnail': False,
            'writeautomaticsub': False,
        }

    async def download_video(self, url: str, platform_name: str, user_id: int) -> Optional[str]:
        """
        Simple video download with basic error handling

        Args:
            url: Video URL
            platform_name: Platform name for logging
            user_id: User ID for unique filename

        Returns:
            Path to downloaded video file or None if failed
        """
        request_id = str(uuid.uuid4())[:8]
        filename = f"{platform_name.lower()}_{user_id}_{request_id}.%(ext)s"
        output_path = os.path.join(self.temp_dir, filename)

        try:
            logger.info(f"Downloading from {platform_name}: {url}")

            options = self.get_simple_ytdlp_options(output_path)

            def run_download():
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])

                    # Find downloaded file
                    base_path = output_path.replace('.%(ext)s', '')
                    for ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov']:
                        potential_path = base_path + ext
                        if os.path.exists(potential_path):
                            return potential_path
                    return None

            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(None, run_download)

            if downloaded_path and os.path.exists(downloaded_path):
                file_size = get_file_size_mb(downloaded_path)
                logger.info(f"Successfully downloaded {platform_name} video: {file_size:.2f}MB")
                return downloaded_path
            else:
                logger.error(f"Failed to download {platform_name} video")
                return None

        except Exception as e:
            logger.error(f"Error downloading {platform_name} video: {str(e)}")
            return None


async def safe_edit_message(progress_msg, new_text: str):
    """Safely edit a message, avoiding errors"""
    if not progress_msg:
        return

    try:
        if hasattr(progress_msg, "text") and progress_msg.text == new_text:
            return
        await progress_msg.edit_text(new_text)
    except Exception as e:
        logger.debug(f"Message edit failed: {e}")


async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    """
    Simplified video processing without compression

    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        platform_name: Name of the platform
        progress_msg: Message object for progress updates
    """
    downloader = SimpleVideoDownloader()
    temp_video_path = None

    try:
        # Update progress
        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Downloading {platform_name} video... 50%")

        # Download video
        temp_video_path = await downloader.download_video(url, platform_name, message.from_user.id)

        if not temp_video_path:
            raise Exception("Failed to download video")

        # Check file size
        file_size_mb = get_file_size_mb(temp_video_path)
        logger.info(f"{platform_name} video size: {file_size_mb:.2f}MB")

        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Checking {platform_name} video... 75%")

        # Check Telegram size limit
        if file_size_mb > TELEGRAM_VIDEO_SIZE_LIMIT_MB:
            # Video is too large for Telegram
            size_limit_message = (
                f"📹 {platform_name} video downloaded successfully!\n"
                f"📊 Size: {file_size_mb:.1f}MB\n\n"
                f"❌ **Video is too large for Telegram**\n"
                f"🚫 Telegram limit: {TELEGRAM_VIDEO_SIZE_LIMIT_MB}MB\n\n"
                f"💡 **Solutions:**\n"
                f"• Try a shorter video\n"
                f"• Use a different quality/resolution\n"
                f"• Upload to cloud storage and share link"
            )

            if progress_msg:
                await safe_edit_message(progress_msg, size_limit_message)
            else:
                await bot.send_message(message.chat.id, size_limit_message)

            logger.info(f"{platform_name} video too large: {file_size_mb:.2f}MB > {TELEGRAM_VIDEO_SIZE_LIMIT_MB}MB")
            return

        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Sending {platform_name} video... 90%")

        # Send video (it's within size limit)
        await send_video_with_fallback(bot, message, temp_video_path, platform_name)

        # Success message
        if progress_msg:
            await safe_edit_message(progress_msg, f"✅ {platform_name} video sent successfully! ({file_size_mb:.1f}MB)")

        logger.info(f"{platform_name} video processed successfully")

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {str(e)}")

        # Simple error message
        error_message = f"❌ Failed to download {platform_name} video.\n💡 Please try again or use a different URL."

        if progress_msg:
            await safe_edit_message(progress_msg, error_message)
        else:
            await bot.send_message(message.chat.id, error_message)

    finally:
        # Cleanup
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
                logger.debug(f"Cleaned up: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")


async def send_video_with_fallback(bot, message, video_path: str, platform_name: str):
    """Send video with document fallback"""
    try:
        # Try sending as video
        video_file = FSInputFile(video_path)
        await bot.send_video(
            chat_id=message.chat.id,
            video=video_file,
            supports_streaming=True
        )
        logger.info("Video sent successfully")
    except Exception as video_error:
        logger.warning(f"Failed to send as video: {video_error}")

        # Fallback to document
        try:
            file_name = f"{platform_name.lower()}_video.mp4"
            doc_file = FSInputFile(video_path, filename=file_name)
            await bot.send_document(
                chat_id=message.chat.id,
                document=doc_file
            )
            logger.info("Video sent as document")
        except Exception as doc_error:
            logger.error(f"Failed to send as document: {doc_error}")
            raise doc_error


async def detect_platform_and_process(message, bot, url, progress_msg=None):
    """
    Detect platform and process video

    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        progress_msg: Message object for progress updates

    Returns:
        bool: True if platform was detected and processed
    """
    # Check supported platforms
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url:
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True

    return False
