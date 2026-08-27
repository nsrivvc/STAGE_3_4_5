"""
amend_base.py
=============
Shared base for the ammendments phase (p2 of stage 3). Not a transformation
itself -- it registers nothing.

WHAT IS BEING AMENDED
---------------------
A transport **contract**, identified by (contract id, TspDuns). The pipeline
re-posts the same contract over time, each posting stamped with PostedDateTime.
`AmendRptg` / `AmendRptgDesc` say what each posting is:

    AmendRptg  AmendRptgDesc     meaning
    ---------  ----------------  --------------------------------------------
    N          "new"             first publication of this contract
    A          "all data"        full restatement -- this posting IS the contract
    A          "changes only"    partial -- carries ONLY the fields that changed

Note this is a header-level concept: `amendrptg`/`amendrptgdesc` exist only on
gtran_firm and gtran_it, never inside the locations or rates elements. The
exploded grains flow through p1 -> p3 untouched by this phase.

THE RUN, START TO FINISH
------------------------
This phase is INCREMENTAL: it consumes only the postings still marked 'fresh'
(the marker stage 2 stamps on every landed row) and folds them into a
VERSIONED contract table -- one 'Current' row per (contract id, TspDuns), with
superseded versions kept as 'Void'. The steps, in order:

  1. FRESH        pick the source rows whose freshness marker is 'fresh'.
                  (Bootstrap: an empty/just-created target processes ALL rows,
                  so a manual drop rebuilds current state from full history.)

  2. CLASSIFY     NEW / ALL_DATA / CHANGES_ONLY from AmendRptgDesc. A NULL or
                  blank descriptor is a NEW posting -- one instance of a
                  contract with a NULL (or "new") descriptor is simply
                  appended -- EXCEPT the null-group rule: when a contract
                  group holds more than `null_group_threshold` NULL
                  descriptors, those postings are re-labelled 'All Data'
                  (the AmendRptgDesc field itself is rewritten) and only the
                  latest of them survives, as any full restatement would.
                  A descriptor that matches nothing goes to the exception
                  table and out of the run.

  3. ALL DATA     one full-restatement candidate per contract: the LATEST
                  NEW / ALL_DATA posting by PostedDateTime. Everything older
                  is superseded by definition.

  4. CHANGES ONLY per contract with CHANGES_ONLY postings: take the target's
                  existing Current row for that contract, overlay the incoming
                  changes (each column takes its latest non-NULL value; the
                  previous Current row is the fallback for everything the
                  changes left NULL), producing one merged candidate.
                  If `locations` or `rates` are STILL NULL after the merge,
                  the candidate goes to the exception table and out of the
                  run -- a partial posting with no baseline to fill it in.

  5. COMBINE      the notebook's GS_ID comparison. gtran_firm/gtran_it carry
                  no GS_ID column; the contract identity here is
                  (contract id, TspDuns), and the posting's own record id is
                  `id`. So: a contract that has an ALL DATA candidate uses the
                  ALL DATA version; a contract that appears only in the
                  CHANGES ONLY set keeps its merged version. Two different
                  contracts claiming the same record id collapse to the
                  latest posting (the duplicate-GS_ID check), and a merged
                  candidate whose data fields are identical to the row it
                  would replace is dropped -- no duplicate version is written.

  6. VERSION      the target's Current rows for the surviving contracts flip
                  to version_status='Void' (voided_ts stamped), and each
                  candidate lands as the new 'Current' row -- one solid
                  unstandardized table, history retained.

  7. PROCESSED    every fresh source row consumed by this run flips
                  'fresh' -> 'processed' with updated_ts = now(), in the
                  deduplicated staging table AND in the Bronze raw table
                  (matched by contract, so rows this run never saw stay
                  fresh for the next one).

Because the target accumulates versions and the source markers flip, this
transformation sets `incremental = True`: the runner never drops the table on
--reload and never load-once skips it. To rebuild from scratch, drop the table
manually -- the bootstrap in step 1 replays the full history on the next run.
"""

from __future__ import annotations

from typing import List

from ....core.base import PipelineTransformation

#: The pipeline's own bookkeeping columns, set aside when two rows are compared
#: for content. Duplicated from deduplication(p1)/dedup.py's LOAD_STAMPS
#: because that folder name cannot appear in an import statement.
BOOKKEEPING = (
    "bronze_row_id", "raw_record_id", "hash_key", "pipeline_run_id",
    "source_system", "source_api", "source_file_name", "ingestion_timestamp",
    "updated_ts", "ingestion_status", "status", "record_status", "raw_payload",
)

#: Posting-level identity: these differ on every re-posting even when nothing
#: substantive changed, so the "no duplicate version" comparison (step 5)
#: sets them aside too -- a posting that changes only its own stamps does not
#: earn a new version.
POSTING_STAMPS = (
    "id", "posteddatetime", "cycle", "amendrptg", "amendrptgdesc",
    "createddatetime",
)

#: Extra columns each side of that comparison carries beyond the shared data
#: fields (subtracting a key a row does not have is a no-op).
_TARGET_EXTRAS = (
    "amend_kind", "amend_postings_applied", "amend_baseline_ts",
    "amended_ts", "version_status", "voided_ts",
)
_CANDIDATE_EXTRAS = ("amend_kind", "_postings", "_baseline_ts")


class ContractAmendments(PipelineTransformation):
    # --- set these in each subclass ------------------------------------------
    feed: str = ""              # "firm" | "interruptible"
    source_table: str = ""      # deduplication(p1) output holding contract headers
    raw_table: str = ""         # the Bronze raw table whose 'fresh' markers flip
    contract_id_col: str = ""   # firmid | interruptibleid
    columns: List[str] = []     # every column of the source table, in order

    #: Second key component. Matches the notebook's partitionBy(FirmId, TspDuns).
    partner_col: str = "tspduns"

    #: The freshness marker stage 2 stamps ('fresh' -> 'processed' here).
    status_col: str = "status"

    #: The null-group rule (step 2): a contract group with MORE than this many
    #: NULL descriptors has them re-labelled 'All Data'. Set `apply_null_rule =
    #: False` to treat every NULL descriptor as a plain NEW posting instead.
    apply_null_rule: bool = True
    null_group_threshold: int = 2

    #: Columns that must be non-NULL on a merged CHANGES_ONLY candidate; a
    #: candidate still NULL in any of them goes to the exception table.
    exception_null_cols = ("locations", "rates")

    #: The target is version history -- see the module docstring and runner.
    incremental = True

    def __init__(self) -> None:
        for attr in ("feed", "source_table", "raw_table", "contract_id_col",
                     "columns", "status_col"):
            if not getattr(self, attr):
                raise ValueError(f"{type(self).__name__} must set `{attr}`.")
        self.source = self.feed
        self.bronze_sources = [self.source_table]
        super().__init__()

    @property
    def source_schema(self) -> str:
        """Reads deduplication(p1) output, which lives in DECOMP_SCHEMA."""
        return self.decomp_schema

    @property
    def target_schema(self) -> str:
        """Writes to DECOMP_SCHEMA, where decompisition(p3) picks it up."""
        return self.decomp_schema

    @property
    def key_cols(self) -> List[str]:
        return [self.contract_id_col, self.partner_col]

    @property
    def folded_cols(self) -> List[str]:
        """Columns resolved by latest-non-null. The keys are excluded -- they are
        what we group by, so they cannot vary within a group."""
        return [c for c in self.columns if c not in self.key_cols]

    @property
    def exceptions_table(self) -> str:
        return f"{self.table_name}_exceptions"

    # ----------------------------------------------------------- SQL helpers
    def _key_match(self, a: str, b: str) -> str:
        """NULL-safe join on the contract key between two row aliases."""
        return " AND ".join(
            f"{a}.{c} IS NOT DISTINCT FROM {b}.{c}" for c in self.key_cols
        )

    def _tmp(self, name: str) -> str:
        return f"_amend_{self.feed}_{name}"

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        tgt = f"{self.target_schema}.{self.table_name}"
        exc = f"{self.target_schema}.{self.exceptions_table}"
        key = ", ".join(self.key_cols)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        -- LIKE clones the source's columns; provenance + versioning appended.
        CREATE TABLE IF NOT EXISTS {tgt} (
            LIKE {self.source_schema}.{self.source_table},

            amend_kind               TEXT,        -- kind of the posting that won
            amend_postings_applied   INTEGER,     -- how many postings folded in
            amend_baseline_ts        TIMESTAMPTZ, -- when the baseline was posted
            amended_ts               TIMESTAMPTZ DEFAULT now(),
            version_status           TEXT NOT NULL DEFAULT 'Current',
            voided_ts                TIMESTAMPTZ
        );

        -- Migrations from the pre-versioning shape (no-ops on a fresh table):
        -- the one-row-per-contract constraint becomes one CURRENT row per
        -- contract, and the source's freshness marker (cloned by LIKE) is
        -- dropped -- the target speaks version_status, not fresh/processed.
        ALTER TABLE {tgt} DROP CONSTRAINT IF EXISTS uq_{self.table_name};
        ALTER TABLE {tgt} ADD COLUMN IF NOT EXISTS version_status TEXT NOT NULL DEFAULT 'Current';
        ALTER TABLE {tgt} ADD COLUMN IF NOT EXISTS voided_ts TIMESTAMPTZ;
        ALTER TABLE {tgt} DROP COLUMN IF EXISTS {self.status_col};

        CREATE UNIQUE INDEX IF NOT EXISTS uq_{self.table_name}_current
            ON {tgt} ({key}) NULLS NOT DISTINCT
            WHERE version_status = 'Current';

        -- Postings this phase could not resolve: unrecognized descriptors, and
        -- merged CHANGES_ONLY candidates whose locations/rates stayed NULL.
        CREATE TABLE IF NOT EXISTS {exc} (
            LIKE {self.source_schema}.{self.source_table},
            amend_kind               TEXT,
            exception_reason         TEXT,
            noted_ts                 TIMESTAMPTZ DEFAULT now()
        );
        ALTER TABLE {exc} DROP COLUMN IF EXISTS {self.status_col};
        """

    # ------------------------------------------------------------ classify
    def _classify_sql(self) -> str:
        """CASE mapping AmendRptgDesc onto NEW / ALL_DATA / CHANGES_ONLY.

        Matched on the description rather than the AmendRptg code because the
        code only distinguishes new from amended; the description carries the
        scope, which is what decides the merge.
        """
        return """
            CASE
                WHEN lower(trim(amendrptgdesc)) IN ('all data', 'alldata', 'all')
                    THEN 'ALL_DATA'
                WHEN lower(trim(amendrptgdesc)) IN ('changes only', 'changesonly', 'changes')
                    THEN 'CHANGES_ONLY'
                WHEN lower(trim(amendrptgdesc)) = 'new'
                    THEN 'NEW'
                WHEN amendrptgdesc IS NULL OR trim(amendrptgdesc) = ''
                    THEN 'NULL_DESC'
                ELSE 'UNKNOWN'
            END
        """.strip()

    def _null_rule_sql(self) -> str:
        """Step 2's null-group rule, applied over the counted subquery."""
        if not self.apply_null_rule:
            return "CASE WHEN f._kind = 'NULL_DESC' THEN 'NEW' ELSE f._kind END"
        return f"""
            CASE
                WHEN f._kind = 'NULL_DESC' AND f._null_count > {self.null_group_threshold}
                    THEN 'ALL_DATA'
                WHEN f._kind = 'NULL_DESC' THEN 'NEW'
                ELSE f._kind
            END
        """.strip()

    def _classified_columns_sql(self) -> str:
        """The source columns, with AmendRptgDesc itself rewritten to
        'All Data' on the postings the null-group rule re-labels -- the
        notebook overwrites the field, so downstream sees the label it acted
        on, not the NULL it replaced."""
        parts = []
        for c in self.columns:
            if c == "amendrptgdesc" and self.apply_null_rule:
                parts.append(
                    f"CASE WHEN f._kind = 'NULL_DESC' "
                    f"AND f._null_count > {self.null_group_threshold} "
                    f"THEN 'All Data' ELSE f.amendrptgdesc END AS amendrptgdesc"
                )
            else:
                parts.append(f"f.{c}")
        return ",\n               ".join(parts)

    # ------------------------------------------------------------ transform
    def _stage_statements(self) -> List[str]:
        """Everything up to (not including) the final INSERT of new versions."""
        key_col, partner = self.contract_id_col, self.partner_col
        part = f"{key_col}, {partner}"
        sep = ",\n            "
        cols = sep.join(self.columns)
        src = f"{self.source_schema}.{self.source_table}"
        tgt = f"{self.target_schema}.{self.table_name}"
        exc = f"{self.target_schema}.{self.exceptions_table}"
        fresh, classified = self._tmp("fresh"), self._tmp("classified")
        full, changes = self._tmp("full"), self._tmp("changes")
        combined = self._tmp("combined")

        # Latest non-null per column, incoming changes ranked above the
        # previous Current row (_is_base), newest posting first. Postgres has
        # no IGNORE NULLS on window functions, so this filters the nulls out
        # of an ordered array_agg and takes the head.
        folded = sep.join(
            f"(array_agg(u.{c} ORDER BY u._is_base, u._posted_ts DESC NULLS LAST, "
            f"u.bronze_row_id DESC NULLS LAST) "
            f"FILTER (WHERE u.{c} IS NOT NULL))[1] AS {c}"
            for c in self.folded_cols
        )

        null_locrates = " OR ".join(
            f"({c} IS NULL OR trim({c}) = '')" for c in self.exception_null_cols
        )

        t_excl = ", ".join(
            f"'{c}'" for c in BOOKKEEPING + POSTING_STAMPS + _TARGET_EXTRAS)
        a_excl = ", ".join(
            f"'{c}'" for c in BOOKKEEPING + POSTING_STAMPS + _CANDIDATE_EXTRAS)

        posted = "NULLIF(posteddatetime, '')::TIMESTAMPTZ"

        return [
            # 1. FRESH -- the rows this run consumes. An empty target means
            # bootstrap (first run, or a manual drop): replay everything.
            f"""
        CREATE TEMP TABLE {fresh} ON COMMIT DROP AS
        SELECT s.*,
               NULLIF(s.posteddatetime, '')::TIMESTAMPTZ AS _posted_ts,
               {self._classify_sql()} AS _kind
        FROM {src} s
        WHERE lower(coalesce(s.{self.status_col}, '')) = 'fresh'
           OR NOT EXISTS (SELECT 1 FROM {tgt})""",

            # 2. CLASSIFY -- apply the null-group rule per contract.
            f"""
        CREATE TEMP TABLE {classified} ON COMMIT DROP AS
        SELECT {self._classified_columns_sql()},
               f._posted_ts,
               {self._null_rule_sql()} AS amend_kind
        FROM (
            SELECT f.*,
                   count(*) FILTER (WHERE f._kind = 'NULL_DESC')
                       OVER (PARTITION BY {part}) AS _null_count
            FROM {fresh} f
        ) f""",

            # 2b. A descriptor this phase does not recognize cannot be folded:
            # exception table, out of the run (its source row still flips to
            # processed below -- it was consumed, just not resolved).
            f"""
        INSERT INTO {exc} (
            {cols},
            amend_kind, exception_reason
        )
        SELECT
            {cols},
            amend_kind,
            'unrecognized amendrptgdesc: ' || coalesce(amendrptgdesc, '(null)')
        FROM {classified}
        WHERE amend_kind = 'UNKNOWN'""",

            # 3. ALL DATA -- one full-restatement candidate per contract: the
            # latest NEW / ALL_DATA posting. A single NULL or "new" instance
            # lands here too, appended as-is.
            f"""
        CREATE TEMP TABLE {full} ON COMMIT DROP AS
        SELECT DISTINCT ON ({part})
            {cols},
            amend_kind,
            count(*) OVER (PARTITION BY {part})::INTEGER AS _postings,
            _posted_ts AS _baseline_ts
        FROM {classified}
        WHERE amend_kind IN ('NEW', 'ALL_DATA')
        ORDER BY {part}, _posted_ts DESC NULLS LAST, bronze_row_id DESC""",

            # 4. CHANGES ONLY -- overlay the incoming changes on the target's
            # existing Current row (the "previous values"): per column, latest
            # non-null wins, the previous Current row is the fallback.
            f"""
        CREATE TEMP TABLE {changes} ON COMMIT DROP AS
        SELECT {key_col},
            {partner},
            {folded},
            count(*) FILTER (WHERE NOT u._is_base)::INTEGER AS _postings,
            max(u._posted_ts) FILTER (WHERE u._is_base) AS _baseline_ts
        FROM (
            SELECT {cols},
                _posted_ts, FALSE AS _is_base
            FROM {classified}
            WHERE amend_kind = 'CHANGES_ONLY'
            UNION ALL
            SELECT {cols},
                {posted}, TRUE
            FROM {tgt} t
            WHERE t.version_status = 'Current'
              AND EXISTS (SELECT 1 FROM {classified} c
                          WHERE c.amend_kind = 'CHANGES_ONLY'
                            AND {self._key_match('c', 't')})
        ) u
        GROUP BY {part}""",

            # 4b. Locations or rates still NULL after the merge? Exception
            # table, out of the main processing.
            f"""
        INSERT INTO {exc} (
            {cols},
            amend_kind, exception_reason
        )
        SELECT
            {cols},
            'CHANGES_ONLY',
            'locations/rates still NULL after merging changes with previous current row'
        FROM {changes}
        WHERE {null_locrates}""",

            f"""
        DELETE FROM {changes}
        WHERE {null_locrates}""",

            # 5. COMBINE -- the GS_ID comparison: a contract with an ALL DATA
            # candidate uses the ALL DATA version; one that exists only in the
            # CHANGES ONLY set keeps its merged version.
            f"""
        CREATE TEMP TABLE {combined} ON COMMIT DROP AS
        SELECT {cols},
            amend_kind, _postings, _baseline_ts
        FROM {full}
        UNION ALL
        SELECT {cols},
            'CHANGES_ONLY', _postings, _baseline_ts
        FROM {changes} c
        WHERE NOT EXISTS (SELECT 1 FROM {full} f WHERE {self._key_match('f', 'c')})""",

            # 5b. Duplicate record ids across DIFFERENT contracts (a data
            # anomaly): keep the latest posting, drop the rest.
            f"""
        DELETE FROM {combined} a
        USING {combined} b
        WHERE a.id IS NOT NULL AND b.id = a.id
          AND NOT ({self._key_match('a', 'b')})
          AND (NULLIF(b.posteddatetime, '')::TIMESTAMPTZ
                   > NULLIF(a.posteddatetime, '')::TIMESTAMPTZ
               OR (NULLIF(b.posteddatetime, '')::TIMESTAMPTZ
                       IS NOT DISTINCT FROM NULLIF(a.posteddatetime, '')::TIMESTAMPTZ
                   AND b.bronze_row_id > a.bronze_row_id))""",

            # 5c. No duplicate versions: a candidate whose DATA fields are
            # identical to the Current row it would replace changes nothing --
            # drop it, keep the existing version. (Bookkeeping and the
            # posting's own stamps are set aside, same idea as p1's dedupe.)
            f"""
        DELETE FROM {combined} a
        USING {tgt} t
        WHERE t.version_status = 'Current'
          AND {self._key_match('t', 'a')}
          AND (to_jsonb(t) - ARRAY[{t_excl}]::text[])
                = (to_jsonb(a) - ARRAY[{a_excl}]::text[])""",

            # 6a. VOID -- the Current rows being replaced.
            f"""
        UPDATE {tgt} t
        SET version_status = 'Void',
            voided_ts      = now()
        WHERE t.version_status = 'Current'
          AND EXISTS (SELECT 1 FROM {combined} c WHERE {self._key_match('c', 't')})""",
        ]

    def _insert_sql(self) -> str:
        """6b. The new Current versions -- the run's one row-producing insert
        (kept separate so run() can RETURNING it into the Parquet export)."""
        sep = ",\n            "
        cols = sep.join(self.columns)
        return f"""
        INSERT INTO {self.target_schema}.{self.table_name} (
            {cols},
            amend_kind,
            amend_postings_applied,
            amend_baseline_ts,
            version_status
        )
        SELECT
            {cols},
            amend_kind,
            _postings,
            _baseline_ts,
            'Current'
        FROM {self._tmp('combined')}
        """

    def _finalize_statements(self) -> List[str]:
        """7. Flip every consumed source row 'fresh' -> 'processed', stamping
        updated_ts -- in the staging table this phase reads AND in the Bronze
        raw table, matched by contract so rows this run never saw stay fresh."""
        status = self.status_col
        fresh = self._tmp("fresh")
        return [
            f"""
        UPDATE {self.source_schema}.{self.source_table} s
        SET {status}   = 'processed',
            updated_ts = now()
        WHERE lower(coalesce(s.{status}, '')) = 'fresh'
          AND EXISTS (SELECT 1 FROM {fresh} f WHERE f.bronze_row_id = s.bronze_row_id)""",

            f"""
        UPDATE {self.bronze_schema}.{self.raw_table} b
        SET {status}   = 'processed',
            updated_ts = now()
        WHERE lower(coalesce(b.{status}, '')) = 'fresh'
          AND EXISTS (SELECT 1 FROM {fresh} f WHERE {self._key_match('f', 'b')})""",
        ]

    def transform_sql(self) -> str:
        """The whole flow as one printable script (--show-sql). run() below
        executes the same statements individually."""
        statements = (
            self._stage_statements() + [self._insert_sql()]
            + self._finalize_statements()
        )
        return ";\n".join(s.rstrip().rstrip(";") for s in statements) + ";"

    # ------------------------------------------------------------------ run
    def run(self, conn, ctx=None) -> int:
        """Multi-statement override of the base single-statement load. Same
        contract: DDL first, then the transform, RETURNING the rows written
        into the Parquet export when one is configured. All inside the
        runner's transaction, so a failure rolls back versions, exceptions
        and status flips together."""
        conn.exec_driver_sql(self.create_table_sql())
        for stmt in self._stage_statements():
            conn.exec_driver_sql(stmt)

        insert = self._insert_sql().rstrip().rstrip(";")
        if ctx is None:
            result = conn.exec_driver_sql(insert)
            written = result.rowcount if result.rowcount is not None else -1
        else:
            from .... import parquet_export

            rows = [dict(r) for r in
                    conn.exec_driver_sql(f"{insert}\nRETURNING *").mappings().all()]
            path = parquet_export.export_for_stage(
                self.table_name, rows, ctx=ctx, source=self.source)
            if path:
                from ....logging_config import get_logger
                get_logger(__name__).info("[%s] parquet: %s", self.name, path)
            written = len(rows)

        for stmt in self._finalize_statements():
            conn.exec_driver_sql(stmt)
        return written
