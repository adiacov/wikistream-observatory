"""Domain-level observability signal detection."""

from __future__ import annotations

from collections import Counter, defaultdict
from collections.abc import Iterable
from datetime import datetime, timedelta
import hashlib

from wikistream_observatory.models import BotContributor, BotSpikeSignal, NormalizedRecentChangeEvent, SourceMode
from wikistream_observatory.time_utils import ensure_utc, floor_to_bucket, utc_now


def _signal_id(domain: str, window_start: datetime, window_end: datetime, source_mode: SourceMode) -> str:
    raw = f"{source_mode}|{domain}|{window_start.isoformat()}|{window_end.isoformat()}"
    return hashlib.sha256(raw.encode("utf-8")).hexdigest()[:24]


def _current_window(computed_at: datetime, current_window_minutes: int) -> tuple[datetime, datetime]:
    computed_at = ensure_utc(computed_at)
    boundary = floor_to_bucket(computed_at, current_window_minutes)
    if computed_at == boundary:
        end = boundary
    else:
        end = boundary + timedelta(minutes=current_window_minutes)
    return end - timedelta(minutes=current_window_minutes), end


def _top_contributors(events: Iterable[NormalizedRecentChangeEvent], limit: int) -> list[BotContributor]:
    counts: Counter[str] = Counter(event.user_label or "unknown" for event in events)
    return [BotContributor(user_label=user, event_count=count) for user, count in counts.most_common(limit)]


def _build_wording(*, domain: str, current_count: int, baseline_per_window: float, ratio: float | None) -> str:
    if ratio is None:
        comparison = "new-or-zero-baseline"
    else:
        comparison = f"{ratio:.1f}x the recent baseline"
    return f"Bot activity spike signal for domain {domain}: {current_count} bot-flagged events versus {baseline_per_window:.1f} baseline events per window ({comparison})."


def _limitations() -> str:
    return "This is an observability signal, not an enforcement decision or account-level accusation. Bot labels and contributor names are contextual and require review."


def detect_bot_spikes(
    events: Iterable[NormalizedRecentChangeEvent],
    *,
    computed_at: datetime | None = None,
    current_window_minutes: int = 5,
    baseline_window_minutes: int = 30,
    threshold_ratio: float = 3.0,
    min_current_events: int = 20,
    top_bots_limit: int = 3,
) -> list[BotSpikeSignal]:
    """Detect domain-level bot activity spikes relative to a recent baseline."""

    if current_window_minutes <= 0:
        raise ValueError("current_window_minutes must be positive")
    if baseline_window_minutes <= 0:
        raise ValueError("baseline_window_minutes must be positive")
    if threshold_ratio <= 0:
        raise ValueError("threshold_ratio must be positive")
    if min_current_events <= 0:
        raise ValueError("min_current_events must be positive")
    if top_bots_limit <= 0:
        raise ValueError("top_bots_limit must be positive")

    computed_at = ensure_utc(computed_at or utc_now())
    window_start, window_end = _current_window(computed_at, current_window_minutes)
    baseline_start = window_start - timedelta(minutes=baseline_window_minutes)
    baseline_end = window_start
    baseline_window_count = baseline_window_minutes / current_window_minutes

    current_by_domain: dict[str, list[NormalizedRecentChangeEvent]] = defaultdict(list)
    baseline_counts: Counter[str] = Counter()

    for event in events:
        if not event.is_bot:
            continue
        event_ts = ensure_utc(event.event_ts)
        if window_start <= event_ts < window_end:
            current_by_domain[event.domain].append(event)
        elif baseline_start <= event_ts < baseline_end:
            baseline_counts[event.domain] += 1

    signals: list[BotSpikeSignal] = []
    for domain, current_events in sorted(current_by_domain.items()):
        current_count = len(current_events)
        if current_count < min_current_events:
            continue

        baseline_per_window = baseline_counts[domain] / baseline_window_count
        if baseline_per_window == 0:
            ratio = None
        else:
            ratio = current_count / baseline_per_window
            if ratio < threshold_ratio:
                continue

        source_mode = current_events[0].source_mode
        signals.append(
            BotSpikeSignal(
                signal_id=_signal_id(domain, window_start, window_end, source_mode),
                source_mode=source_mode,
                domain=domain,
                window_start=window_start,
                window_end=window_end,
                current_bot_events=current_count,
                baseline_window_start=baseline_start,
                baseline_window_end=baseline_end,
                baseline_bot_events_per_window=baseline_per_window,
                spike_ratio=ratio,
                threshold_ratio=threshold_ratio,
                min_current_events=min_current_events,
                top_contributing_bot_labels=_top_contributors(current_events, top_bots_limit),
                wording=_build_wording(
                    domain=domain,
                    current_count=current_count,
                    baseline_per_window=baseline_per_window,
                    ratio=ratio,
                ),
                limitations=_limitations(),
                computed_at=computed_at,
            )
        )

    return signals
