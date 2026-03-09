"""
Facebook extractor — ported from Cobalt's facebook.js

Fetches the Facebook video page and extracts HD/SD URLs from
browser_native_hd_url / browser_native_sd_url in the HTML.
"""

import re
import json
from typing import Optional

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# Facebook URL patterns
FB_VIDEO_PATTERN = re.compile(r'facebook\.com/.*?/videos/(\d+)')
FB_REEL_PATTERN = re.compile(r'facebook\.com/reel/(\d+)')
FB_SHARE_PATTERN = re.compile(r'facebook\.com/share/(?:v|r)/([A-Za-z0-9]+)')
FB_WATCH_PATTERN = re.compile(r'fb\.watch/([A-Za-z0-9_-]+)')
FB_GENERIC_VIDEO = re.compile(r'facebook\.com/(?:watch/?\?v=|video\.php\?v=)(\d+)')

HEADERS = {
    "User-Agent": GENERIC_USER_AGENT,
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
    "Sec-Fetch-Mode": "navigate",
    "Sec-Fetch-Site": "none",
}


class FacebookExtractor(BaseExtractor):

    def _extract_video_id(self, url: str) -> Optional[str]:
        for pattern in [FB_VIDEO_PATTERN, FB_REEL_PATTERN, FB_GENERIC_VIDEO]:
            m = pattern.search(url)
            if m:
                return m.group(1)
        return None

    def _extract_share_id(self, url: str) -> Optional[str]:
        m = FB_SHARE_PATTERN.search(url)
        return m.group(1) if m else None

    def _extract_fb_watch(self, url: str) -> Optional[str]:
        m = FB_WATCH_PATTERN.search(url)
        return m.group(1) if m else None

    async def _resolve_fb_watch(self, short_id: str) -> Optional[str]:
        """Resolve fb.watch short links."""
        resolved = await self.resolve_redirect(
            f"https://fb.watch/{short_id}",
            headers=HEADERS,
        )
        return resolved

    async def _fetch_and_extract(self, url: str, identifier: str) -> Optional[VideoResult]:
        """Fetch a Facebook page and extract video URLs from HTML."""
        # Use web.facebook.com like Cobalt does
        html = await self.fetch(url, headers=HEADERS)
        if not html:
            return None

        urls = []

        # Look for HD and SD video URLs in HTML
        hd_match = re.search(r'"browser_native_hd_url":"(.*?)"', html)
        sd_match = re.search(r'"browser_native_sd_url":"(.*?)"', html)

        if hd_match:
            try:
                urls.append(json.loads(f'"{hd_match.group(1)}"'))
            except Exception:
                urls.append(hd_match.group(1))

        if sd_match:
            try:
                urls.append(json.loads(f'"{sd_match.group(1)}"'))
            except Exception:
                urls.append(sd_match.group(1))

        if not urls:
            # Try alternative patterns
            playable_match = re.search(r'"playable_url(?:_quality_hd)?":"(.*?)"', html)
            if playable_match:
                try:
                    urls.append(json.loads(f'"{playable_match.group(1)}"'))
                except Exception:
                    urls.append(playable_match.group(1))

        if not urls:
            return None

        return VideoResult(
            url=urls[0],  # Prefer HD
            filename=f"facebook_{identifier}.mp4",
        )

    async def extract(self, url: str) -> Optional[VideoResult]:
        # Handle fb.watch short links
        fb_watch = self._extract_fb_watch(url)
        if fb_watch:
            resolved = await self._resolve_fb_watch(fb_watch)
            if resolved:
                url = resolved
            else:
                return None

        video_id = self._extract_video_id(url)
        share_id = self._extract_share_id(url)
        identifier = video_id or share_id or "unknown"

        # Build the Facebook URL to fetch
        if video_id:
            fetch_url = f"https://web.facebook.com/i/videos/{video_id}"
        elif share_id:
            # Try share/v/ and share/r/ patterns
            fetch_url = f"https://web.facebook.com/share/v/{share_id}"
        else:
            # Use the original URL but via web.facebook.com
            fetch_url = url.replace("www.facebook.com", "web.facebook.com")
            fetch_url = fetch_url.replace("m.facebook.com", "web.facebook.com")

        result = await self._fetch_and_extract(fetch_url, identifier)
        if result:
            self.logger.info("Facebook: extracted video URL")
            return result

        # If share pattern, try alternative
        if share_id:
            fetch_url = f"https://web.facebook.com/share/r/{share_id}"
            result = await self._fetch_and_extract(fetch_url, identifier)
            if result:
                return result

        self.logger.debug("Facebook: no video URL found")
        return None
