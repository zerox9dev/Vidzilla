# bot_manager.py - Centralized bot management utilities

import logging
from typing import Optional

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

from config import BOT_TOKEN, ADMIN_IDS

logger = logging.getLogger(__name__)


class BotManager:
    _instance: Optional['BotManager'] = None
    _bot: Optional[Bot] = None

    def __new__(cls) -> 'BotManager':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    @classmethod
    def get_bot(cls) -> Bot:
        if cls._bot is None:
            cls._bot = Bot(token=BOT_TOKEN)
        return cls._bot

    @classmethod
    async def close_bot(cls) -> None:
        if cls._bot:
            await cls._bot.session.close()
            cls._bot = None

    @classmethod
    async def send_to_admins(cls, message: str, exclude_admin_id: int = None) -> None:
        bot = cls.get_bot()

        for admin_id in ADMIN_IDS:
            if exclude_admin_id and admin_id == exclude_admin_id:
                continue

            try:
                await bot.send_message(admin_id, message)
                logger.info(f"Message sent to admin {admin_id}")
            except TelegramAPIError as e:
                logger.error(f"Failed to send message to admin {admin_id}: {e}")

    @classmethod
    async def send_admin_notification(cls, message: str, admin_id: int) -> bool:
        if admin_id not in ADMIN_IDS:
            logger.warning(f"Attempted to send admin notification to non-admin: {admin_id}")
            return False

        bot = cls.get_bot()
        try:
            await bot.send_message(admin_id, message)
            logger.info(f"Admin notification sent to {admin_id}")
            return True
        except TelegramAPIError as e:
            logger.error(f"Failed to send admin notification to {admin_id}: {e}")
            return False


# Convenience functions for backward compatibility
def get_bot_instance() -> Bot:
    return BotManager.get_bot()


async def send_to_admins(message: str, exclude_admin_id: int = None):
    await BotManager.send_to_admins(message, exclude_admin_id)
