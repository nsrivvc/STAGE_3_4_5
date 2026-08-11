"""
final_base.py
=============
Shared base for the three FINAL master capacity transformations. Not a
transformation itself -- it registers nothing.

WHAT THESE DO
-------------
Each of the four feeds produces its own per-grain master capacity table. The
FINAL tables tie all four into one consolidated table per grain:

    firm_core_master_capacity           \\
    interruptible_core_master_capacity   >--- UNION ALL ---> final_core_master_capacity
    awards_core_master_capacity         /
    ioc_core_master_capacity           /

...and the same shape again for `locations` and `rates`. Every consolidated row
carries a `source_type` column naming the feed it came from, so a consolidated
table can always be split back apart.

THE CONSOLIDATION ASSUMPTION
----------------------------
A UNION only works if the four per-feed tables share a column set at a given
grain. That is the assumption baked in here: per-feed tables are the same shape,
and the final adds `source_type`. If feeds end up differing, the per-feed
projection is the place to reconcile them -- see `projection_sql`.

HOOKS LEFT FOR THE BUSINESS RULES
---------------------------------
All marked `SPEC:` and currently holding neutral placeholders, so the tables and
the wiring exist before the rules are written:

  1. `columns`        the consolidated column set for this grain.
  2. `natural_key`    what makes a consolidated row unique (drives the upsert).
  3. `projection_sql` how one feed's rows map onto that column set. The
     placeholder assumes identical column names across feeds.
  4. `dedupe_note`    what to do when the same contract appears in more than one
     feed. The placeholder keeps both rows, distinguished by `source_type`.

BLOCKED UNTIL THE PER-FEED TABLES EXIST
---------------------------------------
`source_tables` lists all four feeds, so the runner reports these as skipped
until every one of them exists. To consolidate only the feeds that are live
(firm and interruptible today), delete the other entries from `source_tables` on
the subclass -- everything else adjusts automatically.
"""

from __future__ import annotations

from typing import Dict, List, Tuple

from .....core.base import SilverTransformation

#: The four JSON source feeds, in pipeline order.
FEEDS = ("firm", "interruptible", "awards", "ioc")


class FinalMasterCapacityTransformation(SilverTransformation):
    # --- set these in each subclass ------------------------------------------
    grain: str = ""                 # "core" | "locations" | "rates"

    # SPEC: the consolidated column set, as (column_name, sql_type) pairs.
    # `source_type` is added automatically and must not be repeated here.
    columns: List[Tuple[str, str]] = []

    # SPEC: what makes a consolidated row unique. Drives the UNIQUE constraint
    # and the ON CONFLICT upsert, so it must not be empty.
    natural_key: Tuple[str, ...] = ()

    # SPEC: how duplicates across feeds are resolved. Documentation only today.
    dedupe_note: str = "keep every feed's row, distinguished by source_type"

    # These are cross-feed by nature, so `source` stays empty and the Parquet
    # export files them under `_combined` rather than any one feed.
    source: str = ""

    def __init__(self) -> None:
        if not self.grain:
            raise ValueError(f"{type(self).__name__} must set a `grain`.")
        if not self.columns:
            raise ValueError(f"{type(self).__name__} must set `columns`.")
        if not self.natural_key:
            raise ValueError(f"{type(self).__name__} must set a `natural_key`.")
        self.bronze_sources = list(self.source_tables.values())
        super().__init__()

    @property
    def source_tables(self) -> Dict[str, str]:
        """Feed -> its per-grain table name. Trim this to consolidate a subset."""
        return {feed: f"{feed}_{self.grain}_master_capacity" for feed in FEEDS}

    @property
    def source_schema(self) -> str:
        """The per-feed tables are Silver output, not Bronze."""
        return self.silver_schema

    # ------------------------------------------------------------------ hooks
    def projection_sql(self, feed: str, table: str) -> str:
        """SPEC: map one feed's rows onto the consolidated column set.

        The placeholder assumes every feed already uses the same column names,
        so it selects them straight through. When a feed differs, override this
        and do the renaming/casting here rather than in the target DDL.
        """
        cols = ",\n                   ".join(name for name, _ in self.columns)
        return f"""
            SELECT '{feed}' AS source_type,
                   {cols}
            FROM {self.source_schema}.{table}
        """

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        s = self.silver_schema
        cols = ",\n            ".join(f"{name:<34} {sql_type}" for name, sql_type in self.columns)
        key = ", ".join(self.natural_key)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {s};

        CREATE TABLE IF NOT EXISTS {s}.{self.table_name} (
            final_{self.grain}_id              BIGSERIAL PRIMARY KEY,

            -- which feed this row was consolidated from
            source_type                        TEXT NOT NULL,

            {cols},

            silver_loaded_ts                   TIMESTAMPTZ DEFAULT now(),

            -- Dedupe rule: {self.dedupe_note}
            -- NULLS NOT DISTINCT (PG15+) so rows with a NULL key part still
            -- collide on rerun instead of duplicating.
            CONSTRAINT uq_{self.table_name}
                UNIQUE NULLS NOT DISTINCT ({key})
        );
        """

    # ------------------------------------------------------------ transform
    def transform_sql(self) -> str:
        s = self.silver_schema
        col_names = [name for name, _ in self.columns]
        insert_cols = ",\n            ".join(["source_type", *col_names])

        union = "\n            UNION ALL\n".join(
            self.projection_sql(feed, table).strip()
            for feed, table in self.source_tables.items()
        )

        # Everything except the natural key is refreshed on conflict.
        # NB: these are built outside the f-string — backslashes are not allowed
        # inside f-string expressions before Python 3.12, and CI pins 3.11.
        sep = ",\n            "
        updatable = [c for c in col_names if c not in self.natural_key]
        updates = sep.join(f"{c:<34} = EXCLUDED.{c}" for c in updatable)
        updates = updates + sep if updates else ""
        select_cols = sep.join(col_names)
        key_cols = ", ".join(self.natural_key)

        return f"""
        WITH consolidated AS (
            {union}
        )
        INSERT INTO {s}.{self.table_name} AS tgt (
            {insert_cols}
        )
        SELECT
            source_type,
            {select_cols}
        FROM consolidated
        ON CONFLICT ({key_cols}) DO UPDATE SET
            {updates}silver_loaded_ts                   = now();
        """
