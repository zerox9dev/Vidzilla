# Vidzilla - Social Media Video Downloader Bot

![Vidzilla Cover](cover.png)

# 🌐 Language / Мова / Язык / 语言 / اللغة
- [English](#english)
- [Українська](#українська)
- [Русский](#русский)
- [中文](#中文)
- [العربية](#العربية)

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

Made with ❤️