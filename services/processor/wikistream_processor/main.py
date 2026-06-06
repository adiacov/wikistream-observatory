"""Processor service: consume raw RecentChanges and write overview snapshots."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass
from datetime import datetime, timedelta
import time
from typing import Any

from wikistream_observatory.config import load_config
from wikistream_observatory.kafka import create_consumer, decode_json_message, wait_for_broker
from wikistream_observatory.logging import configure_logging, log_event
from wikistream_observatory.models import ActivityMetric, BotSpikeSignal, DataQualityCount, NormalizedRecentChangeEvent
from wikistream_observatory.normalization import normalize_recentchange
from wikistream_observatory.signals import detect_bot_spikes
from wikistream_observatory.storage import remove_live_snapshots_older_than, write_parquet_snapshot
from wikistream_observatory.time_utils import ensure_utc, floor_to_bucket, parse_event_timestamp, utc_now
from wikistream_observatory.windows import compute_activity_metrics


@dataclass(frozen=True)
class ProcessorBatchResult:
    normalized_events: list[NormalizedRecentChangeEvent]
    activity_metrics: list[ActivityMetric]
    bot_spike_signals: list[BotSpikeSignal]
    quality_counts: DataQualityCount


def _observed_at_from_raw(raw: dict[str, Any], fallback: datetime) -> datetime:
    parsed = parse_event_timestamp(raw.get("ingested_at"))
    return ensure_utc(parsed or fallback)


def _source_mode_for_quality(raw_messages: list[dict[str, Any]], normalized: list[NormalizedRecentChangeEvent]) -> str:
    if normalized:
        return normalized[0].source_mode
    if any(str(raw.get("source_mode", "")).lower() == "replay" for raw in raw_messages):
        return "replay"
    return "live"


def _quality_counts(
    raw_messages: list[dict[str, Any]],
    normalized: list[NormalizedRecentChangeEvent],
    *,
    malformed_rejected_count: int,
    missing_field_count: int,
    observed_at: datetime,
) -> DataQualityCount:
    event_times = [ensure_utc(event.event_ts) for event in normalized]
    observed_times = [ensure_utc(event.observed_at) for event in normalized]
    window_start = min(event_times) if event_times else observed_at
    window_end = max(event_times) if event_times else observed_at
    source_mode = _source_mode_for_quality(raw_messages, normalized)
    return DataQualityCount(
        window_start=window_start,
        window_end=window_end,
        source_mode=source_mode,  # type: ignore[arg-type]
        malformed_rejected_count=malformed_rejected_count,
        missing_field_count=missing_field_count,
        accepted_count=len(normalized),
        latest_event_observed_at=max(observed_times) if observed_times else None,
        freshness_status="replay" if source_mode == "replay" else "fresh",
        notes="Replay batch quality counts include malformed replay records and records rejected during normalization.",
    )


def process_raw_messages(
    raw_messages: Iterable[dict[str, Any]],
    *,
    observed_at: datetime | None = None,
    compute_signals: bool = False,
    signal_history: list[NormalizedRecentChangeEvent] | None = None,
    current_window_minutes: int = 5,
    baseline_window_minutes: int = 30,
    threshold_ratio: float = 3.0,
    min_current_events: int = 20,
    top_bots_limit: int = 3,
) -> ProcessorBatchResult:
    """Normalize raw messages and compute metrics, signals, and quality counts."""

    fallback_observed_at = ensure_utc(observed_at or utc_now())
    raw_list = list(raw_messages)
    normalized: list[NormalizedRecentChangeEvent] = []
    malformed_rejected_count = 0
    missing_field_count = 0
    for raw in raw_list:
        if raw.get("replay_error"):
            malformed_rejected_count += 1
            continue
        try:
            event = normalize_recentchange(raw, observed_at=_observed_at_from_raw(raw, fallback_observed_at))
        except ValueError:
            malformed_rejected_count += 1
            continue
        normalized.append(event)
        # Phase 6 tracks the replay sample's accepted missing-field example. The
        # fuller Phase 7 data-quality implementation expands this to all expected
        # missing optional fields and timestamp issues.
        if "bot" in event.missing_fields:
            missing_field_count += 1

    metrics = compute_activity_metrics(normalized, computed_at=fallback_observed_at)
    signal_events = signal_history if signal_history is not None and signal_history else normalized
    signal_computed_at = fallback_observed_at
    if compute_signals and signal_events and signal_events[0].source_mode == "replay":
        max_event_ts = max(ensure_utc(event.event_ts) for event in signal_events)
        signal_computed_at = floor_to_bucket(max_event_ts, current_window_minutes) + timedelta(minutes=current_window_minutes)
    signals = (
        compute_bot_spike_signals(
            signal_events,
            computed_at=signal_computed_at,
            current_window_minutes=current_window_minutes,
            baseline_window_minutes=baseline_window_minutes,
            threshold_ratio=threshold_ratio,
            min_current_events=min_current_events,
            top_bots_limit=top_bots_limit,
        )
        if compute_signals
        else []
    )
    return ProcessorBatchResult(
        normalized_events=normalized,
        activity_metrics=metrics,
        bot_spike_signals=signals,
        quality_counts=_quality_counts(
            raw_list,
            normalized,
            malformed_rejected_count=malformed_rejected_count,
            missing_field_count=missing_field_count,
            observed_at=fallback_observed_at,
        ),
    )


def process_raw_message_batch(raw_messages: Iterable[dict[str, Any]], *, observed_at: datetime | None = None) -> tuple[list[NormalizedRecentChangeEvent], list[ActivityMetric]]:
    """Normalize raw messages and compute activity metrics for one batch."""

    result = process_raw_messages(raw_messages, observed_at=observed_at)
    return result.normalized_events, result.activity_metrics


def compute_bot_spike_signals(
    events: list[NormalizedRecentChangeEvent],
    *,
    computed_at: datetime | None = None,
    current_window_minutes: int = 5,
    baseline_window_minutes: int = 30,
    threshold_ratio: float = 3.0,
    min_current_events: int = 20,
    top_bots_limit: int = 3,
) -> list[BotSpikeSignal]:
    """Compute configured bot spike signals for normalized event history."""

    return detect_bot_spikes(
        events,
        computed_at=computed_at,
        current_window_minutes=current_window_minutes,
        baseline_window_minutes=baseline_window_minutes,
        threshold_ratio=threshold_ratio,
        min_current_events=min_current_events,
        top_bots_limit=top_bots_limit,
    )


def prune_signal_history(
    events: list[NormalizedRecentChangeEvent],
    *,
    now: datetime,
    current_window_minutes: int,
    baseline_window_minutes: int,
) -> list[NormalizedRecentChangeEvent]:
    """Keep only events needed for the current plus baseline signal windows."""

    cutoff = ensure_utc(now) - timedelta(minutes=current_window_minutes + baseline_window_minutes)
    return [event for event in events if ensure_utc(event.event_ts) >= cutoff]


def process_replay_records(records: Iterable[Any], *, observed_at: datetime | None = None) -> ProcessorBatchResult:
    """Process replay records directly for deterministic tests and validation."""

    raw_messages: list[dict[str, Any]] = []
    fallback_observed_at = ensure_utc(observed_at or utc_now())
    for record in records:
        payload = getattr(record, "payload", None)
        if getattr(record, "malformed", False) or payload is None:
            raw_messages.append(
                {
                    "source_mode": "replay",
                    "ingested_at": fallback_observed_at.isoformat(),
                    "payload": None,
                    "replay_error": getattr(record, "error", "malformed replay record"),
                    "replay_line_number": getattr(record, "line_number", None),
                    "replay_raw_line": getattr(record, "raw_line", None),
                }
            )
        else:
            raw_messages.append({"source_mode": "replay", "ingested_at": fallback_observed_at.isoformat(), "payload": payload})
    return process_raw_messages(raw_messages, observed_at=fallback_observed_at, compute_signals=True)


def write_processor_snapshots(
    snapshot_path: str,
    normalized: list[NormalizedRecentChangeEvent],
    metrics: list[ActivityMetric],
    signals: list[BotSpikeSignal],
    quality_counts: DataQualityCount | None = None,
) -> None:
    """Write normalized events, activity metrics, bot spike signals, and optional quality snapshots."""

    write_parquet_snapshot(normalized, snapshot_path, "normalized_events")
    write_parquet_snapshot(metrics, snapshot_path, "activity_metrics")
    write_parquet_snapshot(signals, snapshot_path, "bot_spike_signals")
    if quality_counts is not None:
        write_parquet_snapshot([quality_counts], snapshot_path, "data_quality_counts")


def run_processor() -> None:
    config = load_config()
    logger = configure_logging("processor", config.mode)
    wait_for_broker(config.kafka.bootstrap_servers)
    consumer = create_consumer(config.kafka.bootstrap_servers, config.kafka.consumer_group, [config.kafka.raw_topic])

    log_event(logger, "processor_started", "Starting processor", topic=config.kafka.raw_topic)
    pending: list[dict[str, Any]] = []
    signal_history: list[NormalizedRecentChangeEvent] = []
    last_flush = time.monotonic()

    try:
        while True:
            message = consumer.poll(1.0)
            got_message = False
            if message is None:
                pass
            elif message.error():
                log_event(logger, "consumer_error", "Kafka consumer error", error=str(message.error()))
            else:
                pending.append(decode_json_message(message.value()))
                got_message = True

            elapsed = time.monotonic() - last_flush
            should_flush = pending and (elapsed >= config.snapshots.interval_seconds or (config.mode == "replay" and not got_message))
            if should_flush:
                computed_at = utc_now()
                normalized_for_history, _ = process_raw_message_batch(pending, observed_at=computed_at)
                signal_history.extend(normalized_for_history)
                if config.mode == "live":
                    signal_history = prune_signal_history(
                        signal_history,
                        now=computed_at,
                        current_window_minutes=config.signals.current_window_minutes,
                        baseline_window_minutes=config.signals.baseline_window_minutes,
                    )
                result = process_raw_messages(
                    pending,
                    observed_at=computed_at,
                    compute_signals=True,
                    signal_history=signal_history,
                    current_window_minutes=config.signals.current_window_minutes,
                    baseline_window_minutes=config.signals.baseline_window_minutes,
                    threshold_ratio=config.signals.threshold_ratio,
                    min_current_events=config.signals.min_events,
                    top_bots_limit=config.signals.top_bots_limit,
                )
                write_processor_snapshots(
                    str(config.snapshots.path),
                    result.normalized_events,
                    result.activity_metrics,
                    result.bot_spike_signals,
                    result.quality_counts,
                )
                if config.mode == "live":
                    removed = remove_live_snapshots_older_than(config.snapshots.path, config.snapshots.live_retention_hours)
                else:
                    removed = 0
                log_event(
                    logger,
                    "snapshots_written",
                    "Wrote processor snapshots",
                    raw_count=len(pending),
                    normalized_count=len(result.normalized_events),
                    metric_count=len(result.activity_metrics),
                    signal_count=len(result.bot_spike_signals),
                    malformed_rejected_count=result.quality_counts.malformed_rejected_count,
                    missing_field_count=result.quality_counts.missing_field_count,
                    signal_history_count=len(signal_history),
                    old_snapshot_count=removed,
                )
                pending.clear()
                last_flush = time.monotonic()
    finally:
        consumer.close()


def main() -> None:
    run_processor()


if __name__ == "__main__":
    main()
