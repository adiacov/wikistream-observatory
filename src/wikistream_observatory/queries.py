"""DuckDB query helpers for Parquet snapshot datasets."""

from __future__ import annotations

from pathlib import Path
from typing import Any


def snapshot_glob(snapshot_root: Path | str, dataset: str) -> str | None:
    dataset_dir = Path(snapshot_root) / dataset
    if not dataset_dir.exists():
        return None
    files = sorted(dataset_dir.rglob("*.parquet"))
    return str(dataset_dir / "**" / "*.parquet") if files else None


def _sql_string_literal(value: str) -> str:
    """Return a single-quoted SQL string literal with quotes escaped."""

    return "'" + value.replace("'", "''") + "'"


def query_snapshot(snapshot_root: Path | str, dataset: str, sql: str | None = None) -> list[dict[str, Any]]:
    """Query a snapshot dataset and tolerate missing/empty Parquet files."""

    glob = snapshot_glob(snapshot_root, dataset)
    if glob is None:
        return []

    import duckdb

    query = sql or "SELECT * FROM snapshot"
    with duckdb.connect(database=":memory:", read_only=False) as con:
        con.execute(f"CREATE VIEW snapshot AS SELECT * FROM read_parquet({_sql_string_literal(glob)}, union_by_name=True)")
        rows = con.execute(query).fetchall()
        columns = [desc[0] for desc in con.description]
    return [dict(zip(columns, row, strict=True)) for row in rows]


def latest_rows(snapshot_root: Path | str, dataset: str, order_by: str = "computed_at", limit: int = 100) -> list[dict[str, Any]]:
    if limit <= 0:
        raise ValueError("limit must be positive")
    return query_snapshot(snapshot_root, dataset, f"SELECT * FROM snapshot ORDER BY {order_by} DESC LIMIT {int(limit)}")
