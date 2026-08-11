"""
base.py
=======
The shared pattern every Silver transformation follows.

To add a new Silver table, create a file in src/transformations/ that subclasses
SilverTransformation and implements three things:

    name            -> the registry key / CLI name (e.g. "silver_firm_transport_rate")
    table_name      -> the bare table name created in the Silver schema
                        (e.g. "firm_transport_rate"); used by the runner to check
                        whether the table already exists before running at all
    bronze_sources  -> Bronze tables it reads (used for a pre-run existence check)
    create_table_sql()  -> CREATE TABLE IF NOT EXISTS ...   (idempotent DDL)
    transform_sql()     -> INSERT ... SELECT ... ON CONFLICT DO UPDATE  (idempotent load)

...then decorate the class with @register. That's it — the runner discovers it.

NOTE: the runner skips a transformation entirely (no create, no insert/update) once
`silver_schema.table_name` already exists — see runner._silver_table_exists(). The
table is only ever populated on the run that creates it.

The methods return plain SQL strings, so this module deliberately does NOT import
SQLAlchemy. The runner passes a live Connection to run().
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from typing import TYPE_CHECKING, List

from ..config import settings
from ..logging_config import get_logger

if TYPE_CHECKING:  # for type hints only; keeps pyarrow out of the import path
    from ..parquet_export import ExportContext

log = get_logger(__name__)


class SilverTransformation(ABC):
    # --- override these in each subclass -------------------------------------
    name: str = ""                 # e.g. "silver_firm_transport_rate"
    table_name: str = ""           # e.g. "firm_transport_rate" (lives in silver_schema)
    bronze_sources: List[str] = []  # e.g. ["gtran_firm", "gtran_rates", "gtran_loc"]

    # Which of the four JSON source feeds these rows come from: "firm",
    # "interruptible" (aka IT), "awards" or "ioc". Used to partition the Parquet
    # export by feed. Leave empty for anything genuinely cross-feed (e.g. the
    # master capacity finals) and it files under "_combined".
    source: str = ""

    # --- schema names come from config so they're not hardcoded --------------
    def __init__(self) -> None:
        self.bronze_schema = settings.bronze_schema
        self.silver_schema = settings.silver_schema
        self.decomp_schema = settings.decomp_schema
        if not self.source:
            self.source = self._infer_source()
        if not self.name:
            raise ValueError(f"{type(self).__name__} must set a `name`.")
        if not self.table_name:
            raise ValueError(f"{type(self).__name__} must set a `table_name`.")

    def _infer_source(self) -> str:
        """Derive the JSON source feed from the folder this module lives in.

        The stage-5 layout already encodes the feed in the path
        (master_capacity/firm/core/...), so a module that doesn't declare
        `source` still gets its Parquet filed under the right feed instead of
        silently landing in `_combined`. An explicit `source` always wins.

        A `final/` segment means cross-feed and maps to `_combined`, which is
        what those tables actually are.
        """
        from ..parquet_export import COMBINED, SOURCES

        for part in type(self).__module__.split("."):
            if part in SOURCES:
                return part
            if part in ("final", "finals"):
                return COMBINED
        return ""

    @property
    def target_schema(self) -> str:
        """Schema this transformation writes `table_name` into.

        Defaults to Silver. The stage-3 decomposition overrides it to write the
        staging schema that stage 4 reads (`DECOMP_SCHEMA`). The runner's
        load-once check and `--inspect` both follow this, so a table outside
        Silver is still detected correctly.
        """
        return self.silver_schema

    @property
    def source_schema(self) -> str:
        """Schema the runner checks `bronze_sources` against.

        Defaults to Bronze, which is what a straight Bronze -> Silver
        transformation wants. Override it when a transformation reads from a
        later stage instead (e.g. the rec-del pairing classes, which read the
        decomposition phase's output).
        """
        return self.bronze_schema

    # --- implement these in each subclass ------------------------------------
    @abstractmethod
    def create_table_sql(self) -> str:
        """Idempotent DDL: CREATE SCHEMA / CREATE TABLE IF NOT EXISTS ... ."""

    @abstractmethod
    def transform_sql(self) -> str:
        """Idempotent load: INSERT ... SELECT ... ON CONFLICT (...) DO UPDATE ... ."""

    # --- default execution; override only for non-SQL (pure-Python) loads ----
    def run(self, conn, ctx: "ExportContext | None" = None) -> int:
        """Create the table if needed, then upsert. Returns rows affected.

        `conn` is a SQLAlchemy Connection supplied by the runner inside a
        transaction, so partial failures roll back automatically.

        THE PARQUET EXPORT HOOK LIVES HERE, and this is the only place any
        transformation writes rows — so every stage, present and future, is
        exported with no per-stage code.

        When `ctx` is supplied, `RETURNING *` is appended to the transform so
        the rows written come back to Python, get written to Parquet, and only
        then does the transaction commit. The rows are the DB's own output, not
        a reconstruction, and a failed write rolls back both sides.

        Note the export happens after the INSERT statement but before COMMIT:
        the rows do not exist until the INSERT produces them, so exporting
        strictly "before the database write" isn't possible without abandoning
        the set-based SQL design. Nothing is exported that wasn't durably
        written, and nothing is written without being exported.

        Overriding this method for a pure-Python load means opting out of the
        export unless the override calls parquet_export.export_rows itself.
        """
        conn.exec_driver_sql(self.create_table_sql())

        # Trailing semicolon has to go before RETURNING can be appended.
        sql = self.transform_sql().rstrip().rstrip(";")

        if ctx is None:
            result = conn.exec_driver_sql(sql)
            return result.rowcount if result.rowcount is not None else -1

        from .. import parquet_export

        rows = [dict(r) for r in conn.exec_driver_sql(f"{sql}\nRETURNING *").mappings().all()]
        path = parquet_export.export_for_stage(
            self.table_name, rows, ctx=ctx, source=self.source)
        if path:
            log.info("[%s] parquet: %s", self.name, path)
        return len(rows)
