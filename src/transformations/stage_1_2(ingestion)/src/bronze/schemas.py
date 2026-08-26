"""
schemas.py
==========
Single source of truth for the Bronze-layer table definitions.

The column lists below are transcribed directly from the "Bronze Layer" sheet of
FT_Tracker2_0_Tables_Schema-Draft.xlsx. They are used in two places:

  1. To generate the CREATE SCHEMA / CREATE TABLE DDL (see generate_ddl()).
  2. To map incoming JSON keys onto database columns (see bronze.transformers).

Keeping both the SQL and the Python mapping derived from this one module avoids
schema drift between the database and the ingestion code.

Design decision — Bronze lands business fields as TEXT
------------------------------------------------------
The sheet declares native types (int, datetime, date) for each business column.
In the Bronze layer we deliberately land every *business* column as TEXT and
preserve the source value verbatim. This is a common raw-zone pattern: it keeps
ingestion resilient to dirty/ambiguous source values (the sheet's own validation
tab mixes "13/4/2026" with Excel serials like 46360), and defers type
enforcement to the Silver transformation. The originally-declared type is kept
as an inline SQL comment so Silver knows the intended target type.

Metadata columns (timestamps, status, hash, payload) are owned by the pipeline
and therefore use proper native types.
"""

from __future__ import annotations

from typing import Dict, List

from . import feeds

# ---------------------------------------------------------------------------
# Business columns per Bronze table (verbatim from the spreadsheet).
# (db_column is always source_key.lower(); declared_type is the sheet's type,
#  retained only as documentation since Bronze lands everything as TEXT.)
# ---------------------------------------------------------------------------

# Per-feed column lists now live one-module-per-feed in bronze/feeds/. This
# dict is assembled from them so every existing caller keeps working unchanged,
# and so a new feed needs no edit here at all.
#
# Each entry: (source_json_key, declared_type)
BUSINESS_COLUMNS: Dict[str, List[tuple]] = {
    feed.table: list(feed.columns) for feed in feeds.FEEDS
}

# ---------------------------------------------------------------------------
# Pipeline-owned metadata columns appended to EVERY Bronze business table.
# (column_name, postgres_type)
# ---------------------------------------------------------------------------
METADATA_COLUMNS: List[tuple] = [
    ("raw_record_id", "VARCHAR(256)"),       # natural/source id of the record
    ("hash_key", "VARCHAR(64)"),             # SHA-256 content hash -> idempotency key
    ("pipeline_run_id", "VARCHAR(64)"),      # one value per pipeline execution
    ("source_system", "VARCHAR(128)"),       # e.g. "NatGasHub"
    ("source_api", "VARCHAR(256)"),          # e.g. "natgashub/v1/.../firm"
    ("source_file_name", "VARCHAR(512)"),    # input file the record came from
    ("ingestion_timestamp", "TIMESTAMPTZ"),  # == sheet's "ingestion_ts"
    ("updated_ts", "TIMESTAMPTZ"),           # last time this hash_key was touched
    ("ingestion_status", "VARCHAR(32)"),     # LOADED | INVALID
    ("raw_payload", "JSONB"),                # original JSON fragment for this row
]

# ---------------------------------------------------------------------------
# Pipeline freshness marker, per table: every landed row starts 'fresh' and
# ammendments(p2) later flips it to 'processed'. Named per-table because gawd
# already has a business column "status" (the award's own status, which stage 3
# reads), so the marker is "record_status" there. gindex carries none: IOC
# skips the staging phases.
# ---------------------------------------------------------------------------
STATUS_COLUMNS: Dict[str, str] = {
    "gtran_firm": "status",
    "gtran_it": "status",
    "gawd": "record_status",
}
STATUS_FRESH = "fresh"

SCHEMA_NAME = "bronze"

# Convenience lookups -------------------------------------------------------

def business_db_columns(table: str) -> List[str]:
    """Lowercased DB column names for a table's business fields."""
    return [src.lower() for src, _ in BUSINESS_COLUMNS[table]]


def all_db_columns(table: str) -> List[str]:
    """Business columns followed by metadata columns (DB order)."""
    columns = business_db_columns(table) + [c for c, _ in METADATA_COLUMNS]
    status_col = STATUS_COLUMNS.get(table)
    if status_col:
        columns.append(status_col)
    return columns


def source_key_map(table: str) -> Dict[str, str]:
    """Map lowercased-source-key -> db column, for case-insensitive matching.

    Includes the feed's ALIASES, so a producer that spells a field differently
    (live NatGasHub `KQty` vs the fixture's `KQtyK`) resolves to the same
    column with no special-casing in the transformer.
    """
    return feeds.for_table(table).source_key_map


# ---------------------------------------------------------------------------
# DDL generation
# ---------------------------------------------------------------------------

def _q(identifier: str) -> str:
    """Quote a Postgres identifier (lowercased)."""
    return '"' + identifier.replace('"', '""') + '"'


def generate_table_ddl(table: str) -> str:
    lines = [f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.{_q(table)} ("]
    col_lines = ["    bronze_row_id BIGSERIAL PRIMARY KEY,"]

    for src, declared in BUSINESS_COLUMNS[table]:
        col_lines.append(f"    {_q(src.lower()):<28} TEXT,            -- source type: {declared}")

    col_lines.append("    -- ---- pipeline metadata ----")
    for col, pgtype in METADATA_COLUMNS:
        col_lines.append(f"    {_q(col):<28} {pgtype},")
    status_col = STATUS_COLUMNS.get(table)
    if status_col:
        col_lines.append(
            f"    {_q(status_col):<28} VARCHAR(16) DEFAULT '{STATUS_FRESH}',"
        )

    # No UNIQUE here: Bronze is the full history, duplicates included.
    # Stage 3's deduplication(p1) is the one place duplicates are filtered.
    if col_lines[-1].endswith(","):
        col_lines[-1] = col_lines[-1][:-1]

    lines.append("\n".join(col_lines))
    lines.append(");")
    # helpful lookup indexes
    lines.append(
        f"CREATE INDEX IF NOT EXISTS {_q('ix_' + table + '_run')} "
        f"ON {SCHEMA_NAME}.{_q(table)} (pipeline_run_id);"
    )
    lines.append(
        f"CREATE INDEX IF NOT EXISTS {_q('ix_' + table + '_recid')} "
        f"ON {SCHEMA_NAME}.{_q(table)} (raw_record_id);"
    )
    # ---- forward migration for a table that already exists -----------------
    # CREATE TABLE IF NOT EXISTS is a no-op once the table is there, so a column
    # added to a feed later would never reach an existing database and the
    # writer's INSERT would fail on the missing column. ADD COLUMN IF NOT EXISTS
    # closes that: new business columns appear on the next ingest, and the
    # statement is a no-op for every column already present.
    #
    # Only ever ADDITIVE. A column removed from a feed definition is left in
    # place rather than dropped -- dropping one destroys landed data, which is a
    # deliberate migration, not something an ingest should do on its own.
    for src, _declared in BUSINESS_COLUMNS[table]:
        lines.append(
            f"ALTER TABLE {SCHEMA_NAME}.{_q(table)} "
            f"ADD COLUMN IF NOT EXISTS {_q(src.lower())} TEXT;"
        )
    # The freshness marker migrates the same way; the DEFAULT backfills
    # existing rows as 'fresh', which is what a first deployment wants.
    if status_col:
        lines.append(
            f"ALTER TABLE {SCHEMA_NAME}.{_q(table)} "
            f"ADD COLUMN IF NOT EXISTS {_q(status_col)} "
            f"VARCHAR(16) DEFAULT '{STATUS_FRESH}';"
        )
    return "\n".join(lines)


def generate_log_ddl() -> str:
    """Pipeline run/activity log table (from the Logging + Validation sheets)."""
    return f"""CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}."ingestion_log" (
    log_id BIGSERIAL PRIMARY KEY,
    pipeline_name           VARCHAR(128),
    pipeline_layer          VARCHAR(32),
    pipeline_run_id         VARCHAR(64),
    activity_name           VARCHAR(128),
    activity_run_id         VARCHAR(64),
    source_system           VARCHAR(128),
    source_api              VARCHAR(256),
    source_file_name        VARCHAR(512),
    triggered_by            VARCHAR(256),
    pipeline_start_ts       TIMESTAMPTZ,
    pipeline_end_ts         TIMESTAMPTZ,
    activity_duration_secs  NUMERIC,
    objects_read            INTEGER,
    rows_written            INTEGER,
    rows_rejected           INTEGER,
    pipeline_status         VARCHAR(32),
    data_validation_status  VARCHAR(32),
    error_details           TEXT,
    logged_at_ts            TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS "ix_ingestion_log_run"
    ON {SCHEMA_NAME}."ingestion_log" (pipeline_run_id);"""


def generate_ddl() -> str:
    """Full Bronze DDL: schema + all business tables + log table."""
    parts = [
        "-- Auto-generated from src/bronze/schemas.py — do not hand-edit.",
        "-- Regenerate with:  python -m src.bronze.schemas",
        "",
        f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};",
        "",
    ]
    for table in BUSINESS_COLUMNS:
        parts.append(generate_table_ddl(table))
        parts.append("")
    parts.append(generate_log_ddl())
    parts.append("")
    return "\n".join(parts)


if __name__ == "__main__":
    # `python -m src.bronze.schemas` prints the DDL to stdout.
    print(generate_ddl())
