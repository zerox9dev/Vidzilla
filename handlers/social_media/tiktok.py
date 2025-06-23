from handlers.social_media.utils import process_social_media_video


async def process_tiktok(message, bot, tiktok_url, progress_msg=None):
    await process_social_media_video(message, bot, tiktok_url, "TikTok", progress_msg)
