# 🛠️ Installation Guide / Руководство по установке

Полное руководство по установке и настройке Vidzilla для разработчиков.

## 📋 Prerequisites / Предварительные требования

### System Requirements / Системные требования
- **Python 3.11+** (рекомендуется 3.11.13)
- **FFmpeg** (для обработки видео)
- **MongoDB** (база данных)
- **Git** (для клонирования репозитория)
- **4GB RAM** (минимум), 8GB+ (рекомендуется)
- **10GB** свободного места на диске

### External Services / Внешние сервисы
- **Telegram Bot Token** (от @BotFather)
- **RapidAPI Key** (для некоторых платформ)
- **MongoDB Atlas** или локальная установка
- **Stripe Account** (для платежей, опционально)

## 🚀 Quick Installation / Быстрая установка

### 1. Clone Repository / Клонирование репозитория

```bash
# Clone the repository
git clone https://github.com/mirvald-space/Vidzilla.git
cd Vidzilla

# Or clone from alternative source
git clone https://github.com/MauriceWirthApps/TelegramSocialMediaVideoDownloader.git
cd TelegramSocialMediaVideoDownloader
```

### 2. Python Environment / Окружение Python

```bash
# Create virtual environment
python3 -m venv .myebv
source .myebv/bin/activate  # Linux/Mac
# .myebv\Scripts\activate   # Windows

# Upgrade pip
pip install --upgrade pip

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt  # For development
```

### 3. Install FFmpeg / Установка FFmpeg

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install ffmpeg
```

#### macOS
```bash
# Using Homebrew
brew install ffmpeg

# Using MacPorts
sudo port install ffmpeg
```

#### Windows
```bash
# Using Chocolatey
choco install ffmpeg

# Or download from https://ffmpeg.org/download.html
```

#### Verify Installation / Проверка установки
```bash
ffmpeg -version
```

### 4. MongoDB Setup / Настройка MongoDB

#### Option A: MongoDB Atlas (Cloud) / Облачная версия
1. Создайте аккаунт на [MongoDB Atlas](https://www.mongodb.com/atlas)
2. Создайте новый кластер
3. Получите строку подключения
4. Добавьте IP-адрес в whitelist

#### Option B: Local MongoDB / Локальная установка
```bash
# Ubuntu/Debian
sudo apt install mongodb

# macOS
brew install mongodb-community

# Start MongoDB
sudo systemctl start mongodb  # Linux
brew services start mongodb-community  # macOS
```

### 5. Environment Configuration / Конфигурация окружения

```bash
# Copy environment template
cp .env.example .env

# Edit configuration
nano .env  # or your preferred editor
```

#### Required Environment Variables / Обязательные переменные
```env
# Bot Configuration
BOT_TOKEN=your_telegram_bot_token_here
BOT_USERNAME=@your_bot_username

# Database
MONGODB_URI=mongodb+srv://username:password@cluster.mongodb.net/?retryWrites=true&w=majority
MONGODB_DB_NAME=video_downloader_bot

# API Keys
RAPIDAPI_KEY=your_rapidapi_key_here

# Admin Settings
ADMIN_IDS=123456789,987654321
FREE_LIMIT=3
```

### 6. Create Directories / Создание директорий

```bash
# Create required directories
mkdir -p temp_videos/compression
mkdir -p logs
mkdir -p ssl  # If using HTTPS webhooks
```

### 7. Run the Bot / Запуск бота

```bash
# Development mode
python bot.py

# With logging
python bot.py 2>&1 | tee logs/bot.log

# Background mode
nohup python bot.py > logs/bot.log 2>&1 &
```



## ⚙️ Advanced Configuration / Расширенная конфигурация

### Video Compression Settings / Настройки сжатия видео
```env
# Compression Configuration
COMPRESSION_TARGET_SIZE_MB=45
COMPRESSION_MAX_ATTEMPTS=3
COMPRESSION_QUALITY_LEVELS=28,32,36
COMPRESSION_TIMEOUT_SECONDS=300
COMPRESSION_MAX_CONCURRENT=2

# Performance Tuning
COMPRESSION_FFMPEG_PRESET=medium
COMPRESSION_ENABLE_HARDWARE_ACCEL=false
COMPRESSION_MAX_RESOLUTION=1280,720
```

### Monitoring Settings / Настройки мониторинга
```env
# Monitoring Configuration
MONITORING_ENABLED=true
MONITORING_CLEANUP_INTERVAL_HOURS=24
MONITORING_MAX_LOG_SIZE_MB=100
MONITORING_DISK_SPACE_WARNING_THRESHOLD=85
```

### Webhook Configuration / Настройка вебхуков
```env
# Webhook Settings (Production)
WEBHOOK_URL=https://your-domain.com/webhook
WEBHOOK_PATH=/webhook
WEBHOOK_PORT=8443

# SSL Certificate (if using HTTPS)
WEBHOOK_SSL_CERT=ssl/cert.pem
WEBHOOK_SSL_PRIV=ssl/private.key
```

## 🧪 Development Setup / Настройка для разработки

### Install Development Dependencies / Установка зависимостей для разработки
```bash
pip install -r requirements-dev.txt
```

### Pre-commit Hooks / Хуки pre-commit
```bash
# Install pre-commit
pip install pre-commit

# Install hooks
pre-commit install

# Run hooks manually
pre-commit run --all-files
```

### Testing / Тестирование
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=utils --cov=handlers --cov-report=html

# Run specific test file
pytest tests/test_video_compression.py -v
```

### Code Quality / Качество кода
```bash
# Format code
black --line-length=100 .
isort --profile black --line-length=100 .

# Lint code
flake8 --max-line-length=100 .
mypy .

# Security check
bandit -r . -f json -o bandit-report.json
```

## 🚀 Production Deployment / Развертывание в продакшене

### Systemd Service / Сервис systemd
```bash
# Create service file
sudo nano /etc/systemd/system/vidzilla.service
```

```ini
[Unit]
Description=Vidzilla Telegram Bot
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

```bash
# Enable and start service
sudo systemctl enable vidzilla
sudo systemctl start vidzilla
sudo systemctl status vidzilla
```

### Nginx Reverse Proxy / Обратный прокси Nginx
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/private.key;

    location /webhook {
        proxy_pass http://localhost:8443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

## 🔧 Troubleshooting / Решение проблем

### Common Issues / Частые проблемы

#### FFmpeg not found / FFmpeg не найден
```bash
# Check FFmpeg installation
which ffmpeg
ffmpeg -version

# Add to PATH if needed
export PATH=$PATH:/usr/local/bin
```

#### MongoDB connection issues / Проблемы с подключением к MongoDB
```bash
# Test connection
python -c "
import pymongo
client = pymongo.MongoClient('your_mongodb_uri')
print(client.server_info())
"
```

#### Permission errors / Ошибки прав доступа
```bash
# Fix permissions
chmod +x bot.py
chown -R $USER:$USER temp_videos/
```

### Log Analysis / Анализ логов
```bash
# View recent logs
tail -f logs/bot.log

# Search for errors
grep -i error logs/bot.log

# Monitor compression logs
tail -f compression.log
```

## 📊 Performance Optimization / Оптимизация производительности

### System Tuning / Настройка системы
```bash
# Increase file descriptor limits
echo "* soft nofile 65536" >> /etc/security/limits.conf
echo "* hard nofile 65536" >> /etc/security/limits.conf

# Optimize for video processing
echo "vm.swappiness=10" >> /etc/sysctl.conf
```

### Database Optimization / Оптимизация базы данных
```javascript
// MongoDB indexes
db.users.createIndex({ "user_id": 1 })
db.users.createIndex({ "created_at": 1 })
db.coupons.createIndex({ "code": 1 }, { unique: true })
```

## 🔗 Next Steps / Следующие шаги

- [🏗️ Architecture Overview](Architecture-Overview) - Архитектура проекта
- [🧪 Testing Guide](Testing-Guide) - Руководство по тестированию
- [🚀 Deployment Guide](Deployment-Guide) - Развертывание
- [⚙️ Configuration](Configuration) - Детальная конфигурация
