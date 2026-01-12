

import asyncio
import logging
import os
import re
import tempfile
import uuid
import shutil
from concurrent.futures import ThreadPoolExecutor
from typing import Optional

import aiohttp
import yt_dlp
from aiogram.types import FSInputFile

from config import TEMP_DIRECTORY, PLATFORM_IDENTIFIERS
from utils.user_agent_utils import get_random_user_agent
from utils.common_utils import safe_edit_message

# Set up logging
logger = logging.getLogger(__name__)

# Check if ffmpeg is available
def check_ffmpeg_available():
    """Check if ffmpeg is installed and available"""
    return shutil.which('ffmpeg') is not None

FFMPEG_AVAILABLE = check_ffmpeg_available()
if not FFMPEG_AVAILABLE:
    logger.warning("ffmpeg not found! Will use single-format downloads only.")
else:
    logger.info("ffmpeg is available")

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


class SimpleVideoDownloader:

    def __init__(self):
        self.temp_dir = TEMP_DIRECTORY
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_simple_ytdlp_options(self, output_path: str) -> dict:
        # Choose format based on ffmpeg availability
        if FFMPEG_AVAILABLE:
            # Best video+audio merged (requires ffmpeg)
            video_format = 'bv*+ba/b'
        else:
            # Single best format with both video and audio (no merging needed)
            # Prioritize formats with both video and audio
            video_format = 'best[ext=mp4]/best'
        
        options = {
            'outtmpl': output_path,
            'format': video_format,
            'writeinfojson': False,
            'writesubtitles': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'http_headers': {'User-Agent': get_random_user_agent()},
            'extract_flat': False,
            'writethumbnail': False,
            'writeautomaticsub': False,
        }
        
        # Only add merge options if ffmpeg is available
        if FFMPEG_AVAILABLE:
            options['merge_output_format'] = 'mp4'
        
        return options

    async def download_video(self, url: str, platform_name: str, user_id: int) -> Optional[str]:
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
            
            # Fallback for Instagram
            if platform_name == "Instagram":
                logger.info("Trying embed parser as fallback for Instagram")
                try:
                    downloaded_path = await self._download_instagram_embed(url, user_id, request_id)
                    if downloaded_path:
                        return downloaded_path
                except Exception as embed_error:
                    logger.error(f"Embed parser failed: {str(embed_error)}")
            
            return None
    
    async def _download_instagram_embed(self, url: str, user_id: int, request_id: str) -> Optional[str]:
        """Download Instagram video using embed page parsing (fallback method)"""
        try:
            # Extract shortcode from various Instagram URL formats
            shortcode_match = (
                re.search(r'/p/([^/?]+)', url) or 
                re.search(r'/reel/([^/?]+)', url) or
                re.search(r'/tv/([^/?]+)', url)
            )
            if not shortcode_match:
                raise ValueError("Invalid Instagram URL")
            
            shortcode = shortcode_match.group(1)
            
            # Try multiple endpoints
            urls_to_try = [
                f"https://www.instagram.com/p/{shortcode}/embed/captioned/",
                f"https://www.instagram.com/reel/{shortcode}/embed/captioned/",
                f"https://www.instagram.com/p/{shortcode}/embed/",
                f"https://www.instagram.com/reel/{shortcode}/embed/",
            ]
            
            async with aiohttp.ClientSession() as session:
                for embed_url in urls_to_try:
                    try:
                        logger.debug(f"Trying embed URL: {embed_url}")
                        headers = {
                            'User-Agent': get_random_user_agent(),
                            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
                            'Accept-Language': 'en-US,en;q=0.9',
                            'Accept-Encoding': 'gzip, deflate, br',
                            'Referer': 'https://www.instagram.com/',
                        }
                        
                        async with session.get(embed_url, headers=headers, timeout=10) as response:
                            if response.status != 200:
                                logger.debug(f"Embed URL {embed_url} returned {response.status}")
                                continue
                            
                            html = await response.text()
                            
                            # Expanded patterns to find video URL
                            patterns = [
                                r'"video_url"\s*:\s*"([^"]+)"',
                                r'"videoUrl"\s*:\s*"([^"]+)"',
                                r'<meta property="og:video" content="([^"]+)"',
                                r'<meta property="og:video:secure_url" content="([^"]+)"',
                                r'<video[^>]+src="([^"]+)"',
                                r'"src"\s*:\s*"(https://[^"]*?cdninstagram[^"]*?\.mp4[^"]*?)"',
                                r'VideoUrl&quot;:&quot;([^&]+)&quot;',
                                r'"video_versions"\s*:\s*\[{"url"\s*:\s*"([^"]+)"',
                                r'contentUrl":"([^"]+\.mp4[^"]*?)"',
                            ]
                            
                            video_url = None
                            for pattern in patterns:
                                match = re.search(pattern, html)
                                if match:
                                    video_url = match.group(1)
                                    # Clean up URL
                                    video_url = (video_url
                                        .replace('\\u0026', '&')
                                        .replace('&amp;', '&')
                                        .replace('\\/', '/')
                                        .replace('\\/','/')
                                    )
                                    logger.info(f"Found video URL with pattern: {pattern[:40]}...")
                                    break
                            
                            if not video_url:
                                # Last resort: try to find any Instagram CDN mp4 URL
                                mp4_matches = re.findall(
                                    r'(https://[^\s"<>\\]*?(?:cdninstagram|fbcdn)[^\s"<>\\]*?\.mp4[^\s"<>\\]*)',
                                    html
                                )
                                if mp4_matches:
                                    video_url = mp4_matches[0].replace('\\/', '/').replace('\\', '')
                                    logger.info("Found video URL from CDN mp4 search")
                            
                            if video_url:
                                # Try to download the video
                                output_path = os.path.join(self.temp_dir, f"instagram_{user_id}_{request_id}.mp4")
                                
                                logger.debug(f"Attempting to download from: {video_url[:100]}...")
                                async with session.get(video_url, headers=headers, timeout=30) as video_response:
                                    if video_response.status != 200:
                                        logger.warning(f"Video download failed with status {video_response.status}")
                                        continue
                                    
                                    content = await video_response.read()
                                    if len(content) < 1000:  # Less than 1KB is probably an error
                                        logger.warning(f"Downloaded content too small: {len(content)} bytes")
                                        continue
                                    
                                    with open(output_path, 'wb') as f:
                                        f.write(content)
                                
                                if os.path.exists(output_path):
                                    file_size = get_file_size_mb(output_path)
                                    if file_size > 0.01:  # At least 10KB
                                        logger.info(f"Successfully downloaded Instagram via embed: {file_size:.2f}MB")
                                        return output_path
                                    else:
                                        logger.warning(f"Downloaded file too small: {file_size}MB")
                                        os.unlink(output_path)
                                        
                    except asyncio.TimeoutError:
                        logger.debug(f"Timeout for {embed_url}")
                        continue
                    except Exception as e:
                        logger.debug(f"Error with {embed_url}: {str(e)}")
                        continue
            
            raise Exception("Could not find video URL in any embed page")
            
        except Exception as e:
            logger.error(f"Instagram embed download failed: {str(e)}")
            raise
    





async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    downloader = SimpleVideoDownloader()
    temp_video_path = None

    try:
        # Update progress
        if progress_msg:
            await safe_edit_message(progress_msg, f"Downloading...")

        # Download video
        temp_video_path = await downloader.download_video(url, platform_name, message.from_user.id)

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
