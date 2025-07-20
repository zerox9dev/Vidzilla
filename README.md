# Vidzilla - Social Media Video Downloader Bot

![Vidzilla Cover](cover.png)

[![Python](https://img.shields.io/badge/Python-3.11+-blue.svg)](https://python.org)
[![License](https://img.shields.io/badge/License-MIT-green.svg)](LICENSE)
[![Telegram](https://img.shields.io/badge/Telegram-Bot-blue.svg)](https://telegram.org)
[![FFmpeg](https://img.shields.io/badge/FFmpeg-Required-red.svg)](https://ffmpeg.org)
[![MongoDB](https://img.shields.io/badge/MongoDB-Database-green.svg)](https://mongodb.com)
[![Docker](https://img.shields.io/badge/Docker-Ready-blue.svg)](https://docker.com)

[![Tests](https://img.shields.io/badge/Tests-Passing-brightgreen.svg)](#testing)
[![Platforms](https://img.shields.io/badge/Platforms-40+-orange.svg)](#supported-platforms)
[![Compression](https://img.shields.io/badge/Video-Compression-purple.svg)](#video-compression)
[![Monitoring](https://img.shields.io/badge/System-Monitoring-yellow.svg)](#monitoring--maintenance)

# 📋 Table of Contents
- [🚀 Quick Start](#-quick-start)
- [🎬 Supported Platforms](#-supported-platforms-40)
- [✨ Features](#-features)
- [📱 How to Use](#-how-to-use)
- [🤖 Bot Commands](#-bot-commands)
- [💡 Usage Examples](#-usage-examples)
- [❓ FAQ](#-faq)
- [🛠️ Technical Setup](#️-technical-setup)
- [🚀 Deployment Options](#-deployment-options)
- [📊 Architecture & Features](#-architecture--features)
- [🔍 Monitoring & Maintenance](#-monitoring--maintenance)
- [🧪 Testing](#-testing)
- [🤝 Contributing](#-contributing)

---

# 🌐 Language / Мова / Язык / 语言 / اللغة
- [English](#english)
- [Українська](#українська)
- [Русский](#русский)
- [中文](#中文)
- [العربية](#العربية)

<a name="english"></a>
# English

## 🚀 Quick Start

**Ready to use in 3 steps:**

1. **Get the bot**: Search `@YourBotUsername` on Telegram
2. **Send a link**: Paste any video URL from 40+ platforms
3. **Get your video**: Receive optimized video instantly!

```
Example: Send https://www.instagram.com/p/ABC123/
→ Bot downloads and compresses automatically
→ Receive as both video message and file
```

**For developers**: [Jump to Technical Setup](#️-technical-setup)

---

## 🎯 Download videos from any platform!

Vidzilla is a powerful Telegram bot that lets you easily download and share videos from popular social media platforms. Just send a link, and get your video instantly!

### 🎬 Supported Platforms (40+)

#### 🔥 Popular Social Media
- **Instagram** - Reels, Posts, Stories (Direct API)
- **TikTok** - All videos, trending content
- **YouTube** - Videos, Shorts, live streams
- **Facebook** - Videos, Reels, public posts
- **Twitter/X** - Videos, GIFs, embedded media

#### 📱 Social Networks
- **Snapchat** - Public stories and videos
- **LinkedIn** - Professional video content
- **Pinterest** - Video pins and stories
- **Reddit** - Video posts and comments
- **Tumblr** - Video posts and GIFs

#### 🎥 Video Platforms
- **Vimeo** - All video content
- **Dailymotion** - Public videos
- **Bilibili** - Chinese video platform
- **Rumble** - Alternative video platform
- **Streamable** - Short video clips

#### 🌐 International Platforms
- **Telegram** - Public channel videos
- **Kuaishou/Kwai** - Chinese short videos
- **Douyin** - Chinese TikTok
- **Xiaohongshu** - Chinese lifestyle platform
- **Weibo** - Chinese social media

#### 📺 Media & News
- **ESPN** - Sports highlights
- **TED** - Educational talks
- **IMDB** - Movie trailers and clips
- **9GAG** - Viral video content

#### 🔧 Technical Features
- **Smart Detection** - Automatic platform recognition
- **Quality Options** - Multiple resolution downloads
- **Batch Processing** - Handle multiple links
- **Format Support** - MP4, MOV, AVI, WebM, and more
- **Size Optimization** - Intelligent compression for Telegram limits

> 💡 **Tip**: Use `/help` command in the bot to see the complete list and test platform compatibility!

### ✨ Features

- **Simple to Use** - Just send a link, get your video!
- **Fast Downloads** - Videos delivered in seconds
- **Free to Use** - With optional $1 donation to support our servers
- **Multiple Formats** - Receive videos as both playable messages and downloadable files
- **Admin Tools** - Stats tracking, coupon generation, and broadcast messaging

## 📱 How to Use

1. **Start the bot**: Send `/start` to begin
2. **Check supported platforms**: Send `/help` to see all supported platforms
3. **Send a link**: Paste any supported video URL
4. **Get your video**: Receive the video as both a playable message and a downloadable file
5. **Support us**: Use `/donate` if you find the bot useful

## 🤖 Bot Commands

### 👤 User Commands
- `/start` - Initialize bot and see welcome message
- `/help` - View supported platforms and usage guide
- `/donate` - Support the project (optional $1 donation)
- `/activate_coupon` - Redeem coupon codes

### 🔧 Admin Commands
- `/stats` - Comprehensive usage analytics
- `/language_stats` - User language distribution
- `/generate_coupon` - Create new coupon codes
- `/list_users` - View users with usernames
- `/broadcast` - Send message to all users
- `/restart_notification` - Notify users of bot updates

## 💡 Usage Examples

### Basic Video Download
```
1. Send any supported video URL to the bot
2. Bot automatically detects platform
3. Receive video as both playable message and downloadable file
4. Large videos are automatically compressed for Telegram
```

### Supported URL Formats
```
✅ https://www.instagram.com/p/ABC123/
✅ https://www.tiktok.com/@user/video/123456
✅ https://www.youtube.com/watch?v=ABC123
✅ https://twitter.com/user/status/123456
✅ https://www.facebook.com/watch/?v=123456
✅ And 35+ more platforms!
```

### Advanced Features
- **Smart Compression**: Videos >50MB automatically optimized
- **Progress Updates**: Real-time download and compression status
- **Fallback Delivery**: Multiple delivery methods if primary fails
- **Error Recovery**: Detailed troubleshooting for failed downloads

## ❓ FAQ

### General Usage

**Q: Is the bot free to use?**
A: Yes! The bot is completely free. Optional $1 donations help support server costs.

**Q: What's the maximum video size?**
A: No strict limit, but videos >50MB are automatically compressed for Telegram compatibility.

**Q: How long does processing take?**
A: Usually 5-30 seconds depending on video size and compression needs.

**Q: Can I download private videos?**
A: No, only publicly accessible content can be downloaded.

### Technical Questions

**Q: Why do some videos come as documents?**
A: Large videos or those that can't be compressed are sent as documents to ensure delivery.

**Q: What video formats are supported?**
A: MP4, MOV, AVI, WebM, MKV, and most common formats.

**Q: Can I download playlists?**
A: Currently, only individual videos are supported.

### Troubleshooting

**Q: Bot says "platform not supported"?**
A: Check `/help` for the latest platform list, or the platform may have changed their API.

**Q: Download failed with error?**
A: Try again in a few minutes. If persistent, the video may be private or deleted.

**Q: Video quality is poor after compression?**
A: This ensures Telegram compatibility. Original quality is preserved in document format.

## 🛠️ Technical Setup

### Prerequisites

- **Python 3.11+** - Required for async features
- **MongoDB** - Database for user data and statistics
- **FFmpeg** - Video processing and compression
- **Telegram Bot Token** - From @BotFather
- **RapidAPI Key** - For multi-platform video downloading
- **Stripe Account** - Optional, for donation processing

### Quick Installation

1. **Clone and setup:**
   ```bash
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   python -m venv .myebv
   source .myebv/bin/activate  # Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Install FFmpeg:**
   ```bash
   # macOS
   brew install ffmpeg
   
   # Ubuntu/Debian
   sudo apt update && sudo apt install ffmpeg
   
   # Windows
   # Download from https://ffmpeg.org/download.html
   ```

3. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your credentials
   ```
   
   ⚠️ **SECURITY WARNING**: Never commit `.env` file to version control! It contains sensitive credentials.

4. **Create directories and run:**
   ```bash
   mkdir -p temp_videos/compression
   python bot.py
   ```

### 🔧 Configuration

#### Required Environment Variables
```env
# Bot essentials
BOT_TOKEN=your_telegram_bot_token
RAPIDAPI_KEY=your_rapidapi_key
MONGODB_URI=your_mongodb_connection_string
ADMIN_IDS=your_telegram_user_id

# Bot identity
BOT_USERNAME=your_bot_username
WEBHOOK_URL=your_webhook_url  # For production
```

#### Video Compression Settings
```env
# Compression behavior
COMPRESSION_TARGET_SIZE_MB=45          # Target file size
COMPRESSION_MAX_ATTEMPTS=3             # Retry attempts
COMPRESSION_QUALITY_LEVELS=28,32,36    # CRF quality levels
COMPRESSION_TIMEOUT_SECONDS=300        # Max processing time
COMPRESSION_MAX_CONCURRENT=2           # Parallel compressions

# Performance tuning
COMPRESSION_FFMPEG_PRESET=medium       # fast/medium/slow
COMPRESSION_ENABLE_HARDWARE_ACCEL=false
COMPRESSION_MAX_RESOLUTION=1280,720    # Downscale if needed
```

#### Monitoring & Logging
```env
# System monitoring
COMPRESSION_ENABLE_DETAILED_LOGGING=true
COMPRESSION_LOG_LEVEL=INFO
COMPRESSION_ENABLE_PERFORMANCE_METRICS=true
COMPRESSION_METRICS_RETENTION_DAYS=30

# Disk management
COMPRESSION_DISK_SPACE_THRESHOLD_MB=1000
COMPRESSION_CLEANUP_TEMP_FILES_HOURS=24
COMPRESSION_ENABLE_DISK_MONITORING=true
```

### 🚀 Deployment Options

#### Development (Local)
```bash
# Using ngrok for webhook testing
ngrok http 8000
# Update WEBHOOK_URL in .env with ngrok URL
python bot.py
```

#### Production (Docker)
```dockerfile
FROM python:3.11-slim
RUN apt-get update && apt-get install -y ffmpeg
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "bot.py"]
```

```bash
docker build -t vidzilla .
docker run -d --env-file .env -p 8000:8000 vidzilla
```

#### Production (systemd)
```ini
# /etc/systemd/system/vidzilla.service
[Unit]
Description=Vidzilla Video Downloader Bot
After=network.target

[Service]
Type=simple
User=vidzilla
WorkingDirectory=/opt/vidzilla
Environment=PATH=/opt/vidzilla/.myebv/bin
ExecStart=/opt/vidzilla/.myebv/bin/python bot.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 📊 Architecture & Features

#### Core Components
- **Video Compression Engine** - Intelligent size optimization with FFmpeg
- **Multi-Platform Support** - 40+ platforms via RapidAPI + Instagram direct
- **Progress Tracking** - Real-time compression and download progress
- **Admin Dashboard** - Statistics, user management, broadcast messaging
- **Monitoring System** - Performance metrics, error tracking, disk usage

#### Advanced Features
- **Progressive Compression** - Multiple quality attempts for optimal size
- **Fallback Delivery** - Video → Document → Link → Error with troubleshooting
- **Resource Management** - Automatic cleanup, concurrent limits, disk monitoring
- **User Analytics** - Download tracking, language preferences, platform usage
- **Error Recovery** - Comprehensive error handling with user-friendly messages

#### Performance Optimizations
- **Async Processing** - Non-blocking video operations
- **Smart Caching** - Temporary file management with automatic cleanup
- **Memory Efficiency** - Streaming downloads, chunked processing
- **Concurrent Limits** - Prevents system overload
- **Hardware Acceleration** - Optional GPU encoding support

### 🔍 Monitoring & Maintenance

#### Health Checks
```bash
# View compression logs
tail -f temp_videos/compression.log

# Check system metrics
# Use admin commands: /stats, /language_stats

# Test compression system
python -m pytest tests/test_video_compression.py -v
```

#### Common Issues & Solutions

**FFmpeg not found:**
```bash
which ffmpeg  # Should return path
# If not found, reinstall FFmpeg
```

**MongoDB connection issues:**
```bash
# Test connection
python -c "from pymongo import MongoClient; print(MongoClient('your_uri').admin.command('ping'))"
```

**High disk usage:**
```bash
# Check temp directory
du -sh temp_videos/
# Cleanup old files
find temp_videos/ -type f -mtime +1 -delete
```

**Memory issues:**
```bash
# Reduce concurrent compressions
COMPRESSION_MAX_CONCURRENT=1

# Lower quality settings
COMPRESSION_QUALITY_LEVELS=32,36,40
```

### 📦 Dependencies

#### Core Framework
- **aiogram 3.20.0** - Modern async Telegram Bot API
- **aiohttp 3.11.18** - Async HTTP client/server
- **pymongo 4.13.0** - MongoDB driver with async support

#### Video Processing
- **ffmpeg-python 0.2.0** - Python FFmpeg wrapper
- **opencv-python** - Video analysis and processing
- **instaloader 4.14.1** - Instagram direct downloads

#### Utilities
- **python-dotenv 1.1.0** - Environment management
- **stripe 12.1.0** - Payment processing
- **aiofiles 24.1.0** - Async file operations
- **psutil** - System monitoring

### 🧪 Testing

```bash
# Run all tests
python -m pytest tests/ -v

# Test specific components
python -m pytest tests/test_video_compression.py -v
python -m pytest tests/test_compression_config.py -v

# Test with coverage
python -m pytest tests/ --cov=utils --cov=handlers
```

### 📈 Scaling Considerations

#### High Traffic Deployment
- **Load Balancing** - Multiple bot instances behind nginx
- **Database Optimization** - MongoDB replica sets, indexing
- **CDN Integration** - Static asset delivery
- **Caching Layer** - Redis for frequently accessed data
- **Queue System** - Celery for background processing

#### Resource Planning
- **CPU**: 2+ cores recommended for compression
- **RAM**: 4GB+ for concurrent operations  
- **Storage**: 10GB+ for temporary files
- **Network**: High bandwidth for video downloads

---

<a name="українська"></a>
# Українська

## 🚀 Завантажуйте відео з будь-якої платформи!

Vidzilla - це потужний Telegram-бот, який дозволяє легко завантажувати та ділитися відео з популярних соціальних мереж. Просто надішліть посилання і отримайте відео миттєво!

### 🎬 Підтримувані платформи

Vidzilla тепер підтримує понад 40 платформ, включаючи:

- **Instagram** - Reels та публікації
- **TikTok** - Усі відео
- **YouTube** - Відео та Shorts
- **Facebook** - Відео та Reels
- **Twitter/X** - Відео та GIF
- **Pinterest** - Відео-піни
- **Reddit** - Відео
- **Snapchat** - Відео
- **LinkedIn** - Відео
- **Vimeo** - Відео
- **Telegram** - Відео з публічних каналів
- **Bilibili** - Відео
- **Tumblr** - Відео
- **І багато інших!** - Використовуйте команду `/help`, щоб побачити повний список

### ✨ Функції

- **Простота використання** - Просто надішліть посилання, отримайте відео!
- **Швидке завантаження** - Відео доставляються за секунди
- **Безкоштовно** - З можливістю пожертвувати $1 для підтримки наших серверів
- **Кілька форматів** - Отримуйте відео як повідомлення для перегляду та як файли для завантаження
- **Інструменти адміністратора** - Відстеження статистики, генерація купонів та розсилка повідомлень

## 📱 Як користуватися

1. **Запустіть бота**: Надішліть `/start` для початку
2. **Перевірте підтримувані платформи**: Надішліть `/help`, щоб побачити всі підтримувані платформи
3. **Надішліть посилання**: Вставте будь-яке підтримуване відео URL
4. **Отримайте відео**: Отримайте відео як повідомлення для перегляду та як файл для завантаження
5. **Підтримайте нас**: Використовуйте `/donate`, якщо бот вам корисний

## 🤖 Команди бота

- `/start` - Запустити бота та отримати інструкції з використання
- `/help` - Переглянути всі підтримувані платформи та інструкції з використання
- `/donate` - Підтримати проект невеликим пожертвуванням
- `/activate_coupon` - Активувати купон (якщо він у вас є)

### Команди адміністратора

- `/stats` - Переглянути статистику використання
- `/generate_coupon` - Згенерувати новий код купона
- `/list_users` - Список користувачів з іменами користувачів
- `/broadcast` - Надіслати повідомлення всім користувачам

## 🛠️ Технічне налаштування

### Передумови

- Python 3.11+
- База даних MongoDB
- Токен бота Telegram
- Ключ RapidAPI (для TikTok, YouTube, Facebook, Twitter, Pinterest)
- Обліковий запис Stripe (для пожертвувань)

### Встановлення

1. Клонуйте цей репозиторій:
   ```
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. Створіть віртуальне середовище та встановіть залежності:
   ```
   python -m venv .myebv
   source .myebv/bin/activate  # На Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Створіть файл `.env` з наступними змінними:
   ```
   # Конфігурація бота
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url
   BOT_USERNAME=your_bot_username

   # Конфігурація MongoDB
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # Конфігурація адміністратора
   ADMIN_IDS=your_admin_telegram_id

   # Конфігурація Stripe
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. Створіть тимчасовий каталог для завантажених відео:
   ```
   mkdir temp_videos
   ```

5. Запустіть бота:
   ```
   python bot.py
   ```

## 🌐 Налаштування вебхука

Для розгортання у виробництві налаштуйте вебхук:

1. Отримайте домен із SSL-сертифікатом або використовуйте ngrok для розробки:
   ```
   ngrok http 8000
   ```

2. Оновіть файл `.env` з URL вебхука.

## 📦 Залежності

- `aiogram` - Сучасний та повністю асинхронний фреймворк для Telegram Bot API
- `aiohttp` - Асинхронний HTTP-клієнт/сервер
- `python-dotenv` - Управління змінними середовища
- `pymongo` - Драйвер MongoDB
- `requests` - Бібліотека HTTP-запитів
- `instaloader` - Завантажувач контенту Instagram
- `stripe` - Обробка платежів

## 📊 Деталі реалізації

- **Instagram**: Використовує бібліотеку Instaloader для прямих завантажень
- **Інші платформи**: Використовує API "auto-download-all-in-one" від RapidAPI
- **База даних**: MongoDB для даних користувачів та управління купонами
- **Платежі**: Stripe для обробки пожертвувань

---

<a name="русский"></a>
# Русский

## 🚀 Скачивайте видео с любой платформы!

Vidzilla - это мощный Telegram-бот, который позволяет легко скачивать и делиться видео из популярных социальных сетей. Просто отправьте ссылку и получите видео мгновенно!

### 🎬 Поддерживаемые платформы

Vidzilla теперь поддерживает более 40 платформ, включая:

- **Instagram** - Reels и публикации
- **TikTok** - Все видео
- **YouTube** - Видео и Shorts
- **Facebook** - Видео и Reels
- **Twitter/X** - Видео и GIF
- **Pinterest** - Видео-пины
- **Reddit** - Видео
- **Snapchat** - Видео
- **LinkedIn** - Видео
- **Vimeo** - Видео
- **Telegram** - Видео из публичных каналов
- **Bilibili** - Видео
- **Tumblr** - Видео
- **И многие другие!** - Используйте команду `/help`, чтобы увидеть полный список

### ✨ Функции

- **Простота использования** - Просто отправьте ссылку, получите видео!
- **Быстрая загрузка** - Видео доставляются за секунды
- **Бесплатно** - С возможностью пожертвовать $1 для поддержки наших серверов
- **Несколько форматов** - Получайте видео как сообщение для просмотра и как файл для загрузки
- **Инструменты администратора** - Отслеживание статистики, генерация купонов и рассылка сообщений

## 📱 Как пользоваться

1. **Запустите бота**: Отправьте `/start` для начала
2. **Проверьте поддерживаемые платформы**: Отправьте `/help`, чтобы увидеть все поддерживаемые платформы
3. **Отправьте ссылку**: Вставьте любой поддерживаемый видео URL
4. **Получите видео**: Получите видео как сообщение для просмотра и как файл для загрузки
5. **Поддержите нас**: Используйте `/donate`, если бот вам полезен

## 🤖 Команды бота

- `/start` - Запустить бота и получить инструкции по использованию
- `/help` - Просмотреть все поддерживаемые платформы и инструкции по использованию
- `/donate` - Поддержать проект небольшим пожертвованием
- `/activate_coupon` - Активировать купон (если он у вас есть)

### Команды адміністратора

- `/stats` - Переглянути статистику використання
- `/generate_coupon` - Згенерувати новий код купона
- `/list_users` - Список користувачів з іменами користувачів
- `/broadcast` - Надіслати повідомлення всім користувачам

## 🛠️ Технічне налаштування

### Передумови

- Python 3.11+
- База даних MongoDB
- Токен бота Telegram
- Ключ RapidAPI (для TikTok, YouTube, Facebook, Twitter, Pinterest)
- Обліковий запис Stripe (для пожертвувань)

### Встановлення

1. Клонуйте цей репозиторій:
   ```
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. Створіть віртуальне середовище та встановіть залежності:
   ```
   python -m venv .myebv
   source .myebv/bin/activate  # На Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Створіть файл `.env` з наступними змінними:
   ```
   # Конфігурація бота
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url
   BOT_USERNAME=your_bot_username

   # Конфігурація MongoDB
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # Конфігурація адміністратора
   ADMIN_IDS=your_admin_telegram_id

   # Конфігурація Stripe
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. Створіть тимчасовий каталог для завантажених відео:
   ```
   mkdir temp_videos
   ```

5. Запустіть бота:
   ```
   python bot.py
   ```

## 🌐 Налаштування вебхука

Для розгортання у виробництві налаштуйте вебхук:

1. Отримайте домен із SSL-сертифікатом або використовуйте ngrok для розробки:
   ```
   ngrok http 8000
   ```

2. Оновіть файл `.env` з URL вебхука.

## 📦 Залежності

- `aiogram` - Сучасний та повністю асинхронний фреймворк для Telegram Bot API
- `aiohttp` - Асинхронний HTTP-клієнт/сервер
- `python-dotenv` - Управління змінними середовища
- `pymongo` - Драйвер MongoDB
- `requests` - Бібліотека HTTP-запитів
- `instaloader` - Завантажувач контенту Instagram
- `stripe` - Обробка платежів

## 📊 Деталі реалізації

- **Instagram**: Використовує бібліотеку Instaloader для прямих завантажень
- **Інші платформи**: Використовує API "auto-download-all-in-one" від RapidAPI
- **База даних**: MongoDB для даних користувачів та управління купонами
- **Платежі**: Stripe для обробки пожертвувань

---

<a name="中文"></a>
# 中文

## 🚀 从任何平台下载视频！

Vidzilla 是一个功能强大的 Telegram 机器人，可让您轻松下载和分享来自流行社交媒体平台的视频。只需发送链接，立即获取您的视频！

### 🎬 支持的平台

Vidzilla 现在支持超过 40 个平台，包括：

- **Instagram** - Reels 和帖子
- **TikTok** - 所有视频
- **YouTube** - 视频和 Shorts
- **Facebook** - 视频和 Reels
- **Twitter/X** - 视频和 GIF
- **Pinterest** - 视频 Pins
- **Reddit** - 视频
- **Snapchat** - 视频
- **LinkedIn** - 视频
- **Vimeo** - 视频
- **Telegram** - 公共频道视频
- **Bilibili** - 视频
- **Tumblr** - 视频
- **以及更多！** - 使用 `/help` 命令查看完整列表

### ✨ 特点

- **使用简单** - 只需发送链接，获取视频！
- **快速下载** - 视频几秒钟内送达
- **免费使用** - 可选择捐赠 $1 支持我们的服务器
- **多种格式** - 同时接收可播放消息和可下载文件形式的视频
- **管理工具** - 统计跟踪、优惠券生成和广播消息

## 📱 如何使用

1. **启动机器人**：发送 `/start` 开始
2. **查看支持的平台**：发送 `/help` 查看所有支持的平台
3. **发送链接**：粘贴任何支持的视频 URL
4. **获取视频**：同时接收可播放消息和可下载文件形式的视频
5. **支持我们**：如果觉得机器人有用，请使用 `/donate`

## 🤖 机器人命令

- `/start` - 启动机器人并获取使用说明
- `/help` - 查看所有支持的平台和使用说明
- `/donate` - 通过小额捐款支持项目
- `/activate_coupon` - 激活优惠券代码（如果您有）

## 🤖 机器人命令

- `/start` - 启动机器人并获取使用说明
- `/help` - 查看所有支持的平台和使用说明
- `/donate` - 通过小额捐款支持项目
- `/activate_coupon` - 激活优惠券代码（如果您有）

### 管理工具

- `/stats` - 查看使用统计
- `/generate_coupon` - 生成新的优惠券代码
- `/list_users` - 列出用户名用户
- `/broadcast` - 向所有用户发送消息

## 🛠️ 技术设置

### 先决条件

- Python 3.11+
- MongoDB 数据库
- Telegram 机器人令牌
- RapidAPI 密钥（用于 TikTok、YouTube、Facebook、Twitter、Pinterest）
- Stripe 账户（用于捐款）

### 安装

1. 克隆这个仓库：
   ```
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. 创建虚拟环境并安装依赖项：
   ```
   python -m venv .myebv
   source .myebv/bin/activate  # 在 Windows 上：.myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. 创建一个包含以下变量的 `.env` 文件：
   ```
   # 机器人配置
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url
   BOT_USERNAME=your_bot_username

   # MongoDB 配置
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # 管理员配置
   ADMIN_IDS=your_admin_telegram_id

   # Stripe 配置
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. 创建下载的视频临时目录：
   ```
   mkdir temp_videos
   ```

5. 运行机器人：
   ```
   python bot.py
   ```

## 🌐 Webhook 设置

对于生产部署，设置 webhook：

1. 获取带有 SSL 证书的域名或使用 ngrok 进行开发：
   ```
   ngrok http 8000
   ```

2. 更新 `.env` 文件中的 webhook URL。

## 📦 依赖项

- `aiogram` - 现代且完全异步的 Telegram Bot API 框架
- `aiohttp` - 异步 HTTP 客户端/服务器
- `python-dotenv` - 环境变量管理
- `pymongo` - MongoDB 驱动程序
- `requests` - HTTP 请求库
- `instaloader` - Instagram 内容下载器
- `stripe` - 付款处理

## 📊 实现细节

- **Instagram**：使用 Instaloader 库进行直接下载
- **其他平台**：使用 RapidAPI 的 "auto-download-all-in-one" API
- **数据库**：MongoDB 用于用户数据和优惠券管理
- **付款**：Stripe 用于捐款处理

---

<a name="العربية"></a>
# العربية

## 🚀 قم بتنزيل مقاطع الفيديو من أي منصة!

Vidzilla هو روبوت تيليجرام قوي يتيح لك تنزيل ومشاركة مقاطع الفيديو من منصات التواصل الاجتماعي الشهيرة بسهولة. ما عليك سوى إرسال رابط، واحصل على الفيديو الخاص بك على الفور!

### 🎬 المنصات المدعومة

يدعم Vidzilla الآن أكثر من 40 منصة، بما في ذلك:

- **Instagram** - Reels والمنشورات
- **TikTok** - جميع مقاطع الفيديو
- **YouTube** - الفيديوهات والمقاطع القصيرة
- **Facebook** - الفيديوهات والمقاطع القصيرة
- **Twitter/X** - الفيديوهات وملفات GIF
- **Pinterest** - مقاطع الفيديو
- **Reddit** - الفيديوهات
- **Snapchat** - الفيديوهات
- **LinkedIn** - الفيديوهات
- **Vimeo** - الفيديوهات
- **Telegram** - فيديوهات القنوات العامة
- **Bilibili** - الفيديوهات
- **Tumblr** - الفيديوهات
- **والكثير غيرها!** - استخدم الأمر `/help` لمشاهدة القائمة الكاملة

### ✨ الميزات

- **سهل الاستخدام** - فقط أرسل رابطًا، واحصل على الفيديو!
- **تنزيلات سريعة** - يتم تسليم مقاطع الفيديو في ثوانٍ
- **مجاني للاستخدام** - مع تبرع اختياري بقيمة دولار واحد لدعم خوادمنا
- **تنسيقات متعددة** - استلم مقاطع الفيديو كرسائل قابلة للتشغيل وملفات قابلة للتنزيل
- **أدوات المسؤول** - تتبع الإحصائيات، وإنشاء الكوبونات، ورسائل البث

## 📱 كيفية الاستخدام

1. **ابدأ الروبوت**: أرسل `/start` للبدء
2. **تحقق من المنصات المدعومة**: أرسل `/help` لمشاهدة جميع المنصات المدعومة
3. **أرسل رابطًا**: الصق أي عنوان URL لفيديو مدعوم
4. **احصل على الفيديو الخاص بك**: استلم الفيديو كرسالة قابلة للتشغيل وكملف قابل للتنزيل
5. **ادعمنا**: استخدم `/donate` إذا وجدت الروبوت مفيدًا

## 🤖 أوامر الروبوت

- `/start` - بدء تشغيل الروبوت والحصول على تعليمات الاستخدام
- `/help` - عرض جميع المنصات المدعومة وتعليمات الاستخدام
- `/donate` - دعم المشروع بتبرع صغير
- `/activate_coupon` - تفعيل رمز الكوبون (إذا كان لديك)

### أدوات المسؤول

- `/stats` - عرض إحصائيات الاستخدام
- `/generate_coupon` - إنشاء رمز كوبون جديد
- `/list_users` - قائمة بأسماء المستخدمين
- `/broadcast` - إرسال رسالة إلى جميع المستخدمين

---

## 🤝 Contributing

We welcome contributions! Here's how you can help:

### 🐛 Bug Reports
- Use GitHub Issues with detailed error logs
- Include steps to reproduce the problem
- Mention your system info (OS, Python version)

### 💡 Feature Requests
- Check existing issues first
- Describe the use case and expected behavior
- Consider implementation complexity

### 🔧 Code Contributions
```bash
# Development setup
git clone https://github.com/yourusername/vidzilla.git
cd vidzilla
python -m venv .myebv
source .myebv/bin/activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # If exists

# Run tests before submitting
python -m pytest tests/ -v
```

### 📝 Documentation
- Improve README sections
- Add code comments
- Update configuration examples
- Translate to other languages

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

### Third-Party Licenses
- **FFmpeg** - LGPL/GPL (depending on build)
- **Instaloader** - MIT License
- **aiogram** - MIT License
- **MongoDB** - Server Side Public License

## 🙏 Acknowledgments

- **Telegram Bot API** - For the excellent bot platform
- **RapidAPI** - For multi-platform video download APIs
- **FFmpeg Team** - For the powerful video processing library
- **Open Source Community** - For the amazing Python libraries

## 📞 Support

### 🆘 Need Help?
1. **Check FAQ** above for common issues
2. **Search Issues** on GitHub
3. **Create New Issue** with detailed information
4. **Join Discussion** in GitHub Discussions

### 📊 Project Stats
- **40+ Platforms** supported
- **Advanced Compression** with FFmpeg
- **Real-time Monitoring** and analytics
- **Production Ready** with Docker support

### 🔗 Links
- **GitHub Repository**: [Vidzilla](https://github.com/yourusername/vidzilla)
- **Issues & Bug Reports**: [GitHub Issues](https://github.com/yourusername/vidzilla/issues)
- **Feature Requests**: [GitHub Discussions](https://github.com/yourusername/vidzilla/discussions)

---

**Made with ❤️ by the Vidzilla Team**

*Star ⭐ this repo if you find it useful!*