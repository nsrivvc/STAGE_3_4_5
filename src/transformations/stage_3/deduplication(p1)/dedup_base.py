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

from typing import List, Tuple

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


#: Audit columns stamped onto every exploded element row. All but two are
#: copied from the parent contract row; the exceptions are `hash_key` (the
#: ELEMENT's own content fingerprint -- see NestedArrayDeduplication) and
#: `raw_payload` (the element's own JSON object, not the whole contract's).
ELEMENT_AUDIT_COLUMNS: List[Tuple[str, str]] = [
    ("raw_record_id", "TEXT"),
    ("hash_key", "TEXT"),
    ("pipeline_run_id", "TEXT"),
    ("source_system", "TEXT"),
    ("source_api", "TEXT"),
    ("source_file_name", "TEXT"),
    ("ingestion_timestamp", "TIMESTAMPTZ"),
    ("updated_ts", "TIMESTAMPTZ"),
    ("ingestion_status", "TEXT"),
    ("raw_payload", "JSONB"),
]

#: `index` (from the locations' "Index" key) is a SQL keyword.
_NEEDS_QUOTING = {"index"}


def _q(name: str) -> str:
    return f'"{name}"' if name in _NEEDS_QUOTING else name


class NestedArrayDeduplication(SilverTransformation):
    """Entry point for the locations / rates grains: explode-then-dedupe.

    Ingestion lands each feed as ONE raw Bronze table (gtran_firm, gtran_it)
    whose rows carry the contract header plus nested `locations` and `rates`
    JSON arrays -- there are no separate gtran_loc / gtran_rates tables. So the
    nested grains enter the pipeline here: one output row per array element,
    exploded straight out of the raw table's `raw_payload`.

    COLUMNS COME FROM THE JSON. `element_keys` lists one element's keys
    verbatim (CamelCase, as they appear in the payload); each becomes a TEXT
    column named key.lower(), which is exactly the naming decompisition(p3)
    expects. A key absent from some element yields NULL rather than failing.
    `parent_columns` carries the contract-row fields that do not exist inside
    an element but that downstream phases need (the contract id,
    posteddatetime, and for rates tspduns/tspname).

    DEDUPE RULE is the same as Deduplication, applied per element: `hash_key`
    here is md5 of the element's canonical jsonb text, so an element already
    recorded by an earlier fetch is dropped by ON CONFLICT DO NOTHING, and an
    element changed in any field hashes differently and passes through.
    (jsonb canonicalises key order, so the hash is stable across re-serialisations.)
    """

    # --- set these in each subclass ------------------------------------------
    feed: str = ""              # "firm" | "interruptible"
    source_table: str = ""      # raw Bronze feed table holding the nested JSON
    section: str = ""           # top-level raw_payload key: "locations" | "rates"
    parent_columns: List[str] = []   # contract-row columns copied onto each element
    element_keys: List[str] = []     # JSON keys of one element; column = key.lower()

    def __init__(self) -> None:
        for attr in ("feed", "source_table", "section", "parent_columns", "element_keys"):
            if not getattr(self, attr):
                raise ValueError(f"{type(self).__name__} must set `{attr}`.")
        self.source = self.feed
        self.bronze_sources = [self.source_table]
        super().__init__()

    @property
    def target_schema(self) -> str:
        """Staging, not Silver -- p2/p3/p4 and stage 4 all read from here."""
        return self.decomp_schema

    @property
    def columns(self) -> List[Tuple[str, str]]:
        """(name, type) for every target column, in insert order."""
        return (
            [("bronze_row_id", "BIGINT")]
            + [(c, "TEXT") for c in self.parent_columns]
            + [(k.lower(), "TEXT") for k in self.element_keys]
            + ELEMENT_AUDIT_COLUMNS
        )

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        cols = ",\n            ".join(f"{_q(n):<24} {t}" for n, t in self.columns)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            {cols},
            CONSTRAINT uq_{self.table_name}_hash UNIQUE (hash_key)
        );
        """

    # ------------------------------------------------------------ transform
    def transform_sql(self) -> str:
        select_parts = (
            ["s.bronze_row_id"]
            + [f"s.{c}" for c in self.parent_columns]
            + [f"el ->> '{k}'" for k in self.element_keys]
            + [
                "s.raw_record_id",
                "md5(el::text)",        # element-level content fingerprint
                "s.pipeline_run_id",
                "s.source_system",
                "s.source_api",
                "s.source_file_name",
                "s.ingestion_timestamp",
                "s.updated_ts",
                "s.ingestion_status",
                "el",                   # the element's own JSON, not the contract's
            ]
        )
        ins = ",\n            ".join(_q(n) for n, _ in self.columns)
        sel = ",\n            ".join(select_parts)
        return f"""
        INSERT INTO {self.target_schema}.{self.table_name} (
            {ins}
        )
        SELECT
            {sel}
        FROM {self.source_schema}.{self.source_table} s
        CROSS JOIN LATERAL jsonb_array_elements(s.raw_payload -> '{self.section}') AS el
        WHERE jsonb_typeof(s.raw_payload -> '{self.section}') = 'array'
        ON CONFLICT (hash_key) DO NOTHING
        """
