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
