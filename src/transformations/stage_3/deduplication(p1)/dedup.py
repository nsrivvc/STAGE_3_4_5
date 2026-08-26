"""
dedup.py -- phase 1 of stage 3: drop the rows we have already seen.
==================================================================
Ingestion writes a fresh raw batch into Bronze on every fetch, and most of those
rows are identical to what the previous fetch already delivered. This phase
copies Bronze into staging and lets through only what is new or changed:

    firm           bronze.gtran_firm -> silver_staging.firm_dedup
    interruptible  bronze.gtran_it   -> silver_staging.interruptible_dedup
    awards         bronze.gawd       -> silver_staging.awards_dedup

Whole rows in, whole rows out. This phase does not know the core / locations /
rates grains exist and it does not unpack the nested `locations` / `rates` JSON
arrays -- those ride along inside the row, and decompisition(p3) splits them.

THE DUPLICATE CHECK IS ONE LINE: `ON CONFLICT (hash_key) DO NOTHING`, in
transform_sql below. `hash_key` is a SHA-256 of the row's content that stage 2
stamps on every Bronze row (see stage_2/json_to_raw.py), so two rows carry the
same one precisely when their content matches. The target table declares
UNIQUE (hash_key), so Postgres does the comparison as an index lookup: hash
already present -> the row is not copied; hash absent -> the row is inserted.

Nothing is deleted anywhere. Bronze keeps every row forever; a duplicate is
simply never copied into staging. The rows a run lets through are exactly the
rows it inserts, which is what the run reports as "rows affected".

Output goes to DECOMP_SCHEMA (default `silver_staging`), which is what
ammendments(p2), decompisition(p3) and stage 4 read.
"""

from __future__ import annotations

from ....core.base import SilverTransformation
from ....core.registry import register


class Deduplication(SilverTransformation):
    """One Bronze feed table -> one deduplicated staging table.

    A feed is the four declarations below it: what the transformation is called,
    the table it writes, the feed it belongs to, and the Bronze table it reads.
    """

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
        """Staging, not Silver -- p2/p3 and stage 4 all read from here."""
        return self.decomp_schema

    def create_table_sql(self) -> str:
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        -- LIKE clones the Bronze table's columns, so this needs no knowledge of
        -- them and keeps working as the source schema evolves. The UNIQUE below
        -- is what makes the duplicate check in transform_sql work.
        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            LIKE {self.source_schema}.{self.source_table},
            CONSTRAINT uq_{self.table_name}_hash UNIQUE (hash_key)
        );
        """

    def transform_sql(self) -> str:
        return f"""
        INSERT INTO {self.target_schema}.{self.table_name}
        SELECT s.* FROM {self.source_schema}.{self.source_table} s
        -- The duplicate check. Content already recorded -> not copied.
        ON CONFLICT (hash_key) DO NOTHING
        """


@register
class SilverFirmDedup(Deduplication):
    name = "silver_firm_dedup"
    table_name = "firm_dedup"
    feed = "firm"
    source_table = "gtran_firm"


@register
class SilverInterruptibleDedup(Deduplication):
    name = "silver_interruptible_dedup"
    table_name = "interruptible_dedup"
    feed = "interruptible"
    source_table = "gtran_it"


# Awards carry no amendment marker, so ammendments(p2) has nothing to do for
# this feed and decompisition(p3) reads awards_dedup directly.
@register
class SilverAwardsDedup(Deduplication):
    name = "silver_awards_dedup"
    table_name = "awards_dedup"
    feed = "awards"
    source_table = "gawd"
