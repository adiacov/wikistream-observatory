from __future__ import annotations

from datetime import datetime, timezone, timedelta
from pathlib import Path

from wikistream_observatory.models import NormalizedRecentChangeEvent
from wikistream_observatory.signals import detect_bot_spikes


BASE = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)
DOMAIN = "example.wikipedia.org"


FORBIDDEN_ACCUSATION_TERMS = (
    "bad bot",
    "malicious",
    "guilty",
    "abusive",
    "culprit",
    "offender",
)


def _bot_event(i: int, *, minutes_after_base: int, user_label: str = "ExampleBot") -> NormalizedRecentChangeEvent:
    ts = BASE + timedelta(minutes=minutes_after_base, seconds=i)
    return NormalizedRecentChangeEvent(
        event_id=f"bot-{minutes_after_base}-{i}",
        source_mode="replay",
        domain=DOMAIN,
        event_type="edit",
        event_ts=ts,
        observed_at=ts,
        user_label=user_label,
        is_bot=True,
    )


def _events(count: int, *, minutes_after_base: int, user_label: str = "ExampleBot") -> list[NormalizedRecentChangeEvent]:
    return [_bot_event(i, minutes_after_base=minutes_after_base, user_label=user_label) for i in range(count)]


def _sample_signal_text() -> tuple[str, str]:
    signals = detect_bot_spikes(
        [*_events(20, minutes_after_base=31, user_label="ExampleBot")],
        computed_at=BASE + timedelta(minutes=35),
    )
    assert len(signals) == 1
    return signals[0].wording.lower(), signals[0].limitations.lower()


def test_bot_spike_wording_uses_observability_language_not_accusations():
    wording, limitations = _sample_signal_text()
    combined = f"{wording}\n{limitations}"

    assert "signal" in combined
    assert "spike" in combined
    assert "domain" in combined
    assert "review" in combined
    for term in FORBIDDEN_ACCUSATION_TERMS:
        assert term not in combined


def test_bot_spike_limitations_state_no_enforcement_or_account_accusation():
    _wording, limitations = _sample_signal_text()

    assert "not an enforcement decision" in limitations
    assert "not" in limitations and "account-level accusation" in limitations
    assert "context" in limitations or "contextual" in limitations


def test_readme_and_dashboard_avoid_accusation_or_conduct_conclusion_terms():
    user_facing_text = "\n".join(
        [
            Path("README.md").read_text(encoding="utf-8"),
            Path("services/dashboard/app/main.py").read_text(encoding="utf-8"),
        ]
    ).lower()

    forbidden_terms = (
        "bad bot",
        "malicious",
        "guilty",
        "abusive",
        "culprit",
        "offender",
        "abuse detector",
        "proof of misuse",
        "doing something wrong",
    )
    for term in forbidden_terms:
        assert term not in user_facing_text


def test_dashboard_ui_hides_internal_snapshot_path_and_uses_current_streamlit_width_api():
    dashboard_source = Path("services/dashboard/app/main.py").read_text(encoding="utf-8")

    assert "Snapshot path" not in dashboard_source
    assert "use_container_width" not in dashboard_source
    assert 'width="stretch"' in dashboard_source


def test_wording_is_domain_first_even_when_top_bot_labels_are_present():
    signals = detect_bot_spikes(
        [
            *_events(20, minutes_after_base=31, user_label="TopBot"),
            *_events(5, minutes_after_base=31, user_label="SecondBot"),
        ],
        computed_at=BASE + timedelta(minutes=35),
    )

    wording = signals[0].wording.lower()
    first_domain_position = wording.find(DOMAIN)
    first_user_position = wording.find("topbot")

    assert first_domain_position >= 0
    assert first_user_position == -1 or first_domain_position < first_user_position
