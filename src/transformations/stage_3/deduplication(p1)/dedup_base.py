"""
dedup_base.py
=============
Shared base for the deduplication phase (p1 of stage 3). Not a transformation
itself -- it registers nothing.

WHAT IT DOES
------------
Every time a JSON is fetched, ingestion writes a fresh raw batch into Bronze.
Most of those rows are byte-identical to what the previous fetch already
delivered. This phase compares the new batch against everything seen so far and
lets only genuinely new or changed rows through:

    row identical to one already seen  ->  dropped, never reaches p2/p3/p4
    row new, or changed in any field   ->  passes through

HOW "IDENTICAL" IS DECIDED
--------------------------
Bronze stamps every row with `hash_key`, a fingerprint of the row's content. It
is unique per row within each Bronze table (verified: 4,470 rows / 4,470 distinct
hashes in gtran_loc), so two rows share a hash_key precisely when their content
matches. That makes the whole comparison a single `ON CONFLICT (hash_key) DO
NOTHING` -- a row whose content was already recorded is silently skipped, and a
row that differs in any field produces a different hash and is inserted.

The output table therefore accumulates one row per distinct content ever seen,
across every fetch. The rows a run actually lets through are exactly the rows it
inserts, which is what `RETURNING *` gives the Parquet export -- so each run's
Parquet file holds the delta, not the whole table.

WHY `LIKE`
----------
The target is created with `CREATE TABLE ... (LIKE <bronze table>)`, cloning the
source's columns without naming them. That keeps this base completely generic:
it works for any Bronze table, present or future, with no column list to
maintain, and `INSERT ... SELECT *` stays valid because the clone has exactly
the source's columns in the source's order.

WHERE THE OUTPUT GOES
---------------------
DECOMP_SCHEMA (default `silver_staging`), the staging schema the rest of stage 3
and stage 4 read from. `target_schema` is overridden accordingly, so the runner's
load-once check and `--inspect` look in the right place.
"""

from __future__ import annotations

from ....core.base import SilverTransformation


class Deduplication(SilverTransformation):
    # --- set these in each subclass ------------------------------------------
    feed: str = ""             # "firm" | "interruptible" | "awards"
    source_table: str = ""     # the Bronze table this deduplicates

    def __init__(self) -> None:
        for attr in ("feed", "source_table"):
            if not getattr(self, attr):
                raise ValueError(f"{type(self).__name__} must set `{attr}`.")
        self.source = self.feed
        self.bronze_sources = [self.source_table]
        super().__init__()

    @property
    def target_schema(self) -> str:
        """Staging, not Silver -- p2/p3/p4 and stage 4 all read from here."""
        return self.decomp_schema

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        -- LIKE clones the Bronze table's columns, so this base needs no
        -- knowledge of them and keeps working as the source schema evolves.
        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            LIKE {self.source_schema}.{self.source_table},
            CONSTRAINT uq_{self.table_name}_hash UNIQUE (hash_key)
        );
        """

    # ------------------------------------------------------------ transform
    def transform_sql(self) -> str:
        return f"""
        -- DO NOTHING is the whole deduplication rule: a row whose content hash
        -- was already recorded is skipped; anything new or changed hashes
        -- differently and is inserted. Rows inserted here are exactly the rows
        -- that proceed to p2 onwards.
        INSERT INTO {self.target_schema}.{self.table_name}
        SELECT * FROM {self.source_schema}.{self.source_table}
        ON CONFLICT (hash_key) DO NOTHING
        """
