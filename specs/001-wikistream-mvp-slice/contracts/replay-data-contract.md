# Contract: Replay Data

Replay data is bundled under `data/replay/` and is used to demonstrate the dashboard without waiting for live stream conditions.

## JSONL event records

Each line SHOULD contain either a representative RecentChanges event object or a replay wrapper:

```json
{
  "source_mode": "replay",
  "payload": {
    "meta": { "domain": "example.wikipedia.org" },
    "type": "edit",
    "timestamp": 1780639710,
    "user": "ExampleBot",
    "bot": true
  }
}
```

Malformed-line fixtures MAY intentionally violate JSON syntax or required structure, but expected counts MUST be documented in `data/replay/README.md`.

## Required sample coverage

The bundled sample MUST include:
- enough accepted events to populate event volume, top domains, event type breakdown, and bot/non-bot share;
- bot-flagged events that create at least one known domain-level bot spike;
- at least one malformed/rejected example;
- at least one accepted event with missing optional/expected fields;
- metadata or README notes identifying the expected signal domain and quality counts.

## Replay mode behavior

- Replay mode MUST label all emitted events and snapshots as `source_mode = replay`.
- Dashboard freshness areas MUST distinguish replay data from live current activity.
- Replay publication SHOULD preserve event order and may use configurable pacing for demonstration.
