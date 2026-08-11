"""
runner.py
=========
Orchestration. Runs one or all registered transformations, each in its own
transaction, with dependency checks, timing, logging, and error isolation.

A failure in one transformation is logged and does not stop the others; the
runner reports an overall non-zero result if anything failed (run.py turns that
into a non-zero exit code, which schedulers use to flag failed jobs).

A transformation is skipped entirely — no CREATE TABLE, no INSERT/UPDATE — once
its Silver table already exists. The table is only ever populated on the run
that creates it; rerunning after that is a deliberate no-op.
"""

from __future__ import annotations

import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Dict, List

from ..config import settings
from ..db.connection import get_engine, table_exists

if TYPE_CHECKING:  # for type hints only; keeps pyarrow out of the import path
    from ..parquet_export import ExportContext
from ..logging_config import get_logger
from .base import SilverTransformation
from .registry import REGISTRY

# Importing the transformations package triggers auto-discovery (it imports
# every module in src/transformations/, each of which @register-s itself).
from .. import transformations  # noqa: F401  (side-effect import)

log = get_logger(__name__)


@dataclass
class Result:
    name: str
    status: str            # "succeeded" | "failed" | "skipped"
    rows: int = 0
    duration_s: float = 0.0
    error: str = ""


def group_of(t: SilverTransformation) -> str:
    """The folder path a transformation lives in, or "" for a top-level module.

    src.transformations.stage_4.rec_del_pairing.silver_firm_rec_del_pair
        -> "stage_4/rec_del_pairing"
    src.transformations.silver_firm_transport_rate
        -> ""
    """
    parts = type(t).__module__.split(".")
    try:
        rest = parts[parts.index("transformations") + 1:]
    except ValueError:  # pragma: no cover - transformation defined elsewhere
        return ""
    return "/".join(rest[:-1])


def _in_group(path: str, group: str) -> bool:
    """Whether a transformation's folder path is selected by `group`.

    Matching is deliberately loose so a stage, a component, or the full path all
    work as selectors, and so nesting a component under a stage later does not
    invalidate existing callers:

        "stage_4"                       -> everything in stage 4
        "rec_del_pairing"               -> just that component, wherever it sits
        "stage_4/rec_del_pairing"       -> the same, spelled out
        "master_capacity/firm/core"     -> one leaf, without naming its stage

    The last form is why this matches a *contiguous run* of segments rather than
    just a prefix: workflows address a leaf folder by its own path, and should
    not have to repeat the stage that happens to contain it today.
    """
    group = group.strip("/")
    if not group:
        return path == ""
    want = group.split("/")
    have = path.split("/")
    return any(have[i:i + len(want)] == want for i in range(len(have) - len(want) + 1))


def source_of(t: SilverTransformation) -> str:
    """Canonical JSON source feed for a transformation ("firm", "ioc", ...).

    Anything cross-feed or undeclared resolves to "_combined".
    """
    from ..parquet_export import normalize_source

    return normalize_source(t.source)


def list_transformations(group: str | None = None, source: str | None = None) -> List[str]:
    """All registered names, narrowed by phase folder and/or JSON source feed.

    The two filters are independent and compose: group picks the stage or
    component, source picks the feed, so a workflow can run exactly one feed of
    one stage.
    """
    from ..parquet_export import normalize_source

    names = sorted(REGISTRY.keys())
    if group is not None:
        names = [n for n in names if _in_group(group_of(REGISTRY[n]), group)]
    if source is not None:
        wanted = normalize_source(source)
        names = [n for n in names if source_of(REGISTRY[n]) == wanted]
    return names


def list_sources() -> List[str]:
    """Source feeds that currently have at least one transformation."""
    return sorted({source_of(t) for t in REGISTRY.values()})


def list_groups() -> List[str]:
    """Folder paths that currently contain at least one transformation."""
    return sorted({g for g in (group_of(t) for t in REGISTRY.values()) if g})


def _check_dependencies(conn, t: SilverTransformation) -> List[str]:
    """Return the list of missing source tables (empty == all present).

    Sources are looked up in `t.source_schema`, which is Bronze for a plain
    Bronze -> Silver transformation but a later stage for transformations that
    build on one (see SilverTransformation.source_schema).
    """
    missing = []
    for src in t.bronze_sources:
        if not table_exists(conn, t.source_schema, src):
            missing.append(f"{t.source_schema}.{src}")
    return missing


def _silver_table_exists(conn, t: SilverTransformation) -> bool:
    """True if this transformation's Silver table has already been created."""
    return table_exists(conn, t.silver_schema, t.table_name)


def _export_context(t: SilverTransformation, ctx: "ExportContext | None"):
    """Per-transformation export context, or None when export is off.

    Stage folder is whatever PARQUET_STAGE says (the workflows set it, so each
    one produces a single stage directory), falling back to the transformation's
    own stage folder when it isn't set.
    """
    if ctx is None:
        return None
    if settings.parquet_stage:
        return ctx
    return ctx.for_stage(group_of(t).split("/")[0])


def run_one(name: str, ctx: "ExportContext | None" = None, reload: bool = False) -> Result:
    """Run a single transformation by name, in its own transaction."""
    if name not in REGISTRY:
        raise KeyError(f"Unknown transformation {name!r}. Known: {list_transformations()}")
    t = REGISTRY[name]
    engine = get_engine()
    start = time.perf_counter()

    log.info("[%s] starting (reads: %s)", name, ", ".join(t.bronze_sources) or "n/a")
    try:
        with engine.begin() as conn:  # commits on success, rolls back on exception
            missing = _check_dependencies(conn, t)
            if missing:
                msg = f"missing sources: {', '.join(missing)}"
                log.warning("[%s] skipped — %s", name, msg)
                return Result(name, "skipped", 0, time.perf_counter() - start, msg)

            if _silver_table_exists(conn, t):
                if not reload:
                    msg = f"silver table already exists: {t.silver_schema}.{t.table_name}"
                    log.info("[%s] skipped — %s", name, msg)
                    return Result(name, "skipped", 0, time.perf_counter() - start, msg)
                # --reload: drop and rebuild so the table refreshes from source
                # and produces a Parquet export. Inside the same transaction, so
                # a failed rebuild leaves the existing table untouched.
                log.warning("[%s] reload — dropping %s.%s", name, t.silver_schema, t.table_name)
                conn.exec_driver_sql(f"DROP TABLE IF EXISTS {t.silver_schema}.{t.table_name}")

            rows = t.run(conn, _export_context(t, ctx))
        dur = time.perf_counter() - start
        log.info("[%s] succeeded — %s rows affected in %.2fs", name, rows, dur)
        return Result(name, "succeeded", rows, dur)

    except Exception as exc:  # noqa: BLE001 — isolate and report per transformation
        dur = time.perf_counter() - start
        log.exception("[%s] FAILED after %.2fs: %s", name, dur, exc)
        return Result(name, "failed", 0, dur, f"{type(exc).__name__}: {exc}")


def new_export_context() -> "ExportContext | None":
    """One context per process, so every table in a run shares a run_id.

    Returns None when PARQUET_OUTPUT_DIR is empty, which disables the export.
    """
    if not settings.parquet_output_dir:
        log.info("parquet export disabled (PARQUET_OUTPUT_DIR is empty)")
        return None
    from ..parquet_export import ExportContext

    ctx = ExportContext.create(settings.parquet_output_dir, settings.parquet_stage)
    log.info("parquet export -> %s (run_id=%s)", ctx.output_dir, ctx.run_id)
    return ctx


def run_all(ctx: "ExportContext | None" = None, reload: bool = False,
            source: str | None = None) -> List[Result]:
    """Run every registered transformation; continue past failures."""
    names = list_transformations(source=source)
    if source is not None and not names:
        log.warning(
            "No transformations for source %r - nothing to do. Known sources: %s",
            source, ", ".join(list_sources()) or "(none)",
        )
        return []
    results = [run_one(name, ctx, reload) for name in names]
    _summarize(results)
    return results


def run_group(group: str, ctx: "ExportContext | None" = None, reload: bool = False,
              source: str | None = None) -> List[Result]:
    """Run every transformation in one phase folder; continue past failures.

    An empty group is not an error — a phase folder that exists but holds no
    transformations yet (e.g. master_capacity) is a no-op, so scheduled jobs can
    reference it before the code lands without failing.
    """
    names = list_transformations(group, source)
    if not names:
        log.warning(
            "Group %r%s has no registered transformations - nothing to do. "
            "Known groups: %s | known sources: %s",
            group, f" / source {source!r}" if source else "",
            ", ".join(list_groups()) or "(none)",
            ", ".join(list_sources()) or "(none)",
        )
        return []
    log.info("Running group %r%s: %s", group,
             f" / source {source!r}" if source else "", ", ".join(names))
    results = [run_one(name, ctx, reload) for name in names]
    _summarize(results)
    return results


def _summarize(results: List[Result]) -> None:
    by_status: Dict[str, int] = {}
    for r in results:
        by_status[r.status] = by_status.get(r.status, 0) + 1
    total_rows = sum(r.rows for r in results)
    log.info(
        "SUMMARY: %s | total rows affected: %s",
        ", ".join(f"{k}={v}" for k, v in sorted(by_status.items())),
        total_rows,
    )


def any_failed(results: List[Result]) -> bool:
    return any(r.status == "failed" for r in results)
