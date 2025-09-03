# admin.py - FREE version

import asyncio
import logging

from aiogram import Bot, types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message

from config import ADMIN_IDS, BOT_TOKEN
from utils.user_management import (
    broadcast_message_to_all_users,
    get_usage_stats,
    get_users_with_usernames,
    is_admin,
)

# Set up logging
logger = logging.getLogger(__name__)


class AdminActions(StatesGroup):
    waiting_for_broadcast_message = State()


async def send_restart_notification():
    bot = Bot(token=BOT_TOKEN)
    restart_message = "Bot has been restarted and is now online!"

    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(admin_id, restart_message)
            logger.info(f"Restart notification sent to admin {admin_id}")
        except Exception as e:
            logger.error(f"Failed to send restart notification to admin {admin_id}: {e}")

    await bot.session.close()


async def handle_admin_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("No access")
        return

    # Get basic stats
    stats = get_usage_stats()

    admin_menu = f"""
Admin Panel - FREE Version

Statistics:
Total Users: {stats['total_users']}
Total Downloads: {stats['total_downloads']}

Available Commands:
/broadcast - Send message to all users
/users - List users with usernames
/stats - Show detailed statistics

Note: This is the FREE version
For paid features, check other branches:
• channel-subscription-feature
"""

    await message.answer(admin_menu, parse_mode="Markdown")


async def handle_broadcast_command(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        await message.answer("No access")
        return

    await message.answer("Send me the message you want to broadcast to all users:")
    await state.set_state(AdminActions.waiting_for_broadcast_message)


async def handle_broadcast_message(message: Message, state: FSMContext):
    if not is_admin(message.from_user.id):
        return

    broadcast_text = message.text
    await message.answer("Broadcasting message to all users...")

    # Get bot instance
    bot = message.bot

    try:
        successful_sends, failed_sends = await broadcast_message_to_all_users(bot, broadcast_text)

        result_message = f"""
Broadcast Complete

Results:
Successful: {successful_sends}
Failed: {failed_sends}
Total: {successful_sends + failed_sends}
"""

        await message.answer(result_message, parse_mode="Markdown")
        logger.info(f"Broadcast completed: {successful_sends} successful, {failed_sends} failed")

    except Exception as e:
        await message.answer(f"Broadcast failed: {str(e)}")
        logger.error(f"Broadcast error: {e}")

    await state.clear()


async def handle_users_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("No access")
        return

    try:
        users = get_users_with_usernames()

        if not users:
            await message.answer("No users with usernames found.")
            return

        users_text = "Users with usernames:\n\n"
        for user in users:
            username = user.get('username', 'N/A')
            downloads = user.get('downloads_count', 0)
            users_text += f"@{username} (ID: {user['user_id']}) - {downloads} downloads\n"

        # Split long messages
        if len(users_text) > 4000:
            users_text = users_text[:4000] + "...\n\nList truncated due to length"

        await message.answer(users_text, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"Error getting users: {str(e)}")
        logger.error(f"Users command error: {e}")


async def handle_stats_command(message: Message):
    if not is_admin(message.from_user.id):
        await message.answer("No access")
        return

    try:
        stats = get_usage_stats()

        stats_message = f"""
Bot Statistics - FREE Version

Users:
• Total Users: {stats['total_users']}

Downloads:
• Total Downloads: {stats['total_downloads']}

Note: This is the FREE version
For advanced stats, check paid branches
"""

        await message.answer(stats_message, parse_mode="Markdown")

    except Exception as e:
        await message.answer(f"Error getting stats: {str(e)}")
        logger.error(f"Stats command error: {e}")


def register_admin_handlers(dp):
    from aiogram.filters import Command

    # Admin commands
    dp.message.register(handle_admin_command, Command("admin"))
    dp.message.register(handle_broadcast_command, Command("broadcast"))
    dp.message.register(handle_users_command, Command("users"))
    dp.message.register(handle_stats_command, Command("stats"))

    # Admin states
    dp.message.register(handle_broadcast_message, AdminActions.waiting_for_broadcast_message)

    logger.info("Admin handlers registered")


# Export functions for use in main handlers
__all__ = [
    'AdminActions',
    'send_restart_notification',
    'handle_admin_command',
    'handle_broadcast_command',
    'handle_broadcast_message',
    'handle_users_command',
    'handle_stats_command',
    'register_admin_handlers'
]
