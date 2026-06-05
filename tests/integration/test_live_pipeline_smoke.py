from __future__ import annotations

from datetime import datetime, timezone

from services.processor.wikistream_processor.main import process_raw_message_batch


def test_live_pipeline_smoke_normalizes_and_aggregates_fake_payload(tmp_path):
    observed_at = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    raw_messages = [
        {
            "source_mode": "live",
            "ingested_at": observed_at.isoformat(),
            "payload": {
                "meta": {"id": "abc", "domain": "en.wikipedia.org"},
                "type": "edit",
                "timestamp": int(observed_at.timestamp()),
                "user": "ExampleBot",
                "bot": True,
            },
        }
    ]

    normalized, metrics = process_raw_message_batch(raw_messages, observed_at=observed_at)

    assert len(normalized) == 1
    assert normalized[0].domain == "en.wikipedia.org"
    assert any(metric.metric_name == "events_per_minute" for metric in metrics)
    assert any(metric.metric_name == "bot_share" for metric in metrics)
