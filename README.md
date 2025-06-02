# Vidzilla - Social Media Video Downloader Bot

![Vidzilla Cover](cover.png)

## 🚀 Download videos from any platform!

Vidzilla is a powerful Telegram bot that lets you easily download and share videos from popular social media platforms. Just send a link, and get your video instantly!

### 🎬 Supported Platforms

- **Instagram** - Reels and Posts
- **TikTok** - All videos
- **YouTube** - Videos and Shorts
- **Facebook** - Videos and Reels
- **Twitter/X** - Videos and GIFs
- **Pinterest** - Video Pins

### ✨ Features

- **Simple to Use** - Just send a link, get your video!
- **Fast Downloads** - Videos delivered in seconds
- **Free to Use** - With optional $1 donation to support our servers
- **Multiple Formats** - Receive videos as both playable messages and downloadable files
- **Admin Tools** - Stats tracking, coupon generation, and broadcast messaging

## 📱 How to Use

1. **Start the bot**: Send `/start` to begin
2. **Send a link**: Paste any supported video URL
3. **Get your video**: Receive the video as both a playable message and a downloadable file
4. **Support us**: Use `/donate` if you find the bot useful

## 🤖 Bot Commands

- `/start` - Start the bot and get usage instructions
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
- **Other Platforms**: Uses RapidAPI's "social-media-video-downloader" API
- **Database**: MongoDB for user data and coupon management
- **Payments**: Stripe for donation processing

## 📝 License

[MIT License](LICENSE)

---

Made with ❤️
