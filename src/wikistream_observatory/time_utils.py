"""UTC time parsing, windowing, and freshness helpers."""

from __future__ import annotations

from datetime import datetime, timezone, timedelta
from typing import Literal

FreshnessStatus = Literal["fresh", "stale", "replay", "no_data"]


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def ensure_utc(value: datetime) -> datetime:
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def parse_event_timestamp(value: object) -> datetime | None:
    """Parse Wikimedia timestamps from epoch seconds or ISO-like strings."""

    if value is None:
        return None
    if isinstance(value, datetime):
        return ensure_utc(value)
    if isinstance(value, (int, float)):
        return datetime.fromtimestamp(value, tz=timezone.utc)
    if isinstance(value, str):
        text = value.strip()
        if not text:
            return None
        if text.isdigit():
            return datetime.fromtimestamp(int(text), tz=timezone.utc)
        try:
            return ensure_utc(datetime.fromisoformat(text.replace("Z", "+00:00")))
        except ValueError:
            return None
    return None


def choose_event_time(candidate: datetime | None, observed_at: datetime, max_future_skew: timedelta = timedelta(minutes=10)) -> tuple[datetime, bool]:
    """Return the event time to use and whether a fallback was needed."""

    observed_at = ensure_utc(observed_at)
    if candidate is None:
        return observed_at, True
    candidate = ensure_utc(candidate)
    if candidate - observed_at > max_future_skew:
        return observed_at, True
    return candidate, False


def floor_to_bucket(value: datetime, minutes: int = 1) -> datetime:
    if minutes <= 0:
        raise ValueError("minutes must be positive")
    value = ensure_utc(value)
    bucket_minute = (value.minute // minutes) * minutes
    return value.replace(minute=bucket_minute, second=0, microsecond=0)


def bucket_bounds(value: datetime, minutes: int = 1) -> tuple[datetime, datetime]:
    start = floor_to_bucket(value, minutes)
    return start, start + timedelta(minutes=minutes)


def classify_freshness(source_mode: str, latest_observed_at: datetime | None, now: datetime | None = None, freshness_seconds: int = 60) -> FreshnessStatus:
    if source_mode == "replay":
        return "replay"
    if latest_observed_at is None:
        return "no_data"
    now = ensure_utc(now or utc_now())
    latest = ensure_utc(latest_observed_at)
    return "fresh" if now - latest <= timedelta(seconds=freshness_seconds) else "stale"
