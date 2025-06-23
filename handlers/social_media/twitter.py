from handlers.social_media.utils import process_social_media_video


async def process_twitter(message, bot, twitter_url, progress_msg=None):
    await process_social_media_video(message, bot, twitter_url, "Twitter", progress_msg)
