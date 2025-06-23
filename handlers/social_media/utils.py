import json
import requests
from aiogram.types import URLInputFile
from handlers.social_media import instagram

from config import RAPIDAPI_KEY, PLATFORM_IDENTIFIERS


async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    """
    Generic function to process videos from social media platforms
    
    Args:
        message: User message object
        bot: Bot instance
        url: Social media URL to process
        platform_name: Name of the platform (Facebook, Twitter, TikTok, etc.)
        progress_msg: Message object for progress updates
    """
    try:
        if progress_msg:
            await progress_msg.edit_text(f"⏳ Processing {platform_name} link... 50%")
            
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
            await progress_msg.edit_text(f"⏳ Processing {platform_name} link... 75%")

        if response.status_code == 200 and 'medias' in data and len(data['medias']) > 0:
            video_url = data['medias'][0]['url']
            
            if progress_msg:
                await progress_msg.edit_text(f"⏳ Processing {platform_name} link... 90%")

            video_file = URLInputFile(video_url)
            await bot.send_video(
                chat_id=message.chat.id,
                video=video_file
            )

            file_name = f"{platform_name.lower()}_video_{message.from_user.id}.mp4"
            doc_file = URLInputFile(video_url, filename=file_name)
            await bot.send_document(
                chat_id=message.chat.id,
                document=doc_file,
                disable_content_type_detection=True
            )
            
            if progress_msg:
                await progress_msg.edit_text(f"✅ {platform_name} video processed successfully! 100%")
        else:
            error_message = data.get(
                'message', f'Failed to retrieve the video from {platform_name}')
            if progress_msg:
                await progress_msg.edit_text(f"❌ Error: {error_message}")
            else:
                await bot.send_message(message.chat.id, f"Error: {error_message}")

    except Exception as e:
        if progress_msg:
            await progress_msg.edit_text(f"❌ Error processing {platform_name} video: {str(e)}")
        else:
            await bot.send_message(message.chat.id, f"Error processing {platform_name} video: {str(e)}")


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
            await progress_msg.edit_text("⏳ Processing Instagram link... 25%")
        await instagram.process_instagram(message, bot, url, progress_msg)
        return True
    
    # Process all other platforms through the common method
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url and domain != 'instagram.com': # Instagram is already processed above
            if progress_msg:
                await progress_msg.edit_text(f"⏳ Processing {platform_name} link... 25%")
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True
    
    return False 