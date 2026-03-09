# config.py

import os
import re
from typing import Optional

from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Временная директория для хранения загруженных видео
TEMP_DIRECTORY = os.path.join(BASE_DIR, "temp_videos")
BOT_TOKEN = os.getenv("BOT_TOKEN")
BOT_MODE = os.getenv("BOT_MODE", "webhook").strip().lower()

# Server configuration
PORT = int(os.getenv("PORT", "8000"))  # Default port 8000 if not specified
HOST = os.getenv("HOST", "0.0.0.0")   # Default host 0.0.0.0 if not specified

WEBHOOK_PATH = os.getenv("WEBHOOK_PATH")
WEBHOOK_URL = os.getenv("WEBHOOK_URL")

# MongoDB configuration
MONGODB_URI = os.getenv("MONGODB_URI")
MONGODB_DB_NAME = os.getenv("MONGODB_DB_NAME")
MONGODB_USERS_COLLECTION = os.getenv("MONGODB_USERS_COLLECTION")

# User management configuration
ADMIN_IDS = list(map(int, filter(None, os.getenv("ADMIN_IDS", "").split(","))))


# Dictionary for identifying platform based on URL - Top 10 most popular platforms
PLATFORM_IDENTIFIERS = {
    # Top Social Media & Video Platforms (by global usage)
    "youtube.com/shorts": "YouTube",   # YouTube Shorts (before youtube.com)
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "instagram.com/reel": "Instagram", # Instagram Reels (before instagram.com)
    "instagram.com": "Instagram",
    "vm.tiktok.com": "TikTok",        # TikTok short links
    "tiktok.com": "TikTok",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "fb.watch": "Facebook",            # Facebook short links
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "t.co": "Twitter",                 # Twitter short links
    "pinterest.com": "Pinterest",
    "pin.it": "Pinterest",
    "reddit.com": "Reddit",
    "redd.it": "Reddit",               # Reddit short links
    "vimeo.com": "Vimeo",
}


# URL validation
URL_PATTERN = re.compile(r'https?://[^\s<>"{}|\\^`\[\]]+')


def extract_url(text: str) -> Optional[str]:
    """Extract the first URL from text."""
    match = URL_PATTERN.search(text)
    return match.group(0) if match else None
