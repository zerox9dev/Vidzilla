"""
Extractors package — Cobalt-style direct video extraction.

Usage:
    from extractors import get_extractor

    extractor = get_extractor("Instagram", session)
    if extractor:
        result = await extractor.extract(url)
"""

from typing import Optional
import aiohttp

from .base import BaseExtractor, VideoResult
from .instagram import InstagramExtractor
from .tiktok import TikTokExtractor
from .youtube import YouTubeExtractor
from .twitter import TwitterExtractor
from .facebook import FacebookExtractor
from .pinterest import PinterestExtractor
from .reddit import RedditExtractor

_EXTRACTORS = {
    "Instagram": InstagramExtractor,
    "TikTok": TikTokExtractor,
    "YouTube": YouTubeExtractor,
    "Twitter": TwitterExtractor,
    "Facebook": FacebookExtractor,
    "Pinterest": PinterestExtractor,
    "Reddit": RedditExtractor,
}


def get_extractor(platform_name: str, session: aiohttp.ClientSession) -> Optional[BaseExtractor]:
    """Factory: returns an extractor instance for the given platform, or None."""
    cls = _EXTRACTORS.get(platform_name)
    return cls(session) if cls else None


__all__ = [
    "get_extractor",
    "VideoResult",
    "BaseExtractor",
    "InstagramExtractor",
    "TikTokExtractor",
    "YouTubeExtractor",
    "TwitterExtractor",
    "FacebookExtractor",
    "PinterestExtractor",
    "RedditExtractor",
]
