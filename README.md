# Social Media Video Downloader Bot

Easily download and share videos from your favorite social media platforms with our Telegram bot! Whether it's Instagram Reels, TikTok, YouTube, Facebook, Twitter, or Pinterest, this bot has got you covered. Perfect for those who want to save content for offline viewing or reposting.

🎥 **Save videos from multiple platforms in a snap!**
🚀 **Simple, fast, and user-friendly!**
💯 **Updated documentation 2025!**

## Features

- Download videos from Instagram Reels, TikTok, YouTube, Facebook, Twitter, and Pinterest
- Receive videos as both video messages and downloadable files
- User management system with free and premium tiers
- Stripe integration for subscription payments
- Admin functionality for generating coupons and viewing usage statistics
- Simple and user-friendly interface

## Supported Platforms

| Platform  | Status | Implementation Method |
| --------- | ------ | --------------------- |
| Instagram | ✅     | Instaloader library   |
| TikTok    | ✅     | RapidAPI             |
| YouTube   | ✅     | RapidAPI             |
| Facebook  | ✅     | RapidAPI             |
| Twitter   | ✅     | RapidAPI             |
| Pinterest | ✅     | RapidAPI             |

## Commands

- `/start` - Begin interaction with the bot and receive usage instructions
- `/help` - Get detailed information about the bot's functionality
- `/subscribe` - View and select subscription plans
- `/activate_coupon` - Activate a coupon code for premium access

### Admin Commands

- `/generate_coupon` - Generate a new coupon (admin only)
- `/stats` - View usage statistics (admin only)

## Subscription Plans

- 1 month subscription - $1
- 3 months subscription - $5
- Lifetime subscription - $10

## Installation and Setup

1. Clone this repository:

   ```
   git clone https://github.com/yourusername/social-media-video-downloader-bot.git
   cd social-media-video-downloader-bot
   ```

2. Create a virtual environment and install the required dependencies:

   ```
   python -m venv .myebv
   source .myebv/bin/activate  # On Windows: .myebv\Scripts\activate
   pip install -r requirements.txt
   ```

3. Create a `.env` file in the project root (you can copy from `.env.example`):

   ```
   # Existing variables
   BOT_TOKEN=your_telegram_bot_token
   RAPIDAPI_KEY=your_rapidapi_key
   WEBHOOK_PATH='/webhook'
   WEBHOOK_URL=your_webhook_url

   # MongoDB configuration
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=your_db_name
   MONGODB_USERS_COLLECTION=users
   MONGODB_COUPONS_COLLECTION=coupons

   # User management configuration
   ADMIN_IDS=your_admin_telegram_id
   FREE_LIMIT=3

   # Stripe configuration
   STRIPE_PUBLISHABLE_KEY=your_stripe_publishable_key
   STRIPE_SECRET_KEY=your_stripe_secret_key
   STRIPE_WEBHOOK_SECRET=your_stripe_webhook_secret
   BOT_USERNAME=your_bot_username
   STRIPE_SUCCESS_URL=your_success_url
   STRIPE_CANCEL_URL=your_cancel_url
   ```

4. Set up the temporary directory for downloaded videos:

   ```
   mkdir temp_videos
   ```

5. Run the bot:
   ```
   python bot.py
   ```

## Webhook Setup

For production, you need to set up a webhook. The bot supports ngrok for development:

1. Install ngrok and start it with:
   ```
   ngrok http 8000
   ```

2. Copy the ngrok URL and set it as your `WEBHOOK_URL` in the `.env` file.

## Dependencies

The project uses the following main dependencies:

- `aiogram` - Modern and fully asynchronous framework for Telegram Bot API
- `aiohttp` - Asynchronous HTTP client/server framework
- `python-dotenv` - Environment variable management
- `pymongo` - MongoDB driver
- `requests` - HTTP requests library
- `instaloader` - Library for downloading content from Instagram
- `stripe` - Stripe API client for payments
- `asyncio` - Asynchronous I/O library

## API Usage

This bot uses two main methods for downloading content:

1. **Instagram**: Uses the Instaloader library for downloading Instagram Reels and Posts
2. **Other platforms**: Uses the "auto-download-all-in-one" API from RapidAPI to fetch videos from TikTok, YouTube, Facebook, Twitter, and Pinterest

## Technical Notes

- The bot might show a "403 Forbidden" error when accessing Instagram's GraphQL API. This is normal behavior as Instagram restricts automated access, but the Instaloader library has fallback methods that still allow successful downloads in most cases.
- For other platforms, the API might have rate limits depending on your RapidAPI subscription plan.
- Make sure your MongoDB server is running and accessible before starting the bot.

## User Experience

1. Users start with a limited number of free downloads (default: 3)
2. After reaching the limit, they need to subscribe or use a coupon
3. Videos are sent both as a playable video message and as a downloadable file
4. For Instagram posts that contain images instead of videos, the images are sent as photos

## Stripe Integration

This bot uses Stripe for handling payments. It supports both credit card payments and PayPal.

To set up Stripe for production payments:

1. Create a Stripe account at https://stripe.com if you haven't already.
2. In the Stripe Dashboard, navigate to the API keys section.
3. Copy your live secret key and publishable key.
4. Update your `.env` file with these live keys.
5. Set up a webhook in the Stripe Dashboard pointing to your webhook URL.
6. To enable PayPal, connect your PayPal account in the Stripe Dashboard.

## Note

Ensure you comply with the terms of service of all supported platforms when using this bot.

## License

[MIT License](LICENSE)
