# user_management.py - FREE version (with MongoDB resilience)

import asyncio
import logging
from datetime import datetime
from typing import Callable, Optional

from aiogram import Bot
from aiogram.exceptions import (
    TelegramAPIError,
    TelegramForbiddenError,
    TelegramRetryAfter,
)

from config import (
    ADMIN_IDS,
    MONGODB_DB_NAME,
    MONGODB_URI,
    MONGODB_USERS_COLLECTION,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection with resilience
_db_available = False
client = None
db = None
users_collection = None

try:
    from pymongo import MongoClient
    from pymongo.errors import ConnectionFailure

    client = MongoClient(MONGODB_URI, serverSelectionTimeoutMS=5000)
    client.admin.command("ping")
    _db_available = True
    db = client[MONGODB_DB_NAME]
    users_collection = db[MONGODB_USERS_COLLECTION]
    logger.info("Successfully connected to MongoDB")
except Exception as e:
    logger.warning(f"MongoDB unavailable — running without user tracking: {e}")
    client = None
    db = None
    users_collection = None


def _db_op(func, default=None):
    """Wrap a DB operation — return default if DB is down."""
    if not _db_available or users_collection is None:
        return default
    try:
        return func()
    except Exception as e:
        logger.warning(f"MongoDB operation failed: {e}")
        return default


def get_user(user_id):
    return _db_op(lambda: users_collection.find_one({"user_id": user_id}), default=None)


def create_user(user_id, username=None, language=None):
    user = {
        "user_id": user_id,
        "username": username,
        "downloads_count": 0,
        "language": language,
        "created_at": datetime.now(),
    }
    _db_op(lambda: users_collection.insert_one(user))
    return user


def update_user(user_id, username=None, language=None):
    def _update():
        update_data = {"last_activity": datetime.now()}
        if username:
            update_data["username"] = username
        if language:
            update_data["language"] = language
        users_collection.update_one(
            {"user_id": user_id},
            {"$set": update_data}
        )
    _db_op(_update)


def increment_download_count(user_id):
    doc = _db_op(lambda: users_collection.find_one_and_update(
        {"user_id": user_id},
        {"$inc": {"downloads_count": 1}},
        return_document=True,
    ))
    if doc and "downloads_count" in doc:
        return doc["downloads_count"]
    return 0


def is_admin(user_id):
    return user_id in ADMIN_IDS


def get_users_with_usernames():
    return _db_op(
        lambda: list(users_collection.find(
            {"username": {"$ne": None}},
            {"user_id": 1, "username": 1, "downloads_count": 1}
        )),
        default=[]
    )


def get_usage_stats():
    def _stats():
        total_users = users_collection.count_documents({})
        total_downloads = users_collection.aggregate([
            {"$group": {"_id": None, "total": {"$sum": "$downloads_count"}}}
        ])
        total_downloads_count = 0
        for result in total_downloads:
            total_downloads_count = result["total"]
        return {
            "total_users": total_users,
            "total_downloads": total_downloads_count,
        }

    return _db_op(_stats, default={"total_users": 0, "total_downloads": 0})


async def broadcast_message_to_all_users(
    bot: Bot,
    message_text: str,
    parse_mode: Optional[str] = None,
    reply_markup=None,
    rate_per_second: int = 25,
    progress_callback: Optional[Callable[[int, int, int], "asyncio.Future"]] = None,
):
    """Throttled broadcast respecting Telegram limits (~30 msg/s global).

    Returns (successful, blocked, failed). 'blocked' = users who blocked the bot.
    """
    if not _db_available or users_collection is None:
        return 0, 0, 0

    user_ids = [u["user_id"] for u in users_collection.find({}, {"user_id": 1})]
    total = len(user_ids)
    delay = 1.0 / max(1, rate_per_second)

    successful = 0
    blocked = 0
    failed = 0

    for idx, user_id in enumerate(user_ids, 1):
        try:
            await bot.send_message(user_id, message_text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=True)
            successful += 1
        except TelegramRetryAfter as e:
            # Telegram explicitly told us to wait
            wait = e.retry_after + 1
            logger.warning(f"Hit rate limit, sleeping {wait}s")
            await asyncio.sleep(wait)
            try:
                await bot.send_message(user_id, message_text, parse_mode=parse_mode, reply_markup=reply_markup, disable_web_page_preview=True)
                successful += 1
            except Exception as e2:
                failed += 1
                logger.warning(f"Retry failed for {user_id}: {e2}")
        except TelegramForbiddenError:
            # User blocked the bot or deleted account
            blocked += 1
        except TelegramAPIError as e:
            failed += 1
            logger.warning(f"Failed to send to {user_id}: {e}")

        if progress_callback and idx % 500 == 0:
            try:
                await progress_callback(idx, total, successful)
            except Exception as e:
                logger.debug(f"progress_callback failed: {e}")

        await asyncio.sleep(delay)

    return successful, blocked, failed


# FREE version - no subscription checks, everyone has access
async def check_channel_subscription(user_id, bot):
    return True


def check_user_subscription(user_id, username=None, language=None):
    return True
