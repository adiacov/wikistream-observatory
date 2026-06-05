"""Streamlit dashboard for WikiStream Observatory."""

from __future__ import annotations

from collections import defaultdict

import streamlit as st

from wikistream_observatory.config import load_config

from app.data import dashboard_status, load_overview_metrics


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
    metrics = load_overview_metrics(config.snapshots.path)

    st.subheader("Live/replay activity overview")
    if not metrics:
        st.info("No activity snapshots are available yet.")
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


def main() -> None:
    config = load_config()
    st.set_page_config(page_title="WikiStream Observatory", page_icon="🌊", layout="wide")
    st.title("WikiStream Observatory")
    st.caption("Read-only Wikimedia RecentChanges observability signals. Dashboard queries snapshots about every 15 seconds by default.")

    render_mode_and_freshness()
    render_overview()

    st.caption(f"Snapshot path: `{config.snapshots.path}` · Refresh interval target: {config.dashboard_refresh_seconds}s")


if __name__ == "__main__":
    main()
