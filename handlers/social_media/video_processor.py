import asyncio
import logging
import os
import tempfile
import uuid
from typing import Optional

import yt_dlp
from aiogram.types import FSInputFile

from config import COMPRESSION_MESSAGES, COMPRESSION_SETTINGS, TEMP_DIRECTORY, PLATFORM_IDENTIFIERS
from utils.video_compression import VideoCompressor, get_file_size_mb, should_compress_video

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def safe_edit_message(progress_msg, new_text: str, platform_name: str = ""):
    """
    Safely edit a message, avoiding 'message not modified' errors

    Args:
        progress_msg: Message object to edit
        new_text: New text content
        platform_name: Platform name for logging (optional)
    """
    if not progress_msg:
        return

    try:
        # Only edit if the text is different
        if hasattr(progress_msg, "text") and progress_msg.text == new_text:
            logger.debug(f"Skipping message edit for {platform_name} - text unchanged")
            return

        await progress_msg.edit_text(new_text)
    except Exception as e:
        # Log the error but don't raise it to avoid breaking the flow
        error_msg = str(e).lower()
        if "message is not modified" in error_msg:
            logger.debug(f"Message edit skipped for {platform_name} - content unchanged")
        elif "rate" in error_msg or "flood" in error_msg:
            logger.warning(f"Rate limited while editing message for {platform_name}")
        else:
            logger.warning(f"Failed to edit progress message for {platform_name}: {e}")




class YTDLPHandler:
    """Handler for downloading videos using yt-dlp"""

    def __init__(self):
        self.temp_dir = TEMP_DIRECTORY
        os.makedirs(self.temp_dir, exist_ok=True)

    def get_ytdlp_options(self, output_path: str, platform_name: str = ""):
        """Get yt-dlp options based on platform and requirements"""

        # Base options
        options = {
            'outtmpl': output_path,
            'format': 'best[ext=mp4]/best',  # Prefer mp4, fallback to best
            'writeinfojson': False,
            'writesubtitles': False,
            'writeautomaticsub': False,
            'ignoreerrors': False,
            'no_warnings': False,
            'extractaudio': False,
            'audioformat': 'mp3',
            'embed_subs': False,
            'allsubtitles': False,
        }

        # Platform-specific optimizations
        if 'youtube' in platform_name.lower():
            options.update({
                'format': 'best[height<=1080][ext=mp4]/best[height<=1080]/best[ext=mp4]/best',
                'merge_output_format': 'mp4',
            })
        elif 'tiktok' in platform_name.lower():
            options.update({
                'format': 'best[ext=mp4]/best',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
                }
            })
        elif 'twitter' in platform_name.lower() or 'x.com' in platform_name.lower():
            options.update({
                'format': 'best[ext=mp4]/best',
            })
        elif 'instagram' in platform_name.lower():
            options.update({
                'format': 'best[ext=mp4]/best',
                'http_headers': {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                },
                'cookiefile': None,  # Don't use cookies for Instagram
            })

        return options

    async def download_video(self, url: str, platform_name: str, user_id: int) -> Optional[str]:
        """
        Download video using yt-dlp

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
            logger.info(f"Starting download from {platform_name}: {url}")

            options = self.get_ytdlp_options(output_path, platform_name)

            # Run yt-dlp in executor to avoid blocking
            def run_ytdlp():
                with yt_dlp.YoutubeDL(options) as ydl:
                    ydl.download([url])

                    # Find the downloaded file
                    base_path = output_path.replace('.%(ext)s', '')
                    for ext in ['.mp4', '.webm', '.mkv', '.avi', '.mov']:
                        potential_path = base_path + ext
                        if os.path.exists(potential_path):
                            return potential_path
                    return None

            loop = asyncio.get_event_loop()
            downloaded_path = await loop.run_in_executor(None, run_ytdlp)

            if downloaded_path and os.path.exists(downloaded_path):
                file_size = get_file_size_mb(downloaded_path)
                logger.info(f"Successfully downloaded {platform_name} video: {file_size:.2f}MB")
                return downloaded_path
            else:
                logger.error(f"Failed to find downloaded file for {platform_name}")
                return None

        except Exception as e:
            logger.error(f"Error downloading {platform_name} video: {str(e)}")
            return None

    async def extract_info(self, url: str) -> dict:
        """Extract video information without downloading"""
        try:
            def get_info():
                with yt_dlp.YoutubeDL({'quiet': True}) as ydl:
                    return ydl.extract_info(url, download=False)

            loop = asyncio.get_event_loop()
            info = await loop.run_in_executor(None, get_info)
            return info or {}
        except Exception as e:
            logger.error(f"Error extracting info: {str(e)}")
            return {}


async def process_video_with_ytdlp(message, bot, url, platform_name, progress_msg=None):
    """
    Process video using yt-dlp with compression support

    Args:
        message: User message object
        bot: Bot instance
        url: Video URL to process
        platform_name: Name of the platform
        progress_msg: Message object for progress updates
    """
    handler = YTDLPHandler()
    temp_video_path = None
    compressed_video_path = None

    try:
        if progress_msg:
            await safe_edit_message(
                progress_msg, f"⏳ Processing {platform_name} link... 25%", platform_name
            )

        # Extract basic info first
        video_info = await handler.extract_info(url)
        video_title = video_info.get('title', 'Unknown')[:50]  # Limit title length

        if progress_msg:
            await safe_edit_message(
                progress_msg, f"⏳ Downloading {platform_name} video... 50%", platform_name
            )

        # Download video
        temp_video_path = await handler.download_video(url, platform_name, message.from_user.id)

        if not temp_video_path or not os.path.exists(temp_video_path):
            raise Exception("Failed to download video file")

        if progress_msg:
            await safe_edit_message(
                progress_msg, f"⏳ Processing {platform_name} video... 70%", platform_name
            )

        # Check video size and compress if needed
        file_size_mb = get_file_size_mb(temp_video_path)
        logger.info(f"{platform_name} video file size: {file_size_mb:.2f}MB")

        # Initialize video compressor
        compressor = VideoCompressor(COMPRESSION_SETTINGS)
        final_video_path = temp_video_path
        compression_performed = False

        # Check if compression is needed (>50MB)
        if should_compress_video(temp_video_path, max_size_mb=50.0):
            logger.info(
                f"Video size ({file_size_mb:.2f}MB) exceeds 50MB limit - starting compression"
            )

            # Update progress message for compression start
            if progress_msg:
                compression_msg = COMPRESSION_MESSAGES["start"].format(
                    size=f"{file_size_mb:.1f}"
                )
                await safe_edit_message(progress_msg, compression_msg, platform_name)

            try:
                # Define progress callback for compression updates
                async def compression_progress_callback(progress: float):
                    if progress_msg:
                        percent = int(progress * 100)
                        progress_text = COMPRESSION_MESSAGES["progress"].format(
                            percent=percent
                        )
                        await safe_edit_message(progress_msg, progress_text, platform_name)

                # Perform compression with progress updates
                compression_result = await compressor.compress_if_needed(
                    temp_video_path, max_size_mb=50.0
                )

                if compression_result.success and compression_result.compressed_path:
                    final_video_path = compression_result.compressed_path
                    compression_performed = True

                    # Update progress with success message
                    if progress_msg:
                        success_msg = COMPRESSION_MESSAGES["success"].format(
                            original=f"{compression_result.original_size_mb:.1f}",
                            compressed=f"{compression_result.compressed_size_mb:.1f}",
                        )
                        await safe_edit_message(progress_msg, success_msg, platform_name)

                    logger.info(
                        f"Compression successful: {compression_result.original_size_mb:.2f}MB -> {compression_result.compressed_size_mb:.2f}MB"
                    )
                else:
                    # Compression failed, use original file
                    logger.warning(f"Compression failed: {compression_result.error_message}")
                    if progress_msg:
                        fallback_msg = COMPRESSION_MESSAGES["fallback"]
                        await safe_edit_message(progress_msg, fallback_msg, platform_name)

            except Exception as compression_error:
                logger.error(f"Compression error: {str(compression_error)}")
                if progress_msg:
                    error_msg = COMPRESSION_MESSAGES["error"].format(error=str(compression_error))
                    await safe_edit_message(progress_msg, error_msg, platform_name)
        else:
            logger.info(f"Video size ({file_size_mb:.2f}MB) is within 50MB limit - no compression needed")
            if progress_msg:
                await safe_edit_message(
                    progress_msg, f"⏳ Processing {platform_name} video... 90%", platform_name
                )

        # Send video
        await _send_video_with_fallbacks(
            bot, message, final_video_path, platform_name, url,
            file_size_mb, compression_performed, progress_msg, video_title
        )

        # Clean up compressed file if it was created
        if compression_performed and final_video_path != temp_video_path:
            try:
                os.unlink(final_video_path)
                logger.info(f"Cleaned up compressed video file: {final_video_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up compressed file: {cleanup_error}")

        logger.info(f"{platform_name} video successfully processed and sent")

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {str(e)}")
        # Re-raise the exception to be handled by the retry logic
        raise

    finally:
        # Clean up temporary file
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
                logger.info(f"Cleaned up temporary file: {temp_video_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file: {cleanup_error}")


async def _send_video_with_fallbacks(
    bot, message, video_path: str, platform_name: str, original_url: str,
    file_size_mb: float, compression_performed: bool, progress_msg=None, video_title: str = ""
):
    """Send video with multiple delivery methods and fallbacks"""

    try:
        # Try sending as video first
        video_file = FSInputFile(video_path)

        # Prepare caption
        caption = f"🎬 {platform_name}"
        if video_title:
            caption += f" - {video_title}"
        if compression_performed:
            final_size = get_file_size_mb(video_path)
            caption += f"\n📊 Compressed: {file_size_mb:.1f}MB → {final_size:.1f}MB"

        await bot.send_video(
            chat_id=message.chat.id,
            video=video_file,
            caption=caption[:1024],  # Telegram caption limit
            supports_streaming=True
        )
        logger.info(f"Video sent successfully as video message")

    except Exception as video_error:
        logger.warning(f"Failed to send as video: {video_error}")

    # Always send as document too (like Instagram does)
    try:
        file_name = f"{platform_name.lower()}_video_{message.from_user.id}.mp4"
        doc_file = FSInputFile(video_path, filename=file_name)

        caption = f"📁 {platform_name} Video"
        if video_title:
            caption += f" - {video_title}"

        await bot.send_document(
            chat_id=message.chat.id,
            document=doc_file,
            caption=caption[:1024],
            disable_content_type_detection=True
        )
        logger.info(f"Video sent as document")

    except Exception as doc_error:
        logger.error(f"Failed to send as document: {doc_error}")
        # Don't raise exception here - video was already sent successfully

    # Final success message
    if progress_msg:
        final_size_mb = get_file_size_mb(video_path)
        if compression_performed:
            success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {file_size_mb:.1f}MB → {final_size_mb:.1f}MB"
        else:
            success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {final_size_mb:.1f}MB"

        await safe_edit_message(progress_msg, success_text, platform_name)


# Main entry point functions for external usage
async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    """
    Generic function to process videos from social media platforms with compression support
    Includes retry logic with up to 3 attempts

    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        platform_name: Name of the platform (Facebook, Twitter, TikTok, etc.)
        progress_msg: Message object for progress updates
    """
    max_attempts = 3
    last_error = None

    for attempt in range(1, max_attempts + 1):
        try:
            if progress_msg:
                if attempt == 1:
                    await safe_edit_message(
                        progress_msg, f"⏳ Processing {platform_name} link... 25%", platform_name
                    )
                else:
                    await safe_edit_message(
                        progress_msg, f"⏳ Retrying {platform_name} link... (Attempt {attempt}/3)", platform_name
                    )

            # Use yt-dlp for video downloading
            await process_video_with_ytdlp(message, bot, url, platform_name, progress_msg)
            return  # Success, exit the retry loop

        except Exception as e:
            last_error = e
            logger.warning(f"Attempt {attempt}/{max_attempts} failed for {platform_name} video: {str(e)}")

            # If this was the last attempt, handle the final error
            if attempt == max_attempts:
                logger.error(f"All {max_attempts} attempts failed for {platform_name} video: {str(e)}")

                # Enhanced error handling with retry failure message
                error_message = ""
                if "unavailable" in str(e).lower() or "private" in str(e).lower():
                    error_message = f"❌ {platform_name} video is unavailable or private"
                elif "not supported" in str(e).lower():
                    error_message = f"❌ {platform_name} platform is not supported yet"
                elif "age" in str(e).lower() and "restricted" in str(e).lower():
                    error_message = f"❌ {platform_name} video is age-restricted"
                elif "network" in str(e).lower() or "timeout" in str(e).lower() or "connection" in str(e).lower():
                    error_message = f"❌ Network error downloading {platform_name} video after {max_attempts} attempts. Please check your internet connection and try again."
                else:
                    error_message = f"❌ Failed to download {platform_name} video after {max_attempts} attempts.\n💡 Try:\n• Using a different URL format\n• Checking if the video is still available\n• Trying again later"

                if progress_msg:
                    await safe_edit_message(progress_msg, error_message, platform_name)
                else:
                    await bot.send_message(message.chat.id, error_message)

                # Re-raise the exception for any upstream handling
                raise

            # Wait a bit before retrying (exponential backoff)
            wait_time = 2 ** attempt  # 2, 4, 8 seconds
            logger.info(f"Waiting {wait_time} seconds before retry...")
            await asyncio.sleep(wait_time)


async def detect_platform_and_process(message, bot, url, progress_msg=None):
    """
    Detects social media platform type from URL and processes the video

    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        progress_msg: Message object for progress updates

    Returns:
        bool: True if platform was detected and processed, False if not supported
    """
    # Process all platforms through the common ytdlp method
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url:
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True

    return False
