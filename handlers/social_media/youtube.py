from handlers.social_media.utils import process_social_media_video


async def process_youtube(message, bot, youtube_url, progress_msg=None):
    await process_social_media_video(message, bot, youtube_url, "YouTube", progress_msg)
