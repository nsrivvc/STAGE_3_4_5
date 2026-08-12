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
gtran_firm and gtran_it, never on the locations or rates tables. Those children
flow through p1 -> p3 untouched by this phase and are resolved by
decomposition's latest-per-(contract, uniqueid) rule.

THE FOLD
--------
This collapses a contract's posting history into one current row:

  1. CLASSIFY every posting as NEW / ALL_DATA / CHANGES_ONLY.

  2. FIND THE BASELINE -- the latest NEW or ALL_DATA posting. Everything before
     it is superseded by definition: a full restatement makes earlier history
     irrelevant. Postings before the baseline are dropped.

  3. OVERLAY the CHANGES_ONLY postings that came after it. Because those carry
     only changed fields and leave the rest NULL, each column takes its latest
     NON-NULL value in PostedDateTime order. A field nobody amended keeps its
     baseline value; a field amended twice keeps the newer one.

  4. EMIT one row per contract, plus provenance: which kind the newest posting
     was, how many postings were folded, and the baseline timestamp.

A contract with only CHANGES_ONLY postings and no baseline is a real anomaly --
amendments to something never published. Those are kept rather than dropped (see
`orphan_changes_only`) so they surface instead of vanishing silently.

THE NULL-DESCRIPTOR RULE
------------------------
The existing Databricks notebook reclassifies some NULL descriptors as
"All Data": when a contract group has more than `null_group_threshold` NULLs and
this is not the first of them (`null_running_threshold`). The first NULL in a
group is deliberately spared -- it is the original record.

That is a workaround for a data quirk rather than a rule from the spec, so it is
isolated here and switchable. `AmendRptgDesc` is NOT nullable in the sample feed
(it carries "new"), so this may not fire at all on current data.

    SPEC: the two thresholds were read off a screenshot of the notebook and
    should be confirmed against it.
"""

from __future__ import annotations

from typing import List

from ....core.base import SilverTransformation


class ContractAmendments(SilverTransformation):
    # --- set these in each subclass ------------------------------------------
    feed: str = ""              # "firm" | "interruptible"
    source_table: str = ""      # deduplication(p1) output holding contract headers
    contract_id_col: str = ""   # firmid | interruptibleid
    columns: List[str] = []     # every column of the source table, in order

    #: Second key component. Matches the notebook's partitionBy(FirmId, TspDuns).
    partner_col: str = "tspduns"

    #: See "THE NULL-DESCRIPTOR RULE" above. Set `apply_null_rule = False` to
    #: treat every NULL descriptor as a plain NEW posting instead.
    apply_null_rule: bool = True
    null_group_threshold: int = 2
    null_running_threshold: int = 1

    #: Keep contracts that only ever received CHANGES_ONLY postings. They are
    #: amendments to something never published, so they are surfaced rather than
    #: silently dropped.
    orphan_changes_only: bool = True

    def __init__(self) -> None:
        for attr in ("feed", "source_table", "contract_id_col", "columns"):
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

    # ------------------------------------------------------------------ DDL
    def create_table_sql(self) -> str:
        key = ", ".join(self.key_cols)
        return f"""
        CREATE SCHEMA IF NOT EXISTS {self.target_schema};

        -- LIKE clones the source's columns; the amendment provenance below is
        -- appended so downstream can see how a row was resolved.
        CREATE TABLE IF NOT EXISTS {self.target_schema}.{self.table_name} (
            LIKE {self.source_schema}.{self.source_table},

            amend_kind               TEXT,        -- kind of the newest posting
            amend_postings_applied   INTEGER,     -- how many postings folded in
            amend_baseline_ts        TIMESTAMPTZ, -- when the baseline was posted
            amended_ts               TIMESTAMPTZ DEFAULT now(),

            CONSTRAINT uq_{self.table_name}
                UNIQUE NULLS NOT DISTINCT ({key})
        );
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

    def _null_rule_sql(self, part: str) -> str:
        """Reclassification of NULL descriptors (see module docstring)."""
        if not self.apply_null_rule:
            return "CASE WHEN _kind = 'NULL_DESC' THEN 'NEW' ELSE _kind END"
        return f"""
            CASE
                WHEN _kind = 'NULL_DESC'
                 AND sum(CASE WHEN _kind = 'NULL_DESC' THEN 1 ELSE 0 END)
                       OVER (PARTITION BY {part}) > {self.null_group_threshold}
                 AND sum(CASE WHEN _kind = 'NULL_DESC' THEN 1 ELSE 0 END)
                       OVER (PARTITION BY {part} ORDER BY _posted_ts
                             ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW)
                       > {self.null_running_threshold}
                    THEN 'ALL_DATA'
                WHEN _kind = 'NULL_DESC' THEN 'NEW'
                ELSE _kind
            END
        """.strip()

    # ------------------------------------------------------------ transform
    def transform_sql(self) -> str:
        key_col, partner = self.contract_id_col, self.partner_col
        part = f"{key_col}, {partner}"
        sep = ",\n            "

        # Latest non-null per column. Postgres has no IGNORE NULLS on window
        # functions, so this filters the nulls out of an ordered array_agg and
        # takes the head -- which is exactly "most recent value anyone supplied".
        folded = sep.join(
            f"(array_agg({c} ORDER BY _posted_ts DESC NULLS LAST) "
            f"FILTER (WHERE {c} IS NOT NULL))[1] AS {c}"
            for c in self.folded_cols
        )
        # Must mirror the SELECT below: keys first, then the folded columns in
        # the same order they are produced.
        insert_cols = sep.join(self.key_cols + self.folded_cols)
        updatable = sep.join(
            f"{c:<26} = EXCLUDED.{c}" for c in self.folded_cols
        )

        orphan_clause = (
            "b.baseline_ts IS NULL OR " if self.orphan_changes_only else ""
        )

        return f"""
        WITH classified AS (
            SELECT s.*,
                   NULLIF(posteddatetime, '')::TIMESTAMPTZ AS _posted_ts,
                   {self._classify_sql()} AS _kind
            FROM {self.source_schema}.{self.source_table} s
        ),
        reclassified AS (
            SELECT c.*, {self._null_rule_sql(part)} AS amend_kind
            FROM classified c
        ),
        -- A full posting supersedes everything before it.
        baseline AS (
            SELECT {part}, max(_posted_ts) AS baseline_ts
            FROM reclassified
            WHERE amend_kind IN ('NEW', 'ALL_DATA')
            GROUP BY {part}
        ),
        in_scope AS (
            SELECT r.*, b.baseline_ts
            FROM reclassified r
            LEFT JOIN baseline b
                   ON b.{key_col} IS NOT DISTINCT FROM r.{key_col}
                  AND b.{partner}  IS NOT DISTINCT FROM r.{partner}
            WHERE {orphan_clause}r._posted_ts >= b.baseline_ts
        )
        INSERT INTO {self.target_schema}.{self.table_name} AS tgt (
            {insert_cols},
            amend_kind,
            amend_postings_applied,
            amend_baseline_ts
        )
        SELECT
            {key_col},
            {partner},
            {folded},
            (array_agg(amend_kind ORDER BY _posted_ts DESC NULLS LAST))[1],
            count(*)::INTEGER,
            max(baseline_ts)
        FROM in_scope
        GROUP BY {part}
        ON CONFLICT ({part}) DO UPDATE SET
            {updatable},
            amend_kind               = EXCLUDED.amend_kind,
            amend_postings_applied   = EXCLUDED.amend_postings_applied,
            amend_baseline_ts        = EXCLUDED.amend_baseline_ts,
            amended_ts               = now();
        """
