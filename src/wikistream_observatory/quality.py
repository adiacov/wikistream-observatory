"""Data-quality classification and count helpers."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
import json
from typing import Any, Literal

from wikistream_observatory.models import DataQualityCount, NormalizedRecentChangeEvent, SourceMode
from wikistream_observatory.normalization import normalize_recentchange
from wikistream_observatory.time_utils import classify_freshness, ensure_utc, parse_event_timestamp, utc_now

QualityClassificationStatus = Literal["accepted", "accepted_missing_fields", "malformed_rejected"]


@dataclass(frozen=True)
class RawEventQualityClassification:
    """Classification for one raw event before/after normalization."""

    status: QualityClassificationStatus
    source_mode: SourceMode
    event: NormalizedRecentChangeEvent | None = None
    reason: str = ""
    missing_fields: list[str] | None = None
    timestamp_issue: bool = False
    observed_at: datetime | None = None


def _source_mode(raw: dict[str, Any] | None, explicit: str) -> SourceMode:
    mode = str((raw or {}).get("source_mode", explicit)).lower()
    if mode not in {"live", "replay"}:
        mode = explicit if explicit in {"live", "replay"} else "live"
    return mode  # type: ignore[return-value]


def _raw_object(raw: dict[str, Any] | str, *, source_mode: SourceMode, observed_at: datetime) -> tuple[dict[str, Any] | None, str | None]:
    if isinstance(raw, dict):
        return raw, None
    try:
        decoded = json.loads(raw)
    except json.JSONDecodeError as exc:
        return None, f"json parse error: {exc}"
    if not isinstance(decoded, dict):
        return None, "json event must be an object"
    return {"source_mode": source_mode, "ingested_at": observed_at.isoformat(), "payload": decoded}, None


def _observed_at(raw: dict[str, Any] | None, fallback: datetime) -> datetime:
    if raw is None:
        return fallback
    return ensure_utc(parse_event_timestamp(raw.get("ingested_at")) or fallback)


def classify_raw_event(
    raw: dict[str, Any] | str,
    *,
    source_mode: str = "live",
    observed_at: datetime | None = None,
) -> RawEventQualityClassification:
    """Classify a raw event as accepted, accepted-with-missing-fields, or rejected."""

    fallback_observed_at = ensure_utc(observed_at or utc_now())
    explicit_mode: SourceMode = "replay" if source_mode == "replay" else "live"
    raw_obj, parse_error = _raw_object(raw, source_mode=explicit_mode, observed_at=fallback_observed_at)
    mode = _source_mode(raw_obj, explicit_mode)
    event_observed_at = _observed_at(raw_obj, fallback_observed_at)

    if parse_error is not None:
        return RawEventQualityClassification(
            status="malformed_rejected",
            source_mode=mode,
            event=None,
            reason=parse_error,
            missing_fields=[],
            timestamp_issue=False,
            observed_at=event_observed_at,
        )

    if raw_obj and raw_obj.get("replay_error"):
        return RawEventQualityClassification(
            status="malformed_rejected",
            source_mode=mode,
            event=None,
            reason=str(raw_obj.get("replay_error")),
            missing_fields=[],
            timestamp_issue=False,
            observed_at=event_observed_at,
        )

    try:
        event = normalize_recentchange(raw_obj or {}, observed_at=event_observed_at)
    except ValueError as exc:
        return RawEventQualityClassification(
            status="malformed_rejected",
            source_mode=mode,
            event=None,
            reason=str(exc),
            missing_fields=[],
            timestamp_issue=False,
            observed_at=event_observed_at,
        )

    missing_fields = list(event.missing_fields)
    timestamp_issue = "timestamp" in missing_fields
    if missing_fields:
        return RawEventQualityClassification(
            status="accepted_missing_fields",
            source_mode=event.source_mode,
            event=event,
            reason="accepted with missing expected fields",
            missing_fields=missing_fields,
            timestamp_issue=timestamp_issue,
            observed_at=event.observed_at,
        )

    return RawEventQualityClassification(
        status="accepted",
        source_mode=event.source_mode,
        event=event,
        reason="accepted",
        missing_fields=[],
        timestamp_issue=False,
        observed_at=event.observed_at,
    )


def summarize_quality_counts(
    classifications: list[RawEventQualityClassification],
    *,
    source_mode: str,
    freshness_seconds: int,
    now: datetime | None = None,
) -> DataQualityCount:
    """Aggregate event quality classifications into dashboard snapshot counts."""

    mode: SourceMode = "replay" if source_mode == "replay" else "live"
    now_utc = ensure_utc(now or utc_now())
    accepted = [item for item in classifications if item.event is not None]
    rejected = [item for item in classifications if item.status == "malformed_rejected"]
    missing = [item for item in classifications if item.status == "accepted_missing_fields"]
    event_times = [ensure_utc(item.event.event_ts) for item in accepted if item.event is not None]
    observed_times = [ensure_utc(item.event.observed_at) for item in accepted if item.event is not None]
    latest_observed = max(observed_times) if observed_times else None

    window_start = min(event_times) if event_times else now_utc
    window_end = max(event_times) if event_times else now_utc
    freshness = classify_freshness(mode, latest_observed, now=now_utc, freshness_seconds=freshness_seconds)
    return DataQualityCount(
        window_start=window_start,
        window_end=window_end,
        source_mode=mode,
        malformed_rejected_count=len(rejected),
        missing_field_count=len(missing),
        accepted_count=len(accepted),
        latest_event_observed_at=latest_observed,
        freshness_status=freshness,
        notes=(
            f"accepted: {len(accepted)}; "
            f"missing-field accepted: {len(missing)}; "
            f"malformed/rejected: {len(rejected)}"
        ),
    )
