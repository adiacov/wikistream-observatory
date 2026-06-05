from __future__ import annotations

from datetime import datetime, timezone, timedelta

import pytest

from wikistream_observatory.normalization import normalize_recentchange


def test_normalizes_required_and_optional_fields():
    observed_at = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    event = normalize_recentchange(
        {
            "source_mode": "live",
            "ingested_at": observed_at.isoformat(),
            "payload": {
                "meta": {"id": "abc", "domain": "en.wikipedia.org"},
                "type": "edit",
                "timestamp": int(observed_at.timestamp()),
                "user": "ExampleBot",
                "bot": True,
                "namespace": 0,
                "title": "Example",
                "minor": False,
                "patrolled": True,
                "length": {"old": 10, "new": 15},
                "revision": {"old": 1, "new": 2},
                "comment": "update",
            },
        },
        observed_at=observed_at,
    )

    assert event.event_id == "abc"
    assert event.domain == "en.wikipedia.org"
    assert event.event_type == "edit"
    assert event.user_label == "ExampleBot"
    assert event.is_bot is True
    assert event.length_old == 10
    assert event.revision_new == 2
    assert event.comment_present is True
    assert event.missing_fields == []


def test_missing_bot_defaults_false_and_counts_missing_field():
    observed_at = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    event = normalize_recentchange(
        {"source_mode": "live", "payload": {"meta": {"domain": "en.wikipedia.org"}, "type": "edit"}},
        observed_at=observed_at,
    )

    assert event.is_bot is False
    assert "bot" in event.missing_fields
    assert event.quality_status == "accepted_missing_fields"


def test_timestamp_falls_back_when_missing_or_future_skewed():
    observed_at = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
    event = normalize_recentchange(
        {
            "source_mode": "live",
            "payload": {
                "meta": {"domain": "en.wikipedia.org"},
                "type": "edit",
                "timestamp": int((observed_at + timedelta(hours=1)).timestamp()),
            },
        },
        observed_at=observed_at,
    )

    assert event.event_ts == observed_at
    assert "timestamp" in event.missing_fields


def test_rejects_missing_domain_or_event_type():
    with pytest.raises(ValueError, match="domain"):
        normalize_recentchange({"source_mode": "live", "payload": {"type": "edit"}})
    with pytest.raises(ValueError, match="event type"):
        normalize_recentchange({"source_mode": "live", "payload": {"meta": {"domain": "en.wikipedia.org"}}})
