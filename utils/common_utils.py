# common_utils.py - Common utilities and decorators

import logging
from functools import wraps
from typing import Callable, Any

from aiogram.types import Message
from aiogram import Bot

from utils.user_management import is_admin, get_user, create_user, update_user

logger = logging.getLogger(__name__)


def admin_required(func: Callable) -> Callable:
    @wraps(func)
    async def wrapper(message: Message, *args, **kwargs):
        if not is_admin(message.from_user.id):
            await message.answer("No access")
            return
        return await func(message, *args, **kwargs)
    return wrapper


def handle_errors(error_message: str = "Error\nTry again"):
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        async def wrapper(message: Message, *args, **kwargs):
            try:
                return await func(message, *args, **kwargs)
            except Exception as e:
                logger.error(f"Error in {func.__name__}: {e}")
                await message.answer(error_message, parse_mode="Markdown")
        return wrapper
    return decorator


async def safe_edit_message(progress_msg, new_text: str):
    if not progress_msg:
        return

    try:
        if hasattr(progress_msg, "text") and progress_msg.text == new_text:
            return
        await progress_msg.edit_text(new_text)
    except Exception as e:
        logger.debug(f"Message edit failed: {e}")


def get_user_info_from_message(message: Message) -> dict:
    return {
        'user_id': message.from_user.id,
        'username': message.from_user.username,
        'language_code': message.from_user.language_code
    }


def ensure_user_exists(message: Message) -> dict:
    user_info = get_user_info_from_message(message)
    user_id = user_info['user_id']
    username = user_info['username']
    language_code = user_info['language_code']

    # Get or create user
    user = get_user(user_id)
    if not user:
        user = create_user(user_id, username, language_code)
        logger.info(f"Created new user: {user_id}")
    else:
        update_user(user_id, username, language_code)
        logger.debug(f"Updated existing user: {user_id}")

    return user


async def send_message_with_fallback(bot: Bot, chat_id: int, text: str, parse_mode: str = None, **kwargs):
    try:
        if len(text) > 4000:
            # Split long messages
            chunks = [text[i:i+4000] for i in range(0, len(text), 4000)]
            sent_messages = []

            for chunk in chunks[:-1]:  # All chunks except the last
                msg = await bot.send_message(chat_id, chunk, parse_mode=parse_mode, **kwargs)
                sent_messages.append(msg)

            # Send the last chunk
            msg = await bot.send_message(chat_id, chunks[-1], parse_mode=parse_mode, **kwargs)
            sent_messages.append(msg)

            return sent_messages[-1]  # Return the last message

        else:
            return await bot.send_message(chat_id, text, parse_mode=parse_mode, **kwargs)

    except Exception as e:
        logger.error(f"Failed to send message to {chat_id}: {e}")
        # Try without parse_mode as fallback
        if parse_mode:
            return await bot.send_message(chat_id, text, **kwargs)
        raise


async def reply_with_fallback(message: Message, text: str, parse_mode: str = None, **kwargs):
    return await send_message_with_fallback(
        message.bot, message.chat.id, text, parse_mode,
        reply_to_message_id=message.message_id, **kwargs
    )


def format_user_list(users: list, max_length: int = 4000) -> str:
    if not users:
        return "No users found."

    lines = ["Users with usernames:\n"]
    for user in users:
        username = user.get('username', 'N/A')
        downloads = user.get('downloads_count', 0)
        line = f"@{username} (ID: {user['user_id']}) - {downloads} downloads\n"
        lines.append(line)

    result = "".join(lines)

    if len(result) > max_length:
        result = result[:max_length] + "...\n\nList truncated due to length"

    return result
