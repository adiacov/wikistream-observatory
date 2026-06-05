# Replay sample data

This directory is reserved for bundled replay data used to demonstrate WikiStream Observatory without waiting for interesting live Wikimedia stream conditions.

Replay support is part of the MVP plan. The bundled JSONL sample has been added; the replay publisher and full Docker replay path are implemented in later tasks. This README documents the sample contract so reviewers can understand what the replay data is for and how it should be interpreted.

## Planned file

```text
data/replay/recentchange_sample.jsonl
```

Each line is either:

1. a representative Wikimedia RecentChanges-like event object; or
2. a replay wrapper with `source_mode = "replay"` and a `payload` object.

Example wrapper shape:

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

Malformed-line fixtures intentionally violate JSON syntax or required structure so the data-quality path can count malformed/rejected records separately from accepted records with missing fields.

## Provenance and responsible use

The replay sample should be representative of public Wikimedia RecentChanges event shape, not private or non-public data. It may be curated from public stream observations or generated to match public schema patterns, but it must remain clearly labeled as replay/demo data.

Replay data must not be presented as current live Wikimedia activity. Dashboard freshness and signal views should identify replayed data explicitly.

Account/user labels in replay examples are demonstration context only. Bot-spike outputs remain domain-level observability signals and are not enforcement decisions or account-level accusations.

## Required sample coverage

`recentchange_sample.jsonl` includes records to demonstrate:

- event volume over time;
- top active Wikimedia domains;
- event type breakdown;
- bot/non-bot share;
- at least one known domain-level bot spike signal;
- at least one malformed/rejected example;
- at least one accepted event with missing optional or expected fields.

## Expected signal domain

```text
expected_signal_domain: example.wikipedia.org
```

The chosen domain should have bot-flagged replay events that exceed the default MVP bot spike threshold:

- current window: latest 5-minute window;
- baseline: previous 30 minutes for the same domain, normalized to 5-minute equivalents;
- minimum current bot events: 20;
- threshold ratio: 3.0x;
- zero-baseline cases labeled `new-or-zero-baseline`, not infinite ratio.

## Expected data-quality counts

```text
expected_malformed_rejected_count: 2
expected_missing_field_count: 1
expected_accepted_count: 28
```

Sample composition:

- 5 low-baseline bot-flagged events on `example.wikipedia.org`;
- 20 current-window bot-flagged events on `example.wikipedia.org`, producing the known domain-level spike;
- 2 normal non-bot events on other domains;
- 1 accepted event missing the `bot` flag;
- 1 malformed JSON line;
- 1 rejected JSON object missing a required event type.

Malformed/rejected counts and missing-field counts must remain separate:

- malformed/rejected: invalid JSON or records missing required fields such as domain or event type;
- missing-field: accepted records missing optional/expected fields such as bot flag, namespace, title, length, revision, patrol status, or usable event timestamp.

## Validation path once replay is implemented

Planned command:

```bash
WIKISTREAM_MODE=replay docker compose up --build
```

Expected dashboard behavior once replay tasks are complete:

- mode is shown as `replay`;
- overview metrics populate from bundled sample records;
- at least one domain-level bot spike signal appears for the documented expected domain;
- freshness/status text states that the data is replayed, not current live Wikimedia activity;
- data-quality counts match the documented expected counts.
