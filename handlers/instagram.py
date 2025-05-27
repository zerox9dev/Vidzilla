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


async def process_instagram(message, bot, instagram_url):
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
                
                # Find the downloaded files using glob pattern
                video_files = glob.glob(os.path.join(temp_dir, "**/*.mp4"), recursive=True)
                
                if not video_files:
                    # Check if it's an image post
                    image_files = glob.glob(os.path.join(temp_dir, "**/*.jpg"), recursive=True)
                    # Filter out profile pictures
                    image_files = [f for f in image_files if "_profile_pic.jpg" not in f]
                    
                    if image_files:
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
                
                if os.path.getsize(video_path) == 0:
                    raise ValueError("Downloaded video file is empty")

                logger.info(f"""Video file size: {
                            os.path.getsize(video_path)} bytes""")

                # Send as video
                video_file = FSInputFile(video_path)
                await bot.send_video(chat_id=message.chat.id, video=video_file)

                # Send as document
                file_name = f"instagram_video_{message.from_user.id}.mp4"
                doc_file = FSInputFile(video_path, filename=file_name)
                await bot.send_document(
                    chat_id=message.chat.id,
                    document=doc_file,
                    disable_content_type_detection=True
                )

                logger.info("Video successfully sent")
            except Exception as e:
                logger.error(
                    f"Error downloading or processing video: {str(e)}")
                
                # Check if this is an Instagram rate limiting error (401 Unauthorized)
                error_message = str(e)
                if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
                    await bot.send_message(
                        message.chat.id, 
                        "Instagram's servers are currently busy. Please try again in a few minutes."
                    )
                else:
                    await bot.send_message(message.chat.id, f"Error downloading video: {str(e)}")
        else:
            logger.warning(f"Invalid Instagram URL received: {instagram_url}")
            await bot.send_message(message.chat.id, "Invalid Instagram URL. Please provide a link to a post or reel.")

    except Exception as e:
        logger.error(f"Error processing Instagram video: {str(e)}")
        
        # Check if this is an Instagram rate limiting error (401 Unauthorized)
        error_message = str(e)
        if "401 Unauthorized" in error_message and "Please wait a few minutes before you try again" in error_message:
            await bot.send_message(
                message.chat.id, 
                "Instagram's servers are currently busy. Please try again in a few minutes."
            )
        else:
            await bot.send_message(message.chat.id, f"Error processing Instagram video: {str(e)}")
    finally:
        # Clean up the temporary directory
        shutil.rmtree(temp_dir, ignore_errors=True)
        logger.info(f"Cleaned up temporary directory for request {request_id}")
