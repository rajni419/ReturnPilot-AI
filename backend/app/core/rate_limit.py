"""
Thread-safe rate limiter for authentication endpoints.
"""

import threading
import time
from typing import Dict, List, Tuple


class RateLimiter:
    def __init__(self):
        self._lock = threading.Lock()
        # Key -> list of float timestamps
        self._records: Dict[str, List[float]] = {}
        # Key -> float timestamp of last action (for cooldowns)
        self._last_action: Dict[str, float] = {}

    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int,
    ) -> Tuple[bool, int]:
        """
        Sliding window rate limit.
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            timestamps = self._records.get(key, [])
            cutoff = now - window_seconds
            # Purge timestamps outside window
            valid_timestamps = [t for t in timestamps if t > cutoff]

            if len(valid_timestamps) >= max_requests:
                earliest = valid_timestamps[0]
                retry_after = max(1, int(window_seconds - (now - earliest)))
                self._records[key] = valid_timestamps
                return False, retry_after

            valid_timestamps.append(now)
            self._records[key] = valid_timestamps
            return True, 0

    def check_cooldown(self, key: str, cooldown_seconds: int) -> Tuple[bool, int]:
        """
        Enforces a minimum interval between requests (e.g. 60s cooldown for email resends).
        Returns (is_allowed, retry_after_seconds).
        """
        now = time.time()
        with self._lock:
            last = self._last_action.get(key)
            if last is not None and (now - last) < cooldown_seconds:
                retry_after = max(1, int(cooldown_seconds - (now - last)))
                return False, retry_after

            self._last_action[key] = now
            return True, 0

    def clear(self):
        """Resets all records (useful for testing)."""
        with self._lock:
            self._records.clear()
            self._last_action.clear()


# Global rate limiter instance
limiter = RateLimiter()
