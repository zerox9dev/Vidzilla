# rate_limiter.py - In-memory rate limiting

import time
from collections import defaultdict


class RateLimiter:
    def __init__(self, max_requests=3, window_seconds=60):
        self.requests = defaultdict(list)
        self.max_requests = max_requests
        self.window = window_seconds

    def is_allowed(self, user_id: int) -> bool:
        now = time.time()
        # Clean old entries
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]
        if len(self.requests[user_id]) >= self.max_requests:
            return False
        self.requests[user_id].append(now)
        return True

    def seconds_until_allowed(self, user_id: int) -> int:
        if not self.requests[user_id]:
            return 0
        now = time.time()
        # Clean old entries first
        self.requests[user_id] = [
            t for t in self.requests[user_id] if now - t < self.window
        ]
        if not self.requests[user_id]:
            return 0
        oldest = min(self.requests[user_id])
        return max(0, int(self.window - (now - oldest)))


# Global rate limiter instance
rate_limiter = RateLimiter(max_requests=3, window_seconds=60)
