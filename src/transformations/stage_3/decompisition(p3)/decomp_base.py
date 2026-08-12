"""
decomp_base.py
==============
Shared base for the locations decomposition. Not a transformation itself -- it
registers nothing.

WHAT IT DOES
------------
Projects a feed's Bronze locations table into a typed staging table in
DECOMP_SCHEMA, one row per location, matching the agreed schema:

    index LongType, segment, <contract_id>, uniqueid, pk, <qty>, seasnlst,
    seasnlend, uniquekey, id, posteddatetime, kentbegdatetime, kentenddatetime,
    loc, locname, locpurp, locpurpdesc, loczn, locqti, locqtidesc, tspduns,
    tspname, createddatetime

Two feeds differ only in two column names, so they are class attributes:

    firm           firmid          / kqtyloc   <- bronze.gtran_loc
    interruptible  interruptibleid / itqtyloc  <- bronze.gtran_it_loc

WHY IT WRITES OUTSIDE THE SILVER SCHEMA
---------------------------------------
Stage 4 reads `DECOMP_SCHEMA` (default `silver_staging`), not `silver`, so this
overrides `target_schema`. The runner's load-once check and `--inspect` both
follow `target_schema`, so the table is still detected in the right place.

TWO DELIBERATE DEPARTURES FROM THE PYSPARK SCHEMA
-------------------------------------------------
  * `loczn` is ArrayType(StringType) there but TEXT in Bronze, so it stays TEXT
    here. Parsing it into an array is a decision for standardization (p4), which
    is where type normalisation belongs.
  * The audit columns below the business schema (`ingestion_status`,
    `ingestion_timestamp`, `hash_key`, `source_system`, `source_api`,
    `pipeline_run_id`) are carried through deliberately. Stage 4 filters on
    `ingestion_status` and dedupes on `ingestion_timestamp`; dropping them here
    would break pairing.

DEDUPE IS NOT OPTIONAL
----------------------
bronze.gtran_loc holds 4,470 rows over 4,467 distinct (contract, uniqueid)
pairs -- re-ingested rows. Without latest-wins dedupe the upsert would touch the
same target row twice in one statement, which Postgres rejects outright.
"""

from __future__ import annotations

from typing import List, Tuple

from ....core.base import SilverTransformation

#: Business columns, in the order the agreed schema lists them. `{id}` and
#: `{qty}` are substituted per feed. Everything is TEXT in Bronze except index.
LOCATION_COLUMNS: List[Tuple[str, str]] = [
    ("index", "BIGINT"),
    ("segment", "TEXT"),
    ("{id}", "TEXT"),
    ("uniqueid", "TEXT"),
    ("pk", "TEXT"),
    ("{qty}", "TEXT"),
    ("seasnlst", "TEXT"),
    ("seasnlend", "TEXT"),
    ("uniquekey", "TEXT"),
    ("id", "TEXT"),
    ("posteddatetime", "TEXT"),
    ("kentbegdatetime", "TEXT"),
    ("kentenddatetime", "TEXT"),
    ("loc", "TEXT"),
    ("locname", "TEXT"),
    ("locpurp", "TEXT"),
    ("locpurpdesc", "TEXT"),
    ("loczn", "TEXT"),
    ("locqti", "TEXT"),
    ("locqtidesc", "TEXT"),
    ("tspduns", "TEXT"),
    ("tspname", "TEXT"),
    ("createddatetime", "TEXT"),
]

#: Carried through for stage 4 (see module docstring).
AUDIT_COLUMNS: List[Tuple[str, str]] = [
    ("source_system", "TEXT"),
    ("source_api", "TEXT"),
    ("pipeline_run_id", "TEXT"),
    ("hash_key", "TEXT"),
    ("ingestion_status", "TEXT"),
    ("ingestion_timestamp", "TIMESTAMPTZ"),
]

#: `index` is a SQL keyword; quote every identifier that needs it.
_NEEDS_QUOTING = {"index"}

#: Columns whose Bronze type differs from the target type and so need an
#: explicit cast on the way in. Everything is TEXT in Bronze; `index` is
#: LongType in the agreed schema, hence BIGINT here. Empty strings become NULL
#: rather than failing the cast.
SELECT_OVERRIDES = {
    "index": "NULLIF(\"index\", '')::BIGINT",
}


def _q(name: str) -> str:
    return f'"{name}"' if name in _NEEDS_QUOTING else name


def _select_expr(name: str) -> str:
    """How a column is read out of the source table."""
    return SELECT_OVERRIDES.get(name, _q(name))


class LocationsDecomposition(SilverTransformation):
    # --- set these in each subclass ------------------------------------------
    feed: str = ""              # "firm" | "interruptible"
    source_table: str = ""      # deduplication(p1) output table to read
    contract_id_col: str = ""   # firmid | interruptibleid
    qty_col: str = ""           # kqtyloc | itqtyloc

    def __init__(self) -> None:
        for attr in ("feed", "source_table", "contract_id_col", "qty_col"):
            if not getattr(self, attr):
                raise ValueError(f"{type(self).__name__} must set `{attr}`.")
        self.source = self.feed
        self.bronze_sources = [self.source_table]
        super().__init__()

    @property
    def target_schema(self) -> str:
        """Stage 4 reads DECOMP_SCHEMA, so the output lands there, not in Silver."""
        return self.decomp_schema

    @property
    def source_schema(self) -> str:
        """Reads deduplication(p1) output, which also lives in DECOMP_SCHEMA.

        Phase order is deduplication(p1) -> ammendments(p2) -> this. p2 has no
        code yet, so this consumes p1 directly; when p2 lands, point
        `source_table` at its output instead.
        """
        return self.decomp_schema

    @property
    def columns(self) -> List[Tuple[str, str]]:
        """The business schema with this feed's two variable column names filled in."""
        return [
            (name.format(id=self.contract_id_col, qty=self.qty_col), sql_type)
            for name, sql_type in LOCATION_COLUMNS
        ]

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        cols = ",\n            ".join(
            f"{_q(n):<24} {t}" for n, t in self.columns + AUDIT_COLUMNS)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            {cols},
            decomp_loaded_ts         TIMESTAMPTZ DEFAULT now(),

            -- One row per contract per location record. NULLS NOT DISTINCT
            -- (PG15+) so a NULL key part still collides on rerun.
            CONSTRAINT uq_{self.table_name}
                UNIQUE NULLS NOT DISTINCT ({self.contract_id_col}, uniqueid)
        );
        """

    # ------------------------------------------------------------ transform
    def transform_sql(self) -> str:
        all_cols = self.columns + AUDIT_COLUMNS
        names = [n for n, _ in all_cols]
        sel = ",\n                   ".join(_select_expr(n) for n in names)
        ins = ",\n            ".join(_q(n) for n in names)
        updatable = [n for n in names if n not in (self.contract_id_col, "uniqueid")]
        sep = ",\n            "
        updates = sep.join(f"{_q(n):<24} = EXCLUDED.{_q(n)}" for n in updatable)

        return f"""
        WITH latest AS (
            SELECT * FROM (
                SELECT s.*, row_number() OVER (
                    PARTITION BY {self.contract_id_col}, uniqueid
                    ORDER BY ingestion_timestamp DESC, bronze_row_id DESC) AS _rn
                FROM {self.source_schema}.{self.source_table} s
            ) x WHERE _rn = 1
        )
        INSERT INTO {self.target_schema}.{self.table_name} AS tgt (
            {ins}
        )
        SELECT {sel}
        FROM latest
        ON CONFLICT ({self.contract_id_col}, uniqueid) DO UPDATE SET
            {updates},
            decomp_loaded_ts         = now();
        """


class GrainDecomposition(SilverTransformation):
    """Generic decomposition for the core and rates grains.

    Locations has an agreed PySpark schema and its own typed class above. Core
    and rates have no such schema yet, so this projects the source's columns
    straight through onto a keyed staging table -- the point being to produce one
    stable, keyed table per grain that stage 4 and 5 can rely on, rather than to
    retype the fields.

    Sources differ by grain, which is what the phase order dictates:

        core       <- ammendments(p2) output, so the contract history is already
                      folded into one current row per contract
        rates      <- deduplication(p1) output, since rates carry no amendment
                      marker of their own

    SPEC: when core/rates get an agreed schema like locations has, give them a
    typed subclass of their own and retire this passthrough.
    """

    feed: str = ""
    grain: str = ""             # "core" | "rates"
    source_table: str = ""
    key_cols_list: List[str] = []
    columns: List[str] = []

    def __init__(self) -> None:
        for attr in ("feed", "grain", "source_table", "key_cols_list", "columns"):
            if not getattr(self, attr):
                raise ValueError(f"{type(self).__name__} must set `{attr}`.")
        self.source = self.feed
        self.bronze_sources = [self.source_table]
        super().__init__()

    @property
    def source_schema(self) -> str:
        return self.decomp_schema

    @property
    def target_schema(self) -> str:
        return self.decomp_schema

    def create_table_sql(self) -> str:
        key = ", ".join(self.key_cols_list)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            LIKE {self.source_schema}.{self.source_table},
            decomp_loaded_ts         TIMESTAMPTZ DEFAULT now(),
            CONSTRAINT uq_{self.table_name}
                UNIQUE NULLS NOT DISTINCT ({key})
        );
        """

    def transform_sql(self) -> str:
        key = ", ".join(self.key_cols_list)
        sep = ",\n            "
        cols = sep.join(self.columns)
        updatable = [c for c in self.columns if c not in self.key_cols_list]
        updates = sep.join(f"{c:<26} = EXCLUDED.{c}" for c in updatable)
        # Latest wins per key, so a re-run cannot hit the same target row twice.
        return f"""
        WITH latest AS (
            SELECT * FROM (
                SELECT s.*, row_number() OVER (
                    PARTITION BY {key}
                    ORDER BY ingestion_timestamp DESC, bronze_row_id DESC) AS _rn
                FROM {self.source_schema}.{self.source_table} s
            ) x WHERE _rn = 1
        )
        INSERT INTO {self.target_schema}.{self.table_name} AS tgt (
            {cols}
        )
        SELECT
            {cols}
        FROM latest
        ON CONFLICT ({key}) DO UPDATE SET
            {updates},
            decomp_loaded_ts         = now();
        """
