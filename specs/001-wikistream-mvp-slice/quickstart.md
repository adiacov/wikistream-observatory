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

### Phase 6 replay validation note

Validation date: 2026-06-06.

Replay mode was validated with the documented quickstart path and a short snapshot inspection script:

```bash
WIKISTREAM_MODE=replay WIKISTREAM_SNAPSHOT_INTERVAL_SECONDS=2 docker compose up --build -d
```

Validation used `docker compose down -v` before replay to avoid stale Redpanda topic data from previous runs while preserving Docker images/build cache. Generated snapshots were cleaned via a short `busybox:1.36` container because earlier container runs can leave root-owned files under `data/snapshots/`. The Docker build reused uv dependency layers (`uv sync --frozen --no-dev --no-install-project` was cached); only project/source install layers rebuilt after code changes.

Observed outputs within 45 seconds:

| Dataset/check | Observed result |
| --- | --- |
| `normalized_events` snapshots | Present, replay-labeled |
| `activity_metrics` snapshots | Present; 18 replay overview metric rows loaded |
| `bot_spike_signals` snapshots | Present; signal for `example.wikipedia.org` with 20 current bot events and `source_mode = replay` |
| `data_quality_counts` snapshots | Present; `accepted_count = 28`, `missing_field_count = 1`, `malformed_rejected_count = 2`, `freshness_status = replay` |
| Dashboard status helper | `source_mode = replay`, latest observed timestamp populated, `freshness_status = replay` |

Known remaining limits:
- The fuller data-quality dashboard section is still Phase 7 work; Phase 6 writes replay quality snapshots and validates their expected counts.
- Replay validation was inspected through snapshot/dashboard helper outputs rather than a browser screenshot.

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

### Phase 5 bot spike validation note

Validation date: 2026-06-05.

User Story 2 bot spike behavior was validated against `contracts/dashboard-contract.md` after T039-T046. Validation used automated unit tests, a generated Parquet fixture at `tests/fixtures/bot_spike_signals.parquet`, dashboard data-loading smoke checks, and source review of the Streamlit rendering section.

| Contract area | Status | Evidence |
| --- | --- | --- |
| Domain-level grouping | PASS | `detect_bot_spikes()` groups by domain and tests assert `example.wikipedia.org` as the signal domain. |
| Current-vs-baseline comparison | PASS | Unit tests cover 5-minute current window, previous 30-minute baseline, normalized baseline-per-window value, and 4.0x ratio. |
| Thresholds | PASS | Tests cover default 20 current bot events and 3.0x threshold, including no-signal cases below count or ratio. |
| Zero baseline | PASS | Tests assert zero-baseline output uses `new-or-zero-baseline` and does not emit an infinite ratio. |
| Top bot labels | PASS | Tests and fixture include top contributing bot labels limited to three and treated as context. |
| Snapshot output | PASS | Processor writes `bot_spike_signals` snapshots, and fixture smoke confirmed the Parquet schema and values can be read through DuckDB. |
| Dashboard loading | PASS | `load_bot_spike_signals()` returns signal rows and treats missing datasets as an empty/no-signal state. |
| Dashboard rendering | PASS | Streamlit section displays domain, current count, baseline, spike magnitude, threshold, window context, optional top labels, no-signal empty state, and limitation text. |
| Responsible wording | PASS | Tests assert wording uses observability language, avoids accusation-oriented terms, and states signals are not enforcement decisions or account-level accusations. |

Validation commands run:

```bash
PYTHONPATH=. uv run --extra dev pytest tests/unit/test_signals.py tests/unit/test_responsible_language.py tests/integration/test_live_pipeline_smoke.py
docker compose config
```

Additional fixture/dashboard smoke checks confirmed `tests/fixtures/bot_spike_signals.parquet` contains the expected domain, count, ratio, threshold, wording, and limitation fields.

Known remaining limits:
- This validates the signal implementation and dashboard contract using fixtures/smoke checks; deterministic end-to-end replay display is validated in the Phase 6 replay validation note above.

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

### Phase 4 documentation audit note

Validation date: 2026-06-05.

Reviewer-facing documentation was manually audited against FR-015 and SC-009 after T034-T037. The audit checked `README.md`, `.env.example`, and `data/replay/README.md` rather than using brittle README unit tests.

| Requirement area | Status | Evidence |
| --- | --- | --- |
| Project purpose | PASS | `README.md` title, tagline, and introduction explain WikiStream Observatory as a local Wikimedia RecentChanges observability project. |
| Problem framing | PASS | `README.md` "Why this exists" explains cross-wiki activity, automation context, and the value of summarizing the raw stream. |
| Observability solution | PASS | `README.md` describes normalized facts, windowed metrics, snapshots, and dashboard signals. |
| MVP scope/current status | PASS | `README.md` separates the current completed live overview slice from specified but not-yet-implemented replay, bot spike, and data-quality counters. |
| Local run path | PASS | `README.md` documents `docker compose up --build`. |
| Dashboard usage | PASS | `README.md` documents mode/freshness, overview metrics, empty states, and planned sections. |
| Replay mode | PASS | At the time of the Phase 4 audit, `README.md`, `.env.example`, and `data/replay/README.md` documented replay as planned/not yet implemented and required replay data not be shown as current live activity. Later Phase 6 notes above validate implemented replay behavior. |
| Data-quality behavior | PASS | `README.md` documents current limitations; `data/replay/README.md` defines separate malformed/rejected and missing-field expected counts for future replay samples. |
| Responsible-use boundaries | PASS | Docs state read-only use, observability framing, no enforcement decisions, and no account-level accusations. |
| Known limitations | PASS | `README.md` includes a dedicated responsible-use and limitations section. |
| Dashboard URL and local ports | PASS | `README.md` and `.env.example` document `http://localhost:8501` and Redpanda host debug port `localhost:19092`. |
| Cleanup command | PASS | `README.md` documents `rm -rf data/snapshots/*` and `docker compose down`. |

Gaps intentionally left for later phases:
- a fuller data-quality dashboard section remains planned for Phase 7;
- T038 was a documentation audit at the time it ran; later Phase 5/6 validation notes above cover bot spike and replay behavior.
