import logging
import os
import shutil
import tempfile
import uuid
import glob

import instaloader
from aiogram.types import FSInputFile

from config import BASE_DIR, TEMP_DIRECTORY, COMPRESSION_SETTINGS, COMPRESSION_MESSAGES
from utils.video_compression import VideoCompressor, should_compress_video, get_file_size_mb
# Remove circular import - define safe_edit_message locally

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

# Добавим функцию для получения информации о видео
async def get_video_info(video_path):
    try:
        import cv2
        cap = cv2.VideoCapture(video_path)
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        fps = cap.get(cv2.CAP_PROP_FPS)
        frame_count = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        cap.release()
        return {
            "width": width,
            "height": height,
            "aspect_ratio": f"{width}:{height}",
            "fps": fps,
            "frames": frame_count,
            "duration": frame_count / fps if fps else 0
        }
    except Exception as e:
        logger.error(f"Error getting video info: {str(e)}")
        return {"error": str(e)}


async def process_instagram(message, bot, instagram_url, progress_msg=None):
    # Generate a unique identifier for this request
    request_id = str(uuid.uuid4())
    temp_dir = os.path.join(TEMP_DIRECTORY, request_id)

    try:
        logger.info(f"""Processing Instagram URL: {
                    instagram_url} for request {request_id}""")

        # Create a unique temporary directory for this request
        os.makedirs(temp_dir, exist_ok=True)

        if "/reel/" in instagram_url or "/p/" in instagram_url:
            try:
                if progress_msg:
                    await safe_edit_message(progress_msg, "⏳ Processing Instagram link... 50%", "Instagram")
                
                logger.info(f"""Attempting to download video from: {
                            instagram_url}""")
                
                # Initialize Instaloader
                L = instaloader.Instaloader(dirname_pattern=temp_dir, 
                                           download_pictures=True,
                                           download_videos=True, 
                                           download_video_thumbnails=False,
                                           download_geotags=False, 
                                           download_comments=False,
                                           save_metadata=False)
                
                # Extract shortcode from URL
                if "/reel/" in instagram_url:
                    shortcode = instagram_url.split("/reel/")[1].split("/")[0].split("?")[0]
                else:  # "/p/" in instagram_url
                    shortcode = instagram_url.split("/p/")[1].split("/")[0].split("?")[0]
                
                logger.info(f"Extracted shortcode: {shortcode}")
                
                # Download post by shortcode
                post = instaloader.Post.from_shortcode(L.context, shortcode)
                L.download_post(post, target=request_id)
                
                if progress_msg:
                    await safe_edit_message(progress_msg, "⏳ Processing Instagram link... 75%", "Instagram")
                
                # Find the downloaded files using glob pattern
                video_files = glob.glob(os.path.join(temp_dir, "**/*.mp4"), recursive=True)
                
                if not video_files:
                    # Check if it's an image post
                    image_files = glob.glob(os.path.join(temp_dir, "**/*.jpg"), recursive=True)
                    # Filter out profile pictures
                    image_files = [f for f in image_files if "_profile_pic.jpg" not in f]
                    
                    if image_files:
                        if progress_msg:
                            await safe_edit_message(progress_msg, "⏳ Processing Instagram link... 90%", "Instagram")
                            
                        image_path = image_files[0]
                        logger.info(f"Found image file: {image_path}")
                        
                        # Send as photo
                        photo_file = FSInputFile(image_path)
                        await bot.send_photo(chat_id=message.chat.id, photo=photo_file)
                        
                        # Send as document
                        file_name = f"instagram_photo_{message.from_user.id}.jpg"
                        doc_file = FSInputFile(image_path, filename=file_name)
                        await bot.send_document(
                            chat_id=message.chat.id,
                            document=doc_file,
                            disable_content_type_detection=True
                        )
                        
                        logger.info("Image successfully sent")
                        return
                    else:
                        raise FileNotFoundError("No media files found in downloaded content")
                
                video_path = video_files[0]
                logger.info(f"Found video file: {video_path}")
                
                # Логируем информацию о видео
                video_info = await get_video_info(video_path)
                logger.info(f"Video info: {video_info}")
                
                if os.path.getsize(video_path) == 0:
                    raise ValueError("Downloaded video file is empty")

                # Check video size and compress if needed
                file_size_mb = get_file_size_mb(video_path)
                logger.info(f"Video file size: {file_size_mb:.2f}MB")
                
                # Initialize video compressor
                compressor = VideoCompressor(COMPRESSION_SETTINGS)
                final_video_path = video_path
                compression_performed = False
                
                # Check if compression is needed (>50MB)
                if should_compress_video(video_path, max_size_mb=50.0):
                    logger.info(f"Video size ({file_size_mb:.2f}MB) exceeds 50MB limit - starting compression")
                    
                    # Update progress message for compression start
                    if progress_msg:
                        compression_msg = COMPRESSION_MESSAGES['start'].format(size=f"{file_size_mb:.1f}")
                        await safe_edit_message(progress_msg, compression_msg, "Instagram")
                    
                    # Estimate compression time for user feedback
                    try:
                        estimated_time = await compressor.estimate_compression_time(video_path)
                        if progress_msg and estimated_time > 30:
                            time_msg = f"🔄 Video is large ({file_size_mb:.1f}MB), compressing...\n⏱️ Estimated time: ~{estimated_time//60}m {estimated_time%60}s"
                            await safe_edit_message(progress_msg, time_msg, "Instagram")
                    except Exception as est_error:
                        logger.warning(f"Could not estimate compression time: {est_error}")
                    
                    try:
                        # Define progress callback for compression updates
                        async def compression_progress_callback(progress: float):
                            if progress_msg:
                                percent = int(progress * 100)
                                progress_text = COMPRESSION_MESSAGES['progress'].format(percent=percent)
                                await safe_edit_message(progress_msg, progress_text, "Instagram")
                        
                        # Perform compression with progress updates
                        compression_result = await compressor.compress_if_needed(video_path, max_size_mb=50.0)
                        
                        if compression_result.success and compression_result.compressed_path:
                            final_video_path = compression_result.compressed_path
                            compression_performed = True
                            
                            # Calculate compression ratio for user feedback
                            ratio_percent = int((1 - compression_result.compression_ratio) * 100) if compression_result.compression_ratio else 0
                            
                            # Update progress with detailed success message
                            if progress_msg:
                                success_msg = COMPRESSION_MESSAGES['success'].format(
                                    original=f"{compression_result.original_size_mb:.1f}",
                                    compressed=f"{compression_result.compressed_size_mb:.1f}"
                                )
                                detailed_msg = f"{success_msg}\n📉 Size reduced by {ratio_percent}%\n⏳ Sending video..."
                                await safe_edit_message(progress_msg, detailed_msg, "Instagram")
                            
                            logger.info(f"Compression successful: {compression_result.original_size_mb:.2f}MB -> {compression_result.compressed_size_mb:.2f}MB ({ratio_percent}% reduction)")
                        else:
                            # Compression failed, use original file
                            logger.warning(f"Compression failed: {compression_result.error_message}")
                            if progress_msg:
                                fallback_msg = COMPRESSION_MESSAGES['fallback']
                                detailed_fallback = f"{fallback_msg}\n📁 Original size: {file_size_mb:.1f}MB\n⏳ Sending as document..."
                                await safe_edit_message(progress_msg, detailed_fallback, "Instagram")
                    
                    except Exception as compression_error:
                        logger.error(f"Compression error: {str(compression_error)}")
                        if progress_msg:
                            error_msg = COMPRESSION_MESSAGES['error'].format(error=str(compression_error))
                            detailed_error = f"{error_msg}\n📁 Original size: {file_size_mb:.1f}MB\n⏳ Sending original video..."
                            await safe_edit_message(progress_msg, detailed_error, "Instagram")
                else:
                    logger.info(f"Video size ({file_size_mb:.2f}MB) is within 50MB limit - no compression needed")
                    if progress_msg:
                        size_info_msg = f"⏳ Processing Instagram link... 90%\n📁 Video size: {file_size_mb:.1f}MB (within limit)"
                        await safe_edit_message(progress_msg, size_info_msg, "Instagram")

                # Send the video (compressed or original)
                try:
                    video_file = FSInputFile(final_video_path)
                    logger.info("Sending video as video...")
                    
                    # Get video info for the final video (compressed or original)
                    final_video_info = await get_video_info(final_video_path)
                    
                    # Добавляем параметры width и height если они доступны
                    video_params = {}
                    if "width" in final_video_info and "height" in final_video_info:
                        video_params["width"] = final_video_info["width"]
                        video_params["height"] = final_video_info["height"]
                        video_params["supports_streaming"] = True
                    
                    send_result = await bot.send_video(
                        chat_id=message.chat.id, 
                        video=video_file,
                        **video_params
                    )
                    logger.info(f"Video sent as video with params: {video_params}")
                    logger.info(f"Send result: {send_result}")
                except Exception as e:
                    logger.error(f"Error sending video as video: {str(e)}")

                # Send as document
                try:
                    file_name = f"instagram_video_{message.from_user.id}.mp4"
                    doc_file = FSInputFile(final_video_path, filename=file_name)
                    logger.info("Sending video as document...")
                    
                    doc_result = await bot.send_document(
                        chat_id=message.chat.id,
                        document=doc_file,
                        disable_content_type_detection=True  
                    )
                    logger.info("Video sent as document")
                    logger.info(f"Document send result: {doc_result}")
                except Exception as e:
                    logger.error(f"Error sending video as document: {str(e)}")

                # Final success message
                if progress_msg:
                    final_size_mb = get_file_size_mb(final_video_path)
                    if compression_performed:
                        success_text = f"✅ Instagram video processed successfully!\n📊 Size: {file_size_mb:.1f}MB → {final_size_mb:.1f}MB"
                    else:
                        success_text = f"✅ Instagram video processed successfully!\n📊 Size: {final_size_mb:.1f}MB"
                    await safe_edit_message(progress_msg, success_text, "Instagram")
                
                # Clean up compressed file if it was created
                if compression_performed and final_video_path != video_path:
                    try:
                        os.unlink(final_video_path)
                        logger.info(f"Cleaned up compressed video file: {final_video_path}")
                    except Exception as cleanup_error:
                        logger.warning(f"Failed to clean up compressed file: {cleanup_error}")
                    
                logger.info("Video successfully sent")
            except Exception as e:
                logger.error(
                    f"Error downloading or processing video: {str(e)}")
                
                # Check if this is an Instagram rate limiting error (401 Unauthorized)
                error_message = str(e)
                if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
                    if progress_msg:
                        await safe_edit_message(progress_msg, "❌ Instagram's servers are currently busy. Please try again in a few minutes.", "Instagram")
                    else:
                        await bot.send_message(
                            message.chat.id, 
                            "Instagram's servers are currently busy. Please try again in a few minutes."
                        )
                elif "compression" in error_message.lower():
                    # Compression-specific error handling
                    if progress_msg:
                        await safe_edit_message(progress_msg, f"❌ Video compression error: {str(e)}\nTry again or contact support if the issue persists.", "Instagram")
                    else:
                        await bot.send_message(message.chat.id, f"Video compression error: {str(e)}\nTry again or contact support if the issue persists.")
                else:
                    if progress_msg:
                        await safe_edit_message(progress_msg, f"❌ Error downloading video: {str(e)}", "Instagram")
                    else:
                        await bot.send_message(message.chat.id, f"Error downloading video: {str(e)}")
        else:
            logger.warning(f"Invalid Instagram URL received: {instagram_url}")
            if progress_msg:
                await safe_edit_message(progress_msg, "❌ Invalid Instagram URL. Please provide a link to a post or reel.", "Instagram")
            else:
                await bot.send_message(message.chat.id, "Invalid Instagram URL. Please provide a link to a post or reel.")

    except Exception as e:
        logger.error(f"Error processing Instagram video: {str(e)}")
        
        # Check if this is an Instagram rate limiting error (401 Unauthorized)
        error_message = str(e)
        if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
            if progress_msg:
                await safe_edit_message(progress_msg, "❌ Instagram's servers are currently busy. Please try again in a few minutes.", "Instagram")
            else:
                await bot.send_message(
                    message.chat.id, 
                    "Instagram's servers are currently busy. Please try again in a few minutes."
                )
        elif "compression" in error_message.lower():
            # Compression-specific error handling
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ Video compression error: {str(e)}\nTry again or contact support if the issue persists.", "Instagram")
            else:
                await bot.send_message(message.chat.id, f"Video compression error: {str(e)}\nTry again or contact support if the issue persists.")
        else:
            if progress_msg:
                await safe_edit_message(progress_msg, f"❌ Error processing Instagram video: {str(e)}", "Instagram")
            else:
                await bot.send_message(message.chat.id, f"Error processing Instagram video: {str(e)}")
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temporary directory for request {request_id}")
