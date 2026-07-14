from __future__ import annotations

import math
import threading
import time
from collections import deque


class SubmissionRateLimited(ValueError):
    def __init__(self, retry_after_seconds: int) -> None:
        super().__init__("contact submission rate limit exceeded")
        self.retry_after_seconds = retry_after_seconds


class LeadSubmissionGuard:
    """Bounded, process-local abuse control that never trusts forwarded client headers."""

    def __init__(self, *, request_limit: int, window_seconds: int, tracked_clients: int) -> None:
        self.request_limit = request_limit
        self.window_seconds = window_seconds
        self.tracked_clients = tracked_clients
        self._attempts: dict[str, deque[float]] = {}
        self._lock = threading.Lock()

    def check(self, client_host: str | None, *, now: float | None = None) -> None:
        timestamp = time.monotonic() if now is None else now
        cutoff = timestamp - self.window_seconds
        key = client_host or "unknown-client"

        with self._lock:
            attempts = self._attempts.get(key)
            if attempts is None:
                self._discard_inactive_clients(cutoff)
                if len(self._attempts) >= self.tracked_clients:
                    raise SubmissionRateLimited(self.window_seconds)
                attempts = deque()
                self._attempts[key] = attempts

            while attempts and attempts[0] <= cutoff:
                attempts.popleft()
            if len(attempts) >= self.request_limit:
                retry_after = max(1, math.ceil(attempts[0] + self.window_seconds - timestamp))
                raise SubmissionRateLimited(retry_after)
            attempts.append(timestamp)

    def _discard_inactive_clients(self, cutoff: float) -> None:
        inactive = [
            key
            for key, attempts in self._attempts.items()
            if not attempts or attempts[-1] <= cutoff
        ]
        for key in inactive:
            del self._attempts[key]
