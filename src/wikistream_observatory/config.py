"""Configuration loading for WikiStream Observatory services."""

from __future__ import annotations

from dataclasses import dataclass
import os
from pathlib import Path
from typing import Literal

SourceMode = Literal["live", "replay"]


@dataclass(frozen=True)
class KafkaConfig:
    bootstrap_servers: str
    raw_topic: str
    consumer_group: str


@dataclass(frozen=True)
class SnapshotConfig:
    path: Path
    interval_seconds: int
    live_retention_hours: int


@dataclass(frozen=True)
class SignalConfig:
    current_window_minutes: int
    baseline_window_minutes: int
    threshold_ratio: float
    min_events: int
    top_bots_limit: int


@dataclass(frozen=True)
class AppConfig:
    mode: SourceMode
    kafka: KafkaConfig
    snapshots: SnapshotConfig
    replay_path: Path
    freshness_seconds: int
    dashboard_refresh_seconds: int
    user_agent: str
    signals: SignalConfig


def _getenv(name: str, default: str) -> str:
    value = os.getenv(name, default).strip()
    return value if value else default


def _get_int(name: str, default: int) -> int:
    raw = _getenv(name, str(default))
    try:
        value = int(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be an integer, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def _get_float(name: str, default: float) -> float:
    raw = _getenv(name, str(default))
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number, got {raw!r}") from exc
    if value <= 0:
        raise ValueError(f"{name} must be positive, got {value}")
    return value


def load_config() -> AppConfig:
    """Load strongly typed settings from environment variables."""

    mode_raw = _getenv("WIKISTREAM_MODE", "live").lower()
    if mode_raw not in {"live", "replay"}:
        raise ValueError("WIKISTREAM_MODE must be 'live' or 'replay'")
    mode: SourceMode = mode_raw  # type: ignore[assignment]

    return AppConfig(
        mode=mode,
        kafka=KafkaConfig(
            bootstrap_servers=_getenv("WIKISTREAM_KAFKA_BOOTSTRAP_SERVERS", "redpanda:9092"),
            raw_topic=_getenv("WIKISTREAM_RAW_TOPIC", "raw_recentchange"),
            consumer_group=_getenv("WIKISTREAM_CONSUMER_GROUP", "wikistream-processor"),
        ),
        snapshots=SnapshotConfig(
            path=Path(_getenv("WIKISTREAM_SNAPSHOT_PATH", "data/snapshots")),
            interval_seconds=_get_int("WIKISTREAM_SNAPSHOT_INTERVAL_SECONDS", 15),
            live_retention_hours=_get_int("WIKISTREAM_LIVE_RETENTION_HOURS", 6),
        ),
        replay_path=Path(_getenv("WIKISTREAM_REPLAY_PATH", "data/replay/recentchange_sample.jsonl")),
        freshness_seconds=_get_int("WIKISTREAM_FRESHNESS_SECONDS", 60),
        dashboard_refresh_seconds=_get_int("WIKISTREAM_DASHBOARD_REFRESH_SECONDS", 15),
        user_agent=_getenv("WIKISTREAM_USER_AGENT", "wikistream-observatory-local/0.1"),
        signals=SignalConfig(
            current_window_minutes=_get_int("WIKISTREAM_SIGNAL_CURRENT_WINDOW_MINUTES", 5),
            baseline_window_minutes=_get_int("WIKISTREAM_SIGNAL_BASELINE_WINDOW_MINUTES", 30),
            threshold_ratio=_get_float("WIKISTREAM_SIGNAL_THRESHOLD_RATIO", 3.0),
            min_events=_get_int("WIKISTREAM_SIGNAL_MIN_EVENTS", 20),
            top_bots_limit=_get_int("WIKISTREAM_SIGNAL_TOP_BOTS_LIMIT", 3),
        ),
    )
