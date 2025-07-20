import json
import requests
import os
import tempfile
import logging
from aiogram.types import URLInputFile, FSInputFile
from handlers.social_media import instagram

from config import RAPIDAPI_KEY, PLATFORM_IDENTIFIERS, COMPRESSION_SETTINGS, COMPRESSION_MESSAGES
from utils.video_compression import VideoCompressor, should_compress_video, get_file_size_mb

# Set up logging
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
        if hasattr(progress_msg, 'text') and progress_msg.text == new_text:
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


async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    """
    Generic function to process videos from social media platforms with compression support
    
    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        platform_name: Name of the platform (Facebook, Twitter, TikTok, etc.)
        progress_msg: Message object for progress updates
    """
    temp_video_path = None
    compressed_video_path = None
    
    try:
        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Processing {platform_name} link... 25%", platform_name)
            
        api_url = "https://auto-download-all-in-one.p.rapidapi.com/v1/social/autolink"
        payload = {"url": url}
        headers = {
            "x-rapidapi-key": RAPIDAPI_KEY,
            "x-rapidapi-host": "auto-download-all-in-one.p.rapidapi.com",
            "Content-Type": "application/json"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        data = response.json()
        
        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Processing {platform_name} link... 50%", platform_name)

        if response.status_code == 200 and 'medias' in data and len(data['medias']) > 0:
            video_url = data['medias'][0]['url']
            
            if progress_msg:
                await safe_edit_message(progress_msg, f"⏳ Downloading {platform_name} video... 60%", platform_name)

            # Download video to temporary file for size checking and compression
            temp_video_path = await _download_video_to_temp(video_url, platform_name, message.from_user.id)
            
            if not temp_video_path or not os.path.exists(temp_video_path):
                raise Exception("Failed to download video file")
            
            if progress_msg:
                await safe_edit_message(progress_msg, f"⏳ Processing {platform_name} video... 70%", platform_name)

            # Check video size and compress if needed
            file_size_mb = get_file_size_mb(temp_video_path)
            logger.info(f"{platform_name} video file size: {file_size_mb:.2f}MB")
            
            # Initialize video compressor
            compressor = VideoCompressor(COMPRESSION_SETTINGS)
            final_video_path = temp_video_path
            compression_performed = False
            
            # Check if compression is needed (>50MB)
            if should_compress_video(temp_video_path, max_size_mb=50.0):
                logger.info(f"{platform_name} video size ({file_size_mb:.2f}MB) exceeds 50MB limit - starting compression")
                
                # Update progress message for compression start
                if progress_msg:
                    compression_msg = COMPRESSION_MESSAGES['start'].format(size=f"{file_size_mb:.1f}")
                    await safe_edit_message(progress_msg, f"⏳ {platform_name}: {compression_msg}", platform_name)
                
                # Estimate compression time for user feedback
                try:
                    estimated_time = await compressor.estimate_compression_time(temp_video_path)
                    if progress_msg and estimated_time > 30:
                        time_msg = f"🔄 {platform_name} video is large ({file_size_mb:.1f}MB), compressing...\n⏱️ Estimated time: ~{estimated_time//60}m {estimated_time%60}s"
                        await safe_edit_message(progress_msg, time_msg, platform_name)
                except Exception as est_error:
                    logger.warning(f"Could not estimate compression time for {platform_name}: {est_error}")
                
                try:
                    # Define progress callback for compression updates
                    async def compression_progress_callback(progress: float):
                        if progress_msg:
                            percent = int(progress * 100)
                            progress_text = COMPRESSION_MESSAGES['progress'].format(percent=percent)
                            new_text = f"🔄 {platform_name}: {progress_text}"
                            await safe_edit_message(progress_msg, new_text, platform_name)
                    
                    # Perform compression with progress updates
                    compression_result = await compressor.compress_if_needed(temp_video_path, max_size_mb=50.0)
                    
                    if compression_result.success and compression_result.compressed_path:
                        final_video_path = compression_result.compressed_path
                        compressed_video_path = compression_result.compressed_path
                        compression_performed = True
                        
                        # Calculate compression ratio for user feedback
                        ratio_percent = int((1 - compression_result.compression_ratio) * 100) if compression_result.compression_ratio else 0
                        
                        # Update progress with detailed success message
                        if progress_msg:
                            success_msg = COMPRESSION_MESSAGES['success'].format(
                                original=f"{compression_result.original_size_mb:.1f}",
                                compressed=f"{compression_result.compressed_size_mb:.1f}"
                            )
                            detailed_msg = f"✅ {platform_name}: {success_msg}\n📉 Size reduced by {ratio_percent}%\n⏳ Sending video..."
                            await safe_edit_message(progress_msg, detailed_msg, platform_name)
                        
                        logger.info(f"{platform_name} compression successful: {compression_result.original_size_mb:.2f}MB -> {compression_result.compressed_size_mb:.2f}MB ({ratio_percent}% reduction)")
                    else:
                        # Compression failed, use original file
                        logger.warning(f"{platform_name} compression failed: {compression_result.error_message}")
                        if progress_msg:
                            fallback_msg = COMPRESSION_MESSAGES['fallback']
                            detailed_fallback = f"⚠️ {platform_name}: {fallback_msg}\n📁 Original size: {file_size_mb:.1f}MB\n⏳ Sending as document..."
                            await safe_edit_message(progress_msg, detailed_fallback, platform_name)
                
                except Exception as compression_error:
                    logger.error(f"{platform_name} compression error: {str(compression_error)}")
                    if progress_msg:
                        error_msg = COMPRESSION_MESSAGES['error'].format(error=str(compression_error))
                        detailed_error = f"❌ {platform_name}: {error_msg}\n📁 Original size: {file_size_mb:.1f}MB\n⏳ Sending original video..."
                        await safe_edit_message(progress_msg, detailed_error, platform_name)
            else:
                logger.info(f"{platform_name} video size ({file_size_mb:.2f}MB) is within 50MB limit - no compression needed")
                if progress_msg:
                    size_info_msg = f"⏳ Processing {platform_name} video... 80%\n📁 Video size: {file_size_mb:.1f}MB (within limit)"
                    await safe_edit_message(progress_msg, size_info_msg, platform_name)

            # Attempt to send video with fallback delivery methods
            delivery_success = await _attempt_video_delivery_with_fallbacks(
                bot, message, final_video_path, platform_name, video_url, 
                file_size_mb, compression_performed, progress_msg
            )
            
            if delivery_success:
                logger.info(f"{platform_name} video successfully processed and sent")
            else:
                logger.error(f"All delivery methods failed for {platform_name} video")
            
        else:
            error_message = data.get(
                'message', f'Failed to retrieve the video from {platform_name}')
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ Error: {error_message}", platform_name)
            else:
                await bot.send_message(message.chat.id, f"Error: {error_message}")

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {str(e)}")
        
        # Platform-specific error handling
        error_message = str(e)
        if "compression" in error_message.lower():
            # Compression-specific error handling
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ {platform_name} video compression error: {str(e)}\nTry again or contact support if the issue persists.", platform_name)
            else:
                await bot.send_message(message.chat.id, f"{platform_name} video compression error: {str(e)}\nTry again or contact support if the issue persists.")
        elif "download" in error_message.lower() or "Failed to retrieve" in error_message:
            # Download-specific error handling
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ Failed to download {platform_name} video: {str(e)}\nThe video may be private or unavailable.", platform_name)
            else:
                await bot.send_message(message.chat.id, f"Failed to download {platform_name} video: {str(e)}\nThe video may be private or unavailable.")
        else:
            # General error handling
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ Error processing {platform_name} video: {str(e)}", platform_name)
            else:
                await bot.send_message(message.chat.id, f"Error processing {platform_name} video: {str(e)}")
    
    finally:
        # Clean up temporary files
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
                logger.info(f"Cleaned up temporary video file: {temp_video_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up temporary file {temp_video_path}: {cleanup_error}")
        
        if compressed_video_path and compressed_video_path != temp_video_path and os.path.exists(compressed_video_path):
            try:
                os.unlink(compressed_video_path)
                logger.info(f"Cleaned up compressed video file: {compressed_video_path}")
            except Exception as cleanup_error:
                logger.warning(f"Failed to clean up compressed file {compressed_video_path}: {cleanup_error}")


async def _download_video_to_temp(video_url: str, platform_name: str, user_id: int) -> str:
    """
    Download video from URL to a temporary file for processing.
    
    Args:
        video_url: Direct URL to the video file
        platform_name: Name of the platform (for filename)
        user_id: User ID for unique filename
        
    Returns:
        Path to the downloaded temporary file
        
    Raises:
        Exception: If download fails
    """
    try:
        import requests
        import uuid
        
        # Create unique temporary file
        temp_dir = COMPRESSION_SETTINGS.get('temp_dir', tempfile.gettempdir())
        os.makedirs(temp_dir, exist_ok=True)
        
        unique_id = str(uuid.uuid4())[:8]
        temp_filename = f"{platform_name.lower()}_{user_id}_{unique_id}.mp4"
        temp_path = os.path.join(temp_dir, temp_filename)
        
        # Download video with streaming
        logger.info(f"Downloading {platform_name} video from: {video_url}")
        response = requests.get(video_url, stream=True, timeout=60)
        response.raise_for_status()
        
        # Write to temporary file
        with open(temp_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=8192):
                if chunk:
                    f.write(chunk)
        
        # Verify file was downloaded
        if not os.path.exists(temp_path) or os.path.getsize(temp_path) == 0:
            raise Exception("Downloaded file is empty or doesn't exist")
        
        logger.info(f"Successfully downloaded {platform_name} video to: {temp_path}")
        return temp_path
        
    except Exception as e:
        logger.error(f"Failed to download {platform_name} video: {str(e)}")
        # Clean up partial file if it exists
        if 'temp_path' in locals() and os.path.exists(temp_path):
            try:
                os.unlink(temp_path)
            except:
                pass
        raise Exception(f"Failed to download video: {str(e)}")


async def _attempt_video_delivery_with_fallbacks(bot, message, video_path: str, platform_name: str, 
                                                original_url: str, file_size_mb: float, 
                                                compression_performed: bool, progress_msg=None) -> bool:
    """
    Attempt to deliver video using multiple fallback methods.
    
    Fallback chain:
    1. Primary: Send as video message
    2. Secondary: Send as document attachment
    3. Tertiary: Provide original download link
    4. Final: Error message with troubleshooting steps
    
    Args:
        bot: Bot instance
        message: User message object
        video_path: Path to the video file (compressed or original)
        platform_name: Name of the platform
        original_url: Original social media URL
        file_size_mb: Original file size in MB
        compression_performed: Whether compression was performed
        progress_msg: Progress message object
        
    Returns:
        True if any delivery method succeeded, False if all failed
    """
    final_size_mb = get_file_size_mb(video_path)
    delivery_attempted = []
    
    # Method 1: Try to send as video message
    try:
        if progress_msg:
            await safe_edit_message(progress_msg, f"⏳ Sending {platform_name} video...", platform_name)
        
        video_file = FSInputFile(video_path)
        logger.info(f"Attempting to send {platform_name} video as video message...")
        
        await bot.send_video(
            chat_id=message.chat.id,
            video=video_file,
            supports_streaming=True
        )
        
        delivery_attempted.append("video message")
        logger.info(f"{platform_name} video sent successfully as video message")
        
        # Send success message
        if progress_msg:
            if compression_performed:
                success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {file_size_mb:.1f}MB → {final_size_mb:.1f}MB\n📹 Sent as video"
            else:
                success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {final_size_mb:.1f}MB\n📹 Sent as video"
            await safe_edit_message(progress_msg, success_text, platform_name)
        
        return True
        
    except Exception as video_error:
        logger.warning(f"Failed to send {platform_name} video as video message: {str(video_error)}")
        delivery_attempted.append("video message (failed)")
    
    # Method 2: Try to send as document attachment
    try:
        if progress_msg:
            await safe_edit_message(progress_msg, f"⚠️ Sending {platform_name} video as document...", platform_name)
        
        file_name = f"{platform_name.lower()}_video_{message.from_user.id}.mp4"
        doc_file = FSInputFile(video_path, filename=file_name)
        logger.info(f"Attempting to send {platform_name} video as document...")
        
        await bot.send_document(
            chat_id=message.chat.id,
            document=doc_file,
            disable_content_type_detection=True,
            caption=f"📁 {platform_name} video (sent as document due to size constraints)"
        )
        
        delivery_attempted.append("document attachment")
        logger.info(f"{platform_name} video sent successfully as document")
        
        # Send success message with explanation
        if progress_msg:
            if compression_performed:
                success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {file_size_mb:.1f}MB → {final_size_mb:.1f}MB\n📁 Sent as document (due to size constraints)"
            else:
                success_text = f"✅ {platform_name} video processed successfully!\n📊 Size: {final_size_mb:.1f}MB\n📁 Sent as document (due to size constraints)"
            await safe_edit_message(progress_msg, success_text, platform_name)
        
        return True
        
    except Exception as doc_error:
        logger.warning(f"Failed to send {platform_name} video as document: {str(doc_error)}")
        delivery_attempted.append("document attachment (failed)")
    
    # Method 3: Provide original download link as fallback
    try:
        if progress_msg:
            await safe_edit_message(progress_msg, f"⚠️ Providing {platform_name} download link...", platform_name)
        
        logger.info(f"Providing original {platform_name} download link as fallback")
        
        fallback_message = (
            f"⚠️ Unable to send {platform_name} video directly\n\n"
            f"📊 Video size: {final_size_mb:.1f}MB\n"
            f"🔗 You can download it directly from:\n{original_url}\n\n"
            f"💡 Tip: Try downloading with a video downloader app or browser"
        )
        
        await bot.send_message(
            chat_id=message.chat.id,
            text=fallback_message,
            disable_web_page_preview=False
        )
        
        delivery_attempted.append("original link sharing")
        logger.info(f"{platform_name} original link provided as fallback")
        
        # Update progress message
        if progress_msg:
            await safe_edit_message(progress_msg, f"⚠️ {platform_name} video link provided (delivery failed)", platform_name)
        
        return True
        
    except Exception as link_error:
        logger.error(f"Failed to send {platform_name} original link: {str(link_error)}")
        delivery_attempted.append("original link sharing (failed)")
    
    # Method 4: Final error message with troubleshooting steps
    try:
        logger.error(f"All delivery methods failed for {platform_name} video")
        
        error_message = (
            f"❌ Failed to deliver {platform_name} video\n\n"
            f"📊 Video size: {final_size_mb:.1f}MB\n"
            f"🔄 Attempted methods: {', '.join(delivery_attempted)}\n\n"
            f"🛠️ Troubleshooting steps:\n"
            f"• Try again in a few minutes\n"
            f"• Check your internet connection\n"
            f"• The video might be too large or corrupted\n"
            f"• Contact support if the issue persists\n\n"
            f"🔗 Original link: {original_url}"
        )
        
        await bot.send_message(
            chat_id=message.chat.id,
            text=error_message,
            disable_web_page_preview=True
        )
        
        if progress_msg:
            await safe_edit_message(progress_msg, f"❌ {platform_name} video delivery failed - see troubleshooting message", platform_name)
        
        logger.info(f"Sent troubleshooting message for {platform_name} video delivery failure")
        return False
        
    except Exception as final_error:
        logger.error(f"Failed to send final error message for {platform_name}: {str(final_error)}")
        return False


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
    # Special handling for Instagram using a separate module
    if 'instagram.com' in url:
        if progress_msg:
            await safe_edit_message(progress_msg, "⏳ Processing Instagram link... 25%", "Instagram")
        await instagram.process_instagram(message, bot, url, progress_msg)
        return True
    
    # Process all other platforms through the common method
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url and domain != 'instagram.com': # Instagram is already processed above
            if progress_msg:
                await safe_edit_message(progress_msg, f"⏳ Processing {platform_name} link... 25%", platform_name)
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True
    
    return False 