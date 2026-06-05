"""JSON-style structured logging helpers."""

from __future__ import annotations

from datetime import datetime, timezone
import json
import logging
from typing import Any

_RESERVED = {"name", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "message", "asctime"}


class JsonFormatter(logging.Formatter):
    """Format log records as compact JSON objects."""

    def format(self, record: logging.LogRecord) -> str:
        payload: dict[str, Any] = {
            "ts": datetime.fromtimestamp(record.created, tz=timezone.utc).isoformat(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }
        for key, value in record.__dict__.items():
            if key not in _RESERVED and not key.startswith("_"):
                payload[key] = value
        if record.exc_info:
            payload["exception"] = self.formatException(record.exc_info)
        return json.dumps(payload, default=str, sort_keys=True)


def configure_logging(service: str, mode: str, level: int | str = logging.INFO) -> logging.LoggerAdapter:
    """Configure root logging and return an adapter carrying service and mode fields."""

    handler = logging.StreamHandler()
    handler.setFormatter(JsonFormatter())

    root = logging.getLogger()
    root.handlers.clear()
    root.addHandler(handler)
    root.setLevel(level)

    logger = logging.getLogger("wikistream")
    return logging.LoggerAdapter(logger, {"service": service, "mode": mode})


def log_event(logger: logging.LoggerAdapter, event: str, message: str, **fields: Any) -> None:
    """Emit a structured informational event."""

    logger.info(message, extra={"event": event, **fields})
