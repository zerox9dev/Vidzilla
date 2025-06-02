# config.py

import os

from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Временная директория для хранения загруженных видео
TEMP_DIRECTORY = os.path.join(BASE_DIR, 'temp_videos')
BOT_TOKEN = os.getenv('BOT_TOKEN')
RAPIDAPI_KEY = os.getenv('RAPIDAPI_KEY')
RAPIDAPI_HOST = "social-media-video-downloader.p.rapidapi.com"
WEBHOOK_PATH = os.getenv('WEBHOOK_PATH')
WEBHOOK_URL = os.getenv('WEBHOOK_URL')

# MongoDB configuration
MONGODB_URI = os.getenv('MONGODB_URI')
MONGODB_DB_NAME = os.getenv('MONGODB_DB_NAME')
MONGODB_USERS_COLLECTION = os.getenv('MONGODB_USERS_COLLECTION')
MONGODB_COUPONS_COLLECTION = os.getenv('MONGODB_COUPONS_COLLECTION')

# User management configuration
ADMIN_IDS = list(map(int, os.getenv('ADMIN_IDS', '').split(',')))

# Bot configuration
BOT_USERNAME = os.getenv('BOT_USERNAME')
BOT_URL = f"https://t.me/{BOT_USERNAME}"

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
STRIPE_WEBHOOK_SECRET = os.getenv('STRIPE_WEBHOOK_SECRET')
STRIPE_SUCCESS_URL = os.getenv('STRIPE_SUCCESS_URL', BOT_URL)
STRIPE_CANCEL_URL = os.getenv('STRIPE_CANCEL_URL', BOT_URL)

# Subscription plans - only one option now
SUBSCRIPTION_PLANS = {
    '1month': {'price': 100, 'name': 'Support Donation'}
}
