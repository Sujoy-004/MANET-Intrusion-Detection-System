"""Notification adapter providing bounded in-memory notice queue."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
import time


@dataclass(frozen=True)
class NoticeItem:
    """Single notice item in the in-memory notice queue."""

    text: str
    level: str  # "info", "warning", "error", "success"
    timestamp: float


class NotificationAdapter:
    """Bounded in-memory notice queue preventing unbounded memory growth."""

    def __init__(self, maxlen: int = 20) -> None:
        self._queue: deque[NoticeItem] = deque(maxlen=maxlen)

    def add_notice(self, text: str, level: str = "info") -> None:
        """Add a notice message to the bounded queue."""
        self._queue.append(
            NoticeItem(
                text=text,
                level=level,
                timestamp=time.time(),
            )
        )

    def get_active_notice(self) -> str | None:
        """Return the most recent active notice text, or None if queue is empty."""
        if not self._queue:
            return None
        return self._queue[-1].text

    def get_all_notices(self) -> list[str]:
        """Return all notice messages in chronological order."""
        return [item.text for item in self._queue]

    def clear(self) -> None:
        """Clear all notices from the queue."""
        self._queue.clear()


__all__ = ["NoticeItem", "NotificationAdapter"]
