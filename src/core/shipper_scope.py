"""
shipper_scope.py
================
Shipper (DUNS) scoping for the Bronze -> staging boundary.

WHAT THIS IS FOR
----------------
The dashboard lets a workflow attach shippers, each entered as a
KHolderName + KHolderNumber pair with an Add or a Remove action:

    Add    <number>  ->  the feed is filtered DOWN to that DUNS
    Remove <number>  ->  that DUNS is dropped from the feed

This module turns those rows into a SQL predicate. It holds no database
connection and returns plain strings, so `run.py --show-sql` keeps working
without a driver installed, exactly like the rest of core/.

WHERE THE PREDICATE IS APPLIED
------------------------------
Deduplication (stage 3, deduplication(p1)) is the ONLY class in the pipeline
that reads a Bronze table -- p2, p3, stage 4 and stage 5 all read the staging
schema it writes. So filtering there is what makes the scope hold for every feed
and every grain (core / locations / rates) with no per-transformation code, and
it is why the scope cannot be a separate job: the filter has to run inside the
same transaction as the dedup INSERT, or out-of-scope rows land in staging
before anything else can react.

THE RULE
--------
For a given feed:

    no `add` rows           ->  everything passes (the pipeline is unscoped,
                                which is the behaviour before anyone configures
                                a shipper -- so this file changes nothing until
                                the dashboard writes a row)
    one or more `add` rows  ->  ONLY those DUNS pass
    any `remove` row        ->  that DUNS never passes, even if also added

A row whose `source` is NULL applies to every feed; otherwise it applies to the
feed it names. That is what lets one workflow select any number of sources: each
feed's dedup evaluates its own slice of the same table, so selecting one feed or
four needs no extra plumbing and no new CLI flag.

MATCHING IS PER-FEED, NOT PER-COLUMN
------------------------------------
Each Bronze table spells the shipper differently, so the column comes from
SHIPPER_KEYS rather than being hardcoded to `kholder`. A Bronze table absent
from that map is NOT filtered (and says so in the log) -- a feed that has no
shipper concept should not silently lose every row.
"""

from __future__ import annotations

from typing import Dict, Optional, Tuple

from ..logging_config import get_logger

log = get_logger(__name__)

#: Table the dashboard writes shipper rows into. Lives in the Bronze schema
#: because it scopes Bronze, and because it is configuration for the raw feed
#: rather than a curated Silver output.
TABLE = "shipper_mapping"

#: Bronze table -> (DUNS column, name column). The dashboard always calls these
#: "KHolderNumber" and "KHolderName"; the feeds do not.
#:
#:   gtran_firm / gtran_it   kholder      / kholdername    (transactional reporting)
#:   gawd                    bidderduns   / biddername     (capacity awards)
#:   gindex                  shipperduns  / shipper        (contract index)
#:
#: Add a row here when a new Bronze feed arrives; nothing else needs changing.
SHIPPER_KEYS: Dict[str, Tuple[str, str]] = {
    "gtran_firm": ("kholder", "kholdername"),
    "gtran_it": ("kholder", "kholdername"),
    "gawd": ("bidderduns", "biddername"),
    "gindex": ("shipperduns", "shipper"),
}

ADD = "add"
REMOVE = "remove"


def ddl(schema: str) -> str:
    """Idempotent DDL for the mapping table.

    Emitted as part of every dedup transformation's create_table_sql, so the
    table provisions itself on whatever database the pipeline is pointed at and
    the predicate below can never reference something that does not exist.
    """
    return f"""
        CREATE TABLE IF NOT EXISTS {schema}.{TABLE} (
            id            BIGSERIAL PRIMARY KEY,
            -- Which dashboard workflow attached the shipper. Carried for
            -- display and audit only: scoping is by feed (see `source`), so
            -- the pipeline never needs to know which workflow it runs for.
            workflow_id   INTEGER,
            -- Feed this row scopes: 'firm' | 'interruptible' | 'awards' |
            -- 'ioc' | 'index'. NULL means every feed.
            source        TEXT,
            kholdernumber TEXT NOT NULL,
            kholdername   TEXT,
            action        TEXT NOT NULL DEFAULT '{ADD}'
                          CHECK (action IN ('{ADD}', '{REMOVE}')),
            created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
            -- One verdict per shipper per workflow per feed: re-adding an
            -- existing pair updates it rather than stacking duplicates.
            -- NULLS NOT DISTINCT so the "all feeds" / "no workflow" rows
            -- (source or workflow_id NULL) are deduplicated too.
            CONSTRAINT uq_{TABLE}_scope
                UNIQUE NULLS NOT DISTINCT (workflow_id, source, kholdernumber)
        );

        -- The predicate probes by action + source + number on every dedup run.
        CREATE INDEX IF NOT EXISTS ix_{TABLE}_lookup
            ON {schema}.{TABLE} (action, source, kholdernumber);
    """


def _feed_spellings(feed: str) -> Tuple[str, ...]:
    """Every spelling of `feed` the dashboard might write, deduplicated.

    Reuses the alias table the Parquet export already maintains, so a row
    written as 'firms' or 'gtran_firm' scopes the firm feed rather than silently
    matching nothing. Imported inside the function to keep the export module
    (and its lazy pyarrow) off the import path of `--show-sql`.
    """
    from ..parquet_export import _SOURCE_ALIASES, normalize_source

    canonical = normalize_source(feed)
    return tuple(sorted({k for k, v in _SOURCE_ALIASES.items() if v == canonical}
                        | {canonical}))


def _scope_clause(alias: str, feed: str) -> str:
    """`WHERE`-fragment matching the mapping rows that apply to this feed."""
    spellings = ", ".join(f"'{s}'" for s in _feed_spellings(feed))
    return f"({alias}.source IS NULL OR lower(btrim({alias}.source)) IN ({spellings}))"


def predicate(schema: str, source_table: str, feed: str, alias: str = "s") -> str:
    """SQL boolean scoping `alias` (a row of `source_table`) to the feed's shippers.

    Returns "" when the Bronze table declares no shipper column, meaning "do not
    filter" -- callers must treat an empty string as no predicate rather than as
    false.

    Everything is decided in SQL against the mapping table's CURRENT contents,
    so a shipper added or removed in the dashboard takes effect on the next run
    with no cached state to invalidate.
    """
    keys = SHIPPER_KEYS.get(source_table)
    if not keys:
        log.warning(
            "shipper scope: %s.%s has no entry in SHIPPER_KEYS - its rows are NOT "
            "filtered by shipper. Add one to enable scoping for this feed.",
            schema, source_table,
        )
        return ""

    duns_col = keys[0]
    tbl = f"{schema}.{TABLE}"
    row = f"btrim({alias}.{duns_col})"
    scope = _scope_clause("m", feed)

    return f"""(
            -- No shipper attached to this feed => unscoped, everything passes.
            NOT EXISTS (
                SELECT 1 FROM {tbl} m
                WHERE m.action = '{ADD}' AND {scope}
            )
            OR EXISTS (
                SELECT 1 FROM {tbl} m
                WHERE m.action = '{ADD}' AND {scope}
                  AND btrim(m.kholdernumber) = {row}
            )
        )
        AND NOT EXISTS (
            -- An explicit Remove always wins, even over an Add for the same DUNS.
            SELECT 1 FROM {tbl} m
            WHERE m.action = '{REMOVE}' AND {scope}
              AND btrim(m.kholdernumber) = {row}
        )"""


def where(schema: str, source_table: str, feed: str, alias: str = "s") -> str:
    """`predicate` as a complete `WHERE ...` clause, or "" when unscoped."""
    p = predicate(schema, source_table, feed, alias)
    return f"WHERE {p}" if p else ""


def and_where(schema: str, source_table: str, feed: str, alias: str = "s") -> str:
    """`predicate` as `AND ...`, for a query that already has a WHERE."""
    p = predicate(schema, source_table, feed, alias)
    return f"AND {p}" if p else ""


# --------------------------------------------------------------------- report
def describe(conn, schema: str, feed: Optional[str] = None) -> str:
    """Human-readable summary of the configured scope. Used by `run.py --shippers`.

    Takes a live Connection rather than opening one, matching how every other
    module in core/ works.
    """
    from sqlalchemy import text

    from ..db.connection import table_exists

    if not table_exists(conn, schema, TABLE):
        return (f"No {schema}.{TABLE} table yet - the pipeline is unscoped "
                f"(every shipper passes). It is created by the first stage-3 run.")

    rows = conn.execute(
        text(
            f"SELECT workflow_id, source, kholdernumber, kholdername, action "
            f"FROM {schema}.{TABLE} ORDER BY source NULLS FIRST, action, kholdername"
        )
    ).mappings().all()

    if feed:
        allowed = set(_feed_spellings(feed))
        rows = [r for r in rows
                if r["source"] is None or str(r["source"]).strip().lower() in allowed]

    scope_label = f" for feed {feed!r}" if feed else ""
    if not rows:
        return (f"{schema}.{TABLE} has no rows{scope_label} - unscoped "
                f"(every shipper passes).")

    lines = [f"{schema}.{TABLE}{scope_label} - {len(rows)} row(s):"]
    for r in rows:
        src = r["source"] or "(all feeds)"
        wf = f"  wf={r['workflow_id']}" if r["workflow_id"] is not None else ""
        lines.append(f"  {r['action'].upper():<6} {src:<14} {r['kholdernumber']:<12} "
                     f"{r['kholdername'] or ''}{wf}")

    adds = [r for r in rows if r["action"] == ADD]
    lines.append("")
    lines.append(
        f"  => allow-list of {len(adds)}: only these DUNS are processed."
        if adds else
        "  => no allow-list: every shipper is processed except the REMOVEs above."
    )
    return "\n".join(lines)
