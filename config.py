# config.py

import os

from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Временная директория для хранения загруженных видео
TEMP_DIRECTORY = os.path.join(BASE_DIR, "temp_videos")
BOT_TOKEN = os.getenv("BOT_TOKEN")

# Server configuration
PORT = int(os.getenv("PORT", "8000"))  # Default port 8000 if not specified
HOST = os.getenv("HOST", "0.0.0.0")   # Default host 0.0.0.0 if not specified

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
MONGODB_USERS_COLLECTION = os.getenv("MONGODB_USERS_COLLECTION")
MONGODB_COUPONS_COLLECTION = os.getenv("MONGODB_COUPONS_COLLECTION")

# User management configuration
ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))

# Bot configuration
BOT_USERNAME = os.getenv("BOT_USERNAME")
BOT_URL = f"https://t.me/{BOT_USERNAME}"

# Stripe configuration (disabled in main branch)
# Payment functionality is available in 'stripe-payments-feature' branch
STRIPE_SECRET_KEY = None
STRIPE_PUBLISHABLE_KEY = None
STRIPE_WEBHOOK_SECRET = None
STRIPE_SUCCESS_URL = None
STRIPE_CANCEL_URL = None

# Subscription plans (disabled in main branch)
SUBSCRIPTION_PLANS = {}

# Required channels for accessing the bot (disabled in main branch)
# Format: {'channel_id': {'title': 'Channel Name', 'url': 'https://t.me/channel_username'}}
REQUIRED_CHANNELS = {
    # Channel subscription functionality is available in 'channel-subscription-feature' branch
}

# Dictionary for identifying platform based on URL - Top 10 most popular platforms
PLATFORM_IDENTIFIERS = {
    # Top Social Media & Video Platforms (by global usage)
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "pinterest.com": "Pinterest",
    "pin.it": "Pinterest",
    "reddit.com": "Reddit",
    "vimeo.com": "Vimeo",
}
