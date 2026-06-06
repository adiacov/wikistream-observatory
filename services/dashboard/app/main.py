"""Streamlit dashboard for WikiStream Observatory."""

from __future__ import annotations

from collections import defaultdict

import streamlit as st

from wikistream_observatory.config import load_config

from app.data import bot_spike_empty_state, dashboard_status, load_bot_spike_signals, load_overview_metrics


def _metric_rows(metrics: list[dict], metric_name: str) -> list[dict]:
    return [row for row in metrics if row.get("metric_name") == metric_name]


def _latest_by_dimension(rows: list[dict], dimension: str) -> dict[str, float]:
    values: dict[str, float] = defaultdict(float)
    for row in rows:
        key = row.get(dimension)
        if key is not None:
            values[str(key)] += float(row.get("value") or 0)
    return dict(sorted(values.items(), key=lambda item: item[1], reverse=True))


def render_mode_and_freshness() -> None:
    config = load_config()
    status = dashboard_status(config.snapshots.path, source_mode=config.mode, freshness_seconds=config.freshness_seconds)

    st.subheader("Mode and freshness")
    cols = st.columns(3)
    cols[0].metric("Mode", status["source_mode"])
    cols[1].metric("Freshness", status["freshness_status"])
    latest = status["latest_observed_at"]
    cols[2].metric("Latest observed event", latest.isoformat() if latest else "No data yet")

    if status["freshness_status"] == "stale":
        st.warning("Live data is stale: no event has been observed within the configured freshness window.")
    elif status["freshness_status"] == "no_data":
        st.info("No snapshots are available yet. Start live ingestion or replay mode and wait for the processor to write snapshots.")
    elif status["freshness_status"] == "replay":
        st.info("Replay data is shown for demonstration and is not current live Wikimedia activity.")


def render_overview() -> None:
    config = load_config()
    metrics = load_overview_metrics(config.snapshots.path, source_mode=config.mode)

    st.subheader(f"{config.mode.title()} activity overview")
    if config.mode == "replay":
        st.info("Replay overview metrics come from bundled demo data and are not current live Wikimedia activity.")
    if not metrics:
        st.info(f"No {config.mode} activity snapshots are available yet.")
        return

    volume = _metric_rows(metrics, "events_per_minute")
    top_domains = _latest_by_dimension(_metric_rows(metrics, "top_domains"), "domain")
    event_types = _latest_by_dimension(_metric_rows(metrics, "event_type_breakdown"), "event_type")
    shares = _metric_rows(metrics, "bot_share") + _metric_rows(metrics, "non_bot_share")

    if volume:
        st.line_chart({"events_per_minute": [float(row.get("value") or 0) for row in reversed(volume[-60:])]})
    if top_domains:
        st.write("Top active Wikimedia domains")
        st.bar_chart(top_domains)
    if event_types:
        st.write("Event type breakdown")
        st.bar_chart(event_types)
    if shares:
        bot_share = sum(float(row.get("value") or 0) for row in shares if row.get("metric_name") == "bot_share")
        non_bot_share = sum(float(row.get("value") or 0) for row in shares if row.get("metric_name") == "non_bot_share")
        st.write("Bot/non-bot share")
        st.bar_chart({"bot": bot_share, "non_bot": non_bot_share})


def _format_ts(value: object) -> str:
    return value.isoformat() if hasattr(value, "isoformat") else str(value or "n/a")


def _format_ratio(value: object) -> str:
    if value is None:
        return "new-or-zero-baseline"
    try:
        return f"{float(value):.1f}x"
    except (TypeError, ValueError):
        return str(value)


def _contributors(value: object) -> list[dict]:
    if value is None:
        return []
    if isinstance(value, list):
        return [item for item in value if isinstance(item, dict)]
    return []


def render_bot_spike_signals() -> None:
    config = load_config()
    signals = load_bot_spike_signals(config.snapshots.path, source_mode=config.mode)

    st.subheader("Domain-level bot spike signal")
    st.caption(
        "Compares bot-flagged activity in the latest "
        f"{config.signals.current_window_minutes}-minute window with the previous "
        f"{config.signals.baseline_window_minutes}-minute domain baseline."
    )

    if config.mode == "replay":
        st.info("Replay signals are deterministic demo outputs from bundled sample data, not current live Wikimedia activity.")

    if not signals:
        st.info(
            bot_spike_empty_state(
                current_window_minutes=config.signals.current_window_minutes,
                baseline_window_minutes=config.signals.baseline_window_minutes,
                min_current_events=config.signals.min_events,
                threshold_ratio=config.signals.threshold_ratio,
            )
        )
        return

    for signal in signals[:10]:
        domain = signal.get("domain", "unknown domain")
        with st.container(border=True):
            st.markdown(f"**{domain}**")
            cols = st.columns(4)
            cols[0].metric("Current bot events", int(signal.get("current_bot_events") or 0))
            cols[1].metric("Baseline / window", f"{float(signal.get('baseline_bot_events_per_window') or 0):.1f}")
            cols[2].metric("Spike magnitude", _format_ratio(signal.get("spike_ratio")))
            cols[3].metric("Threshold", f"{float(signal.get('threshold_ratio') or config.signals.threshold_ratio):.1f}x")

            st.write(signal.get("wording") or "Domain-level bot activity spike signal.")
            st.caption(
                "Current window: "
                f"{_format_ts(signal.get('window_start'))} → {_format_ts(signal.get('window_end'))} · "
                "Baseline window: "
                f"{_format_ts(signal.get('baseline_window_start'))} → {_format_ts(signal.get('baseline_window_end'))} · "
                f"Minimum current events: {int(signal.get('min_current_events') or config.signals.min_events)}"
            )

            contributors = _contributors(signal.get("top_contributing_bot_labels"))
            if contributors:
                st.write("Top contributing bot labels (context only)")
                st.dataframe(contributors[: config.signals.top_bots_limit], hide_index=True, use_container_width=True)

            st.warning(
                signal.get("limitations")
                or "This is an observability signal, not an enforcement decision or account-level accusation."
            )


def main() -> None:
    config = load_config()
    st.set_page_config(page_title="WikiStream Observatory", page_icon="🌊", layout="wide")
    st.title("WikiStream Observatory")
    st.caption("Read-only Wikimedia RecentChanges observability signals. Dashboard queries snapshots about every 15 seconds by default.")
    if config.mode == "replay":
        st.warning("Replay mode is active: all displayed data is demonstration/sample data, not current live Wikimedia activity.")

    render_mode_and_freshness()
    render_overview()
    render_bot_spike_signals()

    st.caption(f"Snapshot path: `{config.snapshots.path}` · Refresh interval target: {config.dashboard_refresh_seconds}s")


if __name__ == "__main__":
    main()
