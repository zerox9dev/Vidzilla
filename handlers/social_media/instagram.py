import logging
import os
import shutil
import tempfile
import uuid
import glob

import instaloader
from aiogram.types import FSInputFile

from config import BASE_DIR, TEMP_DIRECTORY

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

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
                    await progress_msg.edit_text("⏳ Processing Instagram link... 50%")
                
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
                    await progress_msg.edit_text("⏳ Processing Instagram link... 75%")
                
                # Find the downloaded files using glob pattern
                video_files = glob.glob(os.path.join(temp_dir, "**/*.mp4"), recursive=True)
                
                if not video_files:
                    # Check if it's an image post
                    image_files = glob.glob(os.path.join(temp_dir, "**/*.jpg"), recursive=True)
                    # Filter out profile pictures
                    image_files = [f for f in image_files if "_profile_pic.jpg" not in f]
                    
                    if image_files:
                        if progress_msg:
                            await progress_msg.edit_text("⏳ Processing Instagram link... 90%")
                            
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

                logger.info(f"""Video file size: {
                            os.path.getsize(video_path)} bytes""")
                            
                if progress_msg:
                    await progress_msg.edit_text("⏳ Processing Instagram link... 90%")

                # Send as video
                video_file = FSInputFile(video_path)
                logger.info("Sending video as video...")
                try:
                    # Добавляем параметры width и height если они доступны
                    video_params = {}
                    if "width" in video_info and "height" in video_info:
                        video_params["width"] = video_info["width"]
                        video_params["height"] = video_info["height"]
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
                file_name = f"instagram_video_{message.from_user.id}.mp4"
                doc_file = FSInputFile(video_path, filename=file_name)
                logger.info("Sending video as document...")
                try:
                    doc_result = await bot.send_document(
                        chat_id=message.chat.id,
                        document=doc_file,
                        disable_content_type_detection=False  # Изменено на False для проверки
                    )
                    logger.info("Video sent as document with disable_content_type_detection=False")
                    logger.info(f"Document send result: {doc_result}")
                except Exception as e:
                    logger.error(f"Error sending video as document: {str(e)}")

                if progress_msg:
                    await progress_msg.edit_text("✅ Instagram video processed successfully! 100%")
                    
                logger.info("Video successfully sent")
            except Exception as e:
                logger.error(
                    f"Error downloading or processing video: {str(e)}")
                
                # Check if this is an Instagram rate limiting error (401 Unauthorized)
                error_message = str(e)
                if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
                    if progress_msg:
                        await progress_msg.edit_text("❌ Instagram's servers are currently busy. Please try again in a few minutes.")
                    else:
                        await bot.send_message(
                            message.chat.id, 
                            "Instagram's servers are currently busy. Please try again in a few minutes."
                        )
                else:
                    if progress_msg:
                        await progress_msg.edit_text(f"❌ Error downloading video: {str(e)}")
                    else:
                        await bot.send_message(message.chat.id, f"Error downloading video: {str(e)}")
        else:
            logger.warning(f"Invalid Instagram URL received: {instagram_url}")
            if progress_msg:
                await progress_msg.edit_text("❌ Invalid Instagram URL. Please provide a link to a post or reel.")
            else:
                await bot.send_message(message.chat.id, "Invalid Instagram URL. Please provide a link to a post or reel.")

    except Exception as e:
        logger.error(f"Error processing Instagram video: {str(e)}")
        
        # Check if this is an Instagram rate limiting error (401 Unauthorized)
        error_message = str(e)
        if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
            if progress_msg:
                await progress_msg.edit_text("❌ Instagram's servers are currently busy. Please try again in a few minutes.")
            else:
                await bot.send_message(
                    message.chat.id, 
                    "Instagram's servers are currently busy. Please try again in a few minutes."
                )
        else:
            if progress_msg:
                await progress_msg.edit_text(f"❌ Error processing Instagram video: {str(e)}")
            else:
                await bot.send_message(message.chat.id, f"Error processing Instagram video: {str(e)}")
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temporary directory for request {request_id}")
