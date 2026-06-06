"""Ingestor service entry point for live or replay Wikimedia RecentChanges."""

from __future__ import annotations

from datetime import timezone
import json
from typing import Any

from wikistream_observatory.config import load_config
from wikistream_observatory.kafka import create_producer, wait_for_broker
from wikistream_observatory.logging import configure_logging, log_event
from wikistream_observatory.time_utils import utc_now

from wikistream_ingestor.eventstreams import recentchange_events
from wikistream_ingestor.replay import publish_replay_records, read_replay_records


def event_key(payload: dict[str, Any]) -> str | None:
    meta = payload.get("meta")
    if isinstance(meta, dict) and meta.get("id"):
        return str(meta["id"])
    if payload.get("id"):
        return str(payload["id"])
    return None


def raw_envelope(payload: dict[str, Any], *, source_mode: str = "live") -> dict[str, Any]:
    return {
        "source_mode": source_mode,
        "ingested_at": utc_now().astimezone(timezone.utc).isoformat(),
        "payload": payload,
    }


def publish_payload(producer: Any, topic: str, payload: dict[str, Any], *, source_mode: str = "live") -> None:
    envelope = raw_envelope(payload, source_mode=source_mode)
    producer.produce(
        topic,
        key=event_key(payload),
        value=json.dumps(envelope, separators=(",", ":"), default=str).encode("utf-8"),
    )
    producer.poll(0)


def run_live() -> None:
    config = load_config()
    logger = configure_logging("ingestor", config.mode)

    wait_for_broker(config.kafka.bootstrap_servers)
    producer = create_producer(config.kafka.bootstrap_servers)
    log_event(logger, "ingestor_started", "Starting live RecentChanges ingestion", topic=config.kafka.raw_topic)

    count = 0
    for payload in recentchange_events(user_agent=config.user_agent):
        publish_payload(producer, config.kafka.raw_topic, payload, source_mode="live")
        count += 1
        if count % 100 == 0:
            producer.flush(5)
            log_event(logger, "events_published", "Published RecentChanges events", count=count, topic=config.kafka.raw_topic)


def run_replay() -> None:
    config = load_config()
    logger = configure_logging("ingestor", config.mode)

    wait_for_broker(config.kafka.bootstrap_servers)
    producer = create_producer(config.kafka.bootstrap_servers)
    log_event(
        logger,
        "replay_started",
        "Starting replay RecentChanges publication",
        topic=config.kafka.raw_topic,
        replay_path=str(config.replay_path),
    )
    published_count, skipped_count = publish_replay_records(
        read_replay_records(config.replay_path),
        producer=producer,
        topic=config.kafka.raw_topic,
        logger=logger,
        publish_rejected=True,
    )
    log_event(
        logger,
        "replay_completed",
        "Completed replay RecentChanges publication",
        topic=config.kafka.raw_topic,
        published_count=published_count,
        skipped_count=skipped_count,
    )


def main() -> None:
    config = load_config()
    if config.mode == "replay":
        run_replay()
    else:
        run_live()


if __name__ == "__main__":
    main()
