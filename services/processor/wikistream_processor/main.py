"""Processor service: consume raw RecentChanges and write overview snapshots."""

from __future__ import annotations

from collections.abc import Iterable
from datetime import datetime
import time
from typing import Any

from wikistream_observatory.config import load_config
from wikistream_observatory.kafka import create_consumer, decode_json_message, wait_for_broker
from wikistream_observatory.logging import configure_logging, log_event
from wikistream_observatory.models import ActivityMetric, NormalizedRecentChangeEvent
from wikistream_observatory.normalization import normalize_recentchange
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


def write_overview_snapshots(snapshot_path: str, normalized: list[NormalizedRecentChangeEvent], metrics: list[ActivityMetric]) -> None:
    """Write normalized events and activity metrics snapshots."""

    write_parquet_snapshot(normalized, snapshot_path, "normalized_events")
    write_parquet_snapshot(metrics, snapshot_path, "activity_metrics")


def run_processor() -> None:
    config = load_config()
    logger = configure_logging("processor", config.mode)
    wait_for_broker(config.kafka.bootstrap_servers)
    consumer = create_consumer(config.kafka.bootstrap_servers, config.kafka.consumer_group, [config.kafka.raw_topic])

    log_event(logger, "processor_started", "Starting processor", topic=config.kafka.raw_topic)
    pending: list[dict[str, Any]] = []
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
                normalized, metrics = process_raw_message_batch(pending)
                write_overview_snapshots(str(config.snapshots.path), normalized, metrics)
                if config.mode == "live":
                    removed = remove_live_snapshots_older_than(config.snapshots.path, config.snapshots.live_retention_hours)
                else:
                    removed = 0
                log_event(
                    logger,
                    "snapshots_written",
                    "Wrote overview snapshots",
                    raw_count=len(pending),
                    normalized_count=len(normalized),
                    metric_count=len(metrics),
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
