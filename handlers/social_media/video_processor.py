import logging
import os
import uuid
from typing import Optional

import aiohttp
from aiogram.types import FSInputFile

from config import (
    TEMP_DIRECTORY,
    PLATFORM_IDENTIFIERS,
    COBALT_API_URL,
    COBALT_API_KEY,
)
from utils.common_utils import safe_edit_message
from utils.cleanup import cleanup_temp_directory
from utils.ads import GEO_BLOCK_AD

logger = logging.getLogger(__name__)

TELEGRAM_VIDEO_SIZE_LIMIT_MB = 50
TELEGRAM_VIDEO_SIZE_LIMIT_BYTES = TELEGRAM_VIDEO_SIZE_LIMIT_MB * 1024 * 1024
DOWNLOAD_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15"
)

PROGRESS_MESSAGES = {
    'downloading': '⬇️ Downloading from {platform}...',
    'processing': '⚙️ Processing video...',
    'sending_video': '📤 Sending video...',
    'done': '✅ Done! ({size:.1f}MB)',
    'too_large': '📦 Too large: {size:.1f}MB (limit: 50MB)',
}


class CobaltError(Exception):
    def __init__(self, code: str, message: str = ""):
        self.code = code or ""
        super().__init__(message or code)


def get_file_size_mb(file_path: str) -> float:
    try:
        return os.path.getsize(file_path) / (1024 * 1024)
    except Exception:
        return 0.0


def generate_thumbnail(video_path: str) -> Optional[str]:
    """Extract a JPG frame at ~1s for use as Telegram thumbnail."""
    import subprocess
    thumb_path = video_path.rsplit(".", 1)[0] + "_thumb.jpg"
    for ss_args in (["-ss", "1"], []):
        try:
            result = subprocess.run(
                [
                    "ffmpeg", "-y", "-loglevel", "error",
                    *ss_args,
                    "-i", video_path,
                    "-frames:v", "1",
                    "-vf", "scale='min(320,iw)':-2",
                    "-q:v", "5",
                    thumb_path,
                ],
                capture_output=True, timeout=15,
            )
            if result.returncode == 0 and os.path.exists(thumb_path) and os.path.getsize(thumb_path) > 0:
                return thumb_path
        except Exception as e:
            logger.debug(f"thumbnail generation failed: {e}")
    return None


def probe_video(file_path: str) -> dict:
    """Return {width, height, duration} via ffprobe, or {} on failure."""
    import json
    import subprocess
    try:
        result = subprocess.run(
            [
                "ffprobe", "-v", "error",
                "-select_streams", "v:0",
                "-show_entries", "stream=width,height:format=duration",
                "-of", "json",
                file_path,
            ],
            capture_output=True, text=True, timeout=10,
        )
        if result.returncode != 0:
            return {}
        data = json.loads(result.stdout or "{}")
        stream = (data.get("streams") or [{}])[0]
        fmt = data.get("format") or {}
        out = {}
        if isinstance(stream.get("width"), int) and stream["width"] > 0:
            out["width"] = stream["width"]
        if isinstance(stream.get("height"), int) and stream["height"] > 0:
            out["height"] = stream["height"]
        if fmt.get("duration"):
            try:
                out["duration"] = int(float(fmt["duration"]))
            except (TypeError, ValueError):
                pass
        return out
    except Exception as e:
        logger.debug(f"ffprobe failed: {e}")
        return {}


def cobalt_error_to_user_message(code: str) -> str:
    """Map Cobalt error codes to user-friendly messages."""
    c = (code or "").lower()
    if "private" in c:
        return "🔒 This video is private"
    if "age" in c:
        return "🔞 Age-restricted content — can't download"
    if "region" in c or "geo" in c:
        return "🌍 This video is not available in our region" + GEO_BLOCK_AD
    if "rate" in c:
        return "⏳ Too many requests — try again in a minute"
    if "timed_out" in c or "timeout" in c:
        return "⏳ Timeout — try again in a moment"
    if "unavailable" in c or "not_found" in c or "empty" in c:
        return "❌ Video not found — it may have been deleted"
    if "no_matching_format" in c or "unsupported" in c:
        return "🚫 Couldn't find a downloadable format for this link"
    if "post" in c and "no_video" in c:
        return "📝 This post doesn't contain a video"
    return "⚠️ Couldn't download this one — try again or send another link"


async def cobalt_request_media_url(session: aiohttp.ClientSession, url: str) -> tuple[str, dict]:
    """Ask Cobalt for a media URL. Returns (media_url, headers_for_download)."""
    headers = {
        "Accept": "application/json",
        "Content-Type": "application/json",
        "User-Agent": "Vidzilla/1.0",
    }
    if COBALT_API_KEY:
        headers["Authorization"] = f"Api-Key {COBALT_API_KEY}"

    payload = {
        "url": url,
        "videoQuality": "720",
        "filenameStyle": "basic",
        "downloadMode": "auto",
    }

    async with session.post(
        COBALT_API_URL,
        json=payload,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=30),
    ) as resp:
        try:
            data = await resp.json(content_type=None)
        except Exception as e:
            raise CobaltError("cobalt.invalid_response", f"HTTP {resp.status}: {e}")

    status = data.get("status")
    if status in ("tunnel", "redirect"):
        media_url = data.get("url")
        if not media_url:
            raise CobaltError("cobalt.empty_url", "No URL in response")
        return media_url, {}

    if status == "picker":
        # Pick first video item
        items = data.get("picker") or []
        for item in items:
            if item.get("type") == "video" and item.get("url"):
                return item["url"], {}
        # Fallback: any item with url
        for item in items:
            if item.get("url"):
                return item["url"], {}
        raise CobaltError("cobalt.picker_empty", "No items in picker response")

    if status == "error":
        err = data.get("error") or {}
        code = err.get("code") or "error.api.unknown"
        raise CobaltError(code, str(err))

    raise CobaltError("cobalt.unknown_status", f"Unknown status: {status}")


async def download_to_file(
    session: aiohttp.ClientSession,
    url: str,
    output_path: str,
    extra_headers: Optional[dict] = None,
) -> bool:
    """Stream download to file. Returns False if exceeds size limit, raises on other errors."""
    headers = dict(extra_headers or {})
    headers.setdefault("User-Agent", DOWNLOAD_USER_AGENT)

    async with session.get(
        url,
        headers=headers,
        timeout=aiohttp.ClientTimeout(total=120),
    ) as resp:
        resp.raise_for_status()

        if resp.content_length and resp.content_length > TELEGRAM_VIDEO_SIZE_LIMIT_BYTES:
            logger.info(f"File too large per Content-Length: {resp.content_length}")
            return False

        total = 0
        with open(output_path, "wb") as f:
            async for chunk in resp.content.iter_chunked(64 * 1024):
                f.write(chunk)
                total += len(chunk)
                if total > TELEGRAM_VIDEO_SIZE_LIMIT_BYTES:
                    logger.info("Exceeded size limit during download, aborting")
                    return False

    return os.path.exists(output_path) and os.path.getsize(output_path) > 0


async def download_via_cobalt(url: str, platform_name: str, user_id: int) -> Optional[str]:
    os.makedirs(TEMP_DIRECTORY, exist_ok=True)
    request_id = str(uuid.uuid4())[:8]
    filename = f"{platform_name.lower()}_{user_id}_{request_id}.mp4"
    output_path = os.path.join(TEMP_DIRECTORY, filename)

    async with aiohttp.ClientSession() as session:
        media_url, dl_headers = await cobalt_request_media_url(session, url)
        logger.info(f"Cobalt returned media URL for {platform_name}")

        ok = await download_to_file(session, media_url, output_path, dl_headers)
        if not ok:
            if os.path.exists(output_path):
                try:
                    os.unlink(output_path)
                except Exception:
                    pass
            return None

    size_mb = get_file_size_mb(output_path)
    logger.info(f"Downloaded {platform_name} via Cobalt: {size_mb:.2f}MB")
    return output_path


async def process_social_media_video(message, bot, url, platform_name, progress_msg=None):
    temp_video_path = None

    try:
        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['downloading'].format(platform=platform_name)
            )

        try:
            temp_video_path = await download_via_cobalt(url, platform_name, message.from_user.id)
        except CobaltError as e:
            logger.warning(f"Cobalt error for {platform_name}: {e.code}")
            error_message = cobalt_error_to_user_message(e.code)
            if progress_msg:
                await safe_edit_message(progress_msg, error_message)
            else:
                await bot.send_message(message.chat.id, error_message)
            return

        if not temp_video_path:
            too_large_msg = "📦 Video is too large for Telegram (limit: 50MB)"
            if progress_msg:
                await safe_edit_message(progress_msg, too_large_msg)
            else:
                await bot.send_message(message.chat.id, too_large_msg)
            return

        file_size_mb = get_file_size_mb(temp_video_path)
        logger.info(f"{platform_name} video size: {file_size_mb:.2f}MB")

        if progress_msg:
            await safe_edit_message(progress_msg, PROGRESS_MESSAGES['sending_video'])

        await send_video_with_fallback(bot, message, temp_video_path, platform_name)

        if progress_msg:
            await safe_edit_message(
                progress_msg,
                PROGRESS_MESSAGES['done'].format(size=file_size_mb)
            )

        logger.info(f"{platform_name} video processed successfully")

    except Exception as e:
        logger.error(f"Error processing {platform_name} video: {e}")

        error_str = str(e).lower()
        if 'timeout' in error_str or 'timed out' in error_str:
            error_message = "⏳ Timeout — try again in a moment"
        else:
            error_message = "⚠️ Something went wrong — please try again"

        if progress_msg:
            await safe_edit_message(progress_msg, error_message)
        else:
            await bot.send_message(message.chat.id, error_message)

    finally:
        if temp_video_path and os.path.exists(temp_video_path):
            try:
                os.unlink(temp_video_path)
            except Exception as e:
                logger.warning(f"Cleanup failed: {e}")

        try:
            cleanup_temp_directory()
        except Exception:
            pass


async def send_video_with_fallback(bot, message, video_path: str, platform_name: str):
    video_sent = False
    document_sent = False
    errors = []
    video_message = None

    meta = probe_video(video_path)
    thumb_path = generate_thumbnail(video_path)

    try:
        video_file = FSInputFile(video_path)
        thumbnail = FSInputFile(thumb_path) if thumb_path else None
        video_message = await bot.send_video(
            chat_id=message.chat.id,
            video=video_file,
            supports_streaming=True,
            width=meta.get("width"),
            height=meta.get("height"),
            duration=meta.get("duration"),
            thumbnail=thumbnail,
        )
        logger.info(f"Video sent (meta: {meta}, thumb: {bool(thumb_path)})")
        video_sent = True
    except Exception as video_error:
        logger.warning(f"Failed to send as video: {video_error}")
        errors.append(f"Video: {video_error}")

    try:
        file_name = f"{platform_name.lower()}_video.mp4"
        doc_file = FSInputFile(video_path, filename=file_name)
        reply_to_message_id = video_message.message_id if video_message else None
        await bot.send_document(
            chat_id=message.chat.id,
            document=doc_file,
            reply_to_message_id=reply_to_message_id,
            disable_content_type_detection=True,
        )
        logger.info("Video sent as document")
        document_sent = True
    except Exception as doc_error:
        logger.warning(f"Failed to send as document: {doc_error}")
        errors.append(f"Document: {doc_error}")

    if not video_sent and not document_sent:
        raise Exception("Failed to send video in both formats: " + "; ".join(errors))

    if thumb_path and os.path.exists(thumb_path):
        try:
            os.unlink(thumb_path)
        except Exception:
            pass


async def detect_platform_and_process(message, bot, url, progress_msg=None):
    for domain, platform_name in PLATFORM_IDENTIFIERS.items():
        if domain in url:
            await process_social_media_video(message, bot, url, platform_name, progress_msg)
            return True
    return False
