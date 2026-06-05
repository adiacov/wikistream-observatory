from __future__ import annotations

from datetime import datetime, timezone, timedelta

from wikistream_observatory.models import NormalizedRecentChangeEvent
from wikistream_observatory.signals import detect_bot_spikes


BASE = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
DOMAIN = "example.wikipedia.org"


def _event(
    i: int,
    *,
    minutes_after_base: int,
    domain: str = DOMAIN,
    user_label: str = "ExampleBot",
    is_bot: bool = True,
) -> NormalizedRecentChangeEvent:
    ts = BASE + timedelta(minutes=minutes_after_base, seconds=i)
    return NormalizedRecentChangeEvent(
        event_id=f"e-{minutes_after_base}-{i}",
        source_mode="replay",
        domain=domain,
        event_type="edit",
        event_ts=ts,
        observed_at=ts,
        user_label=user_label,
        is_bot=is_bot,
    )


def _events(count: int, *, minutes_after_base: int, **kwargs) -> list[NormalizedRecentChangeEvent]:
    return [_event(i, minutes_after_base=minutes_after_base, **kwargs) for i in range(count)]


def test_detects_domain_level_bot_spike_with_baseline_ratio_and_thresholds():
    events: list[NormalizedRecentChangeEvent] = []
    # Baseline window is 12:00-12:30. Thirty bot events normalize to
    # five bot events per 5-minute window.
    for minute in range(0, 30):
        events.extend(_events(1, minutes_after_base=minute))
    # Current window is 12:30-12:35. Twenty bot events is 4.0x baseline.
    events.extend(_events(20, minutes_after_base=31))
    events.extend(_events(100, minutes_after_base=31, is_bot=False, user_label="HumanEditor"))

    signals = detect_bot_spikes(events, computed_at=BASE + timedelta(minutes=35))

    assert len(signals) == 1
    signal = signals[0]
    assert signal.domain == DOMAIN
    assert signal.source_mode == "replay"
    assert signal.window_start == BASE + timedelta(minutes=30)
    assert signal.window_end == BASE + timedelta(minutes=35)
    assert signal.baseline_window_start == BASE
    assert signal.baseline_window_end == BASE + timedelta(minutes=30)
    assert signal.current_bot_events == 20
    assert signal.baseline_bot_events_per_window == 5
    assert signal.spike_ratio == 4.0
    assert signal.threshold_ratio == 3.0
    assert signal.min_current_events == 20


def test_does_not_emit_when_current_count_or_ratio_is_below_threshold():
    baseline_events = []
    for minute in range(0, 30):
        baseline_events.extend(_events(1, minutes_after_base=minute))

    assert detect_bot_spikes(
        [*baseline_events, *_events(19, minutes_after_base=31)],
        computed_at=BASE + timedelta(minutes=35),
    ) == []

    high_baseline_events = []
    for minute in range(0, 30):
        high_baseline_events.extend(_events(4, minutes_after_base=minute))
    assert detect_bot_spikes(
        [*high_baseline_events, *_events(20, minutes_after_base=31)],
        computed_at=BASE + timedelta(minutes=35),
    ) == []


def test_zero_baseline_signal_uses_categorical_label_not_infinite_ratio():
    signals = detect_bot_spikes(
        _events(20, minutes_after_base=31),
        computed_at=BASE + timedelta(minutes=35),
    )

    assert len(signals) == 1
    signal = signals[0]
    assert signal.baseline_bot_events_per_window == 0
    assert signal.spike_ratio is None
    assert "new-or-zero-baseline" in signal.wording


def test_top_contributing_bot_labels_are_limited_to_three_and_sorted():
    events: list[NormalizedRecentChangeEvent] = []
    events.extend(_events(20, minutes_after_base=31, user_label="TopBot"))
    events.extend(_events(10, minutes_after_base=31, user_label="SecondBot"))
    events.extend(_events(5, minutes_after_base=31, user_label="ThirdBot"))
    events.extend(_events(4, minutes_after_base=31, user_label="FourthBot"))

    signals = detect_bot_spikes(events, computed_at=BASE + timedelta(minutes=35), top_bots_limit=3)

    assert len(signals) == 1
    contributors = signals[0].top_contributing_bot_labels
    assert [(c.user_label, c.event_count) for c in contributors] == [
        ("TopBot", 20),
        ("SecondBot", 10),
        ("ThirdBot", 5),
    ]


def test_non_bot_activity_and_other_domains_do_not_create_bot_spike():
    events = [
        *_events(100, minutes_after_base=31, is_bot=False, user_label="HumanEditor"),
        *_events(10, minutes_after_base=31, domain="other.wikipedia.org"),
    ]

    assert detect_bot_spikes(events, computed_at=BASE + timedelta(minutes=35)) == []
