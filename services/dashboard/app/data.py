"""Dashboard data-loading helpers over DuckDB/Parquet snapshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from wikistream_observatory.queries import latest_rows, query_snapshot
from wikistream_observatory.time_utils import classify_freshness, parse_event_timestamp


def load_overview_metrics(snapshot_path: Path | str, limit: int = 500) -> list[dict[str, Any]]:
    return latest_rows(snapshot_path, "activity_metrics", order_by="computed_at", limit=limit)


def load_recent_events(snapshot_path: Path | str, limit: int = 100) -> list[dict[str, Any]]:
    return latest_rows(snapshot_path, "normalized_events", order_by="observed_at", limit=limit)


def load_bot_spike_signals(snapshot_path: Path | str, limit: int = 50) -> list[dict[str, Any]]:
    """Load latest domain-level bot spike signal snapshots.

    Missing or empty signal datasets are a valid no-signal state and return an
    empty list so dashboard rendering can show explanatory text instead of an
    error.
    """

    return latest_rows(snapshot_path, "bot_spike_signals", order_by="computed_at", limit=limit)


def bot_spike_empty_state(
    *,
    current_window_minutes: int = 5,
    baseline_window_minutes: int = 30,
    min_current_events: int = 20,
    threshold_ratio: float = 3.0,
) -> str:
    """Explain that no domain-level bot spike currently meets the threshold."""

    return (
        "No domain-level bot activity spike currently meets the configured threshold. "
        f"The MVP compares bot-flagged events in the latest {current_window_minutes}-minute window "
        f"with the previous {baseline_window_minutes}-minute baseline for the same domain, "
        f"and emits a signal only when there are at least {min_current_events} current bot-flagged events "
        f"and activity is at least {threshold_ratio:.1f}x the baseline."
    )


def latest_observed_at(snapshot_path: Path | str) -> datetime | None:
    rows = query_snapshot(snapshot_path, "normalized_events", "SELECT max(observed_at) AS latest_observed_at FROM snapshot")
    if not rows:
        return None
    return parse_event_timestamp(rows[0].get("latest_observed_at"))


def dashboard_status(snapshot_path: Path | str, *, source_mode: str, freshness_seconds: int) -> dict[str, Any]:
    latest = latest_observed_at(snapshot_path)
    return {
        "source_mode": source_mode,
        "latest_observed_at": latest,
        "freshness_status": classify_freshness(source_mode, latest, freshness_seconds=freshness_seconds),
    }
