"""
parquet_export.py
=================
Writes each table's rows to Parquet, partitioned by stage and by JSON source
feed. Called from the single choke point every transformation funnels through
(core/base.py :: SilverTransformation.run), so a new table is exported without
touching this file.

LAYOUT
------
    <output_dir>/<stage>/<source>/<table>/run_date=YYYY-MM-DD/<run_id>.parquet

`run_id` is shared across every table in a run, so one run's output is greppable
and re-runnable. `run_date=` is Hive-style, so a whole tree reads back as one
partitioned dataset (pyarrow reconstructs `run_date` as a column on read; it is
deliberately not duplicated inside the files).

THE FOUR JSON SOURCE FEEDS
--------------------------
Everything upstream originates in one of four feeds, and each gets its own
directory so a consumer can read one feed without scanning the others:

    firm           gtran_firm  / gtran_loc     / gtran_rates
    interruptible  gtran_it    / gtran_it_loc  / gtran_it_rates   (aka "IT")
    awards         no ingestion feed yet
    ioc            no ingestion feed yet

Only firm and interruptible have feeds today; awards and ioc are declared here so
their tables land in the right place the moment those feeds arrive. Anything that
spans feeds (or hasn't declared one) goes to `_combined`, which is why the
resolver never raises -- a mislabelled source should not fail a load.

PER-STAGE FUNCTIONS
-------------------
`export_rows` holds the mechanics and knows nothing about any stage. Each stage
then gets its own named entry point, so a stage can diverge later (different
partitioning, a manifest, a different compression) without touching the others
or the caller:

    export_stage3_rows   Bronze -> Silver          (bronze_to_silver.yml)
    export_stage4_rows   rec-del pairing           (rec_del_pairing.yml)
    export_stage5_rows   master capacity           (master_capacity.yml)

`export_for_stage` dispatches on the stage label, and falls back to the generic
exporter for a stage that has no dedicated function yet -- so adding a stage
still needs no change here, only a dict entry if it wants custom behaviour.

pyarrow is imported lazily, matching how db/connection.py defers the database
driver: commands that don't export (--list, --show-sql) work without it.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional
from uuid import uuid4

from .logging_config import get_logger

log = get_logger(__name__)

# --------------------------------------------------------------------- sources

FIRM = "firm"
INTERRUPTIBLE = "interruptible"
AWARDS = "awards"
IOC = "ioc"

#: The four JSON source feeds, in pipeline order.
SOURCES = (FIRM, INTERRUPTIBLE, AWARDS, IOC)

#: Bucket for rows that span feeds or never declared one.
COMBINED = "_combined"

#: Spellings seen across the feeds, the dashboard and the Bronze table names.
_SOURCE_ALIASES = {
    "firm": FIRM,
    "firms": FIRM,
    "gtran_firm": FIRM,
    "it": INTERRUPTIBLE,
    "interruptible": INTERRUPTIBLE,
    "interruptibles": INTERRUPTIBLE,
    "gtran_it": INTERRUPTIBLE,
    "award": AWARDS,
    "awards": AWARDS,
    "ioc": IOC,
}


def normalize_source(source: Optional[str]) -> str:
    """Map any known spelling of a feed to its canonical directory name.

    Never raises: an unrecognised or missing source becomes COMBINED and is
    logged, because a labelling mistake should not fail a load that otherwise
    succeeded.
    """
    if not source:
        return COMBINED
    key = str(source).strip().lower()
    resolved = _SOURCE_ALIASES.get(key)
    if resolved is None:
        log.warning("parquet: unrecognised source %r — filing under %s", source, COMBINED)
        return COMBINED
    return resolved


# --------------------------------------------------------------------- context


@dataclass(frozen=True)
class ExportContext:
    """Everything the exporter needs that isn't the rows themselves.

    Built once per run by the runner and passed down, so every table in a run
    shares one run_id and run_date.
    """
    run_id: str
    run_date: str
    output_dir: str
    stage: str = "unstaged"

    @classmethod
    def create(cls, output_dir: str, stage: str = "unstaged") -> "ExportContext":
        now = datetime.now(timezone.utc)
        return cls(
            run_id=f"{now.strftime('%Y%m%dT%H%M%SZ')}-{uuid4().hex[:8]}",
            run_date=now.strftime("%Y-%m-%d"),
            output_dir=output_dir,
            stage=stage or "unstaged",
        )

    def for_stage(self, stage: str) -> "ExportContext":
        """Same run, different stage folder."""
        return ExportContext(self.run_id, self.run_date, self.output_dir, stage or "unstaged")


# ------------------------------------------------------------------ mechanics


def _parquet_safe(value: Any) -> Any:
    """Coerce values Arrow can't type cleanly.

    Nested dicts/lists (e.g. a raw JSON payload column) become JSON text rather
    than being inferred as a struct, which would make the schema shift between
    runs as the payload shape varies.
    """
    if isinstance(value, (dict, list)):
        return json.dumps(value, sort_keys=True, default=str)
    return value


def target_path(table: str, ctx: ExportContext, source: Optional[str] = None) -> Path:
    """Where a table's file for this run goes. Pure -- creates nothing."""
    return (
        Path(ctx.output_dir)
        / ctx.stage
        / normalize_source(source)
        / table
        / f"run_date={ctx.run_date}"
        / f"{ctx.run_id}.parquet"
    )


def export_rows(
    table: str,
    rows: List[Dict[str, Any]],
    *,
    ctx: ExportContext,
    source: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> Optional[str]:
    """Write `rows` to one Parquet file. Returns the path, or None if no rows.

    Generic: knows nothing about any stage or table. The per-stage functions
    below all bottom out here.

    `columns` pins the column set so a table's schema stays stable even when
    some rows omit a key; it defaults to the first row's keys, which is correct
    for rows that came back from a single SQL RETURNING clause.
    """
    if not rows:
        return None

    import pyarrow as pa
    import pyarrow.parquet as pq

    cols = columns or list(rows[0].keys())
    records = [{c: _parquet_safe(row.get(c)) for c in cols} for row in rows]
    arrow_table = pa.Table.from_pylist(records)

    file_path = target_path(table, ctx, source)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    pq.write_table(arrow_table, file_path, compression="snappy")
    return str(file_path)


# --------------------------------------------------------------- per-stage API


def export_stage3_rows(table, rows, *, ctx, source=None, columns=None) -> Optional[str]:
    """Stage 3 — Bronze -> Silver staging (bronze_to_silver.yml).

    One file per Silver table, split by the feed the rows came from.
    """
    return export_rows(table, rows, ctx=ctx, source=source, columns=columns)


def export_stage4_rows(table, rows, *, ctx, source=None, columns=None) -> Optional[str]:
    """Stage 4 — rec-del pairing (rec_del_pairing.yml).

    Same mechanics as stage 3; `source` is the transport type being paired, so
    each feed's paths land in their own directory.
    """
    return export_rows(table, rows, ctx=ctx, source=source, columns=columns)


def export_stage5_rows(table, rows, *, ctx, source=None, columns=None) -> Optional[str]:
    """Stage 5 — master capacity (master_capacity.yml).

    The final tables are cross-feed by nature, so rows with no declared source
    land under `_combined` rather than being forced into one feed.
    """
    return export_rows(table, rows, ctx=ctx, source=source, columns=columns)


#: Stage label -> dedicated exporter. A stage with no entry uses `export_rows`.
STAGE_EXPORTERS: Dict[str, Callable[..., Optional[str]]] = {
    "stage3": export_stage3_rows,
    "stage_3": export_stage3_rows,
    "stage4": export_stage4_rows,
    "stage_4": export_stage4_rows,
    "stage5": export_stage5_rows,
    "stage_5": export_stage5_rows,
}


def export_for_stage(
    table: str,
    rows: List[Dict[str, Any]],
    *,
    ctx: ExportContext,
    source: Optional[str] = None,
    columns: Optional[List[str]] = None,
) -> Optional[str]:
    """Dispatch to the stage's dedicated exporter, or the generic one.

    This is what the choke point calls, so callers never name a stage and a new
    stage needs no change here to be exported.
    """
    exporter = STAGE_EXPORTERS.get(ctx.stage, export_rows)
    return exporter(table, rows, ctx=ctx, source=source, columns=columns)
