from handlers.social_media.utils import process_social_media_video


async def process_facebook(message, bot, facebook_url, progress_msg=None):
    await process_social_media_video(message, bot, facebook_url, "Facebook", progress_msg)
