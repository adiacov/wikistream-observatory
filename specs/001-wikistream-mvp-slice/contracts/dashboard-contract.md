# Contract: Streamlit Dashboard

Dashboard URL: `http://localhost:8501` when started with Docker Compose.

## Required sections

1. **Mode and freshness**
   - Shows whether data is `live` or `replay`.
   - Shows latest observed event time.
   - Marks live data fresh only when latest observed event is within 60 seconds; otherwise marks stale.

2. **Live/replay activity overview**
   - Event volume over time.
   - Top active Wikimedia domains.
   - Event type breakdown.
   - Bot/non-bot share.

3. **Domain-level bot spike signal**
   - Shows current bot-flagged activity, baseline comparison, spike magnitude, domain, comparison window, and threshold context.
   - May show limited top contributing bot account labels as context.
   - Must include limitation text that the signal is not an enforcement decision, abuse determination, or account-level accusation.
   - If no signal meets threshold, shows clear empty-state text and explains the evaluation method.

4. **Data quality**
   - Shows malformed/rejected counts separately from missing-field counts.
   - Explains how missing fields affect metrics/signals.

5. **Limitations/responsible use**
   - States that the project is read-only and observability-focused.
   - Avoids accusation-oriented language.
   - Notes that stream-derived signals require contextual review.

## Empty/error states

- If snapshots are missing, dashboard should instruct the reviewer to start live ingestion or replay mode.
- If live stream is unavailable, dashboard should show stale/no-data status rather than implying current activity.
- If replay mode is active, no widget may present replay data as current live activity.
