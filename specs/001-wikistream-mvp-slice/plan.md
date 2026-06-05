# Implementation Plan: WikiStream MVP Vertical Slice

**Branch**: `001-wikistream-mvp-slice` | **Date**: 2026-06-05 | **Spec**: [`spec.md`](spec.md)

**Input**: Feature specification from `/specs/001-wikistream-mvp-slice/spec.md` plus plan input requiring Docker Compose, Redpanda, Python services, DuckDB/Parquet snapshots, Streamlit, pytest, structured logging, live Wikimedia RecentChanges ingestion, normalized event storage, windowed metrics, domain-level bot spike detection, replay data, data-quality counts, and README/project documentation.

## Summary

Build a local, Docker Compose-orchestrated streaming MVP that reads public Wikimedia RecentChanges events, publishes raw events to a Kafka-compatible Redpanda topic, processes them into normalized observability facts and windowed metrics, stores local analytical snapshots in Parquet/DuckDB, and exposes a Streamlit dashboard. The MVP includes live mode, replay mode with bundled representative data, freshness and data-quality visibility, and one explainable non-trivial signal: domain-level bot spike detection relative to a recent domain baseline.

## Technical Context

**Language/Version**: Python 3.12 for ingestion, stream processing, reusable core logic, and Streamlit dashboard.

**Primary Dependencies**: Docker Compose; Redpanda single-node broker; Python packages managed with a root `pyproject.toml` using editable installs for the shared package. Use `httpx` plus `httpx-sse` for Wikimedia EventStreams SSE ingestion, `confluent-kafka` for Kafka-compatible producer/consumer, `duckdb`, `pyarrow`, `pandas` for analytical snapshots/dashboard reads, `streamlit`, `pytest`, and Python `logging` with JSON-style structured messages.

**Storage**: Local volume-backed analytical storage using Parquet snapshots as the processor write path plus DuckDB views/queries for dashboard analytics. A DuckDB file may be used for metadata/summary tables if single-writer access remains simple; Parquet snapshots are the default concurrency-safe interchange between the processor and dashboard.

**Testing**: `pytest` for core parsing, normalization, windowed aggregation, bot spike signal logic, replay handling, and data-quality classification. Docker/local quickstart scenarios validate end-to-end live and replay behavior.

**Target Platform**: Local developer workstation with Docker and Docker Compose; Linux containers; dashboard available at `http://localhost:8501`.

**Project Type**: Local multi-service data application: ingestion service, stream processor service, analytical storage files, Streamlit dashboard, and tests/shared Python package.

**Performance Goals**: Reviewer sees dashboard metrics within 5 minutes of quickstart; replay mode demonstrates metrics and at least one bot spike within 2 minutes; live freshness indicator updates within 60 seconds of observed events; dashboard refreshes snapshot queries every 15 seconds by default. The MVP target is to process at least 300 RecentChanges events per minute on a typical local developer machine while keeping memory bounded by window state and snapshot batching; under higher live volume, services may sample/log backpressure warnings but dashboard views must summarize rather than list every event.

**Constraints**: Read-only access to Wikimedia; no paid services, cloud deployment, Kubernetes, historical backfill, complex ML, or enforcement/reporting actions; distinguish live versus replayed data; mark live data stale when no event has been observed for more than 60 seconds; keep malformed/rejected and missing-field counts separate. The ingestor must reconnect to Wikimedia EventStreams with capped exponential backoff after disconnects or transient HTTP errors. Services must be restart-safe for MVP use: Redpanda retains topic data in its local volume, the processor may reprocess recent raw messages idempotently using event ids/deterministic hashes, and generated snapshots may be rebuilt from replay data.

**Scale/Scope**: MVP vertical slice only: one live stream, one raw topic, normalized selected fields, basic windowed metrics, one domain-level bot spike signal, bundled sample/replay data, local dashboard, README documentation, and core tests. Local snapshot retention is intentionally bounded: keep approximately the latest 6 hours of live normalized/metric/signal snapshots by default, keep bundled replay data indefinitely, and provide a documented cleanup command that removes generated `data/snapshots/` files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

- Specification-first traceability: PASS. Technical choices map to `spec.md` requirements FR-001 through FR-015 and user stories 1-5.
- Responsible observability: PASS. Planned dashboard and docs use signal/spike terminology, domain-level detection, optional limited top bot-account context, and explicit non-enforcement limitations.
- Local reproducibility/free tooling: PASS. Docker Compose, Redpanda, Python, DuckDB/Parquet, Streamlit, and pytest are local/free tools; Wikimedia RecentChanges is public read-only data.
- Testable data transformations: PASS. Core parsing, normalization, aggregation, spike detection, replay, freshness, and data-quality behavior are planned for `pytest` coverage and quickstart validation.
- Narrow vertical slice/simplicity: PASS. Scope is limited to live ingestion, normalization, basic metrics, one signal, replay data, dashboard, and documentation. No complex ML or extra infrastructure.

## Project Structure

### Documentation (this feature)

```text
specs/001-wikistream-mvp-slice/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── dashboard-contract.md
│   ├── replay-data-contract.md
│   └── topic-contracts.md
└── tasks.md              # Created later by /speckit.tasks
```

### Source Code (repository root)

```text
compose.yaml
README.md
.env.example

services/
├── ingestor/
│   ├── Dockerfile
│   └── wikistream_ingestor/
├── processor/
│   ├── Dockerfile
│   └── wikistream_processor/
└── dashboard/
    ├── Dockerfile
    └── app/

src/
└── wikistream_observatory/
    ├── normalization.py
    ├── quality.py
    ├── windows.py
    ├── signals.py
    ├── storage.py
    └── logging.py

data/
├── replay/
│   ├── recentchange_sample.jsonl
│   └── README.md
└── snapshots/            # Runtime volume / ignored generated files

schemas/
└── recentchange_normalized.schema.json

tests/
├── unit/
│   ├── test_normalization.py
│   ├── test_quality.py
│   ├── test_windows.py
│   └── test_signals.py
└── integration/
    └── test_replay_pipeline.py
```

**Structure Decision**: Use a small multi-service layout for the runnable pipeline and a shared `src/wikistream_observatory/` Python package for core logic so parsing, aggregation, and signal detection are testable outside Docker services. Runtime snapshots live under `data/snapshots/` and are excluded from version control; bundled replay data lives under `data/replay/`. A root `pyproject.toml` defines shared dependencies and service entry points; service Dockerfiles install the shared package in editable mode for local development.

## Local Orchestration Decisions

- `compose.yaml` includes `redpanda`, `ingestor`, `processor`, and `dashboard` services.
- Redpanda exposes Kafka API internally as `redpanda:9092`; external host access may use `localhost:19092` for debugging.
- Dashboard exposes Streamlit on host port `8501`.
- A shared named volume or bind mount provides `data/snapshots/` to both processor and dashboard; processor is the only writer and dashboard is read-only.
- Live mode is the default. Replay mode is selected with `WIKISTREAM_MODE=replay`, causing the ingestor/replay publisher to read `data/replay/recentchange_sample.jsonl` instead of Wikimedia EventStreams.
- `processor` depends on Redpanda readiness; `dashboard` can start before snapshots exist and must show the documented empty-state message.

## Initial Signal and Window Defaults

- Activity metrics use 1-minute buckets for dashboard overview charts.
- Bot spike current window: latest complete or in-progress 5-minute window.
- Bot spike baseline: previous 30 minutes for the same domain, excluding the current 5-minute window, normalized to 5-minute-window equivalents.
- Default signal threshold: emit when `current_bot_events >= 20` and `spike_ratio >= 3.0`.
- Low-baseline rule: if baseline is zero, emit only when `current_bot_events >= 20` and label the ratio as `new-or-zero-baseline` rather than infinite.
- Top contributing bot account labels are limited to the top 3 by event count within the signal window and are shown only as context with limitation text.

## Snapshot and Cleanup Decisions

- Processor writes snapshot files via temporary paths followed by atomic rename/move so the dashboard reads only complete files.
- Snapshot batches should be written at least every 15 seconds in live mode and at replay completion in replay mode.
- Local live retention target is approximately 6 hours for generated snapshots; older live snapshot files may be compacted or deleted by the processor.
- Documentation must include a cleanup command such as `rm -rf data/snapshots/*` or a project wrapper command once available.

## Recovery and Restart Decisions

- Ingestor reconnects to EventStreams after disconnects with capped exponential backoff and structured logs for disconnect, retry, and reconnect events.
- Processor uses Kafka consumer offsets where available and idempotent event ids/deterministic hashes to tolerate limited reprocessing after restarts.
- Dashboard treats missing or empty snapshots as a valid no-data state and remains usable while ingestion/processing catches up.
- Replay mode can be rerun from the beginning and may overwrite/rebuild replay snapshots.

## Phase 0 Research Summary

See [`research.md`](research.md). Decisions resolved: EventStreams access pattern, Redpanda/Kafka topic usage, Python client choices, Parquet/DuckDB snapshot strategy, windowing/baseline approach, replay data packaging, data-quality categories, structured logging, and responsible observability language.

## Phase 1 Design Summary

See [`data-model.md`](data-model.md) for entities, validation rules, and relationships. Contracts are documented in [`contracts/topic-contracts.md`](contracts/topic-contracts.md), [`contracts/replay-data-contract.md`](contracts/replay-data-contract.md), and [`contracts/dashboard-contract.md`](contracts/dashboard-contract.md). End-to-end reviewer validation is documented in [`quickstart.md`](quickstart.md).

## Post-Design Constitution Check

- Specification-first traceability: PASS. Design artifacts explicitly cover spec entities, functional requirements, and acceptance scenarios.
- Responsible observability: PASS. Contracts require non-accusatory wording, domain-first spike presentation, and limitation text whenever top contributing bot labels are shown.
- Local reproducibility/free tooling: PASS. Quickstart uses Docker Compose and local files only; replay mode avoids dependence on live stream availability.
- Testable data transformations: PASS. Data model and quickstart define validation expectations for malformed/rejected events, missing fields, replay events, freshness, and bot spike outputs.
- Narrow vertical slice/simplicity: PASS. The design defers extra signals, public reports, cloud, Kubernetes, ML scoring, and historical backfill.

## Complexity Tracking

No constitution violations or unjustified complexity are planned.
