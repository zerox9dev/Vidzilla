# user_management.py

import logging
from datetime import datetime, timedelta

from pymongo import MongoClient
from pymongo.errors import ConnectionFailure

from config import (
    ADMIN_IDS,
    FREE_LIMIT,
    MONGODB_COUPONS_COLLECTION,
    MONGODB_DB_NAME,
    MONGODB_URI,
    MONGODB_USERS_COLLECTION,
)

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# MongoDB connection
try:
    client = MongoClient(MONGODB_URI)
    client.admin.command('ping')
    logger.info("Successfully connected to MongoDB")
except ConnectionFailure:
    logger.error(
        "Failed to connect to MongoDB. Check your connection string and network.")
    raise

db = client[MONGODB_DB_NAME]
users_collection = db[MONGODB_USERS_COLLECTION]
coupons_collection = db[MONGODB_COUPONS_COLLECTION]


def get_user(user_id):
    return users_collection.find_one({'user_id': user_id})


def create_user(user_id, username=None):
    user = {
        'user_id': user_id,
        'username': username,
        'downloads_count': 0,
        'subscription_end': None
    }
    users_collection.insert_one(user)
    return user


def increment_downloads(user_id):
    users_collection.update_one(
        {'user_id': user_id},
        {'$inc': {'downloads_count': 1}}
    )


def check_user_limit(user_id, username=None):
    user = get_user(user_id) or create_user(user_id, username)

    if user['subscription_end'] and user['subscription_end'] > datetime.now():
        return True

    if user['downloads_count'] < FREE_LIMIT:
        increment_downloads(user_id)
        return True

    return False


def create_coupon(duration):
    coupon_code = f"COUPON-{datetime.now().strftime('%Y%m%d%H%M%S')}"
    coupons_collection.insert_one({
        'code': coupon_code,
        'duration': duration,
        'used': False,
        'created_at': datetime.now()
    })
    return coupon_code


def activate_coupon(user_id, coupon_code):
    coupon = coupons_collection.find_one({'code': coupon_code, 'used': False})
    if not coupon:
        return False

    duration_map = {
        '1month': timedelta(days=30),
        '3months': timedelta(days=90),
        'lifetime': timedelta(days=36500)  # ~100 years
    }

    duration = duration_map.get(coupon['duration'])
    if not duration:
        return False

    users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'subscription_end': datetime.now() + duration}}
    )

    coupons_collection.update_one(
        {'code': coupon_code},
        {'$set': {'used': True, 'used_by': user_id, 'used_at': datetime.now()}}
    )

    return True


def get_limit_exceeded_message():
    return f"You have exceeded the free limit of {FREE_LIMIT} downloads.\n\nPlease choose a subscription plan to continue using the bot:\n\n1. 1 month - $1\n2. 3 months - $5\n3. Lifetime - $10\n\nUse /subscribe command to select a plan."


async def update_subscription(user_id, plan):
    duration_map = {
        '1month': timedelta(days=30),
        '3months': timedelta(days=90),
        'lifetime': timedelta(days=36500)  # ~100 years
    }

    duration = duration_map.get(plan)
    if not duration:
        return False

    result = users_collection.update_one(
        {'user_id': user_id},
        {'$set': {'subscription_end': datetime.now() + duration}}
    )
    return result.modified_count > 0


def is_admin(user_id):
    return user_id in ADMIN_IDS


def get_usage_stats():
    total_users = users_collection.count_documents({})
    users_with_username = users_collection.count_documents({'username': {'$ne': None}})
    active_subscriptions = users_collection.count_documents(
        {'subscription_end': {'$gt': datetime.now()}})
    total_downloads = sum(user['downloads_count']
                          for user in users_collection.find())
    unused_coupons = coupons_collection.count_documents({'used': False})

    return {
        'total_users': total_users,
        'users_with_username': users_with_username,
        'active_subscriptions': active_subscriptions,
        'total_downloads': total_downloads,
        'unused_coupons': unused_coupons
    }


def get_users_with_usernames():
    return list(users_collection.find(
        {'username': {'$ne': None}}, 
        {'user_id': 1, 'username': 1, 'downloads_count': 1, 'subscription_end': 1}
    ))


def get_all_users():
    """Get all user IDs from the database."""
    return list(users_collection.find({}, {'user_id': 1}))


async def broadcast_message_to_all_users(bot, message_text):
    """Send a broadcast message to all users.
    
    Args:
        bot: The bot instance to use for sending messages
        message_text: The message text to send to all users
        
    Returns:
        tuple: (success_count, failed_count)
    """
    all_users = get_all_users()
    success_count = 0
    failed_count = 0
    
    for user in all_users:
        try:
            await bot.send_message(
                chat_id=user['user_id'],
                text=message_text,
                parse_mode="HTML"
            )
            success_count += 1
        except Exception as e:
            failed_count += 1
            logger.error(f"Failed to send message to user {user['user_id']}: {str(e)}")
    
    return success_count, failed_count


async def handle_coupon_activation(message):
    coupon_code = message.text.strip()
    if activate_coupon(message.from_user.id, coupon_code):
        await message.answer("Coupon activated successfully! You now have access to unlimited downloads.")
    else:
        await message.answer("Invalid or already used coupon code. Please try again or contact the admin.")
