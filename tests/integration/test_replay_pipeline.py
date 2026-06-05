from __future__ import annotations

from datetime import datetime, timezone
import json

from services.ingestor.wikistream_ingestor.replay import read_replay_records
from services.processor.wikistream_processor.main import process_replay_records


EXPECTED_SIGNAL_DOMAIN = "example.wikipedia.org"


def _event(*, event_id: str, domain: str = EXPECTED_SIGNAL_DOMAIN, timestamp: datetime, user: str, bot: bool, event_type: str = "edit") -> dict[str, object]:
    return {
        "meta": {"id": event_id, "domain": domain},
        "type": event_type,
        "timestamp": int(timestamp.timestamp()),
        "user": user,
        "bot": bot,
        "namespace": 0,
        "title": f"Page {event_id}",
    }


def test_replay_pipeline_populates_overview_signal_and_quality_counts(tmp_path):
    """Replay JSONL should exercise parsing, normalization, metrics, signals, and quality accounting."""

    sample = tmp_path / "recentchange_sample.jsonl"
    computed_at = datetime(2026, 6, 5, 12, 40, tzinfo=timezone.utc)
    baseline_ts = datetime(2026, 6, 5, 12, 10, tzinfo=timezone.utc)
    spike_ts = datetime(2026, 6, 5, 12, 36, tzinfo=timezone.utc)

    lines: list[str] = []

    # Low baseline: five bot-flagged events in the previous 30-minute baseline window.
    for i in range(5):
        lines.append(json.dumps(_event(event_id=f"baseline-{i}", timestamp=baseline_ts, user="ExampleBot", bot=True)))

    # Current 5-minute spike window: twenty bot-flagged events on the expected domain.
    for i in range(20):
        payload = _event(event_id=f"spike-{i}", timestamp=spike_ts, user="SpikeBot", bot=True)
        lines.append(json.dumps({"source_mode": "replay", "pacing_ms": 1, "payload": payload}))

    # Non-bot activity on another domain to prove overview metrics are not bot-only.
    lines.append(
        json.dumps(
            _event(
                event_id="human-1",
                domain="commons.wikimedia.org",
                timestamp=spike_ts,
                user="HumanEditor",
                bot=False,
                event_type="new",
            )
        )
    )

    # Accepted missing-field example: missing bot defaults false and should be counted separately.
    lines.append(json.dumps({"meta": {"id": "missing-bot", "domain": "fr.wikipedia.org"}, "type": "edit", "timestamp": int(spike_ts.timestamp())}))

    # Rejected/malformed examples: one invalid JSON line and one JSON object missing required type/domain.
    lines.append("{not valid json")
    lines.append(json.dumps({"source_mode": "replay", "payload": {"meta": {"id": "missing-required"}}}))

    sample.write_text("\n".join(lines) + "\n", encoding="utf-8")

    replay_records = list(read_replay_records(sample))
    result = process_replay_records(replay_records, observed_at=computed_at)

    assert len(result.normalized_events) == 27
    assert {event.source_mode for event in result.normalized_events} == {"replay"}

    assert any(metric.metric_name == "events_per_minute" and metric.source_mode == "replay" for metric in result.activity_metrics)
    assert any(
        metric.metric_name == "top_domains"
        and metric.domain == EXPECTED_SIGNAL_DOMAIN
        and metric.value >= 20
        for metric in result.activity_metrics
    )
    assert any(metric.metric_name == "event_type_breakdown" and metric.event_type == "new" for metric in result.activity_metrics)
    assert any(metric.metric_name == "bot_share" and metric.record_count > 0 for metric in result.activity_metrics)

    assert len(result.bot_spike_signals) == 1
    signal = result.bot_spike_signals[0]
    assert signal.source_mode == "replay"
    assert signal.domain == EXPECTED_SIGNAL_DOMAIN
    assert signal.current_bot_events == 20
    assert signal.threshold_ratio == 3.0
    assert signal.min_current_events == 20
    assert signal.spike_ratio is not None and signal.spike_ratio >= 3.0

    assert result.quality_counts.source_mode == "replay"
    assert result.quality_counts.accepted_count == 27
    assert result.quality_counts.missing_field_count == 1
    assert result.quality_counts.malformed_rejected_count == 2
    assert result.quality_counts.freshness_status == "replay"
