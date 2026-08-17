"""
parquet_export.py
=================
Writes the routed/transformed Bronze rows to Parquet files before they are
loaded into the database.

The export happens after routing + transformation (so the files contain the
exact table-shaped rows the writer would insert, metadata columns included)
but before any database write. Because it operates on `rows_by_table` — the
generic structure every feed is fanned out into — the same code path covers
any feed type and any future contract file with no per-file changes.

Layout
------
Each run writes one file per Bronze table under a dedicated output directory
(default `parquet_output/`, configurable via PARQUET_OUTPUT_DIR or
--parquet-dir):

    <output_dir>/<feed_type>/<table>/ingest_date=YYYY-MM-DD/<pipeline_run_id>.parquet

The Hive-style `ingest_date=` partition and run-id filename mean repeated runs
never clobber each other, and engines like DuckDB / Spark / Synapse can read
the whole directory as a partitioned dataset.

Column values are already Parquet-friendly: `transformers._scalarize` reduces
every business column to text (or None), and the metadata columns are strings
and timezone-aware datetimes. The only exception is `raw_payload`, which is
still a dict and is serialised to a JSON string here.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List

from .bronze import schemas
from .config import RunContext


def _parquet_safe(column: str, value: Any) -> Any:
    """raw_payload is the one non-scalar column; store it as JSON text."""
    if column == "raw_payload" and value is not None and not isinstance(value, str):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def export_tables(
    rows_by_table: Dict[str, List[Dict[str, Any]]],
    ctx: RunContext,
    feed_type: str,
    output_dir: str,
) -> List[str]:
    """Write one Parquet file per table and return the paths written."""
    # Imported lazily (like the DB drivers) so environments that never export
    # Parquet don't need pyarrow installed.
    import pyarrow as pa
    import pyarrow.parquet as pq

    written: List[str] = []
    ingest_date = ctx.pipeline_start_ts.strftime("%Y-%m-%d")

    for table in schemas.BUSINESS_COLUMNS:  # deterministic order, like the writer
        rows = rows_by_table.get(table, [])
        if not rows:
            continue

        columns = schemas.all_db_columns(table)
        records = [{c: _parquet_safe(c, row.get(c)) for c in columns} for row in rows]
        arrow_table = pa.Table.from_pylist(records)

        target_dir = (
            Path(output_dir) / feed_type / table / f"ingest_date={ingest_date}"
        )
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / f"{ctx.pipeline_run_id}.parquet"

        pq.write_table(arrow_table, file_path, compression="snappy")
        written.append(str(file_path))

    return written
