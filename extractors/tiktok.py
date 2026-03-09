"""
TikTok extractor — ported from Cobalt's tiktok.js

Extraction logic:
1. Resolve short links (vt.tiktok.com, vm.tiktok.com)
2. Fetch page HTML from tiktok.com/@i/video/{postId}
3. Parse __UNIVERSAL_DATA_FOR_REHYDRATION__ JSON
4. Extract playAddr from itemStruct.video
"""

import re
import json
from typing import Optional

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# Pattern to extract post ID from TikTok URLs
TIKTOK_POST_PATTERN = re.compile(r'/video/(\d+)')
TIKTOK_PHOTO_PATTERN = re.compile(r'/photo/(\d+)')
SHORT_LINK_PATTERN = re.compile(r'(?:vm|vt)\.tiktok\.com/([A-Za-z0-9]+)')


class TikTokExtractor(BaseExtractor):

    def _extract_post_id(self, url: str) -> Optional[str]:
        for pattern in [TIKTOK_POST_PATTERN, TIKTOK_PHOTO_PATTERN]:
            m = pattern.search(url)
            if m:
                return m.group(1)
        return None

    def _is_short_link(self, url: str) -> bool:
        return bool(SHORT_LINK_PATTERN.search(url))

    async def _resolve_short_link(self, url: str) -> Optional[str]:
        """Resolve vm.tiktok.com / vt.tiktok.com short links."""
        try:
            # TikTok short links return HTML with <a href="...">
            # Use a trimmed user agent (no Chrome version) like Cobalt does
            ua = GENERIC_USER_AGENT.split(" Chrome/1")[0]
            async with self.session.get(
                url,
                headers={"user-agent": ua},
                allow_redirects=False,
                timeout=__import__("aiohttp").ClientTimeout(total=10),
            ) as resp:
                # Check Location header first
                location = resp.headers.get("Location") or resp.headers.get("location")
                if location and "tiktok.com" in location:
                    return location.split("?")[0]

                # Parse HTML fallback
                html = await resp.text()
                if html and html.startswith('<a href="https://'):
                    extracted = html.split('<a href="')[1].split("?")[0]
                    if "tiktok.com" in extracted:
                        return extracted
        except Exception as e:
            self.logger.debug(f"Short link resolve error: {e}")

        # Fallback: follow redirects
        resolved = await self.resolve_redirect(url)
        if resolved and "tiktok.com" in resolved:
            return resolved.split("?")[0]
        return None

    async def extract(self, url: str) -> Optional[VideoResult]:
        post_id = self._extract_post_id(url)

        # Resolve short links
        if not post_id and self._is_short_link(url):
            resolved_url = await self._resolve_short_link(url)
            if resolved_url:
                post_id = self._extract_post_id(resolved_url)

        if not post_id:
            # Try resolving any TikTok URL via redirect
            resolved_url = await self.resolve_redirect(url)
            if resolved_url:
                post_id = self._extract_post_id(resolved_url)

        if not post_id:
            self.logger.debug(f"Could not extract TikTok post ID from {url}")
            return None

        # Fetch video page — always use /video/ path (works for photos too)
        page_url = f"https://www.tiktok.com/@i/video/{post_id}"
        headers = {
            "user-agent": GENERIC_USER_AGENT,
        }

        html = await self.fetch(page_url, headers=headers)
        if not html:
            return None

        # Parse __UNIVERSAL_DATA_FOR_REHYDRATION__
        try:
            marker = '<script id="__UNIVERSAL_DATA_FOR_REHYDRATION__" type="application/json">'
            if marker not in html:
                self.logger.debug("No rehydration data found in TikTok page")
                return None

            json_str = html.split(marker)[1].split("</script>")[0]
            data = json.loads(json_str)

            video_detail = data.get("__DEFAULT_SCOPE__", {}).get("webapp.video-detail")
            if not video_detail:
                self.logger.debug("No video detail in rehydration data")
                return None

            # Check if post is unavailable
            if video_detail.get("statusMsg"):
                self.logger.debug(f"TikTok post unavailable: {video_detail['statusMsg']}")
                return None

            detail = video_detail.get("itemInfo", {}).get("itemStruct")
            if not detail:
                return None

        except (json.JSONDecodeError, IndexError, KeyError) as e:
            self.logger.debug(f"TikTok parse error: {e}")
            return None

        # Check content classification (age-restricted)
        if detail.get("isContentClassified"):
            self.logger.debug("TikTok content is age-restricted")
            return None

        if not detail.get("author"):
            return None

        author = detail.get("author", {}).get("uniqueId", "unknown")
        filename_base = f"tiktok_{author}_{post_id}"

        # Check for image post (slideshow)
        images = detail.get("imagePost", {}).get("images") if detail.get("imagePost") else None
        if images:
            # For image posts, return the music/audio URL if available
            # or the first image
            image_urls = []
            for img in images:
                img_url_list = img.get("imageURL", {}).get("urlList", [])
                jpeg_url = next((u for u in img_url_list if ".jpeg?" in u), None)
                if jpeg_url:
                    image_urls.append(jpeg_url)

            if image_urls:
                # Return first image as photo
                return VideoResult(
                    url=image_urls[0],
                    filename=f"{filename_base}_photo_1.jpg",
                    is_photo=True,
                )
            return None

        # Video post
        play_addr = detail.get("video", {}).get("playAddr")
        if not play_addr:
            # Try bitrateInfo for alternative URLs
            bitrate_info = detail.get("video", {}).get("bitrateInfo", [])
            if bitrate_info:
                for br in bitrate_info:
                    urls = br.get("PlayAddr", {}).get("UrlList", [])
                    if urls:
                        play_addr = urls[0]
                        break

        if not play_addr:
            self.logger.debug("No playAddr found")
            return None

        return VideoResult(
            url=play_addr,
            filename=f"{filename_base}.mp4",
        )
