from __future__ import annotations

from datetime import datetime, timezone, timedelta

from wikistream_observatory.quality import classify_raw_event, summarize_quality_counts


OBSERVED_AT = datetime(2026, 6, 5, 12, 0, tzinfo=timezone.utc)


def _raw(payload: dict, *, source_mode: str = "live") -> dict:
    return {"source_mode": source_mode, "ingested_at": OBSERVED_AT.isoformat(), "payload": payload}


def test_classifies_malformed_json_as_rejected_without_normalized_event():
    result = classify_raw_event("{not valid json", source_mode="replay", observed_at=OBSERVED_AT)

    assert result.status == "malformed_rejected"
    assert result.event is None
    assert "json" in result.reason.lower()
    assert result.source_mode == "replay"


def test_classifies_missing_required_fields_as_rejected():
    missing_domain = classify_raw_event(_raw({"type": "edit"}), observed_at=OBSERVED_AT)
    missing_type = classify_raw_event(_raw({"meta": {"domain": "en.wikipedia.org"}}), observed_at=OBSERVED_AT)

    assert missing_domain.status == "malformed_rejected"
    assert missing_domain.event is None
    assert "domain" in missing_domain.reason.lower()
    assert missing_type.status == "malformed_rejected"
    assert missing_type.event is None
    assert "event type" in missing_type.reason.lower()


def test_classifies_accepted_record_with_missing_optional_fields_separately():
    result = classify_raw_event(
        _raw({"meta": {"domain": "en.wikipedia.org"}, "type": "edit", "timestamp": int(OBSERVED_AT.timestamp())}),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "accepted_missing_fields"
    assert result.event is not None
    assert result.event.is_bot is False
    assert "bot" in result.missing_fields
    assert "title" in result.missing_fields
    assert result.reason == "accepted with missing expected fields"


def test_classifies_timestamp_fallback_as_missing_field_issue():
    result = classify_raw_event(
        _raw(
            {
                "meta": {"domain": "en.wikipedia.org"},
                "type": "edit",
                "timestamp": int((OBSERVED_AT + timedelta(hours=1)).timestamp()),
                "bot": False,
            }
        ),
        observed_at=OBSERVED_AT,
    )

    assert result.status == "accepted_missing_fields"
    assert result.event is not None
    assert result.event.event_ts == OBSERVED_AT
    assert result.timestamp_issue is True
    assert "timestamp" in result.missing_fields


def test_summarize_quality_counts_keeps_rejected_and_missing_fields_separate():
    classifications = [
        classify_raw_event(_raw({"meta": {"domain": "en.wikipedia.org"}, "type": "edit", "timestamp": int(OBSERVED_AT.timestamp())}), observed_at=OBSERVED_AT),
        classify_raw_event(_raw({"meta": {"domain": "commons.wikimedia.org"}, "type": "new", "timestamp": int(OBSERVED_AT.timestamp()), "bot": False}), observed_at=OBSERVED_AT),
        classify_raw_event(_raw({"type": "edit"}), observed_at=OBSERVED_AT),
        classify_raw_event("{not valid json", source_mode="live", observed_at=OBSERVED_AT),
    ]

    counts = summarize_quality_counts(classifications, source_mode="live", freshness_seconds=60, now=OBSERVED_AT)

    assert counts.source_mode == "live"
    assert counts.accepted_count == 2
    assert counts.missing_field_count == 2
    assert counts.malformed_rejected_count == 2
    assert counts.latest_event_observed_at == OBSERVED_AT
    assert counts.freshness_status == "fresh"
    assert "malformed/rejected: 2" in counts.notes
    assert "missing-field accepted: 2" in counts.notes
