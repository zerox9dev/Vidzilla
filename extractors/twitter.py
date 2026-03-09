"""
Twitter/X extractor — ported from Cobalt's twitter.js

Extraction chain:
1. GraphQL API with guest token → TweetDetail
2. Syndication API fallback → cdn.syndication.twimg.com
"""

import re
import json
import math
from typing import Optional, List, Dict, Any
from urllib.parse import urlencode, quote

from .base import BaseExtractor, VideoResult, GENERIC_USER_AGENT

# Tweet ID pattern
TWEET_ID_PATTERN = re.compile(
    r'(?:twitter\.com|x\.com)/[^/]+/status/(\d+)'
)
# Also handle t.co short links — need redirect resolution
TCO_PATTERN = re.compile(r't\.co/([A-Za-z0-9]+)')

BEARER_TOKEN = (
    "AAAAAAAAAAAAAAAAAAAAANRILgAAAAAAnNwIzUejRCOuH5E6I8xnZz4puTs"
    "%3D1Zv7ttfk8LF81IUq16cHjhLTvJu4FA33AGWWjCpTnA"
)

COMMON_HEADERS = {
    "user-agent": GENERIC_USER_AGENT,
    "authorization": f"Bearer {BEARER_TOKEN}",
    "x-twitter-client-language": "en",
    "x-twitter-active-user": "yes",
    "accept-language": "en",
}

GRAPHQL_URL = "https://api.x.com/graphql/4Siu98E55GquhG52zHdY5w/TweetDetail"

TWEET_FEATURES = {
    "rweb_video_screen_enabled": False,
    "profile_label_improvements_pcf_label_in_post_enabled": True,
    "rweb_tipjar_consumption_enabled": True,
    "creator_subscriptions_tweet_preview_api_enabled": True,
    "responsive_web_graphql_timeline_navigation_enabled": True,
    "responsive_web_graphql_skip_user_profile_image_extensions_enabled": False,
    "communities_web_enable_tweet_community_results_fetch": True,
    "c9s_tweet_anatomy_moderator_badge_enabled": True,
    "articles_preview_enabled": True,
    "responsive_web_edit_tweet_api_enabled": True,
    "graphql_is_translatable_rweb_tweet_is_translatable_enabled": True,
    "view_counts_everywhere_api_enabled": True,
    "longform_notetweets_consumption_enabled": True,
    "responsive_web_twitter_article_tweet_consumption_enabled": True,
    "tweet_awards_web_tipping_enabled": False,
    "creator_subscriptions_quote_tweet_preview_enabled": False,
    "freedom_of_speech_not_reach_fetch_enabled": True,
    "standardized_nudges_misinfo": True,
    "tweet_with_visibility_results_prefer_gql_limited_actions_policy_enabled": True,
    "longform_notetweets_rich_text_read_enabled": True,
    "longform_notetweets_inline_media_enabled": True,
    "responsive_web_enhance_cards_enabled": False,
}

TWEET_FIELD_TOGGLES = {
    "withArticleRichContentState": True,
    "withArticlePlainText": False,
    "withGrokAnalyze": False,
    "withDisallowedReplyControls": False,
}

# Cached guest token
_cached_guest_token: Optional[str] = None


class TwitterExtractor(BaseExtractor):

    def _extract_tweet_id(self, url: str) -> Optional[str]:
        m = TWEET_ID_PATTERN.search(url)
        return m.group(1) if m else None

    async def _get_guest_token(self, force: bool = False) -> Optional[str]:
        global _cached_guest_token
        if _cached_guest_token and not force:
            return _cached_guest_token

        data = await self.fetch_json(
            "https://api.x.com/1.1/guest/activate.json",
            headers=COMMON_HEADERS,
            method="POST",
        )
        if data and data.get("guest_token"):
            _cached_guest_token = data["guest_token"]
            return _cached_guest_token
        return None

    async def _request_graphql(self, tweet_id: str, guest_token: str) -> Optional[dict]:
        """Request tweet data via GraphQL API."""
        variables = {
            "focalTweetId": tweet_id,
            "with_rux_injections": False,
            "rankingMode": "Relevance",
            "includePromotedContent": True,
            "withCommunity": True,
            "withQuickPromoteEligibilityTweetFields": True,
            "withBirdwatchNotes": True,
            "withVoice": True,
        }

        params = {
            "variables": json.dumps(variables),
            "features": json.dumps(TWEET_FEATURES),
            "fieldToggles": json.dumps(TWEET_FIELD_TOGGLES),
        }

        url = f"{GRAPHQL_URL}?{urlencode(params, quote_via=quote)}"

        headers = {
            **COMMON_HEADERS,
            "content-type": "application/json",
            "x-guest-token": guest_token,
            "cookie": f"guest_id=v1%3A{guest_token}",
        }

        return await self.fetch_json(url, headers=headers)

    async def _request_syndication(self, tweet_id: str) -> Optional[dict]:
        """Use syndication API."""
        # Token from Cobalt: ((id / 1e15) * Math.PI).toString(36).replace(/(0+|\.)/g, '')
        token_float = (int(tweet_id) / 1e15) * math.pi
        # JS toString(36) for float — we approximate with hex of the hash
        token = format(abs(hash(str(token_float))), 'x')[:12]

        url = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}&token={token}"
        result = await self.fetch_json(url, headers={"user-agent": GENERIC_USER_AGENT})
        if result:
            return result

        # Try without token
        url2 = f"https://cdn.syndication.twimg.com/tweet-result?id={tweet_id}"
        return await self.fetch_json(url2, headers={"user-agent": GENERIC_USER_AGENT})

    async def _request_fxtwitter(self, tweet_id: str) -> Optional[dict]:
        """Fallback: use fxtwitter API (public, no auth needed)."""
        url = f"https://api.fxtwitter.com/status/{tweet_id}"
        return await self.fetch_json(url, headers={"user-agent": GENERIC_USER_AGENT})

    def _best_video_quality(self, variants: list) -> Optional[str]:
        """Select highest bitrate mp4 variant."""
        mp4s = [v for v in variants if v.get("content_type") == "video/mp4"]
        if not mp4s:
            return None
        best = max(mp4s, key=lambda v: int(v.get("bitrate", 0)))
        return best.get("url")

    def _extract_media_from_graphql(self, data: dict, tweet_id: str) -> Optional[list]:
        """Extract media array from GraphQL response."""
        try:
            instructions = (
                data.get("data", {})
                .get("threaded_conversation_with_injections_v2", {})
                .get("instructions", [])
            )

            add_insn = next(
                (i for i in instructions if i.get("type") == "TimelineAddEntries"),
                None,
            )
            if not add_insn:
                return None

            entries = add_insn.get("entries", [])
            tweet_entry = next(
                (e for e in entries if e.get("entryId") == f"tweet-{tweet_id}"),
                None,
            )
            if not tweet_entry:
                return None

            tweet_result = (
                tweet_entry.get("content", {})
                .get("itemContent", {})
                .get("tweet_results", {})
                .get("result", {})
            )

            typename = tweet_result.get("__typename")
            if typename not in ("Tweet", "TweetWithVisibilityResults"):
                return None

            if typename == "TweetWithVisibilityResults":
                base_tweet = tweet_result.get("tweet", {}).get("legacy", {})
            else:
                base_tweet = tweet_result.get("legacy", {})

            # Check for retweet
            reposted = base_tweet.get("retweeted_status_result", {}).get("result", {})
            if reposted:
                reposted_legacy = reposted.get("legacy", {}) or reposted.get("tweet", {}).get("legacy", {})
                reposted_media = reposted_legacy.get("extended_entities", {}).get("media")
                if reposted_media:
                    return reposted_media

            return base_tweet.get("extended_entities", {}).get("media")

        except Exception as e:
            self.logger.debug(f"GraphQL extraction error: {e}")
            return None

    async def extract(self, url: str) -> Optional[VideoResult]:
        tweet_id = self._extract_tweet_id(url)

        # Handle t.co short links
        if not tweet_id and "t.co/" in url:
            resolved = await self.resolve_redirect(url)
            if resolved:
                tweet_id = self._extract_tweet_id(resolved)

        if not tweet_id:
            self.logger.debug(f"Could not extract tweet ID from {url}")
            return None

        media = None

        # Strategy 1: Syndication API (more stable)
        try:
            syn_data = await self._request_syndication(tweet_id)
            if syn_data:
                media = syn_data.get("mediaDetails")
                if media:
                    self.logger.info(f"Twitter: extracted via syndication")
        except Exception as e:
            self.logger.debug(f"Syndication failed: {e}")

        # Strategy 2: GraphQL API fallback
        if not media:
            try:
                guest_token = await self._get_guest_token()
                if guest_token:
                    data = await self._request_graphql(tweet_id, guest_token)
                    if data:
                        media = self._extract_media_from_graphql(data, tweet_id)
                        if media:
                            self.logger.info(f"Twitter: extracted via GraphQL")
            except Exception as e:
                self.logger.debug(f"GraphQL failed: {e}")

        # Strategy 3: fxtwitter API (public proxy)
        if not media:
            try:
                fx_data = await self._request_fxtwitter(tweet_id)
                if fx_data and fx_data.get("tweet"):
                    tweet_data = fx_data["tweet"]
                    # fxtwitter returns direct video URL in media
                    fx_media = tweet_data.get("media", {})
                    videos = fx_media.get("videos", [])
                    if videos:
                        video_url = videos[0].get("url")
                        if video_url:
                            self.logger.info(f"Twitter: extracted via fxtwitter")
                            return VideoResult(
                                url=video_url,
                                filename=f"twitter_{tweet_id}.mp4",
                            )
                    # Check for photos
                    photos = fx_media.get("photos", [])
                    if photos:
                        photo_url = photos[0].get("url")
                        if photo_url:
                            return VideoResult(
                                url=photo_url,
                                filename=f"twitter_{tweet_id}.jpg",
                            )
            except Exception as e:
                self.logger.debug(f"fxtwitter failed: {e}")

        if not media:
            return None

        # Extract video from media
        for item in media:
            media_type = item.get("type")

            if media_type == "video" or media_type == "animated_gif":
                variants = item.get("video_info", {}).get("variants", [])
                video_url = self._best_video_quality(variants)
                if video_url:
                    return VideoResult(
                        url=video_url,
                        filename=f"twitter_{tweet_id}.mp4",
                    )

            elif media_type == "photo":
                photo_url = item.get("media_url_https")
                if photo_url:
                    return VideoResult(
                        url=f"{photo_url}?name=4096x4096",
                        filename=f"twitter_{tweet_id}.jpg",
                        is_photo=True,
                    )

        return None
