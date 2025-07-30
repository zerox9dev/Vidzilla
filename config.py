# config.py

import os

from dotenv import load_dotenv

load_dotenv()

# Базовая директория проекта
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Временная директория для хранения загруженных видео
TEMP_DIRECTORY = os.path.join(BASE_DIR, "temp_videos")
BOT_TOKEN = os.getenv("BOT_TOKEN")

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

# Stripe configuration
STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY")
STRIPE_PUBLISHABLE_KEY = os.getenv("STRIPE_PUBLISHABLE_KEY")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET")
STRIPE_SUCCESS_URL = os.getenv("STRIPE_SUCCESS_URL", BOT_URL)
STRIPE_CANCEL_URL = os.getenv("STRIPE_CANCEL_URL", BOT_URL)

# Subscription plans - only one option now
SUBSCRIPTION_PLANS = {"1month": {"price": 100, "name": "Support Donation"}}

# Required channels for accessing the bot
# Format: {'channel_id': {'title': 'Channel Name', 'url': 'https://t.me/channel_username'}}
REQUIRED_CHANNELS = {
    # Update these values with your actual channel IDs, names, and URLs
    "@talentx_tg": {"title": "TalentX", "url": "https://t.me/talentx_tg"},
    "@Pix2Code": {"title": "Pix2Code", "url": "https://t.me/Pix2Code"},
}

# Dictionary for identifying platform based on URL
PLATFORM_IDENTIFIERS = {
    # Social Media Platforms
    "instagram.com": "Instagram",
    "tiktok.com": "TikTok",
    "douyin.com": "Douyin",
    "capcut.com": "Capcut",
    "threads.net": "Threads",
    "facebook.com": "Facebook",
    "fb.com": "Facebook",
    "kuaishou.com": "Kuaishou",
    "kwai.com": "Kuaishou",
    "espn.com": "ESPN",
    "pinterest.com": "Pinterest",
    "pin.it": "Pinterest",
    "imdb.com": "IMDB",
    "imgur.com": "Imgur",
    "ifunny.co": "iFunny",
    "izlesene.com": "Izlesene",
    "reddit.com": "Reddit",
    "youtube.com": "YouTube",
    "youtu.be": "YouTube",
    "twitter.com": "Twitter",
    "x.com": "Twitter",
    "vimeo.com": "Vimeo",
    "snapchat.com": "Snapchat",
    "bilibili.com": "Bilibili",
    "dailymotion.com": "Dailymotion",
    "sharechat.com": "Sharechat",
    "likee.video": "Likee",
    "linkedin.com": "LinkedIn",
    "tumblr.com": "Tumblr",
    "hipi.co.in": "Hipi",
    "t.me": "Telegram",
    "telegram.me": "Telegram",
    "telegram.org": "Telegram",
    "getstickerpack.com": "GetStickerpack",
    "bitchute.com": "Bitchute",
    "febspot.com": "Febspot",
    "9gag.com": "9GAG",
    "ok.ru": "Odnoklassniki",
    "rumble.com": "Rumble",
    "streamable.com": "Streamable",
    "ted.com": "TED",
    "tv.sohu.com": "SohuTV",
    # Adult content platforms
    "pornbox.com": "Pornbox",
    "xvideos.com": "Xvideos",
    "xnxx.com": "Xnxx",
    # Chinese platforms
    "xiaohongshu.com": "Xiaohongshu",
    "ixigua.com": "Ixigua",
    "weibo.com": "Weibo",
    "miaopai.com": "Miaopai",
    "meipai.com": "Meipai",
    "xiaoying.tv": "Xiaoying",
    "yingke.com": "Yingke",
    "sina.com.cn": "Sina",
    # Other platforms
    "bsky.app": "Bluesky",
    "soundcloud.com": "SoundCloud",
    "mixcloud.com": "Mixcloud",
    "spotify.com": "Spotify",
    "open.spotify.com": "Spotify",
    "zingmp3.vn": "Zingmp3",
    "bandcamp.com": "Bandcamp",
}

# Video compression configuration with environment variable support
COMPRESSION_SETTINGS = {
    "target_size_mb": float(os.getenv("COMPRESSION_TARGET_SIZE_MB", "45")),
    "max_attempts": int(os.getenv("COMPRESSION_MAX_ATTEMPTS", "3")),
    "quality_levels": list(
        map(int, os.getenv("COMPRESSION_QUALITY_LEVELS", "28,32,36").split(","))
    ),
    "max_resolution": tuple(
        map(int, os.getenv("COMPRESSION_MAX_RESOLUTION", "1280,720").split(","))
    ),
    "timeout_seconds": int(os.getenv("COMPRESSION_TIMEOUT_SECONDS", "300")),
    "temp_dir": os.getenv(
        "COMPRESSION_TEMP_DIR", os.path.join(BASE_DIR, "temp_videos", "compression")
    ),
    "min_quality_crf": int(os.getenv("COMPRESSION_MIN_QUALITY_CRF", "18")),
    "max_quality_crf": int(os.getenv("COMPRESSION_MAX_QUALITY_CRF", "40")),
    "disk_space_threshold_mb": float(os.getenv("COMPRESSION_DISK_SPACE_THRESHOLD_MB", "1000")),
    "cleanup_temp_files_hours": int(os.getenv("COMPRESSION_CLEANUP_TEMP_FILES_HOURS", "24")),
    "enable_progress_callbacks": os.getenv("COMPRESSION_ENABLE_PROGRESS_CALLBACKS", "true").lower()
    == "true",
    "enable_resolution_downscaling": os.getenv(
        "COMPRESSION_ENABLE_RESOLUTION_DOWNSCALING", "true"
    ).lower()
    == "true",
    "max_concurrent_compressions": int(os.getenv("COMPRESSION_MAX_CONCURRENT", "2")),
    "ffmpeg_preset": os.getenv("COMPRESSION_FFMPEG_PRESET", "medium"),
    "enable_hardware_acceleration": os.getenv("COMPRESSION_ENABLE_HARDWARE_ACCEL", "false").lower()
    == "true",
}

# Compression monitoring and logging configuration
COMPRESSION_MONITORING = {
    "enable_detailed_logging": os.getenv("COMPRESSION_ENABLE_DETAILED_LOGGING", "true").lower()
    == "true",
    "log_level": os.getenv("COMPRESSION_LOG_LEVEL", "INFO"),
    "enable_performance_metrics": os.getenv(
        "COMPRESSION_ENABLE_PERFORMANCE_METRICS", "true"
    ).lower()
    == "true",
    "metrics_retention_days": int(os.getenv("COMPRESSION_METRICS_RETENTION_DAYS", "30")),
    "enable_disk_space_monitoring": os.getenv("COMPRESSION_ENABLE_DISK_MONITORING", "true").lower()
    == "true",
    "disk_space_warning_threshold": float(os.getenv("COMPRESSION_DISK_WARNING_THRESHOLD", "90.0")),
    "enable_admin_notifications": os.getenv(
        "COMPRESSION_ENABLE_ADMIN_NOTIFICATIONS", "true"
    ).lower()
    == "true",
    "admin_notification_threshold_failures": int(
        os.getenv("COMPRESSION_ADMIN_NOTIFICATION_THRESHOLD", "5")
    ),
    "enable_compression_stats_tracking": os.getenv(
        "COMPRESSION_ENABLE_STATS_TRACKING", "true"
    ).lower()
    == "true",
    "stats_log_interval_minutes": int(os.getenv("COMPRESSION_STATS_LOG_INTERVAL", "60")),
}

# Compression progress messages
COMPRESSION_MESSAGES = {
    "start": "🔄 Video is large ({size}MB), compressing...",
    "progress": "🔄 Compressing video... {percent}% complete",
    "success": "✅ Video compressed from {original}MB to {compressed}MB",
    "fallback": "⚠️ Sending as document due to size constraints",
    "error": "❌ Compression failed: {error}",
}


def validate_compression_config():
    """
    Validate compression configuration settings and log warnings for invalid values.

    Returns:
        bool: True if configuration is valid, False otherwise
    """
    import logging

    logger = logging.getLogger(__name__)

    is_valid = True

    # Validate COMPRESSION_SETTINGS
    if COMPRESSION_SETTINGS["target_size_mb"] <= 0 or COMPRESSION_SETTINGS["target_size_mb"] > 100:
        logger.warning(
            f"Invalid target_size_mb: {COMPRESSION_SETTINGS['target_size_mb']}. Should be between 1-100MB"
        )
        is_valid = False

    if COMPRESSION_SETTINGS["max_attempts"] < 1 or COMPRESSION_SETTINGS["max_attempts"] > 10:
        logger.warning(
            f"Invalid max_attempts: {COMPRESSION_SETTINGS['max_attempts']}. Should be between 1-10"
        )
        is_valid = False

    if not COMPRESSION_SETTINGS["quality_levels"] or any(
        q < 0 or q > 51 for q in COMPRESSION_SETTINGS["quality_levels"]
    ):
        logger.warning(
            f"Invalid quality_levels: {COMPRESSION_SETTINGS['quality_levels']}. CRF values should be between 0-51"
        )
        is_valid = False

    if len(COMPRESSION_SETTINGS["max_resolution"]) != 2 or any(
        r <= 0 for r in COMPRESSION_SETTINGS["max_resolution"]
    ):
        logger.warning(
            f"Invalid max_resolution: {COMPRESSION_SETTINGS['max_resolution']}. Should be (width, height) with positive values"
        )
        is_valid = False

    if (
        COMPRESSION_SETTINGS["timeout_seconds"] < 30
        or COMPRESSION_SETTINGS["timeout_seconds"] > 3600
    ):
        logger.warning(
            f"Invalid timeout_seconds: {COMPRESSION_SETTINGS['timeout_seconds']}. Should be between 30-3600 seconds"
        )
        is_valid = False

    if COMPRESSION_SETTINGS["min_quality_crf"] < 0 or COMPRESSION_SETTINGS["min_quality_crf"] > 51:
        logger.warning(
            f"Invalid min_quality_crf: {COMPRESSION_SETTINGS['min_quality_crf']}. Should be between 0-51"
        )
        is_valid = False

    if COMPRESSION_SETTINGS["max_quality_crf"] < 0 or COMPRESSION_SETTINGS["max_quality_crf"] > 51:
        logger.warning(
            f"Invalid max_quality_crf: {COMPRESSION_SETTINGS['max_quality_crf']}. Should be between 0-51"
        )
        is_valid = False

    if COMPRESSION_SETTINGS["min_quality_crf"] >= COMPRESSION_SETTINGS["max_quality_crf"]:
        logger.warning(
            f"min_quality_crf ({COMPRESSION_SETTINGS['min_quality_crf']}) should be less than max_quality_crf ({COMPRESSION_SETTINGS['max_quality_crf']})"
        )
        is_valid = False

    if COMPRESSION_SETTINGS["disk_space_threshold_mb"] < 100:
        logger.warning(
            f"Invalid disk_space_threshold_mb: {COMPRESSION_SETTINGS['disk_space_threshold_mb']}. Should be at least 100MB"
        )
        is_valid = False

    if (
        COMPRESSION_SETTINGS["cleanup_temp_files_hours"] < 1
        or COMPRESSION_SETTINGS["cleanup_temp_files_hours"] > 168
    ):
        logger.warning(
            f"Invalid cleanup_temp_files_hours: {COMPRESSION_SETTINGS['cleanup_temp_files_hours']}. Should be between 1-168 hours"
        )
        is_valid = False

    if (
        COMPRESSION_SETTINGS["max_concurrent_compressions"] < 1
        or COMPRESSION_SETTINGS["max_concurrent_compressions"] > 10
    ):
        logger.warning(
            f"Invalid max_concurrent_compressions: {COMPRESSION_SETTINGS['max_concurrent_compressions']}. Should be between 1-10"
        )
        is_valid = False

    # Validate COMPRESSION_MONITORING
    if (
        COMPRESSION_MONITORING["metrics_retention_days"] < 1
        or COMPRESSION_MONITORING["metrics_retention_days"] > 365
    ):
        logger.warning(
            f"Invalid metrics_retention_days: {COMPRESSION_MONITORING['metrics_retention_days']}. Should be between 1-365 days"
        )
        is_valid = False

    if (
        COMPRESSION_MONITORING["disk_space_warning_threshold"] < 50.0
        or COMPRESSION_MONITORING["disk_space_warning_threshold"] > 99.0
    ):
        logger.warning(
            f"Invalid disk_space_warning_threshold: {COMPRESSION_MONITORING['disk_space_warning_threshold']}. Should be between 50.0-99.0 percent"
        )
        is_valid = False

    if (
        COMPRESSION_MONITORING["admin_notification_threshold_failures"] < 1
        or COMPRESSION_MONITORING["admin_notification_threshold_failures"] > 100
    ):
        logger.warning(
            f"Invalid admin_notification_threshold_failures: {COMPRESSION_MONITORING['admin_notification_threshold_failures']}. Should be between 1-100"
        )
        is_valid = False

    if (
        COMPRESSION_MONITORING["stats_log_interval_minutes"] < 1
        or COMPRESSION_MONITORING["stats_log_interval_minutes"] > 1440
    ):
        logger.warning(
            f"Invalid stats_log_interval_minutes: {COMPRESSION_MONITORING['stats_log_interval_minutes']}. Should be between 1-1440 minutes"
        )
        is_valid = False

    # Validate temp directory exists and is writable
    try:
        temp_dir = COMPRESSION_SETTINGS["temp_dir"]
        if not os.path.exists(temp_dir):
            os.makedirs(temp_dir, exist_ok=True)

        # Test write permissions
        test_file = os.path.join(temp_dir, ".config_test")
        with open(test_file, "w") as f:
            f.write("test")
        os.unlink(test_file)

    except Exception as e:
        logger.error(
            f"Cannot access or write to temp directory {COMPRESSION_SETTINGS['temp_dir']}: {str(e)}"
        )
        is_valid = False

    if is_valid:
        logger.info("Compression configuration validation passed")
    else:
        logger.error("Compression configuration validation failed - check warnings above")

    return is_valid


def get_compression_config():
    """
    Get validated compression configuration.

    Returns:
        dict: Combined compression settings and monitoring configuration
    """
    validate_compression_config()

    return {
        "settings": COMPRESSION_SETTINGS,
        "monitoring": COMPRESSION_MONITORING,
        "messages": COMPRESSION_MESSAGES,
    }
