

import asyncio
import logging
import os
import uuid
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import yt_dlp
from aiogram.types import FSInputFile

from config import TEMP_DIRECTORY, PLATFORM_IDENTIFIERS
from utils.user_agent_utils import get_random_user_agent
from utils.common_utils import safe_edit_message

# Set up logging
logger = logging.getLogger(__name__)

# Check for ffmpeg (system or imageio-ffmpeg)
FFMPEG_PATH = None
FFMPEG_AVAILABLE = False

# First, try imageio-ffmpeg (Python package)
try:
    import imageio_ffmpeg
    FFMPEG_PATH = imageio_ffmpeg.get_ffmpeg_exe()
    FFMPEG_AVAILABLE = True
    logger.info(f"Using imageio-ffmpeg: {FFMPEG_PATH}")
except ImportError:
    logger.debug("imageio-ffmpeg not installed")
except Exception as e:
    logger.debug(f"Error loading imageio-ffmpeg: {e}")

# If imageio-ffmpeg not available, check system ffmpeg
if not FFMPEG_AVAILABLE:
    system_ffmpeg = shutil.which('ffmpeg')
    if system_ffmpeg:
        FFMPEG_PATH = system_ffmpeg
        FFMPEG_AVAILABLE = True
        logger.info(f"Using system ffmpeg: {FFMPEG_PATH}")
    else:
        logger.warning("ffmpeg not found! Install with: pip install imageio-ffmpeg")

# Telegram limits
TELEGRAM_VIDEO_SIZE_LIMIT_MB = 50  # Telegram's video size limit

# Thread pool for downloads (max 10 concurrent downloads)
download_executor = ThreadPoolExecutor(max_workers=10)


def get_file_size_mb(file_path: str) -> float:
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def get_ytdlp_options(output_path: str) -> dict:
    """Get yt-dlp options for video download - following official documentation"""
    options = {
        'outtmpl': output_path,
    }
    
    # Configure format based on ffmpeg availability
    if FFMPEG_AVAILABLE:
        # With ffmpeg: download and merge best video + audio streams
        options['format'] = 'bestvideo+bestaudio/best'
        options['merge_output_format'] = 'mp4'
        options['ffmpeg_location'] = FFMPEG_PATH
    else:
        # Without ffmpeg: best quality video that MUST have audio
        # Filters: vcodec!=none (has video) AND acodec!=none (has audio)
        options['format'] = 'best[vcodec!=none][acodec!=none]/worst[vcodec!=none][acodec!=none]'
    
    return options


async def download_video(url: str, platform_name: str, user_id: int) -> Optional[str]:
    """Download video using yt-dlp"""
    os.makedirs(TEMP_DIRECTORY, exist_ok=True)
    
    request_id = str(uuid.uuid4())[:8]
    filename = f"{platform_name.lower()}_{user_id}_{request_id}.%(ext)s"
    output_path = os.path.join(TEMP_DIRECTORY, filename)

    try:
        logger.info(f"Downloading from {platform_name}: {url}")

        options = get_ytdlp_options(output_path)

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
        downloaded_path = await loop.run_in_executor(download_executor, run_download)

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





async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    temp_video_path = None

    try:
        # Update progress
        if progress_msg:
            await safe_edit_message(progress_msg, f"Downloading...")

        # Download video
        temp_video_path = await download_video(url, platform_name, message.from_user.id)

        if not temp_video_path:
            raise Exception("Failed to download video")

        # Check file size
        file_size_mb = get_file_size_mb(temp_video_path)
        logger.info(f"{platform_name} video size: {file_size_mb:.2f}MB")

        if progress_msg:
            await safe_edit_message(progress_msg, f"Checking...")

        # Check Telegram size limit
        if file_size_mb > TELEGRAM_VIDEO_SIZE_LIMIT_MB:
            # Video is too large for Telegram
            size_limit_message = f"Too large ({file_size_mb:.1f}MB)\nLimit: {TELEGRAM_VIDEO_SIZE_LIMIT_MB}MB"

            if progress_msg:
                await safe_edit_message(progress_msg, size_limit_message)
            else:
                await bot.send_message(message.chat.id, size_limit_message)

            logger.info(f"{platform_name} video too large: {file_size_mb:.2f}MB > {TELEGRAM_VIDEO_SIZE_LIMIT_MB}MB")
            return

        if progress_msg:
            await safe_edit_message(progress_msg, f"Sending video & document...")

        # Send video and document in media group (it's within size limit)
        await send_video_with_fallback(bot, message, temp_video_path, platform_name)

        # Success message
        if progress_msg:
            await safe_edit_message(progress_msg, f"Sent video & document! ({file_size_mb:.1f}MB)")

        logger.info(f"{platform_name} video processed successfully")

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {str(e)}")

        # Simple error message
        error_message = "Error\nTry another link"

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
    video_sent = False
    document_sent = False
    errors = []
    video_message = None

    # Send as video first
    try:
        video_file = FSInputFile(video_path)
        video_message = await bot.send_video(
            chat_id=message.chat.id,
            video=video_file,
            supports_streaming=True
        )
        logger.info("Video sent successfully")
        video_sent = True
    except Exception as video_error:
        logger.warning(f"Failed to send as video: {video_error}")
        errors.append(f"Video: {video_error}")

    # Send as document second, with reply to video if available
    try:
        file_name = f"{platform_name.lower()}_video.mp4"
        doc_file = FSInputFile(video_path, filename=file_name)

        # Reply to video message if it was sent successfully
        reply_to_message_id = video_message.message_id if video_message else None

        await bot.send_document(
            chat_id=message.chat.id,
            document=doc_file,
            reply_to_message_id=reply_to_message_id,
            disable_content_type_detection=True
        )
        logger.info("Video sent as document")
        document_sent = True
    except Exception as doc_error:
        logger.warning(f"Failed to send as document: {doc_error}")
        errors.append(f"Document: {doc_error}")

    # Check if at least one method succeeded
    if not video_sent and not document_sent:
        error_msg = "Failed to send video in both formats: " + "; ".join(errors)
        raise Exception(error_msg)

    # Log success status
    if video_sent and document_sent:
        logger.info("Video sent successfully in both formats (linked)")
    elif video_sent:
        logger.info("Video sent successfully as video only")
    elif document_sent:
        logger.info("Video sent successfully as document only")


async def detect_platform_and_process(message, bot, url, progress_msg=None):
    # Check supported platforms
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url:
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True

    return False
