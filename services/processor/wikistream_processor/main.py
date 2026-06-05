"""Processor service: consume raw RecentChanges and write overview snapshots."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime, timedelta
import time
from typing import Any

from wikistream_observatory.config import load_config
from wikistream_observatory.kafka import create_consumer, decode_json_message, wait_for_broker
from wikistream_observatory.logging import configure_logging, log_event
from wikistream_observatory.models import ActivityMetric, BotSpikeSignal, NormalizedRecentChangeEvent
from wikistream_observatory.normalization import normalize_recentchange
from wikistream_observatory.signals import detect_bot_spikes
from wikistream_observatory.storage import remove_live_snapshots_older_than, write_parquet_snapshot
from wikistream_observatory.time_utils import ensure_utc, parse_event_timestamp, utc_now
from wikistream_observatory.windows import compute_activity_metrics


def _observed_at_from_raw(raw: dict[str, Any], fallback: datetime) -> datetime:
    parsed = parse_event_timestamp(raw.get("ingested_at"))
    return ensure_utc(parsed or fallback)


def process_raw_message_batch(raw_messages: Iterable[dict[str, Any]], *, observed_at: datetime | None = None) -> tuple[list[NormalizedRecentChangeEvent], list[ActivityMetric]]:
    """Normalize raw messages and compute activity metrics for one batch."""

    fallback_observed_at = ensure_utc(observed_at or utc_now())
    normalized: list[NormalizedRecentChangeEvent] = []
    for raw in raw_messages:
        try:
            normalized.append(normalize_recentchange(raw, observed_at=_observed_at_from_raw(raw, fallback_observed_at)))
        except ValueError:
            # Data-quality counters are added in a later phase; for US1 we drop
            # records that cannot support required dashboard metrics.
            continue
    return normalized, compute_activity_metrics(normalized, computed_at=fallback_observed_at)


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


def write_processor_snapshots(
    snapshot_path: str,
    normalized: list[NormalizedRecentChangeEvent],
    metrics: list[ActivityMetric],
    signals: list[BotSpikeSignal],
) -> None:
    """Write normalized events, activity metrics, and bot spike signals snapshots."""

    write_parquet_snapshot(normalized, snapshot_path, "normalized_events")
    write_parquet_snapshot(metrics, snapshot_path, "activity_metrics")
    write_parquet_snapshot(signals, snapshot_path, "bot_spike_signals")


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
            if message is None:
                pass
            elif message.error():
                log_event(logger, "consumer_error", "Kafka consumer error", error=str(message.error()))
            else:
                pending.append(decode_json_message(message.value()))

            should_flush = pending and (time.monotonic() - last_flush >= config.snapshots.interval_seconds)
            if should_flush:
                computed_at = utc_now()
                normalized, metrics = process_raw_message_batch(pending, observed_at=computed_at)
                signal_history.extend(normalized)
                signal_history = prune_signal_history(
                    signal_history,
                    now=computed_at,
                    current_window_minutes=config.signals.current_window_minutes,
                    baseline_window_minutes=config.signals.baseline_window_minutes,
                )
                signals = compute_bot_spike_signals(
                    signal_history,
                    computed_at=computed_at,
                    current_window_minutes=config.signals.current_window_minutes,
                    baseline_window_minutes=config.signals.baseline_window_minutes,
                    threshold_ratio=config.signals.threshold_ratio,
                    min_current_events=config.signals.min_events,
                    top_bots_limit=config.signals.top_bots_limit,
                )
                write_processor_snapshots(str(config.snapshots.path), normalized, metrics, signals)
                if config.mode == "live":
                    removed = remove_live_snapshots_older_than(config.snapshots.path, config.snapshots.live_retention_hours)
                else:
                    removed = 0
                log_event(
                    logger,
                    "snapshots_written",
                    "Wrote processor snapshots",
                    raw_count=len(pending),
                    normalized_count=len(normalized),
                    metric_count=len(metrics),
                    signal_count=len(signals),
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
