# Contract: Streaming Topics and Analytical Snapshots

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
- Dashboard consumers MUST tolerate empty datasets and show useful empty-state text.
