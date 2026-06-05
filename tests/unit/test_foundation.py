from __future__ import annotations

from datetime import datetime, timezone, timedelta
import json

from wikistream_observatory.config import load_config
from wikistream_observatory.kafka import decode_json_message, encode_json_message
from wikistream_observatory.models import NormalizedRecentChangeEvent
from wikistream_observatory.queries import snapshot_glob
from wikistream_observatory.storage import dataset_path, remove_live_snapshots_older_than
from wikistream_observatory.time_utils import bucket_bounds, classify_freshness, parse_event_timestamp


def test_load_config_defaults(monkeypatch):
    for name in list(__import__("os").environ):
        if name.startswith("WIKISTREAM_"):
            monkeypatch.delenv(name, raising=False)

    config = load_config()

    assert config.mode == "live"
    assert config.kafka.bootstrap_servers == "redpanda:9092"
    assert config.kafka.raw_topic == "raw_recentchange"
    assert config.freshness_seconds == 60
    assert config.signals.threshold_ratio == 3.0


def test_model_can_represent_normalized_event():
    now = datetime(2026, 6, 5, tzinfo=timezone.utc)
    event = NormalizedRecentChangeEvent(
        event_id="event-1",
        source_mode="live",
        domain="en.wikipedia.org",
        event_type="edit",
        event_ts=now,
        observed_at=now,
    )

    assert event.is_bot is False
    assert event.missing_fields == []
    assert event.quality_status == "accepted"


def test_normalized_schema_is_valid_json_object():
    with open("schemas/recentchange_normalized.schema.json", encoding="utf-8") as fh:
        schema = json.load(fh)

    assert schema["title"] == "NormalizedRecentChangeEvent"
    assert "event_id" in schema["required"]
    assert schema["properties"]["source_mode"]["enum"] == ["live", "replay"]


def test_time_helpers_parse_bucket_and_freshness():
    ts = parse_event_timestamp(1780639710)
    assert ts is not None
    start, end = bucket_bounds(ts, minutes=5)
    assert end - start == timedelta(minutes=5)

    now = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    assert classify_freshness("live", now - timedelta(seconds=30), now=now) == "fresh"
    assert classify_freshness("live", now - timedelta(seconds=90), now=now) == "stale"
    assert classify_freshness("replay", now - timedelta(days=1), now=now) == "replay"
    assert classify_freshness("live", None, now=now) == "no_data"


def test_storage_and_query_helpers_tolerate_missing_datasets(tmp_path):
    assert dataset_path(tmp_path, "activity_metrics") == tmp_path / "activity_metrics"
    assert snapshot_glob(tmp_path, "activity_metrics") is None
    assert remove_live_snapshots_older_than(tmp_path / "missing", retention_hours=6) == 0


def test_kafka_json_helpers_round_trip():
    encoded = encode_json_message({"source_mode": "live", "payload": {"type": "edit"}})
    assert decode_json_message(encoded) == {"source_mode": "live", "payload": {"type": "edit"}}
