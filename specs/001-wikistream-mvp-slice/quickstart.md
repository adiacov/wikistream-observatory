# Quickstart Validation Guide: WikiStream MVP Vertical Slice

This guide defines expected reviewer validation scenarios. Implementation happens later in `tasks.md` and code.

## Prerequisites

- Docker and Docker Compose available locally.
- Internet access for live Wikimedia RecentChanges mode.
- No cloud account, paid API, Kubernetes, or Wikimedia credentials are required.

## Live mode validation

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
   - live freshness is `fresh` only when latest event age is 60 seconds or less.

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

Expected signal contents:
- domain;
- current bot-flagged event count or rate;
- baseline window and baseline count/rate;
- numeric or categorical spike magnitude;
- threshold context;
- optional limited top contributing bot account labels;
- limitation text stating that this is an observability signal, not an enforcement decision or account-level accusation.

If no spike meets the threshold, the dashboard should say no current signal meets the configured threshold and explain the evaluation method.

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
