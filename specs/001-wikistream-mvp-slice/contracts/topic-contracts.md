# Contract: Streaming Topics and Analytical Snapshots

## Redpanda service contract

- Internal Kafka bootstrap address: `redpanda:9092`.
- Optional host/debug Kafka bootstrap address: `localhost:19092`.
- Redpanda data is stored in a local Docker volume so service restarts do not require topic recreation during normal MVP use.
- `processor` should wait for broker readiness before consuming; `dashboard` does not depend on broker readiness directly.

## Redpanda topics

### `raw_recentchange`

Producer: `ingestor` service in live mode or replay publisher in replay mode.
Consumer: `processor` service.

Message key:
- Prefer source event id/meta id when present.
- Fallback to deterministic hash for replay/sample records.

Message value:
```json
{
  "source_mode": "live",
  "ingested_at": "2026-06-05T12:00:00Z",
  "payload": { "meta": { "domain": "en.wikipedia.org" }, "type": "edit" }
}
```

Rules:
- `source_mode` MUST be `live` or `replay`.
- `payload` MUST preserve the Wikimedia event object when JSON parsing succeeds.
- Malformed replay lines MAY be represented as rejected quality records without publishing invalid Kafka JSON.

## Snapshot datasets

The processor writes local Parquet snapshots under `data/snapshots/` for DuckDB dashboard queries.

Required logical datasets:
- `normalized_events`: accepted normalized events.
- `activity_metrics`: windowed overview metrics.
- `bot_spike_signals`: emitted domain-level bot spike signals.
- `data_quality_counts`: malformed/rejected, missing-field, accepted, and freshness counts.

Common rules:
- Include `source_mode` in every dataset.
- Include `computed_at` or `observed_at` where applicable.
- Processor MUST write snapshots through temporary paths followed by atomic rename/move so dashboard readers see only complete files.
- Processor is the only writer to snapshot datasets; dashboard access is read-only through DuckDB queries over Parquet.
- Snapshot batches SHOULD be written at least every 15 seconds in live mode and at replay completion in replay mode.
- Generated live snapshots SHOULD be retained for approximately 6 hours by default; bundled replay data is retained indefinitely.
- Dashboard consumers MUST tolerate empty datasets and show useful empty-state text.
