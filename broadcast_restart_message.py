import asyncio
import logging

from aiogram import Bot

from config import BOT_TOKEN
from utils.user_management import broadcast_message_to_all_users

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def send_restart_notification():
    """Send a notification to all users that the bot is working again."""
    bot = Bot(token=BOT_TOKEN)
    
    restart_message = """<b>🎉 Good news!</b>

Our bot is now back online and fully functional!

Thank you for your patience while we were making improvements.

You can continue using all features as normal:
- Download videos from Instagram, TikTok, YouTube, and more
- Convert and save videos in different formats
- Access your subscription benefits

If you have any questions or encounter any issues, please let us know.

Happy downloading! 🚀"""

    logger.info("Starting to broadcast restart notification...")
    success_count, failed_count = await broadcast_message_to_all_users(bot, restart_message)
    logger.info(f"Broadcast completed. Success: {success_count}, Failed: {failed_count}")
    
    # Close the bot session
    await bot.session.close()

if __name__ == "__main__":
    try:
        asyncio.run(send_restart_notification())
        logger.info("Restart notification sent successfully")
    except Exception as e:
        logger.error(f"Error sending restart notification: {e}") 