"""Windowed activity metric aggregation."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import datetime
from typing import Iterable

from wikistream_observatory.models import ActivityMetric, NormalizedRecentChangeEvent
from wikistream_observatory.time_utils import bucket_bounds, utc_now


def compute_activity_metrics(events: Iterable[NormalizedRecentChangeEvent], *, computed_at: datetime | None = None) -> list[ActivityMetric]:
    """Compute 1-minute overview metrics for dashboard snapshots."""

    event_list = list(events)
    if not event_list:
        return []
    computed_at = computed_at or utc_now()

    buckets: dict[tuple[datetime, datetime, str], list[NormalizedRecentChangeEvent]] = defaultdict(list)
    for event in event_list:
        start, end = bucket_bounds(event.event_ts, minutes=1)
        buckets[(start, end, event.source_mode)].append(event)

    metrics: list[ActivityMetric] = []
    for (window_start, window_end, source_mode), bucket_events in sorted(buckets.items()):
        total = len(bucket_events)
        metrics.append(
            ActivityMetric(
                window_start=window_start,
                window_end=window_end,
                source_mode=source_mode,
                metric_name="events_per_minute",
                value=float(total),
                record_count=total,
                computed_at=computed_at,
            )
        )

        for domain, count in Counter(event.domain for event in bucket_events).most_common(20):
            metrics.append(
                ActivityMetric(
                    window_start=window_start,
                    window_end=window_end,
                    source_mode=source_mode,
                    metric_name="top_domains",
                    domain=domain,
                    value=float(count),
                    record_count=count,
                    computed_at=computed_at,
                )
            )

        for event_type, count in Counter(event.event_type for event in bucket_events).most_common():
            metrics.append(
                ActivityMetric(
                    window_start=window_start,
                    window_end=window_end,
                    source_mode=source_mode,
                    metric_name="event_type_breakdown",
                    event_type=event_type,
                    value=float(count),
                    record_count=count,
                    computed_at=computed_at,
                )
            )

        bot_count = sum(1 for event in bucket_events if event.is_bot)
        non_bot_count = total - bot_count
        metrics.append(
            ActivityMetric(
                window_start=window_start,
                window_end=window_end,
                source_mode=source_mode,
                metric_name="bot_share",
                is_bot=True,
                value=bot_count / total if total else 0.0,
                record_count=bot_count,
                computed_at=computed_at,
            )
        )
        metrics.append(
            ActivityMetric(
                window_start=window_start,
                window_end=window_end,
                source_mode=source_mode,
                metric_name="non_bot_share",
                is_bot=False,
                value=non_bot_count / total if total else 0.0,
                record_count=non_bot_count,
                computed_at=computed_at,
            )
        )

    return metrics
