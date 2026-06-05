"""Kafka-compatible utility wrappers for Redpanda access."""

from __future__ import annotations

from dataclasses import dataclass
import json
import time
from typing import Any, Iterable

RAW_RECENTCHANGE_TOPIC = "raw_recentchange"


@dataclass(frozen=True)
class KafkaMessage:
    key: str | None
    value: dict[str, Any]


def encode_json_message(value: dict[str, Any]) -> bytes:
    return json.dumps(value, separators=(",", ":"), default=str).encode("utf-8")


def decode_json_message(value: bytes | str) -> dict[str, Any]:
    if isinstance(value, bytes):
        value = value.decode("utf-8")
    decoded = json.loads(value)
    if not isinstance(decoded, dict):
        raise ValueError("Kafka JSON message must decode to an object")
    return decoded


def create_producer(bootstrap_servers: str, **overrides: Any):
    from confluent_kafka import Producer

    return Producer({"bootstrap.servers": bootstrap_servers, **overrides})


def create_consumer(bootstrap_servers: str, group_id: str, topics: Iterable[str], **overrides: Any):
    from confluent_kafka import Consumer

    consumer = Consumer(
        {
            "bootstrap.servers": bootstrap_servers,
            "group.id": group_id,
            "auto.offset.reset": "earliest",
            "enable.auto.commit": True,
            **overrides,
        }
    )
    consumer.subscribe(list(topics))
    return consumer


def wait_for_broker(bootstrap_servers: str, timeout_seconds: int = 60, poll_interval_seconds: float = 2.0) -> None:
    """Wait until Kafka metadata is available from Redpanda."""

    from confluent_kafka.admin import AdminClient

    deadline = time.monotonic() + timeout_seconds
    last_error: Exception | None = None
    while time.monotonic() < deadline:
        try:
            admin = AdminClient({"bootstrap.servers": bootstrap_servers})
            admin.list_topics(timeout=5)
            return
        except Exception as exc:  # pragma: no cover - depends on broker availability
            last_error = exc
            time.sleep(poll_interval_seconds)
    raise TimeoutError(f"Kafka broker not ready after {timeout_seconds}s: {last_error}")
