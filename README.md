# 🎬 Vidzilla - Video Downloader Bot

> **Fast, reliable video downloads from top social platforms**

## 🆓 FREE Version (main branch)

This is the **completely FREE** version of Vidzilla with no limitations:

- ✅ Download from 8 popular platforms
- ✅ No download limits
- ✅ No subscriptions required
- ✅ Simple and clean

### 📱 Supported Platforms
YouTube • Instagram • TikTok • Facebook • Twitter/X • Pinterest • Reddit • Vimeo

---

## 🌟 Other Versions

### 💳 Premium with Payments
**Branch:** `stripe-payments-feature`
- Stripe integration for premium subscriptions
- Advanced features and priority support
- Payment processing and user tiers

### 📢 Channel Subscription
**Branch:** `channel-subscription-feature`
- Require users to join specific channels
- Access control based on channel membership
- Automated subscription verification

---

## 🚀 Quick Start

1. **Clone the repo:**
   ```bash
   git clone https://github.com/your-username/Vidzilla.git
   cd Vidzilla
   ```

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your bot token and MongoDB URI
   ```

4. **Run the bot:**
   ```bash
   python bot.py
   ```

## ⚙️ Configuration

Required environment variables:
- `BOT_TOKEN` - Your Telegram bot token
- `MONGODB_URI` - MongoDB connection string
- `ADMIN_IDS` - Comma-separated admin user IDs

## 📊 Features

- 🎥 **Video Downloads** - From 8 major platforms
- 📱 **Telegram Integration** - Send videos directly to chat
- 👥 **User Management** - Track downloads and users
- 🛠️ **Admin Panel** - Broadcast messages and view stats
- 🚫 **Size Limits** - Clear messages for large videos (>50MB)

## 🔧 Tech Stack

- **Python 3.8+** with aiogram 3.x
- **MongoDB** for user data
- **yt-dlp** for video downloading
- **Docker** ready for deployment

## 📄 License

MIT License - see [LICENSE](LICENSE) file for details.

---

**Choose your version and start downloading! 🎉**
