"""
Reddit extractor — ported from Cobalt's reddit.js

Uses Reddit's JSON API: appends .json to the post URL.
Extracts video from secure_media.reddit_video.fallback_url
and checks for separate audio stream.
"""

import re
from typing import Optional

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# URL patterns
REDDIT_POST_PATTERN = re.compile(
    r'reddit\.com/r/([^/]+)/comments/([A-Za-z0-9]+)'
)
REDDIT_SHORT_PATTERN = re.compile(r'redd\.it/([A-Za-z0-9]+)')
REDDIT_SHARE_PATTERN = re.compile(
    r'reddit\.com/r/([^/]+)/s/([A-Za-z0-9]+)'
)


class RedditExtractor(BaseExtractor):

    def _extract_post_info(self, url: str) -> dict:
        """Extract subreddit and post ID from URL."""
        m = REDDIT_POST_PATTERN.search(url)
        if m:
            return {"sub": m.group(1), "id": m.group(2)}

        m = REDDIT_SHORT_PATTERN.search(url)
        if m:
            return {"short_id": m.group(1)}

        m = REDDIT_SHARE_PATTERN.search(url)
        if m:
            return {"sub": m.group(1), "share_id": m.group(2)}

        return {}

    async def _check_url_exists(self, url: str) -> bool:
        """HEAD request to check if URL returns 200."""
        try:
            async with self.session.head(
                url,
                headers={"user-agent": GENERIC_USER_AGENT},
                timeout=__import__("aiohttp").ClientTimeout(total=8),
            ) as resp:
                return resp.status == 200
        except Exception:
            return False

    async def extract(self, url: str) -> Optional[VideoResult]:
        info = self._extract_post_info(url)

        # Resolve short links / share links
        if info.get("short_id"):
            resolved = await self.resolve_redirect(
                f"https://www.reddit.com/video/{info['short_id']}",
                headers={"user-agent": GENERIC_USER_AGENT},
            )
            if resolved:
                info = self._extract_post_info(resolved)

        if not info.get("id") and info.get("share_id"):
            sub = info.get("sub", "")
            resolved = await self.resolve_redirect(
                f"https://www.reddit.com/r/{sub}/s/{info['share_id']}",
                headers={"user-agent": GENERIC_USER_AGENT},
            )
            if resolved:
                info = self._extract_post_info(resolved)

        post_id = info.get("id")
        if not post_id:
            self.logger.debug(f"Could not extract Reddit post ID from {url}")
            return None

        # Fetch post JSON
        json_url = f"https://www.reddit.com/comments/{post_id}.json"
        headers = {
            "user-agent": GENERIC_USER_AGENT,
            "accept": "application/json",
        }

        data = await self.fetch_json(json_url, headers=headers)
        if not data or not isinstance(data, list):
            return None

        try:
            post_data = data[0]["data"]["children"][0]["data"]
        except (KeyError, IndexError):
            return None

        sub = info.get("sub") or post_data.get("subreddit", "")
        source_id = f"{sub.lower()}_{post_id}" if sub else post_id

        # Check for GIF posts
        post_url = post_data.get("url", "")
        if post_url.endswith(".gif"):
            return VideoResult(
                url=post_url,
                filename=f"reddit_{source_id}.gif",
            )

        # Check for Reddit video
        reddit_video = post_data.get("secure_media", {})
        if reddit_video:
            reddit_video = reddit_video.get("reddit_video")

        if not reddit_video:
            # Try media field
            reddit_video = post_data.get("media", {})
            if reddit_video:
                reddit_video = reddit_video.get("reddit_video")

        if not reddit_video:
            self.logger.debug(f"No Reddit video found for {post_id}")
            return None

        fallback_url = reddit_video.get("fallback_url", "")
        if not fallback_url:
            return None

        # Clean up the video URL
        video_url = fallback_url.split("?")[0]

        # Try to find audio
        audio_url = None

        # Method 1: Replace DASH part with audio
        base_url = fallback_url.split("DASH")[0]
        audio_candidate = f"{base_url}audio"
        if await self._check_url_exists(audio_candidate):
            audio_url = audio_candidate
        else:
            # Method 2: For mp4 URLs
            if ".mp4" in video_url:
                audio_candidate = f"{video_url.split('_')[0]}_audio.mp4"
                if await self._check_url_exists(audio_candidate):
                    audio_url = audio_candidate
                else:
                    # Method 3: Variable audio quality
                    audio_candidate = f"{video_url.split('_')[0]}_AUDIO_128.mp4"
                    if await self._check_url_exists(audio_candidate):
                        audio_url = audio_candidate

        return VideoResult(
            url=video_url,
            filename=f"reddit_{source_id}.mp4",
            audio_url=audio_url,
        )
