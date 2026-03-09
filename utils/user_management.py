# user_management.py - FREE version (with MongoDB resilience)

import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError

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
    _db_op(lambda: users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads_count": 1}}
    ))


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


async def broadcast_message_to_all_users(bot: Bot, message_text: str):
    if not _db_available or users_collection is None:
        return 0, 0

    users = users_collection.find({}, {"user_id": 1})
    successful_sends = 0
    failed_sends = 0

    for user in users:
        try:
            await bot.send_message(user["user_id"], message_text)
            successful_sends += 1
        except TelegramAPIError as e:
            failed_sends += 1
            logger.warning(f"Failed to send message to {user['user_id']}: {e}")

    return successful_sends, failed_sends


# FREE version - no subscription checks, everyone has access
async def check_channel_subscription(user_id, bot):
    return True


def check_user_subscription(user_id, username=None, language=None):
    return True
