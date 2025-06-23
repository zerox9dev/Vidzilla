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

# Required channels for accessing the bot
# Format: {'channel_id': {'title': 'Channel Name', 'url': 'https://t.me/channel_username'}}
REQUIRED_CHANNELS = {
    # Update these values with your actual channel IDs, names, and URLs
    '@talentx_tg': {'title': 'TalentX', 'url': 'https://t.me/talentx_tg'},
    '@Pix2Code': {'title': 'Pix2Code', 'url': 'https://t.me/Pix2Code'}
}

# Dictionary for identifying platform based on URL
PLATFORM_IDENTIFIERS = {
    # Social Media Platforms
    'instagram.com': 'Instagram',
    'tiktok.com': 'TikTok',
    'douyin.com': 'Douyin',
    'capcut.com': 'Capcut',
    'threads.net': 'Threads',
    'facebook.com': 'Facebook',
    'fb.com': 'Facebook',
    'kuaishou.com': 'Kuaishou',
    'kwai.com': 'Kuaishou',
    'espn.com': 'ESPN',
    'pinterest.com': 'Pinterest',
    'pin.it': 'Pinterest',
    'imdb.com': 'IMDB',
    'imgur.com': 'Imgur',
    'ifunny.co': 'iFunny',
    'izlesene.com': 'Izlesene',
    'reddit.com': 'Reddit',
    'youtube.com': 'YouTube',
    'youtu.be': 'YouTube',
    'twitter.com': 'Twitter',
    'x.com': 'Twitter',
    'vimeo.com': 'Vimeo',
    'snapchat.com': 'Snapchat',
    'bilibili.com': 'Bilibili',
    'dailymotion.com': 'Dailymotion',
    'sharechat.com': 'Sharechat',
    'likee.video': 'Likee',
    'linkedin.com': 'LinkedIn',
    'tumblr.com': 'Tumblr',
    'hipi.co.in': 'Hipi',
    't.me': 'Telegram',
    'telegram.me': 'Telegram',
    'telegram.org': 'Telegram',
    'getstickerpack.com': 'GetStickerpack',
    'bitchute.com': 'Bitchute',
    'febspot.com': 'Febspot',
    '9gag.com': '9GAG',
    'ok.ru': 'Odnoklassniki',
    'rumble.com': 'Rumble',
    'streamable.com': 'Streamable',
    'ted.com': 'TED',
    'tv.sohu.com': 'SohuTV',
    
    # Adult content platforms
    'pornbox.com': 'Pornbox',
    'xvideos.com': 'Xvideos',
    'xnxx.com': 'Xnxx',
    
    # Chinese platforms
    'xiaohongshu.com': 'Xiaohongshu',
    'ixigua.com': 'Ixigua',
    'weibo.com': 'Weibo',
    'miaopai.com': 'Miaopai',
    'meipai.com': 'Meipai',
    'xiaoying.tv': 'Xiaoying',
    'yingke.com': 'Yingke',
    'sina.com.cn': 'Sina',
    
    # Other platforms
    'bsky.app': 'Bluesky',
    'soundcloud.com': 'SoundCloud',
    'mixcloud.com': 'Mixcloud',
    'spotify.com': 'Spotify',
    'open.spotify.com': 'Spotify',
    'zingmp3.vn': 'Zingmp3',
    'bandcamp.com': 'Bandcamp'
}
