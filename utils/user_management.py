# user_management.py - FREE version

import asyncio
import logging
from datetime import datetime

from aiogram import Bot
from aiogram.exceptions import TelegramAPIError
from motor.motor_asyncio import AsyncIOMotorClient

from config import (
    ADMIN_IDS,
    MONGODB_DB_NAME,
    MONGODB_URI,
    MONGODB_USERS_COLLECTION,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
client = AsyncIOMotorClient(MONGODB_URI)
db = client[MONGODB_DB_NAME]
users_collection = db[MONGODB_USERS_COLLECTION]


async def get_user(user_id):
    return await users_collection.find_one({"user_id": user_id})


async def create_user(user_id, username=None, language=None):
    user = {
        "user_id": user_id,
        "username": username,
        "downloads_count": 0,
        "language": language,
        "created_at": datetime.now(),
    }
    await users_collection.insert_one(user)
    return user


async def update_user(user_id, username=None, language=None):
    update_data = {"last_activity": datetime.now()}
    if username:
        update_data["username"] = username
    if language:
        update_data["language"] = language

    await users_collection.update_one(
        {"user_id": user_id},
        {"$set": update_data}
    )


async def increment_download_count(user_id):
    await users_collection.update_one(
        {"user_id": user_id},
        {"$inc": {"downloads_count": 1}}
    )


def is_admin(user_id):
    return user_id in ADMIN_IDS


async def get_users_with_usernames():
    cursor = users_collection.find(
        {"username": {"$ne": None}},
        {"user_id": 1, "username": 1, "downloads_count": 1}
    )
    return await cursor.to_list(length=None)


async def get_usage_stats():
    total_users = await users_collection.count_documents({})
    cursor = users_collection.aggregate([
        {"$group": {"_id": None, "total": {"$sum": "$downloads_count"}}}
    ])

    total_downloads_count = 0
    async for result in cursor:
        total_downloads_count = result["total"]

    return {
        "total_users": total_users,
        "total_downloads": total_downloads_count,
    }


async def broadcast_message_to_all_users(bot: Bot, message_text: str):
    cursor = users_collection.find({}, {"user_id": 1})
    users = await cursor.to_list(length=None)
    successful_sends = 0
    failed_sends = 0

    for user in users:
        try:
            await bot.send_message(user["user_id"], message_text)
            successful_sends += 1
            await asyncio.sleep(0.05)  # Rate limit: 20 msg/sec
        except TelegramAPIError as e:
            failed_sends += 1
            logger.warning(f"Failed to send message to {user['user_id']}: {e}")

    return successful_sends, failed_sends


# FREE version - no subscription checks, everyone has access
async def check_channel_subscription(user_id, bot):
    return True
