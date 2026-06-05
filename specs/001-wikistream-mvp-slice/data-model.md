# Data Model: WikiStream MVP Vertical Slice

## RecentChangeRawEvent

Raw JSON payload received from Wikimedia RecentChanges or replay data before normalization.

**Fields**
- `source_mode`: `live` or `replay`
- `raw_payload`: original JSON object or raw line for malformed replay records
- `ingested_at`: processing timestamp when observed locally
- `event_id`: best-effort unique id from Wikimedia metadata when available
- `kafka_topic`: `raw_recentchange`

**Validation rules**
- JSON parsing failure marks the record malformed/rejected.
- Raw payloads are not used directly by the dashboard; they feed normalization.

## NormalizedRecentChangeEvent

Consistent event fact used for metrics, storage, and signals.

**Fields**
- `event_id`: string, required when available; fallback deterministic hash allowed for replay/sample events
- `source_mode`: `live` or `replay`
- `domain`: Wikimedia domain, required for dashboard metrics and bot spike signal
- `event_type`: RecentChange event type, required for event-type breakdown
- `event_ts`: event timestamp from source when available
- `observed_at`: local processing timestamp
- `user_label`: account/user label when present
- `is_bot`: boolean bot flag; missing values default to `false` only with a missing-field data-quality count
- `namespace`: integer or null
- `title`: page title or null
- `minor`: boolean or null
- `patrolled`: boolean or null
- `length_old`: integer or null
- `length_new`: integer or null
- `revision_old`: integer or null
- `revision_new`: integer or null
- `comment_present`: boolean
- `missing_fields`: array of expected fields absent from the raw event
- `quality_status`: `accepted`, `accepted_missing_fields`, or `rejected`

**Validation rules**
- Records missing `domain` or `event_type` are rejected for MVP metrics because they cannot support required dashboard groups.
- Records missing optional fields such as `namespace`, `title`, size, revision, or patrol fields remain accepted with missing-field counts.
- Event-time and observed-time are both stored. Windowing uses `event_ts` when it is present, parseable, and no more than 10 minutes ahead of `observed_at`; otherwise it uses `observed_at` and records the timestamp issue as a missing-field/data-quality note. This prevents missing, malformed, or highly skewed event timestamps from placing events into inconsistent windows.

## ActivityMetric

Aggregated measurement over a bounded time window.

**Fields**
- `window_start`
- `window_end`
- `source_mode`
- `metric_name`: `events_per_minute`, `top_domains`, `event_type_breakdown`, `bot_share`, `non_bot_share`
- `domain`: nullable; present for domain-level metrics
- `event_type`: nullable; present for event-type metrics
- `is_bot`: nullable; present for bot-share metrics
- `value`: numeric count, rate, or share
- `record_count`: source event count behind the metric
- `computed_at`

**Relationships**
- Derived from many `NormalizedRecentChangeEvent` records.
- Used by the dashboard overview.

## BotSpikeSignal

Explainable domain-level observability signal for unusually high bot-flagged activity.

**Fields**
- `signal_id`
- `source_mode`
- `domain`
- `window_start`
- `window_end`
- `current_bot_events`
- `baseline_window_start`
- `baseline_window_end`
- `baseline_bot_events_per_window`
- `spike_ratio`
- `threshold_ratio`
- `min_current_events`
- `top_contributing_bot_labels`: optional limited list of `{user_label, event_count}`
- `wording`: non-accusatory human-readable summary
- `limitations`: required explanation that this is not an enforcement decision or account-level accusation
- `computed_at`

**Validation rules**
- Primary grouping is `domain`, not account.
- Only bot-flagged normalized events are used for current and baseline counts.
- Default current window is 5 minutes. Default baseline is the previous 30 minutes for the same domain, excluding the current window, normalized to 5-minute equivalents.
- Default thresholds are `min_current_events = 20` and `threshold_ratio = 3.0`.
- Do not emit a signal unless `current_bot_events >= min_current_events` and `spike_ratio >= threshold_ratio`.
- If baseline is zero, do not calculate an infinite ratio; emit only when `current_bot_events >= min_current_events` and mark the comparison as `new-or-zero-baseline`.
- If top contributing bot labels are shown, include limitation text.

## ReplaySample

Bundled representative replay dataset for demos and tests.

**Fields**
- `sample_id`
- `description`
- `source_note`: explains public-data-derived/representative nature
- `events_path`: JSONL path under `data/replay/`
- `expected_signal_domain`
- `expected_quality_counts`: malformed/rejected count and missing-field count

**Validation rules**
- Must demonstrate overview metrics and at least one bot spike signal within 2 minutes of replay mode startup.
- Must be clearly identified as replayed data in dashboard freshness and signal views.

## DataQualityCount

Aggregated data-quality status for ingestion/replay and dashboard display.

**Fields**
- `window_start`
- `window_end`
- `source_mode`
- `malformed_rejected_count`
- `missing_field_count`
- `accepted_count`
- `latest_event_observed_at`
- `freshness_status`: `fresh`, `stale`, or `replay`
- `notes`

**Validation rules**
- Malformed/rejected and missing-field counts are never merged.
- Live freshness is `fresh` only when the latest observed event is no more than 60 seconds old.
- Replay freshness must be labeled as replay, not live fresh/stale current activity.
