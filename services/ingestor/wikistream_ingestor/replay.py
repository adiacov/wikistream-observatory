"""Replay-mode JSONL reader and publisher for bundled RecentChanges samples."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timezone
import json
from pathlib import Path
import time
from typing import Any, Callable, Iterable

from wikistream_observatory.kafka import encode_json_message
from wikistream_observatory.logging import log_event
from wikistream_observatory.models import SourceMode
from wikistream_observatory.time_utils import utc_now


@dataclass(frozen=True)
class ReplayRecord:
    """One replay JSONL line after best-effort parsing."""

    line_number: int
    source_mode: SourceMode
    payload: dict[str, Any] | None
    raw_line: str
    pacing_seconds: float = 0
    malformed: bool = False
    error: str | None = None


def _event_key(payload: dict[str, Any]) -> str | None:
    meta = payload.get("meta")
    if isinstance(meta, dict) and meta.get("id"):
        return str(meta["id"])
    if payload.get("id"):
        return str(payload["id"])
    return None


def _pacing_seconds(record: dict[str, Any], default_pacing_seconds: float) -> float:
    if record.get("pacing_seconds") is not None:
        return max(0.0, float(record["pacing_seconds"]))
    if record.get("pacing_ms") is not None:
        return max(0.0, float(record["pacing_ms"]) / 1000.0)
    return max(0.0, float(default_pacing_seconds))


def _accepted_record(line_number: int, raw_line: str, decoded: dict[str, Any], *, default_pacing_seconds: float) -> ReplayRecord:
    has_wrapper_payload = "payload" in decoded
    payload = decoded["payload"] if has_wrapper_payload else decoded
    if not isinstance(payload, dict):
        raise ValueError("replay payload must be a JSON object")
    return ReplayRecord(
        line_number=line_number,
        source_mode="replay",
        payload=payload,
        raw_line=raw_line,
        pacing_seconds=_pacing_seconds(decoded, default_pacing_seconds) if has_wrapper_payload else max(0.0, float(default_pacing_seconds)),
    )


def read_replay_records(path: str | Path, *, default_pacing_seconds: float = 0) -> Iterable[ReplayRecord]:
    """Yield replay records from a JSONL file without stopping on malformed lines.

    Lines can be plain RecentChanges-like JSON objects or replay wrappers with a
    ``payload`` object plus optional ``pacing_seconds``/``pacing_ms`` metadata.
    Accepted records are always labeled ``source_mode='replay'`` regardless of
    any source-mode value embedded in the file.
    """

    replay_path = Path(path)
    with replay_path.open("r", encoding="utf-8") as stream:
        for line_number, raw_line_with_newline in enumerate(stream, start=1):
            raw_line = raw_line_with_newline.rstrip("\n")
            if not raw_line.strip():
                continue
            try:
                decoded = json.loads(raw_line)
                if not isinstance(decoded, dict):
                    raise ValueError("replay line must be a JSON object")
                yield _accepted_record(line_number, raw_line, decoded, default_pacing_seconds=default_pacing_seconds)
            except json.JSONDecodeError as exc:
                yield ReplayRecord(
                    line_number=line_number,
                    source_mode="replay",
                    payload=None,
                    raw_line=raw_line,
                    pacing_seconds=0,
                    malformed=True,
                    error=f"json parse error: {exc}",
                )
            except Exception as exc:
                yield ReplayRecord(
                    line_number=line_number,
                    source_mode="replay",
                    payload=None,
                    raw_line=raw_line,
                    pacing_seconds=0,
                    malformed=True,
                    error=str(exc),
                )


def replay_envelope(payload: dict[str, Any]) -> dict[str, Any]:
    """Create the Kafka envelope used by replay publication."""

    return {
        "source_mode": "replay",
        "ingested_at": utc_now().astimezone(timezone.utc).isoformat(),
        "payload": payload,
    }


def publish_replay_records(
    records: Iterable[ReplayRecord],
    *,
    producer: Any,
    topic: str,
    logger: Any | None = None,
    sleep_fn: Callable[[float], None] = time.sleep,
) -> tuple[int, int]:
    """Publish accepted replay records to Kafka in input order.

    Malformed/rejected lines are skipped here; later data-quality work will make
    their counts visible. The return value is ``(published_count, skipped_count)``.
    """

    published_count = 0
    skipped_count = 0
    for record in records:
        if record.malformed or record.payload is None:
            skipped_count += 1
            if logger is not None:
                log_event(
                    logger,
                    "replay_record_skipped",
                    "Skipped malformed replay record",
                    line_number=record.line_number,
                    error=record.error,
                )
            continue

        producer.produce(topic, key=_event_key(record.payload), value=encode_json_message(replay_envelope(record.payload)))
        producer.poll(0)
        published_count += 1
        if logger is not None and published_count % 100 == 0:
            log_event(logger, "replay_records_published", "Published replay records", count=published_count, topic=topic)
        if record.pacing_seconds > 0:
            sleep_fn(record.pacing_seconds)

    producer.flush(30)
    return published_count, skipped_count
