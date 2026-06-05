from __future__ import annotations

from datetime import datetime, timezone, timedelta

from wikistream_observatory.models import NormalizedRecentChangeEvent
from wikistream_observatory.windows import compute_activity_metrics


def _event(i: int, *, domain: str, event_type: str = "edit", is_bot: bool = False) -> NormalizedRecentChangeEvent:
    ts = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc) + timedelta(seconds=i)
    return NormalizedRecentChangeEvent(
        event_id=f"e{i}",
        source_mode="live",
        domain=domain,
        event_type=event_type,
        event_ts=ts,
        observed_at=ts,
        is_bot=is_bot,
    )


def test_activity_metrics_include_volume_domains_types_and_bot_share():
    events = [
        _event(1, domain="en.wikipedia.org", event_type="edit", is_bot=True),
        _event(2, domain="en.wikipedia.org", event_type="new", is_bot=False),
        _event(3, domain="de.wikipedia.org", event_type="edit", is_bot=False),
    ]

    metrics = compute_activity_metrics(events)

    by_name = {(m.metric_name, m.domain, m.event_type, m.is_bot): m for m in metrics}
    assert by_name[("events_per_minute", None, None, None)].value == 3
    assert by_name[("top_domains", "en.wikipedia.org", None, None)].value == 2
    assert by_name[("event_type_breakdown", None, "edit", None)].value == 2
    assert by_name[("bot_share", None, None, True)].value == 1 / 3
    assert by_name[("non_bot_share", None, None, False)].value == 2 / 3


def test_activity_metrics_are_bucketed_per_minute():
    first = _event(1, domain="en.wikipedia.org")
    second = NormalizedRecentChangeEvent(
        event_id="later",
        source_mode="live",
        domain="en.wikipedia.org",
        event_type="edit",
        event_ts=first.event_ts + timedelta(minutes=1, seconds=5),
        observed_at=first.observed_at,
    )

    metrics = [m for m in compute_activity_metrics([first, second]) if m.metric_name == "events_per_minute"]

    assert len(metrics) == 2
    assert {m.value for m in metrics} == {1}
