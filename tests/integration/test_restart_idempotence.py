from __future__ import annotations

from datetime import datetime, timezone
import json

from services.ingestor.wikistream_ingestor.replay import read_replay_records
from services.processor.wikistream_processor.main import process_replay_records


EXPECTED_SIGNAL_DOMAIN = "example.wikipedia.org"


def _event(*, event_id: str, timestamp: datetime, user: str, bot: bool, domain: str = EXPECTED_SIGNAL_DOMAIN) -> dict[str, object]:
    return {
        "meta": {"id": event_id, "domain": domain},
        "type": "edit",
        "timestamp": int(timestamp.timestamp()),
        "user": user,
        "bot": bot,
        "namespace": 0,
        "title": f"Idempotence page {event_id}",
        "minor": False,
        "patrolled": True,
        "length": {"old": 100, "new": 105},
        "revision": {"old": 1, "new": 2},
        "comment": "Representative restart/idempotence replay event",
    }


def _write_replay_sample(path, lines: list[str]) -> None:
    path.write_text("\n".join(lines) + "\n", encoding="utf-8")


def _quality_tuple(result) -> tuple[int, int, int, str]:
    return (
        result.quality_counts.accepted_count,
        result.quality_counts.missing_field_count,
        result.quality_counts.malformed_rejected_count,
        result.quality_counts.freshness_status,
    )


def _signal_tuple(result) -> tuple[str, int, float | None]:
    assert len(result.bot_spike_signals) == 1
    signal = result.bot_spike_signals[0]
    return signal.domain, signal.current_bot_events, signal.spike_ratio


def _event_volume(result) -> float:
    return sum(metric.value for metric in result.activity_metrics if metric.metric_name == "events_per_minute")


def test_replay_restart_reprocessing_uses_deterministic_event_ids_for_idempotent_metrics_and_signals(tmp_path):
    """Duplicate replay delivery should not inflate normalized facts, metrics, or signals."""

    sample = tmp_path / "restart_idempotence_sample.jsonl"
    computed_at = datetime(2026, 6, 5, 12, 40, tzinfo=timezone.utc)
    baseline_ts = datetime(2026, 6, 5, 12, 10, tzinfo=timezone.utc)
    spike_ts = datetime(2026, 6, 5, 12, 36, tzinfo=timezone.utc)

    unique_lines: list[str] = []
    for i in range(5):
        unique_lines.append(json.dumps(_event(event_id=f"baseline-{i}", timestamp=baseline_ts, user="BaselineBot", bot=True)))
    for i in range(20):
        payload = _event(event_id=f"spike-{i}", timestamp=spike_ts, user="SpikeBot", bot=True)
        unique_lines.append(json.dumps({"source_mode": "replay", "payload": payload}))
    unique_lines.append(json.dumps(_event(event_id="human-context", timestamp=spike_ts, user="HumanEditor", bot=False, domain="commons.wikimedia.org")))

    _write_replay_sample(sample, unique_lines)
    first_run = process_replay_records(list(read_replay_records(sample)), observed_at=computed_at)
    second_run = process_replay_records(list(read_replay_records(sample)), observed_at=computed_at)

    # Rerunning replay from the same file is deterministic.
    assert [event.event_id for event in first_run.normalized_events] == [event.event_id for event in second_run.normalized_events]
    assert _event_volume(first_run) == _event_volume(second_run) == 26.0
    assert _signal_tuple(first_run) == _signal_tuple(second_run) == (EXPECTED_SIGNAL_DOMAIN, 20, 24.0)
    assert _quality_tuple(first_run) == _quality_tuple(second_run) == (26, 0, 0, "replay")

    duplicate_sample = tmp_path / "restart_idempotence_duplicate_delivery.jsonl"
    _write_replay_sample(duplicate_sample, unique_lines + unique_lines)
    duplicate_delivery = process_replay_records(list(read_replay_records(duplicate_sample)), observed_at=computed_at)

    # Simulated restart/reprocessing duplicates have the same deterministic event ids
    # and therefore must not double dashboard facts, event-volume metrics, or signals.
    assert len(duplicate_delivery.normalized_events) == len(first_run.normalized_events) == 26
    assert [event.event_id for event in duplicate_delivery.normalized_events] == [event.event_id for event in first_run.normalized_events]
    assert _event_volume(duplicate_delivery) == _event_volume(first_run) == 26.0
    assert _signal_tuple(duplicate_delivery) == _signal_tuple(first_run) == (EXPECTED_SIGNAL_DOMAIN, 20, 24.0)

    # Quality counts still describe raw replay delivery evidence, while metrics/signals
    # are protected from duplicate accepted event IDs.
    assert _quality_tuple(duplicate_delivery) == (52, 0, 0, "replay")
