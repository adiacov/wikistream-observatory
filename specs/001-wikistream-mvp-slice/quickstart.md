# Quickstart Validation Guide: WikiStream MVP Vertical Slice

This guide defines expected reviewer validation scenarios. Implementation happens later in `tasks.md` and code.

## Prerequisites

- Docker and Docker Compose available locally.
- Internet access for live Wikimedia RecentChanges mode.
- No cloud account, paid API, Kubernetes, or Wikimedia credentials are required.
- Expected local ports: Streamlit dashboard on `localhost:8501`; Redpanda Kafka API may be exposed on `localhost:19092` for debugging.
- Generated analytical snapshots are written under `data/snapshots/` and may be deleted between runs.

## Live mode validation

### Phase 3 validation note

Validation date: 2026-06-05.

Phase 3 live-mode startup smoke was run with Docker Compose after building service images. The stack reached a healthy local state: Redpanda became healthy, ingestor connected to `https://stream.wikimedia.org/v2/stream/recentchange` with HTTP 200, ingestor published live RecentChanges messages, processor wrote `normalized_events` and `activity_metrics` snapshots, and Streamlit started on `http://localhost:8501`. A Redpanda healthcheck issue was found during the first attempt and fixed by switching the healthcheck to `rpk cluster info -X brokers=redpanda:9092` with a start period.

Host Python did not have `pytest` installed during this validation, so pytest execution was deferred to a dev environment/container with project dev dependencies. Direct smoke checks, `compileall`, `docker compose config`, `docker compose build`, and a short `docker compose up` live startup were completed.

1. Start the local stack:

   ```bash
   docker compose up --build
   ```

2. Open the dashboard:

   ```text
   http://localhost:8501
   ```

3. Expected outcomes within 5 minutes:
   - dashboard identifies mode as `live`;
   - event volume over time is populated;
   - top Wikimedia domains are shown;
   - event type breakdown is shown;
   - bot/non-bot share is shown;
   - latest observed event time is visible;
   - live freshness is `fresh` only when latest event age is 60 seconds or less;
   - dashboard views refresh/query snapshots every 15 seconds by default.

4. If no event has arrived for more than 60 seconds, expected outcome:
   - dashboard marks data as stale and does not silently present stale data as current.

## Replay mode validation

1. Start the local stack in replay mode using the implemented project command or environment variable, for example:

   ```bash
   WIKISTREAM_MODE=replay docker compose up --build
   ```

2. Open the dashboard at `http://localhost:8501`.

3. Expected outcomes within 2 minutes:
   - dashboard identifies mode as `replay`;
   - overview metrics are populated from bundled representative data;
   - at least one domain-level bot spike signal appears for the expected sample domain;
   - freshness/status areas clearly state that the data is replayed, not current live activity.

## Bot spike signal validation

Use either live data with a natural spike or bundled replay data with the known spike.

Default MVP signal semantics:
- current window: latest 5-minute window;
- baseline: previous 30 minutes for the same domain, normalized to 5-minute equivalents;
- threshold: at least 20 bot-flagged events and at least 3.0x the baseline;
- zero baseline: label as `new-or-zero-baseline` instead of infinite ratio.

Expected signal contents:
- domain;
- current bot-flagged event count or rate;
- baseline window and baseline count/rate;
- numeric or categorical spike magnitude;
- threshold context;
- optional limited top contributing bot account labels;
- limitation text stating that this is an observability signal, not an enforcement decision or account-level accusation.

If no spike meets the threshold, the dashboard should say no current signal meets the configured threshold and explain the evaluation method.

## Recovery and cleanup validation

Expected recovery behavior:
- Wikimedia EventStreams disconnects are handled with capped exponential backoff and structured reconnect logs.
- Restarting the ingestor or processor does not require deleting local data for normal MVP use.
- Missing or empty snapshots show a dashboard no-data/empty-state message rather than an error-only page.

Cleanup generated local snapshots between runs:

```bash
rm -rf data/snapshots/*
```

Bundled replay data under `data/replay/` should not be deleted by cleanup.

## Data-quality validation

Use bundled replay fixtures containing malformed/rejected and missing-field records.

Expected outcomes:
- malformed/rejected event count is visible;
- missing-field event count is visible separately;
- accepted events with missing optional fields do not crash metrics;
- intentionally malformed or missing-field sample events are handled safely or rejected, with at least 95% represented by the visible counts required by the spec.

## Core logic checks

After implementation, run:

```bash
pytest
```

Expected tested areas:
- RecentChanges normalization;
- missing-field and malformed/rejected classification;
- windowed activity metrics;
- domain-level bot spike detection;
- replay sample handling;
- freshness classification.

## Documentation validation

A first-time reviewer should be able to read `README.md` and identify within 10 minutes:
- project purpose and problem framing;
- local quickstart path;
- dashboard usage;
- live versus replay mode behavior;
- architecture overview;
- data-quality behavior;
- responsible observability limits;
- known limitations.
