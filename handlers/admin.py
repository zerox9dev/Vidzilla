import asyncio
import logging

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import ADMIN_IDS, BOT_TOKEN
from utils.user_management import (
    broadcast_message_to_all_users,
    create_coupon,
    get_usage_stats,
    get_users_with_usernames,
    is_admin,
    users_collection,
)

# Set up logging
logger = logging.getLogger(__name__)


class AdminActions(StatesGroup):
    waiting_for_coupon_duration = State()
    waiting_for_coupon = State()
    waiting_for_broadcast_message = State()


async def send_restart_notification():
    """Send a notification to all users that the bot is working again."""
    bot = Bot(token=BOT_TOKEN)

    restart_message = """<b>🎉 Good news!</b>

Our bot is now back online and fully functional!

Thank you for your patience while we were making improvements.

You can continue using all features as normal:
- Download videos from Instagram, TikTok, YouTube, and more
- Convert and save videos in different formats
- Free access to all video downloading features

If you have any questions or encounter any issues, please let us know.

Happy downloading! 🚀"""

    logger.info("Starting to broadcast restart notification...")
    success_count, failed_count = await broadcast_message_to_all_users(bot, restart_message)
    logger.info(f"Broadcast completed. Success: {success_count}, Failed: {failed_count}")

    # Close the bot session
    await bot.session.close()
    return success_count, failed_count


async def generate_coupon_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    # Only 1-month coupons are available now
    coupon_code = create_coupon("1month")
    await message.answer("Coupon generated successfully!")
    await message.answer(f"`{coupon_code}`", parse_mode="Markdown")


async def stats_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    stats = get_usage_stats()
    stats_message = (
        f"Usage Statistics:\n\n"
        f"Total Users: {stats['total_users']}\n"
        f"Users With Username: {stats['users_with_username']}\n"
        f"Users With Language: {stats['users_with_language']}\n"
        f"Active Subscriptions: {stats['active_subscriptions']}\n"
        f"Total Downloads: {stats['total_downloads']}\n"
        f"Unused Coupons: {stats['unused_coupons']}"
    )
    await message.answer(stats_message)


async def list_users_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    users = get_users_with_usernames()
    if not users:
        await message.answer("No users with usernames found.")
        return

    # Limit to first 20 users to avoid message too long errors
    users = users[:20]
    user_list = "\n".join(
        [
            f"ID: {user['user_id']}, Username: @{user['username']}, "
            f"Lang: {user.get('language', 'N/A')}, Downloads: {user['downloads_count']}"
            for user in users
        ]
    )

    await message.answer(f"Users with usernames (showing first {len(users)}):\n\n{user_list}")


async def language_stats_command(message: Message):
    """Command to show statistics about users' languages."""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    # Aggregate users by language
    pipeline = [{"$group": {"_id": "$language", "count": {"$sum": 1}}}, {"$sort": {"count": -1}}]
    language_stats = list(users_collection.aggregate(pipeline))

    if not language_stats:
        await message.answer("No language statistics available.")
        return

    # Format the statistics message
    stats_message = "User language statistics:\n\n"
    for stat in language_stats:
        language = stat["_id"] if stat["_id"] else "Not specified"
        count = stat["count"]
        stats_message += f"{language}: {count} users\n"

    await message.answer(stats_message)


async def broadcast_command(message: Message, state: FSMContext):
    """Command to send a notification to all users that the bot is working again."""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    await message.answer("Please enter the message you want to broadcast to all users:")
    await state.set_state(AdminActions.waiting_for_broadcast_message)


async def restart_notification_command(message: Message):
    """Command to send restart notification to all users."""
    if not is_admin(message.from_user.id):
        await message.answer("This command is only available for admins.")
        return

    await message.answer("Sending restart notification to all users...")

    try:
        success_count, failed_count = await send_restart_notification()
        await message.answer(
            f"Restart notification sent.\nSuccess: {success_count}\nFailed: {failed_count}"
        )
    except Exception as e:
        await message.answer(f"Error sending restart notification: {str(e)}")


async def handle_broadcast_message(message: Message, state: FSMContext, bot: Bot):
    """Handle the broadcast message entered by the admin."""
    broadcast_message = message.text

    await message.answer("Broadcasting message to all users. This may take some time...")

    success_count, failed_count = await broadcast_message_to_all_users(bot, broadcast_message)

    await message.answer(f"Broadcast completed.\nSuccess: {success_count}\nFailed: {failed_count}")
    await state.set_state(AdminActions.waiting_for_broadcast_message)


def register_admin_handlers(dp):
    """Register all admin-related handlers"""
    from aiogram.filters.command import Command

    dp.message.register(generate_coupon_command, Command(commands=["generate_coupon"]))
    dp.message.register(stats_command, Command(commands=["stats"]))
    dp.message.register(broadcast_command, Command(commands=["broadcast"]))
    dp.message.register(restart_notification_command, Command(commands=["restart_notification"]))
    dp.message.register(handle_broadcast_message, AdminActions.waiting_for_broadcast_message)
    dp.message.register(list_users_command, Command(commands=["list_users"]))
    dp.message.register(language_stats_command, Command(commands=["language_stats"]))
