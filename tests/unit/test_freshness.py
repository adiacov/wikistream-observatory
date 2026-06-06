from __future__ import annotations

from datetime import datetime, timezone, timedelta

from wikistream_observatory.time_utils import classify_freshness


NOW = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)


def test_live_data_is_fresh_within_configured_threshold():
    assert classify_freshness("live", NOW - timedelta(seconds=60), now=NOW, freshness_seconds=60) == "fresh"


def test_live_data_is_stale_after_configured_threshold():
    assert classify_freshness("live", NOW - timedelta(seconds=61), now=NOW, freshness_seconds=60) == "stale"


def test_no_live_data_reports_no_data():
    assert classify_freshness("live", None, now=NOW, freshness_seconds=60) == "no_data"


def test_replay_data_is_always_replay_not_live_fresh_or_stale():
    assert classify_freshness("replay", None, now=NOW, freshness_seconds=60) == "replay"
    assert classify_freshness("replay", NOW - timedelta(days=365), now=NOW, freshness_seconds=60) == "replay"
    assert classify_freshness("replay", NOW + timedelta(days=365), now=NOW, freshness_seconds=60) == "replay"
