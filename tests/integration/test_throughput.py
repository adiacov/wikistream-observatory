from __future__ import annotations

from datetime import datetime, timedelta, timezone
import time
import tracemalloc

from services.dashboard.app.data import load_overview_metrics, load_recent_events
from services.processor.wikistream_processor.main import process_raw_messages, write_processor_snapshots


def _raw_replay_event(index: int, event_ts: datetime) -> dict[str, object]:
    domain = f"throughput-{index % 30:02d}.wikipedia.org"
    return {
        "source_mode": "replay",
        "ingested_at": event_ts.isoformat(),
        "payload": {
            "meta": {"id": f"throughput-{index:04d}", "domain": domain},
            "type": "edit" if index % 5 else "new",
            "namespace": 0,
            "title": f"Throughput page {index}",
            "timestamp": int(event_ts.timestamp()),
            "user": f"ThroughputUser{index % 25}",
            "bot": index % 7 == 0,
            "minor": False,
            "patrolled": True,
            "length": {"old": 100 + index, "new": 105 + index},
            "revision": {"old": 10_000 + index, "new": 20_000 + index},
            "comment": "Synthetic throughput validation event",
        },
    }


def test_processor_handles_300_events_per_minute_with_bounded_memory_and_summary_outputs(tmp_path):
    """Synthetic replay load should exceed the MVP 300 events/minute target.

    The test uses two event-time minutes with 300 events each. It validates the
    core processor path, snapshot writes, and dashboard loaders without listing
    every event in dashboard-facing outputs.
    """

    target_events_per_minute = 300
    minute_count = 2
    event_count = target_events_per_minute * minute_count
    start_ts = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    observed_at = start_ts + timedelta(minutes=minute_count, seconds=5)

    raw_messages = [
        _raw_replay_event(index, start_ts + timedelta(minutes=index // target_events_per_minute))
        for index in range(event_count)
    ]

    tracemalloc.start()
    started = time.perf_counter()
    try:
        result = process_raw_messages(raw_messages, observed_at=observed_at, compute_signals=True)
        elapsed_seconds = time.perf_counter() - started
        _, peak_bytes = tracemalloc.get_traced_memory()
    finally:
        tracemalloc.stop()

    processed_per_minute = event_count / (elapsed_seconds / 60)
    assert processed_per_minute >= target_events_per_minute
    assert peak_bytes < 32 * 1024 * 1024

    assert len(result.normalized_events) == event_count
    assert result.quality_counts.accepted_count == event_count
    assert result.quality_counts.malformed_rejected_count == 0
    assert result.quality_counts.missing_field_count == 0

    event_volume_metrics = [metric for metric in result.activity_metrics if metric.metric_name == "events_per_minute"]
    assert [metric.value for metric in event_volume_metrics] == [300.0, 300.0]

    top_domain_metrics = [metric for metric in result.activity_metrics if metric.metric_name == "top_domains"]
    assert len(top_domain_metrics) == 40  # top 20 domains for each of 2 minute buckets, not all 30 domains.

    write_processor_snapshots(
        str(tmp_path),
        result.normalized_events,
        result.activity_metrics,
        result.bot_spike_signals,
        result.quality_counts,
    )

    dashboard_metrics = load_overview_metrics(tmp_path, source_mode="replay")
    dashboard_events = load_recent_events(tmp_path, source_mode="replay")

    assert 0 < len(dashboard_metrics) < event_count
    assert any(row["metric_name"] == "events_per_minute" and row["value"] == 300.0 for row in dashboard_metrics)
    assert len(dashboard_events) == 100
