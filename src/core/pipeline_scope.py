"""
pipeline_scope.py
=================
Pipeline (TSP) onboarding gate for the Bronze -> staging boundary.

WHAT THIS IS FOR
----------------
`pipeline_attributes` is the register of pipelines this warehouse knows how to
treat: one row per TSP, keyed by DUNS, carrying the name it reports under and
how it reports amendments. A contract whose TSP is NOT in that register cannot
be processed correctly -- there is no declared treatment for it -- so its rows
must not silently flow into staging as if they were understood.

This module turns the register into a SQL predicate that keeps unregistered
TSPs OUT, and a report that says which ones were turned away.

PER-TSP, NOT PER-RUN
--------------------
A load usually mixes registered and unregistered pipelines. Rejecting the whole
load would throw away good contracts because of an unrelated one, so the gate
is a FILTER, not an assert: registered TSPs process exactly as before, and only
the unregistered ones are held back. `report_uncovered()` then logs what was
held back, at ERROR, so a rejection is loud rather than a quietly short load.

This is deliberately different from `amend_base.assert_pipeline_attributes()`,
which raises: that one is about the register being self-inconsistent (a mode
spelled in a way the join cannot read), which is a configuration fault that
makes the whole phase untrustworthy. An unregistered TSP is ordinary
day-to-day data, and only that TSP's rows are affected.

WHERE THE PREDICATE IS APPLIED
------------------------------
Deduplication (deduplication(p1)) -- the same single choke point shipper_scope
uses, and for the same reason: it is the only phase that reads Bronze, so
filtering there covers every downstream grain with no per-transformation code,
inside the transaction that does the insert.

THE RULE
--------
    register empty              ->  everything passes (nothing is configured
                                    yet, so this file changes nothing until the
                                    dashboard writes rows)
    TSP has a matching row      ->  passes
    TSP has no matching row     ->  held back, and reported

"Matching" is DUNS plus name by default (PipelineAttributes.match_name): a DUNS
that reports under a name the register does not list is as unrecognized as a
DUNS that is absent, because the pair is what identifies the pipeline.

MATCHING IS PER-FEED, NOT PER-COLUMN
------------------------------------
Bronze tables spell the TSP differently, so the columns come from PIPELINE_KEYS.
A Bronze table absent from that map is NOT filtered (and says so in the log) --
a feed with no TSP concept must not silently lose every row. Awards (gawd) and
IOC (gindex) carry no TSP name/DUNS pair and are therefore never gated here.
"""

from __future__ import annotations

from typing import Dict, List, Optional, Tuple

from ..logging_config import get_logger
from .table_config import PipelineAttributes as PA

log = get_logger(__name__)

TABLE = PA.table

#: Bronze table -> (DUNS column, name column). Only feeds that actually carry a
#: TSP identity are gated; anything absent here passes through untouched.
PIPELINE_KEYS: Dict[str, Tuple[str, str]] = {
    "gtran_firm": ("tspduns", "tspname"),
    "gtran_it": ("tspduns", "tspname"),
}


def ddl(schema: str) -> str:
    """Idempotent DDL for the register.

    Emitted from dedup's create_table_sql so the predicate below can never
    reference a missing table. Deliberately identical to the CREATE in
    amend_base.create_table_sql -- whichever phase runs first provisions it and
    the other's CREATE IF NOT EXISTS is a no-op.
    """
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.{TABLE} (
            {PA.duns_col}         TEXT PRIMARY KEY,
            {PA.name_col}         TEXT,
            {PA.mode_col}         TEXT NOT NULL,
            {PA.noted_col}        TIMESTAMPTZ DEFAULT now()
        );
    """


def _match_clause(attr_alias: str, row_alias: str, duns_col: str, name_col: str) -> str:
    """How a Bronze row is matched to a register row."""
    match = (f"btrim({attr_alias}.{PA.duns_col}) = btrim({row_alias}.{duns_col})")
    if PA.match_name:
        # The pair identifies the pipeline: a known DUNS reporting under an
        # unlisted name is not the pipeline we onboarded.
        match += (f"\n                  AND lower(btrim(coalesce({attr_alias}.{PA.name_col}, ''))) "
                  f"= lower(btrim(coalesce({row_alias}.{name_col}, '')))")
    return match


def predicate(attr_schema: str, source_table: str, alias: str = "s") -> str:
    """SQL boolean keeping `alias` (a row of `source_table`) to registered TSPs.

    Returns "" when the gate is off or the Bronze table declares no TSP columns,
    meaning "do not filter" -- callers must treat an empty string as no
    predicate rather than as false.

    Everything is decided in SQL against the register's CURRENT contents, so a
    pipeline added on the dashboard takes effect on the next run with no cached
    state to invalidate.
    """
    if not PA.require_known_pipeline:
        return ""

    keys = PIPELINE_KEYS.get(source_table)
    if not keys:
        log.info(
            "pipeline gate: %s has no entry in PIPELINE_KEYS - its rows are NOT "
            "gated on pipeline_attributes (this feed carries no TSP identity).",
            source_table,
        )
        return ""

    duns_col, name_col = keys
    tbl = f"{attr_schema}.{TABLE}"

    return f"""(
            -- Register empty => nothing is configured yet, everything passes.
            NOT EXISTS (SELECT 1 FROM {tbl})
            OR EXISTS (
                SELECT 1 FROM {tbl} pa
                WHERE {_match_clause('pa', alias, duns_col, name_col)}
            )
        )"""


def where(attr_schema: str, source_table: str, alias: str = "s") -> str:
    """`predicate` as a complete `WHERE ...` clause, or "" when the gate is off."""
    p = predicate(attr_schema, source_table, alias)
    return f"WHERE {p}" if p else ""


def and_where(attr_schema: str, source_table: str, alias: str = "s") -> str:
    """`predicate` as `AND ...`, for a query that already has a WHERE."""
    p = predicate(attr_schema, source_table, alias)
    return f"AND {p}" if p else ""


# --------------------------------------------------------------------- report
def uncovered(conn, attr_schema: str, src_schema: str, source_table: str
              ) -> List[Tuple[str, str, int]]:
    """The (DUNS, name, row count) triples this gate would hold back.

    Returns [] when the gate is off, the feed is not gated, or the register is
    empty -- in each of those cases nothing is being turned away.
    """
    from ..db.connection import table_exists

    if not PA.require_known_pipeline:
        return []
    keys = PIPELINE_KEYS.get(source_table)
    if not keys:
        return []
    # The register is provisioned by create_table_sql, which on a first run has
    # not executed yet when this is called. No table is the same situation as
    # an empty one: nothing is registered, so the predicate lets everything
    # through and there is nothing to report.
    if not table_exists(conn, attr_schema, TABLE):
        return []

    duns_col, name_col = keys
    tbl = f"{attr_schema}.{TABLE}"
    src = f"{src_schema}.{source_table}"

    return [
        (r[0], r[1], r[2])
        for r in conn.exec_driver_sql(f"""
            SELECT btrim(coalesce(s.{duns_col}, '')) AS duns,
                   btrim(coalesce(s.{name_col}, '')) AS name,
                   count(*) AS rows
            FROM {src} s
            WHERE EXISTS (SELECT 1 FROM {tbl})
              AND NOT EXISTS (
                  SELECT 1 FROM {tbl} pa
                  WHERE {_match_clause('pa', 's', duns_col, name_col)}
              )
            GROUP BY 1, 2
            ORDER BY rows DESC, duns
        """).all()
    ]


def report_uncovered(conn, attr_schema: str, src_schema: str, source_table: str,
                     feed: Optional[str] = None) -> List[Tuple[str, str, int]]:
    """Log every TSP the gate is holding back, and return them.

    Logged at ERROR because a held-back contract is a real problem someone has
    to fix (register the pipeline, or correct the name it reports under) -- it
    just is not a reason to throw away the contracts that ARE registered, which
    is why this reports instead of raising.
    """
    rejected = uncovered(conn, attr_schema, src_schema, source_table)
    if not rejected:
        return []

    label = f" [{feed}]" if feed else ""
    total = sum(n for _, _, n in rejected)
    log.error(
        "pipeline gate%s: REJECTED %s row(s) from %s unregistered TSP(s) - "
        "not in %s.%s, so their contracts were NOT loaded into staging: %s. "
        "Add each pipeline (DUNS + the exact name it reports under) to the "
        "register, or set PipelineAttributes.require_known_pipeline = False "
        "to let them through.",
        label, total, len(rejected), attr_schema, TABLE,
        "; ".join(f"{duns or '(no duns)'} {name or '(no name)'} "
                  f"({n} row{'s' if n != 1 else ''})" for duns, name, n in rejected),
    )
    # Machine-readable companion, one line per TSP, for log readers (the
    # dashboard surfaces these on the run card).
    for duns, name, n in rejected:
        log.error("pipeline_rejected duns=%s name=%s rows=%s feed=%s",
                  duns or "", name or "", n, feed or "")
    return rejected
