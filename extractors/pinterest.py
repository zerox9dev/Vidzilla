"""
Pinterest extractor — ported from Cobalt's pinterest.js

Fetches the pin page HTML and extracts video/image URLs via regex.
"""

import re
from typing import Optional

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# URL patterns
PIN_PATTERN = re.compile(r'pinterest\.com/pin/(\d+(?:--\d+)?)')
PIN_SHORT_PATTERN = re.compile(r'pin\.it/([A-Za-z0-9]+)')

# Content patterns from HTML
VIDEO_REGEX = re.compile(r'"url":"(https://v1\.pinimg\.com/videos/.*?)"')
IMAGE_REGEX = re.compile(r'src="(https://i\.pinimg\.com/.*?\.(?:jpg|gif))"')
NOT_FOUND_REGEX = re.compile(r'"__typename"\s*:\s*"PinNotFound"')


class PinterestExtractor(BaseExtractor):

    def _extract_pin_id(self, url: str) -> Optional[str]:
        m = PIN_PATTERN.search(url)
        if m:
            pin_id = m.group(1)
            # Handle IDs like "123--456" → use "456"
            if "--" in pin_id:
                pin_id = pin_id.split("--")[1]
            return pin_id
        return None

    def _is_short_link(self, url: str) -> bool:
        return bool(PIN_SHORT_PATTERN.search(url))

    async def _resolve_short_link(self, url: str) -> Optional[str]:
        """Resolve pin.it short links via Pinterest redirect API."""
        m = PIN_SHORT_PATTERN.search(url)
        if not m:
            return None

        short_id = m.group(1)
        resolved = await self.resolve_redirect(
            f"https://api.pinterest.com/url_shortener/{short_id}/redirect/",
        )
        return resolved

    async def extract(self, url: str) -> Optional[VideoResult]:
        pin_id = self._extract_pin_id(url)

        # Handle short links
        if not pin_id and self._is_short_link(url):
            resolved = await self._resolve_short_link(url)
            if resolved:
                pin_id = self._extract_pin_id(resolved)

        if not pin_id:
            # Try direct redirect resolution
            resolved = await self.resolve_redirect(url)
            if resolved:
                pin_id = self._extract_pin_id(resolved)

        if not pin_id:
            self.logger.debug(f"Could not extract Pinterest pin ID from {url}")
            return None

        # Fetch pin page
        html = await self.fetch(
            f"https://www.pinterest.com/pin/{pin_id}/",
            headers={"user-agent": GENERIC_USER_AGENT},
        )

        if not html:
            return None

        # Check if pin exists
        if NOT_FOUND_REGEX.search(html):
            self.logger.debug(f"Pinterest pin not found: {pin_id}")
            return None

        # Look for video
        video_matches = VIDEO_REGEX.findall(html)
        video_link = next((v for v in video_matches if v.endswith(".mp4")), None)

        if video_link:
            return VideoResult(
                url=video_link,
                filename=f"pinterest_{pin_id}.mp4",
            )

        # Look for image
        image_matches = IMAGE_REGEX.findall(html)
        image_link = next(
            (img for img in image_matches if img.endswith(".jpg") or img.endswith(".gif")),
            None,
        )

        if image_link:
            ext = "gif" if image_link.endswith(".gif") else "jpg"
            return VideoResult(
                url=image_link,
                filename=f"pinterest_{pin_id}.{ext}",
                is_photo=True,
            )

        self.logger.debug(f"Pinterest: no media found for {pin_id}")
        return None
