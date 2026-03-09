
import asyncio
import logging
import os
import uuid
from typing import Optional

import aiohttp
import yt_dlp
from aiogram.types import FSInputFile

from config import TEMP_DIRECTORY, PLATFORM_IDENTIFIERS, COOKIES_FILE, COOKIES_ENABLED
from utils.user_agent_utils import get_random_user_agent
from utils.common_utils import safe_edit_message
from utils.cleanup import cleanup_temp_directory
from extractors import get_extractor

# Set up logging
logger = logging.getLogger(__name__)

# Telegram limits
TELEGRAM_VIDEO_SIZE_LIMIT_MB = 50  # Telegram's video size limit

# Retry format strings (best → worst)
FORMAT_ATTEMPTS = [
    'best[ext=mp4][filesize<50M]/best[ext=mp4]/best[filesize<50M]',
    'best/bestvideo+bestaudio',
    'worst',
]

# Progress messages
PROGRESS_MESSAGES = {
    'downloading': '⬇️ Downloading from {platform}...',
    'processing': '⚙️ Processing video...',
    'sending_video': '📤 Sending video...',
    'sending_doc': '📁 Sending as file...',
    'done': '✅ Done! ({size:.1f}MB)',
    'too_large': '📦 Too large: {size:.1f}MB (limit: 50MB)',
}


def get_file_size_mb(file_path: str) -> float:
    try:
        size_bytes = os.path.getsize(file_path)
        return size_bytes / (1024 * 1024)
    except Exception:
        return 0.0


def classify_download_error(error: Exception) -> str:
    """Classify a yt-dlp error into a user-friendly message."""
    error_str = str(error).lower()

    if 'private' in error_str:
        return "🔒 This video is private"
    if 'login' in error_str or 'authentication' in error_str or 'cookies' in error_str:
        return "🔑 This platform requires login — try sending a different link or a public video"
    elif 'not found' in error_str or '404' in error_str or 'deleted' in error_str or 'does not exist' in error_str:
        return "❌ Video not found — it may have been deleted"
    elif 'age' in error_str or 'sign in' in error_str or 'confirm your age' in error_str:
        return "🔞 Age-restricted content — can't download"
    elif 'geo' in error_str or 'country' in error_str or 'not available' in error_str or 'blocked' in error_str:
        return "🌍 This video is not available in our region"
    elif 'rate' in error_str or 'too many' in error_str or '429' in error_str:
        return "⏳ Too many requests — try again in a minute"
    elif 'timed out' in error_str or 'timeout' in error_str or 'urlopen error' in error_str:
        return "⏳ Timeout — try again in a moment"
    elif 'copyright' in error_str or 'dmca' in error_str:
        return "🚫 This video was removed due to copyright"
    elif 'unsupported' in error_str or 'no video' in error_str or 'unable to extract' in error_str:
        return "🚫 This platform blocked the download — try again later"
    else:
        # Show first 100 chars of error for debugging
        short = str(error)[:100]
        return f"⚠️ Download failed: {short}"


class SimpleVideoDownloader:

    def __init__(self):
        self.temp_dir = TEMP_DIRECTORY
        os.makedirs(self.temp_dir, exist_ok=True)

    async def try_extractor(self, url: str, platform_name: str, user_id: int) -> Optional[str]:
        """Try Cobalt-style direct extraction before falling back to yt-dlp."""
        try:
            async with aiohttp.ClientSession() as session:
                extractor = get_extractor(platform_name, session)
                if not extractor:
                    return None

                result = await extractor.extract(url)
                if not result or not result.url:
                    return None

                # Download from direct URL
                request_id = str(uuid.uuid4())[:8]
                ext = "jpg" if result.is_photo else "mp4"
                filename = f"{platform_name.lower()}_{user_id}_{request_id}.{ext}"
                output_path = os.path.join(self.temp_dir, filename)

                headers = result.headers or {}
                if "User-Agent" not in headers and "user-agent" not in headers:
                    headers["User-Agent"] = get_random_user_agent()

                async with session.get(
                    result.url,
                    headers=headers,
                    timeout=aiohttp.ClientTimeout(total=60),
                ) as resp:
                    if resp.status != 200:
                        logger.warning(f"Extractor download HTTP {resp.status} for {result.url[:80]}")
                        return None

                    # Check content length if available
                    content_length = resp.content_length
                    if content_length and content_length > TELEGRAM_VIDEO_SIZE_LIMIT_MB * 1024 * 1024:
                        logger.info(f"Extractor: file too large ({content_length} bytes), skipping")
                        return None

                    with open(output_path, "wb") as f:
                        total = 0
                        async for chunk in resp.content.iter_chunked(64 * 1024):
                            f.write(chunk)
                            total += len(chunk)
                            # Safety limit: stop if exceeding 50MB
                            if total > TELEGRAM_VIDEO_SIZE_LIMIT_MB * 1024 * 1024:
                                logger.info("Extractor: exceeded size limit during download")
                                os.unlink(output_path)
                                return None

                if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
                    size_mb = get_file_size_mb(output_path)
                    logger.info(
                        f"Extractor: downloaded {platform_name} media: "
                        f"{size_mb:.2f}MB via direct extraction"
                    )
                    return output_path
                else:
                    return None

        except Exception as e:
            logger.warning(f"Extractor failed for {platform_name}: {e}")
            return None

    def get_simple_ytdlp_options(self, output_path: str, format_string: str) -> dict:
        opts = {
            'outtmpl': output_path,
            'format': format_string,
            'writeinfojson': False,
            'writesubtitles': False,
            'writethumbnail': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extract_flat': False,
            'http_headers': {'User-Agent': get_random_user_agent()},
            'socket_timeout': 30,
            'retries': 3,
            'fragment_retries': 3,
            'file_access_retries': 3,
            'extractor_retries': 3,
            'concurrent_fragment_downloads': 4,
            'noprogress': True,
            'quiet': True,
            'no_color': True,
            'geo_bypass': True,
            'nocheckcertificate': True,
            'extractor_args': {
                'youtube': {'player_client': ['ios', 'web']},
                'tiktok': {'api_hostname': ['api22-normal-c-useast2a.tiktokv.com']},
            },
        }

        # Add cookies if available (needed for Instagram, TikTok login-required content)
        if COOKIES_ENABLED:
            opts['cookiefile'] = COOKIES_FILE
            logger.info("Using cookies file for authentication")

        return opts

    async def download_video(self, url: str, platform_name: str, user_id: int) -> Optional[str]:
        """Download video: try direct extractor first, then yt-dlp fallback."""

        # TRY 1: Cobalt-style direct extractor (fast, no yt-dlp overhead)
        try:
            extractor_path = await self.try_extractor(url, platform_name, user_id)
            if extractor_path:
                logger.info(f"Direct extractor succeeded for {platform_name}")
                return extractor_path
            else:
                logger.info(f"Direct extractor returned nothing for {platform_name}, falling back to yt-dlp")
        except Exception as e:
            logger.info(f"Direct extractor error for {platform_name}: {e}, falling back to yt-dlp")

        # TRY 2: yt-dlp fallback
        request_id = str(uuid.uuid4())[:8]
        filename = f"{platform_name.lower()}_{user_id}_{request_id}.%(ext)s"
        output_path = os.path.join(self.temp_dir, filename)
        base_path = output_path.replace('.%(ext)s', '')

        last_error = None

        for attempt, format_string in enumerate(FORMAT_ATTEMPTS, 1):
            try:
                logger.info(
                    f"[Attempt {attempt}/{len(FORMAT_ATTEMPTS)}] "
                    f"Downloading from {platform_name}: {url} (format: {format_string})"
                )

                options = self.get_simple_ytdlp_options(output_path, format_string)

                def run_download():
                    with yt_dlp.YoutubeDL(options) as ydl:
                        ydl.download([url])

                    # Find downloaded file
                    for ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.m4v']:
                        potential_path = base_path + ext
                        if os.path.exists(potential_path):
                            return potential_path
                    return None

                loop = asyncio.get_event_loop()
                downloaded_path = await loop.run_in_executor(None, run_download)

                if downloaded_path and os.path.exists(downloaded_path):
                    file_size = get_file_size_mb(downloaded_path)
                    logger.info(
                        f"Successfully downloaded {platform_name} video: "
                        f"{file_size:.2f}MB (attempt {attempt})"
                    )
                    return downloaded_path
                else:
                    logger.warning(
                        f"[Attempt {attempt}] Download completed but no file found"
                    )
                    last_error = Exception("Download completed but no output file found")

            except yt_dlp.utils.DownloadError as e:
                last_error = e
                error_msg = classify_download_error(e)
                logger.warning(
                    f"[Attempt {attempt}] yt-dlp DownloadError: {e}"
                )
                # Don't retry on permanent errors (private, deleted, age-restricted, geo)
                if any(marker in error_msg for marker in ['🔒', '❌', '🔞', '🌍', '🚫']):
                    logger.info(f"Permanent error detected, skipping further retries")
                    break

            except Exception as e:
                last_error = e
                logger.warning(f"[Attempt {attempt}] Error: {e}")

            # Clean up any partial files before retry
            for ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov', '.flv', '.m4v', '.part']:
                potential_path = base_path + ext
                if os.path.exists(potential_path):
                    try:
                        os.unlink(potential_path)
                    except Exception:
                        pass

        # All attempts failed
        if last_error:
            raise last_error
        raise Exception("All download attempts failed")


async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    downloader = SimpleVideoDownloader()
    temp_video_path = None

    try:
        # Update progress with platform-specific message
        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['downloading'].format(platform=platform_name)
            )

        # Download video
        temp_video_path = await downloader.download_video(url, platform_name, message.from_user.id)

        if not temp_video_path:
            raise Exception("Failed to download video")

        # Check file size
        file_size_mb = get_file_size_mb(temp_video_path)
        logger.info(f"{platform_name} video size: {file_size_mb:.2f}MB")

        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['processing']
            )

        # Check Telegram size limit
        if file_size_mb > TELEGRAM_VIDEO_SIZE_LIMIT_MB:
            too_large_msg = PROGRESS_MESSAGES['too_large'].format(size=file_size_mb)

            if progress_msg:
                await safe_edit_message(progress_msg, too_large_msg)
            else:
                await bot.send_message(message.chat.id, too_large_msg)

            logger.info(f"{platform_name} video too large: {file_size_mb:.2f}MB > {TELEGRAM_VIDEO_SIZE_LIMIT_MB}MB")
            return

        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['sending_video']
            )

        # Send video and document in media group (it's within size limit)
        await send_video_with_fallback(bot, message, temp_video_path, platform_name)

        # Success message
        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['done'].format(size=file_size_mb)
            )

        logger.info(f"{platform_name} video processed successfully")

    except yt_dlp.utils.DownloadError as e:
        error_message = classify_download_error(e)
        logger.error(f"yt-dlp error processing {platform_name} video: {e}")

        if progress_msg:
            await safe_edit_message(progress_msg, error_message)
        else:
            await bot.send_message(message.chat.id, error_message)

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {str(e)}")

        # Try to classify even generic exceptions
        error_str = str(e).lower()
        if 'timeout' in error_str or 'timed out' in error_str:
            error_message = "⏳ Timeout — try again in a moment"
        elif 'failed to download' in error_str:
            error_message = "⚠️ Download failed — please try another link"
        else:
            short = str(e)[:100]
            error_message = f"⚠️ Something went wrong. Error: {short}"

        if progress_msg:
            await safe_edit_message(progress_msg, error_message)
        else:
            await bot.send_message(message.chat.id, error_message)

    finally:
        # Cleanup temp file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
                logger.debug(f"Cleaned up: {temp_video_path}")
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

        # Periodic cleanup of old temp files
        try:
            cleanup_temp_directory()
        except Exception:
            pass


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
