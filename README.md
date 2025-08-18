# 🎬 Vidzilla - Video Downloader Bot

> **Fast, reliable video downloads from top social platforms**

## ✨ Features

- ✅ Download from 8 popular platforms
- ✅ Dual format delivery (video + document)
- ✅ No download limits
- ✅ No subscriptions required
- ✅ Simple and clean interface
- ✅ Admin panel with broadcast and stats

### 📱 Supported Platforms
YouTube • Instagram • TikTok • Facebook • Twitter/X • Pinterest • Reddit • Vimeo

---

## 🚀 Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/zerox9dev/Vidzilla.git
   cd Vidzilla
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   Create a `.env` file with your configuration:
   ```env
   BOT_TOKEN=your_telegram_bot_token
   MONGODB_URI=your_mongodb_connection_string
   MONGODB_DB_NAME=vidzilla
   MONGODB_USERS_COLLECTION=users
   ADMIN_IDS=123456789,987654321
   WEBHOOK_URL=https://your-domain.com
   WEBHOOK_PATH=/webhook
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

### Required Environment Variables
- `BOT_TOKEN` - Your Telegram bot token
- `MONGODB_URI` - MongoDB connection string
- `MONGODB_DB_NAME` - Database name
- `MONGODB_USERS_COLLECTION` - Users collection name
- `ADMIN_IDS` - Comma-separated admin user IDs

### Optional Environment Variables
- `WEBHOOK_URL` - Your webhook URL for production
- `WEBHOOK_PATH` - Webhook endpoint path
- `HOST` - Server host (default: 0.0.0.0)
- `PORT` - Server port (default: 8000)

## 📊 Detailed Features

- 🎥 **Dual Format Downloads** - Each video sent as both video and document
- 📱 **Telegram Integration** - Seamless video delivery to chat
- 👥 **User Management** - MongoDB-based user tracking
- 🛠️ **Admin Panel** - Broadcast messages and view statistics
- 🚫 **Size Limits** - Smart handling of large videos (>50MB limit)
- 📈 **Analytics** - Download counts and user statistics
- 🔧 **Webhook Support** - Production-ready deployment

## 🔧 Tech Stack

- **Python 3.8+** with aiogram 3.x
- **MongoDB** for user data
- **yt-dlp** for video downloading
- **Docker** ready for deployment

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Ready to download? Start using Vidzilla today! 🎉**

### 🎬 How it works:
1. Send any video link to the bot
2. Get your video in **two formats**: 
   - 📺 Video file (for instant viewing)
   - 📁 Document file (for easy downloading)
3. Enjoy your content! 
