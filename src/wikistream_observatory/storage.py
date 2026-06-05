"""Parquet snapshot storage helpers."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone, timedelta
from pathlib import Path
import os
import uuid
from typing import Any, Iterable


def dataset_path(snapshot_root: Path | str, dataset: str) -> Path:
    """Return the directory for a logical snapshot dataset."""

    return Path(snapshot_root) / dataset


def _records_to_dicts(records: Iterable[Any]) -> list[dict[str, Any]]:
    output: list[dict[str, Any]] = []
    for record in records:
        if is_dataclass(record):
            output.append(asdict(record))
        elif isinstance(record, dict):
            output.append(dict(record))
        else:
            raise TypeError(f"Unsupported snapshot record type: {type(record)!r}")
    return output


def write_parquet_snapshot(records: Iterable[Any], snapshot_root: Path | str, dataset: str, *, partition: str | None = None) -> Path | None:
    """Write records to a Parquet file using temp-file then atomic rename.

    Returns the final path, or ``None`` when there are no records to write.
    """

    rows = _records_to_dicts(records)
    if not rows:
        return None

    import pyarrow as pa
    import pyarrow.parquet as pq

    target_dir = dataset_path(snapshot_root, dataset)
    if partition:
        target_dir = target_dir / partition
    target_dir.mkdir(parents=True, exist_ok=True)

    file_id = uuid.uuid4().hex
    tmp_path = target_dir / f".{file_id}.tmp.parquet"
    final_path = target_dir / f"part-{file_id}.parquet"

    table = pa.Table.from_pylist(rows)
    pq.write_table(table, tmp_path)
    os.replace(tmp_path, final_path)
    return final_path


def remove_live_snapshots_older_than(snapshot_root: Path | str, retention_hours: int, *, now: datetime | None = None) -> int:
    """Remove generated Parquet snapshots older than the live retention window."""

    root = Path(snapshot_root)
    if not root.exists():
        return 0
    cutoff = (now or datetime.now(timezone.utc)) - timedelta(hours=retention_hours)
    removed = 0
    for path in root.rglob("*.parquet"):
        try:
            mtime = datetime.fromtimestamp(path.stat().st_mtime, tz=timezone.utc)
        except FileNotFoundError:
            continue
        if mtime < cutoff:
            path.unlink(missing_ok=True)
            removed += 1
    return removed
