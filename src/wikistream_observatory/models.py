"""Typed data structures for normalized events, metrics, signals, and quality counts."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Literal

SourceMode = Literal["live", "replay"]
QualityStatus = Literal["accepted", "accepted_missing_fields", "rejected"]
FreshnessStatus = Literal["fresh", "stale", "replay", "no_data"]


@dataclass(frozen=True)
class RecentChangeRawEvent:
    source_mode: SourceMode
    raw_payload: dict[str, Any] | str
    ingested_at: datetime
    event_id: str | None = None
    kafka_topic: str = "raw_recentchange"


@dataclass(frozen=True)
class NormalizedRecentChangeEvent:
    event_id: str
    source_mode: SourceMode
    domain: str
    event_type: str
    event_ts: datetime
    observed_at: datetime
    user_label: str | None = None
    is_bot: bool = False
    namespace: int | None = None
    title: str | None = None
    minor: bool | None = None
    patrolled: bool | None = None
    length_old: int | None = None
    length_new: int | None = None
    revision_old: int | None = None
    revision_new: int | None = None
    comment_present: bool = False
    missing_fields: list[str] = field(default_factory=list)
    quality_status: QualityStatus = "accepted"


@dataclass(frozen=True)
class ActivityMetric:
    window_start: datetime
    window_end: datetime
    source_mode: SourceMode
    metric_name: str
    value: float
    record_count: int
    computed_at: datetime
    domain: str | None = None
    event_type: str | None = None
    is_bot: bool | None = None


@dataclass(frozen=True)
class BotContributor:
    user_label: str
    event_count: int


@dataclass(frozen=True)
class BotSpikeSignal:
    signal_id: str
    source_mode: SourceMode
    domain: str
    window_start: datetime
    window_end: datetime
    current_bot_events: int
    baseline_window_start: datetime
    baseline_window_end: datetime
    baseline_bot_events_per_window: float
    spike_ratio: float | None
    threshold_ratio: float
    min_current_events: int
    top_contributing_bot_labels: list[BotContributor]
    wording: str
    limitations: str
    computed_at: datetime


@dataclass(frozen=True)
class DataQualityCount:
    window_start: datetime
    window_end: datetime
    source_mode: SourceMode
    malformed_rejected_count: int
    missing_field_count: int
    accepted_count: int
    latest_event_observed_at: datetime | None
    freshness_status: FreshnessStatus
    notes: str = ""
