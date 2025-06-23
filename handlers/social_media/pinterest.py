from handlers.social_media.utils import process_social_media_video


async def process_pinterest(message, bot, pinterest_url, progress_msg=None):
    await process_social_media_video(message, bot, pinterest_url, "Pinterest", progress_msg)
