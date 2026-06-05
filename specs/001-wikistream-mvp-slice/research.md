# Research: WikiStream MVP Vertical Slice

Research date: 2026-06-05. Live checks confirmed `https://stream.wikimedia.org/v2/stream/recentchange` returns `text/event-stream` and the current RecentChange schema endpoint is reachable at `https://schema.wikimedia.org/repositories/primary/jsonschema/mediawiki/recentchange/latest`.

## Wikimedia RecentChanges ingestion

- **Decision**: Consume Wikimedia EventStreams RecentChanges over SSE in a Python ingestor using `httpx` plus `httpx-sse`, then publish each valid JSON event envelope to Redpanda topic `raw_recentchange`.
- **Rationale**: EventStreams is the public live source named by the spec. Keeping ingestion thin preserves raw event evidence and separates external connectivity from normalization and signal logic.
- **Alternatives considered**: Direct dashboard polling was rejected because it would skip the streaming architecture. Server-side filtering was rejected because Wikimedia EventStreams consumers should filter client-side. Historical API backfill was rejected as out of MVP scope. `requests`-based SSE handling was considered but rejected in favor of `httpx`/`httpx-sse` for clearer streaming-client semantics and timeout configuration.

## Redpanda as Kafka-compatible broker

- **Decision**: Use a single-node Redpanda container as the local Kafka-compatible broker.
- **Rationale**: Redpanda provides Kafka APIs with simpler local Docker operation than a full Kafka/ZooKeeper stack, supporting the portfolio goal of a realistic but runnable pipeline.
- **Alternatives considered**: Apache Kafka was rejected for heavier local orchestration. In-process queues were rejected because the spec requires Kafka-compatible streaming architecture.

## Python service implementation

- **Decision**: Implement ingestor, processor, and shared core logic in Python 3.12.
- **Rationale**: Python has mature Kafka, DuckDB, Parquet, testing, and Streamlit support and keeps transformation logic easy to review.
- **Alternatives considered**: JVM stream processors and Flink/Spark were rejected as too heavy for the first vertical slice.

## Analytical storage: Parquet snapshots plus DuckDB reads

- **Decision**: Processor writes append/periodic Parquet snapshots for normalized events, windowed metrics, bot spike signals, and data-quality counts. Dashboard queries these files through DuckDB. Snapshot writes use temporary files followed by atomic rename/move, and generated live snapshots are retained for approximately the latest 6 hours by default.
- **Rationale**: DuckDB is excellent for local analytical queries, while Parquet files avoid concurrent write/read complexity between processor and dashboard. DuckDB can also materialize local views or summaries if later needed.
- **Alternatives considered**: Direct DuckDB writes from the processor were considered but deferred unless single-writer/read-only access is proven simple. PostgreSQL/ClickHouse were rejected as extra infrastructure for the MVP.

## Windowed metrics and domain-level bot spike signal

- **Decision**: Compute simple windowed metrics using event-time when valid and processing-time fallback when event-time is missing, malformed, or highly skewed. The first signal compares current 5-minute domain-level bot event counts against the previous 30-minute baseline for the same domain, normalized to 5-minute equivalents. Default thresholds are at least 20 bot events and at least a 3.0x spike ratio; zero-baseline cases are labeled `new-or-zero-baseline` instead of infinite-ratio anomalies.
- **Rationale**: This meets the non-trivial signal requirement while remaining explainable and testable. Domain-level detection aligns with clarified requirements and reduces account-level accusation risk. Concrete default windows and thresholds prevent implementation tasks from inventing signal semantics.
- **Alternatives considered**: Account-first bot anomaly detection, non-bot automation-like scoring, and small-wiki burst detection were rejected for MVP scope; they remain future signals.

## Replay/sample data

- **Decision**: Bundle a small JSONL replay sample derived from representative public RecentChanges-like events, including normal activity, missing-field examples, malformed/rejected examples, and a known domain-level bot spike.
- **Rationale**: Reviewers can validate dashboard behavior without waiting for live stream conditions. JSONL is easy to inspect and stream through the same normalization and processing path.
- **Alternatives considered**: Large captured datasets were rejected to keep the repo lightweight. Synthetic-only data was rejected because representative public-data shape is more credible.

## Data-quality categories

- **Decision**: Track malformed/rejected events separately from events accepted with missing optional/expected fields. Expose both in snapshots and dashboard.
- **Rationale**: The spec requires distinct visible counts, and separating these categories demonstrates production-like data handling.
- **Alternatives considered**: A single error count was rejected as too ambiguous. Event-level error browsing in the dashboard was rejected as unnecessary for MVP.

## Structured logging

- **Decision**: Use simple structured logs from each service with fields such as `service`, `event`, `mode`, `topic`, `count`, `domain`, `window_start`, `window_end`, and `error_type`.
- **Rationale**: JSON-style logs are easy to inspect with Docker Compose and demonstrate operational hygiene without adding a logging stack.
- **Alternatives considered**: OpenTelemetry/Prometheus/Grafana were rejected as extra infrastructure for the first slice.

## Responsible observability presentation

- **Decision**: Dashboard and README must describe outputs as signals, not enforcement decisions. Bot spike output is domain-first; top contributing bot account labels are optional context and must include limitation text.
- **Rationale**: This directly implements the project constitution and the spec's responsible framing requirements.
- **Alternatives considered**: Account-level leaderboards and accusation-oriented anomaly labels were rejected as inconsistent with the constitution.
