"""Dashboard data-loading helpers over DuckDB/Parquet snapshots."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import Any

from wikistream_observatory.queries import query_snapshot
from wikistream_observatory.time_utils import classify_freshness, parse_event_timestamp


def _source_mode_where(source_mode: str | None) -> str:
    if source_mode is None:
        return ""
    mode = source_mode.lower()
    if mode not in {"live", "replay"}:
        raise ValueError("source_mode must be 'live', 'replay', or None")
    return f"WHERE source_mode = '{mode}'"


def load_overview_metrics(snapshot_path: Path | str, limit: int = 500, *, source_mode: str | None = None) -> list[dict[str, Any]]:
    where = _source_mode_where(source_mode)
    return query_snapshot(snapshot_path, "activity_metrics", f"SELECT * FROM snapshot {where} ORDER BY computed_at DESC LIMIT {int(limit)}")


def load_recent_events(snapshot_path: Path | str, limit: int = 100, *, source_mode: str | None = None) -> list[dict[str, Any]]:
    where = _source_mode_where(source_mode)
    return query_snapshot(snapshot_path, "normalized_events", f"SELECT * FROM snapshot {where} ORDER BY observed_at DESC LIMIT {int(limit)}")


def load_bot_spike_signals(snapshot_path: Path | str, limit: int = 50, *, source_mode: str | None = None) -> list[dict[str, Any]]:
    """Load latest domain-level bot spike signal snapshots.

    Missing or empty signal datasets are a valid no-signal state and return an
    empty list so dashboard rendering can show explanatory text instead of an
    error.
    """

    where = _source_mode_where(source_mode)
    return query_snapshot(snapshot_path, "bot_spike_signals", f"SELECT * FROM snapshot {where} ORDER BY computed_at DESC LIMIT {int(limit)}")


def load_data_quality_counts(snapshot_path: Path | str, limit: int = 20, *, source_mode: str | None = None) -> list[dict[str, Any]]:
    """Load latest data-quality count snapshots.

    Missing quality snapshots are valid while the processor is starting; callers
    should render an explanatory empty state.
    """

    where = _source_mode_where(source_mode)
    return query_snapshot(snapshot_path, "data_quality_counts", f"SELECT * FROM snapshot {where} ORDER BY window_end DESC LIMIT {int(limit)}")


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


def latest_observed_at(snapshot_path: Path | str, *, source_mode: str | None = None) -> datetime | None:
    where = _source_mode_where(source_mode)
    rows = query_snapshot(snapshot_path, "normalized_events", f"SELECT max(observed_at) AS latest_observed_at FROM snapshot {where}")
    if not rows:
        return None
    return parse_event_timestamp(rows[0].get("latest_observed_at"))


def dashboard_status(snapshot_path: Path | str, *, source_mode: str, freshness_seconds: int) -> dict[str, Any]:
    latest = latest_observed_at(snapshot_path, source_mode=source_mode)
    return {
        "source_mode": source_mode,
        "latest_observed_at": latest,
        "freshness_status": classify_freshness(source_mode, latest, freshness_seconds=freshness_seconds),
    }
