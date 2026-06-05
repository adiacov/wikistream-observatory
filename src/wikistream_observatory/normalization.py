"""RecentChanges normalization helpers."""

from __future__ import annotations

from datetime import datetime
import hashlib
import json
from typing import Any

from wikistream_observatory.models import NormalizedRecentChangeEvent, SourceMode
from wikistream_observatory.time_utils import choose_event_time, ensure_utc, parse_event_timestamp, utc_now

EXPECTED_OPTIONAL_FIELDS = [
    "bot",
    "namespace",
    "title",
    "minor",
    "patrolled",
    "length.old",
    "length.new",
    "revision.old",
    "revision.new",
    "comment",
    "user",
]


def _payload_from_envelope(raw: dict[str, Any]) -> dict[str, Any]:
    payload = raw.get("payload", raw)
    if not isinstance(payload, dict):
        raise ValueError("payload must be an object")
    return payload


def _nested(payload: dict[str, Any], *keys: str) -> Any:
    current: Any = payload
    for key in keys:
        if not isinstance(current, dict) or key not in current:
            return None
        current = current[key]
    return current


def _event_id(raw: dict[str, Any], payload: dict[str, Any]) -> str:
    candidates = [
        raw.get("event_id"),
        _nested(payload, "meta", "id"),
        payload.get("id"),
    ]
    for candidate in candidates:
        if candidate is not None and str(candidate).strip():
            return str(candidate)
    encoded = json.dumps(payload, sort_keys=True, default=str, separators=(",", ":"))
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def _missing_optional_fields(payload: dict[str, Any], timestamp_fallback: bool) -> list[str]:
    missing: list[str] = []
    checks = {
        "bot": payload.get("bot"),
        "namespace": payload.get("namespace"),
        "title": payload.get("title"),
        "minor": payload.get("minor"),
        "patrolled": payload.get("patrolled"),
        "length.old": _nested(payload, "length", "old"),
        "length.new": _nested(payload, "length", "new"),
        "revision.old": _nested(payload, "revision", "old"),
        "revision.new": _nested(payload, "revision", "new"),
        "comment": payload.get("comment"),
        "user": payload.get("user"),
    }
    missing.extend(name for name in EXPECTED_OPTIONAL_FIELDS if checks[name] is None)
    if timestamp_fallback:
        missing.append("timestamp")
    return sorted(set(missing))


def _optional_int(value: Any) -> int | None:
    if value is None:
        return None
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _optional_bool(value: Any) -> bool | None:
    if value is None:
        return None
    return bool(value)


def normalize_recentchange(raw: dict[str, Any], *, observed_at: datetime | None = None) -> NormalizedRecentChangeEvent:
    """Normalize a raw Kafka envelope or RecentChanges payload.

    Missing required dashboard fields (`meta.domain`, `type`) raise ``ValueError``.
    Missing optional fields are preserved in ``missing_fields`` and do not prevent
    downstream metrics from being computed.
    """

    observed_at = ensure_utc(observed_at or utc_now())
    payload = _payload_from_envelope(raw)

    source_mode = str(raw.get("source_mode", payload.get("source_mode", "live"))).lower()
    if source_mode not in {"live", "replay"}:
        raise ValueError("source_mode must be live or replay")
    mode: SourceMode = source_mode  # type: ignore[assignment]

    domain = _nested(payload, "meta", "domain") or payload.get("domain")
    if not domain:
        raise ValueError("RecentChange event is missing required domain")

    event_type = payload.get("type")
    if not event_type:
        raise ValueError("RecentChange event is missing required event type")

    parsed_ts = parse_event_timestamp(payload.get("timestamp"))
    event_ts, timestamp_fallback = choose_event_time(parsed_ts, observed_at)
    missing_fields = _missing_optional_fields(payload, timestamp_fallback)

    return NormalizedRecentChangeEvent(
        event_id=_event_id(raw, payload),
        source_mode=mode,
        domain=str(domain),
        event_type=str(event_type),
        event_ts=event_ts,
        observed_at=observed_at,
        user_label=str(payload["user"]) if payload.get("user") is not None else None,
        is_bot=bool(payload.get("bot", False)),
        namespace=_optional_int(payload.get("namespace")),
        title=str(payload["title"]) if payload.get("title") is not None else None,
        minor=_optional_bool(payload.get("minor")),
        patrolled=_optional_bool(payload.get("patrolled")),
        length_old=_optional_int(_nested(payload, "length", "old")),
        length_new=_optional_int(_nested(payload, "length", "new")),
        revision_old=_optional_int(_nested(payload, "revision", "old")),
        revision_new=_optional_int(_nested(payload, "revision", "new")),
        comment_present=payload.get("comment") is not None,
        missing_fields=missing_fields,
        quality_status="accepted_missing_fields" if missing_fields else "accepted",
    )
