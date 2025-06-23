# Vidzilla - Social Media Video Downloader Bot

![Vidzilla Cover](cover.png)

# 🌐 Language / Мова / Язык
- [English](#english)
- [Українська](#українська)
- [Русский](#русский)

<a name="english"></a>
# English

## 🚀 Download videos from any platform!

Vidzilla is a powerful Telegram bot that lets you easily download and share videos from popular social media platforms. Just send a link, and get your video instantly!

### 🎬 Supported Platforms

Vidzilla now supports over 40 platforms, including:

- **Instagram** - Reels and Posts
- **TikTok** - All videos
- **YouTube** - Videos and Shorts
- **Facebook** - Videos and Reels
- **Twitter/X** - Videos and GIFs
- **Pinterest** - Video Pins
- **Reddit** - Videos
- **Snapchat** - Videos
- **LinkedIn** - Videos
- **Vimeo** - Videos
- **Telegram** - Public channel videos
- **Bilibili** - Videos
- **Tumblr** - Videos
- **And many more!** - Use `/help` command to see the full list

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

- `/start` - Start the bot and get usage instructions
- `/help` - View all supported platforms and usage instructions
- `/donate` - Support the project with a small donation
- `/activate_coupon` - Activate a coupon code (if you have one)

### Admin Commands

- `/stats` - View usage statistics
- `/generate_coupon` - Generate a new coupon code
- `/list_users` - List users with usernames
- `/broadcast` - Send a message to all users

## 🛠️ Technical Setup

### Prerequisites

- Python 3.11+
- MongoDB database
- Telegram Bot Token
- RapidAPI Key (for TikTok, YouTube, Facebook, Twitter, Pinterest)
- Stripe account (for donations)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. Create a virtual environment and install dependencies:
   ```
   python -m venv .myebv
   source .myebv/bin/activate  # On Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file with the following variables:
   ```
   # Bot configuration
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url
   BOT_USERNAME=your_bot_username

   # MongoDB configuration
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # Admin configuration
   ADMIN_IDS=your_admin_telegram_id

   # Stripe configuration
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. Create the temporary directory for downloaded videos:
   ```
   mkdir temp_videos
   ```

5. Run the bot:
   ```
   python bot.py
   ```

## 🌐 Webhook Setup

For production deployment, set up a webhook:

1. Get a domain with SSL certificate or use ngrok for development:
   ```
   ngrok http 8000
   ```

2. Update your `.env` file with the webhook URL.

## 📦 Dependencies

- `aiogram` - Modern and fully asynchronous Telegram Bot API framework
- `aiohttp` - Asynchronous HTTP client/server
- `python-dotenv` - Environment variable management
- `pymongo` - MongoDB driver
- `requests` - HTTP requests library
- `instaloader` - Instagram content downloader
- `stripe` - Payment processing

## 📊 Implementation Details

- **Instagram**: Uses Instaloader library for direct downloads
- **Other Platforms**: Uses RapidAPI's "auto-download-all-in-one" API
- **Database**: MongoDB for user data and coupon management
- **Payments**: Stripe for donation processing

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

### Команды администратора

- `/stats` - Просмотреть статистику использования
- `/generate_coupon` - Сгенерировать новый код купона
- `/list_users` - Список пользователей с именами пользователей
- `/broadcast` - Отправить сообщение всем пользователям

## 🛠️ Техническая настройка

### Предварительные требования

- Python 3.11+
- База данных MongoDB
- Токен бота Telegram
- Ключ RapidAPI (для TikTok, YouTube, Facebook, Twitter, Pinterest)
- Аккаунт Stripe (для пожертвований)

### Установка

1. Клонируйте этот репозиторий:
   ```
   git clone https://github.com/yourusername/vidzilla.git
   cd vidzilla
   ```

2. Создайте виртуальное окружение и установите зависимости:
   ```
   python -m venv .myebv
   source .myebv/bin/activate  # На Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Создайте файл `.env` со следующими переменными:
   ```
   # Конфигурация бота
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url
   BOT_USERNAME=your_bot_username

   # Конфигурация MongoDB
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # Конфигурация администратора
   ADMIN_IDS=your_admin_telegram_id

   # Конфигурация Stripe
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. Создайте временный каталог для загруженных видео:
   ```
   mkdir temp_videos
   ```

5. Запустите бота:
   ```
   python bot.py
   ```

## 🌐 Настройка вебхука

Для развертывания в производстве настройте вебхук:

1. Получите домен с SSL-сертификатом или используйте ngrok для разработки:
   ```
   ngrok http 8000
   ```

2. Обновите файл `.env` с URL вебхука.

## 📦 Зависимости

- `aiogram` - Современный и полностью асинхронный фреймворк для Telegram Bot API
- `aiohttp` - Асинхронный HTTP-клиент/сервер
- `python-dotenv` - Управление переменными окружения
- `pymongo` - Драйвер MongoDB
- `requests` - Библиотека HTTP-запросов
- `instaloader` - Загрузчик контента Instagram
- `stripe` - Обработка платежей

## 📊 Детали реализации

- **Instagram**: Использует библиотеку Instaloader для прямых загрузок
- **Другие платформы**: Использует API "auto-download-all-in-one" от RapidAPI
- **База данных**: MongoDB для данных пользователей и управления купонами
- **Платежи**: Stripe для обработки пожертвований

---

Made with ❤️
