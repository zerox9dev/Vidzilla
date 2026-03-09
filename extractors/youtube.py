"""
YouTube extractor — ported from Cobalt's youtube.js

Uses the Innertube API with iOS client context to bypass some restrictions.
POST https://www.youtube.com/youtubei/api/v1/player

Note: This is a simplified port. The full Cobalt implementation uses
youtubei.js library for cipher decryption, HLS parsing, etc.
This extractor handles basic cases; yt-dlp fallback covers the rest.
"""

import re
import json
from typing import Optional

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# YouTube video ID patterns
YT_ID_PATTERN = re.compile(
    r'(?:youtube\.com/(?:watch\?v=|shorts/|embed/|v/|live/)|youtu\.be/)([A-Za-z0-9_-]{11})'
)

# iOS client context for Innertube API
IOS_CLIENT = {
    "clientName": "IOS",
    "clientVersion": "19.29.1",
    "deviceMake": "Apple",
    "deviceModel": "iPhone16,2",
    "userAgent": "com.google.ios.youtube/19.29.1 (iPhone16,2; U; CPU iOS 17_5_1 like Mac OS X;)",
    "osName": "iPhone",
    "osVersion": "17.5.1.21F90",
    "hl": "en",
    "gl": "US",
}

INNERTUBE_API_URL = "https://www.youtube.com/youtubei/api/v1/player"
INNERTUBE_API_KEY = "AIzaSyB-63vPrdThhKuerbB2N_l7Kwwcxj6yUAc"

# Video quality preference (descending)
QUALITY_PREFERENCE = [2160, 1440, 1080, 720, 480, 360, 240, 144]


class YouTubeExtractor(BaseExtractor):

    def _extract_video_id(self, url: str) -> Optional[str]:
        m = YT_ID_PATTERN.search(url)
        return m.group(1) if m else None

    async def _innertube_request(self, video_id: str) -> Optional[dict]:
        """Make an Innertube player API request with iOS client."""
        payload = {
            "context": {
                "client": IOS_CLIENT,
            },
            "videoId": video_id,
            "playbackContext": {
                "contentPlaybackContext": {
                    "html5Preference": "HTML5_PREF_WANTS",
                }
            },
            "contentCheckOk": True,
            "racyCheckOk": True,
        }

        headers = {
            "Content-Type": "application/json",
            "User-Agent": IOS_CLIENT["userAgent"],
            "X-YouTube-Client-Name": "5",  # iOS
            "X-YouTube-Client-Version": IOS_CLIENT["clientVersion"],
        }

        url = f"{INNERTUBE_API_URL}?key={INNERTUBE_API_KEY}"

        return await self.fetch_json(
            url,
            headers=headers,
            method="POST",
            data=json.dumps(payload),
            timeout=15,
        )

    def _select_best_format(self, formats: list, max_height: int = 1080) -> Optional[dict]:
        """Select the best mp4 video format up to max_height."""
        mp4_videos = [
            f for f in formats
            if f.get("mimeType", "").startswith("video/mp4")
            and f.get("url")
            and f.get("height")
        ]

        if not mp4_videos:
            return None

        # Filter to max height, then pick highest quality
        suitable = [f for f in mp4_videos if f["height"] <= max_height]
        if not suitable:
            suitable = mp4_videos  # take what we can get

        return max(suitable, key=lambda f: f.get("height", 0) * f.get("width", 0))

    def _select_best_audio(self, formats: list) -> Optional[dict]:
        """Select best audio format."""
        audio_formats = [
            f for f in formats
            if f.get("mimeType", "").startswith("audio/")
            and f.get("url")
        ]

        if not audio_formats:
            return None

        return max(audio_formats, key=lambda f: f.get("bitrate", 0))

    async def extract(self, url: str) -> Optional[VideoResult]:
        video_id = self._extract_video_id(url)
        if not video_id:
            self.logger.debug(f"Could not extract YouTube video ID from {url}")
            return None

        data = await self._innertube_request(video_id)
        if not data:
            return None

        # Check playability
        playability = data.get("playabilityStatus", {})
        status = playability.get("status")

        if status != "OK":
            reason = playability.get("reason", "unknown")
            self.logger.debug(f"YouTube video not playable: {status} - {reason}")
            return None

        # Check for live stream
        video_details = data.get("videoDetails", {})
        if video_details.get("isLive") or video_details.get("isLiveContent"):
            self.logger.debug("YouTube live streams not supported")
            return None

        # Check duration (skip very long videos > 1 hour for Telegram)
        duration_seconds = int(video_details.get("lengthSeconds", 0))
        if duration_seconds > 3600:
            self.logger.debug(f"YouTube video too long: {duration_seconds}s")
            return None

        streaming_data = data.get("streamingData", {})

        # Try adaptive formats first (separate video + audio = higher quality)
        adaptive = streaming_data.get("adaptiveFormats", [])
        # Also check combined formats
        combined = streaming_data.get("formats", [])

        title = video_details.get("title", f"youtube_{video_id}")

        # Strategy 1: Combined format (video+audio in one stream)
        best_combined = None
        for fmt in combined:
            if (fmt.get("mimeType", "").startswith("video/mp4")
                    and fmt.get("url")
                    and fmt.get("height", 0) <= 1080):
                if not best_combined or fmt.get("height", 0) > best_combined.get("height", 0):
                    best_combined = fmt

        if best_combined and best_combined.get("url"):
            return VideoResult(
                url=best_combined["url"],
                filename=f"youtube_{video_id}.mp4",
                title=title,
                duration=duration_seconds,
                thumbnail=f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            )

        # Strategy 2: Adaptive formats (video + separate audio)
        best_video = self._select_best_format(adaptive)
        best_audio = self._select_best_audio(adaptive)

        if best_video and best_video.get("url"):
            return VideoResult(
                url=best_video["url"],
                filename=f"youtube_{video_id}.mp4",
                audio_url=best_audio["url"] if best_audio and best_audio.get("url") else None,
                title=title,
                duration=duration_seconds,
                thumbnail=f"https://i.ytimg.com/vi/{video_id}/maxresdefault.jpg",
            )

        # Strategy 3: HLS manifest
        hls_url = streaming_data.get("hlsManifestUrl")
        if hls_url:
            # Return HLS URL — the downloader will need to handle this
            return VideoResult(
                url=hls_url,
                filename=f"youtube_{video_id}.mp4",
                title=title,
                duration=duration_seconds,
            )

        self.logger.warning(f"YouTube: no suitable format found for {video_id}")
        return None
