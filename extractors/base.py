import aiohttp
import logging
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field


GENERIC_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/124.0.0.0 Safari/537.36"
)


@dataclass
class VideoResult:
    """Result of a video extraction."""
    url: str                                # direct video URL
    filename: str                           # suggested filename
    audio_url: Optional[str] = None         # separate audio stream URL (for merge)
    thumbnail: Optional[str] = None
    title: Optional[str] = None
    duration: Optional[int] = None
    filesize: Optional[int] = None
    is_photo: bool = False
    headers: Optional[Dict[str, str]] = None  # headers needed to download
    picker: Optional[List[Dict[str, str]]] = None  # multiple media items (carousel)


class BaseExtractor:
    def __init__(self, session: aiohttp.ClientSession):
        self.session = session
        self.logger = logging.getLogger(self.__class__.__name__)

    async def fetch(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        data: Any = None,
        allow_redirects: bool = True,
        timeout: int = 15,
    ) -> Optional[str]:
        """Fetch URL and return text response."""
        try:
            kwargs: Dict[str, Any] = {
                "headers": headers or {},
                "allow_redirects": allow_redirects,
                "timeout": aiohttp.ClientTimeout(total=timeout),
            }
            if data is not None:
                kwargs["data"] = data

            async with self.session.request(method, url, **kwargs) as resp:
                if resp.status != 200:
                    self.logger.warning(f"HTTP {resp.status} for {url}")
                    return None
                return await resp.text()
        except Exception as e:
            self.logger.warning(f"Fetch error for {url}: {e}")
            return None

    async def fetch_json(
        self,
        url: str,
        headers: Optional[Dict[str, str]] = None,
        method: str = "GET",
        data: Any = None,
        timeout: int = 15,
    ) -> Optional[dict]:
        """Fetch URL and return parsed JSON."""
        try:
            kwargs: Dict[str, Any] = {
                "headers": headers or {},
                "timeout": aiohttp.ClientTimeout(total=timeout),
            }
            if data is not None:
                kwargs["data"] = data

            async with self.session.request(method, url, **kwargs) as resp:
                if resp.status != 200:
                    self.logger.warning(f"HTTP {resp.status} for {url}")
                    return None
                return await resp.json(content_type=None)
        except Exception as e:
            self.logger.warning(f"Fetch JSON error for {url}: {e}")
            return None

    async def resolve_redirect(self, url: str, headers: Optional[Dict[str, str]] = None) -> Optional[str]:
        """Follow a URL and return the final redirected URL."""
        try:
            async with self.session.get(
                url,
                headers=headers or {"User-Agent": GENERIC_USER_AGENT},
                allow_redirects=True,
                timeout=aiohttp.ClientTimeout(total=10),
            ) as resp:
                return str(resp.url)
        except Exception as e:
            self.logger.warning(f"Redirect resolve error for {url}: {e}")
            return None

    async def extract(self, url: str) -> Optional[VideoResult]:
        """Extract video from URL. Return None on failure."""
        raise NotImplementedError
