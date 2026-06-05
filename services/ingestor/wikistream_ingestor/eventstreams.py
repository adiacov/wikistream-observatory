"""Wikimedia EventStreams RecentChanges SSE client."""

from __future__ import annotations

from collections.abc import Iterator
import json
import time
from typing import Any

RECENTCHANGE_STREAM_URL = "https://stream.wikimedia.org/v2/stream/recentchange"


def recentchange_events(*, user_agent: str, url: str = RECENTCHANGE_STREAM_URL, max_backoff_seconds: int = 60) -> Iterator[dict[str, Any]]:
    """Yield RecentChanges events, reconnecting with capped exponential backoff."""

    import httpx
    from httpx_sse import connect_sse

    headers = {"Accept": "text/event-stream", "User-Agent": user_agent}
    backoff = 1
    while True:
        try:
            with httpx.Client(timeout=None, headers=headers) as client:
                with connect_sse(client, "GET", url) as event_source:
                    event_source.response.raise_for_status()
                    backoff = 1
                    for sse in event_source.iter_sse():
                        if not sse.data:
                            continue
                        try:
                            decoded = json.loads(sse.data)
                        except json.JSONDecodeError:
                            continue
                        if isinstance(decoded, dict):
                            yield decoded
        except (httpx.HTTPError, httpx.TimeoutException):
            time.sleep(backoff)
            backoff = min(max_backoff_seconds, backoff * 2)
