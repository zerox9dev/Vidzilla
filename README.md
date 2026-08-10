

# Vidzilla 🤖

**Telegram bot for downloading videos from social media — powered by self-hosted [Cobalt](https://github.com/imputnet/cobalt).**

## Features

- Downloads videos from 8 platforms via Cobalt API
- Sends each video in two formats: streamable video + original file
- Proper aspect ratio and thumbnail (via `ffprobe` + `ffmpeg`)
- 50 MB cap (Telegram bot limit) with size pre-check
- Per-user rate limiting
- MongoDB for user/download tracking
- Polling and webhook modes
- `/health` endpoint and Docker healthcheck

## Supported platforms

YouTube · Instagram · TikTok · Facebook · Twitter/X · Pinterest · Reddit · Vimeo

(Cobalt actually handles 20+; bot filters by URL match — extend `PLATFORM_IDENTIFIERS` in [config.py](config.py) to enable more.)

## Architecture

```
Telegram ─┬──► vidzilla-bot ──► cobalt-api (POST /)
          │         │                │
          │         │                ▼
          │         │        media URL (tunnel/redirect)
          │         ▼
          │    download to temp_videos/
          │    ffprobe + ffmpeg thumbnail
          ▼
       send_video + send_document
```

Two containers, one docker network. Bot calls `http://cobalt-api:9000/`, gets a media URL, streams it to disk with a 50 MB hard cap, sends to Telegram, cleans up.

## Quick start (Docker)

Requires Docker + Docker Compose.

```bash
git clone https://github.com/zerox9dev/Vidzilla.git
cd Vidzilla
cp .env.example .env   # if present, otherwise see "Environment" below
docker compose up -d --build
docker compose logs -f vidzilla-bot
```

Two containers come up: `vidzilla-bot` and `cobalt-api`.

## Environment

Create `.env` in the project root:

```env
# Telegram
BOT_TOKEN=123456:ABC...
BOT_MODE=polling                # or "webhook"
PORT=8000
HOST=0.0.0.0

# Webhook mode only
WEBHOOK_PATH=/webhook
WEBHOOK_URL=https://your-domain.com

# MongoDB
MONGODB_URI=mongodb+srv://user:pass@cluster.mongodb.net/
MONGODB_DB_NAME=video_downloader_bot
MONGODB_USERS_COLLECTION=users

# Admin Telegram user IDs (comma-separated)
ADMIN_IDS=111111111,222222222

# Cobalt (defaults work with bundled compose)
COBALT_API_URL=http://cobalt-api:9000/
COBALT_API_KEY=                 # optional, only if cobalt is started with keys.json
```

## Local development (without Docker)

Requires Python 3.11–3.13 and `ffmpeg` installed (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Linux).

```bash
python3.13 -m venv .venv
source .venv/bin/activate
pip install -U pip
pip install -r requirements.txt

# Bring up cobalt locally
docker compose up -d cobalt-api

# Cobalt validates the Host header against its API_URL.
# For local testing override:
export COBALT_API_URL=http://localhost:9000/
# ...and start cobalt with API_URL=http://localhost:9000/ instead of cobalt-api:9000

python bot.py
```

> Python 3.14 is currently unsupported by `pydantic-core` builds — use 3.13.

## Bot commands

- `/start` — welcome message
- (any link) — paste a video URL, bot downloads and sends back

## How it works

1. User sends a URL → [handlers/handlers.py](handlers/handlers.py) routes by `F.text.regexp(r'https?://')`.
2. Platform detection by URL substring → [config.py](config.py) `PLATFORM_IDENTIFIERS`.
3. [video_processor.py](handlers/social_media/video_processor.py) calls Cobalt:
   - `POST /` with `{url, videoQuality: "720", downloadMode: "auto"}`.
   - Cobalt replies with `tunnel`, `redirect`, `picker`, or `error`.
4. Bot streams the media URL to `temp_videos/`, aborting if size > 50 MB.
5. `ffprobe` extracts width/height/duration; `ffmpeg` extracts a thumbnail frame at ~1s.
6. `send_video` (with metadata + thumbnail) → `send_document` linked as reply.
7. Temp files cleaned up.
8. MongoDB download counter incremented; every Nth download triggers a sponsor blurb (configurable in [utils/ads.py](utils/ads.py)).

## Healthcheck

Both polling and webhook modes expose `GET /health` returning `{"status":"ok"}`. Compose runs a Python-based healthcheck every 30s.

## Project layout

```
Vidzilla/
├── bot.py                       # entry point, polling/webhook bootstrap, /health
├── config.py                    # env vars, platform map, URL extraction
├── docker-compose.yml           # bot + cobalt-api
├── Dockerfile                   # python:3.11-slim + ffmpeg
├── handlers/
│   ├── handlers.py              # /start, link handler, fallback hint
│   ├── admin.py                 # admin-only commands
│   └── social_media/
│       └── video_processor.py   # Cobalt client + send pipeline
└── utils/
    ├── ads.py                   # sponsor message config
    ├── cleanup.py               # temp dir housekeeping
    ├── common_utils.py          # shared helpers, error decorator
    ├── rate_limiter.py          # in-memory per-user rate limit
    ├── user_agent_utils.py
    └── user_management.py       # MongoDB user/download tracking
```

## Cobalt notes

- Cobalt is open source: <https://github.com/imputnet/cobalt>. Updates land roughly weekly. To upgrade: `docker compose pull cobalt-api && docker compose up -d cobalt-api`.
- `read_only: true` and `init: true` are set in compose per Cobalt's recommended config.
- For login-only content (private IG, age-restricted YT) mount a `cookies.json` and set `COOKIE_PATH` on the cobalt service. See <https://github.com/imputnet/cobalt/blob/main/docs/cookies.md>.
- Public Cobalt instance (`https://api.cobalt.tools`) works as a drop-in `COBALT_API_URL` if you don't want to self-host, but is rate-limited.

## Updating on a server

```bash
cd /root/Vidzilla
git pull
docker compose up -d --build
```

## License

MIT — see [LICENSE](LICENSE).
