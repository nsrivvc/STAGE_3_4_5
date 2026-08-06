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
from typing import Dict, List

from ..db.connection import get_engine, table_exists
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

        "stage_4"                  -> everything in stage 4
        "rec_del_pairing"          -> just that component, wherever it sits
        "stage_4/rec_del_pairing"  -> the same, spelled out
    """
    group = group.strip("/")
    if not group:
        return path == ""
    return (
        path == group
        or path.startswith(group + "/")
        or group in path.split("/")
    )


def list_transformations(group: str | None = None) -> List[str]:
    """All registered names, or just those selected by a group (see _in_group)."""
    names = sorted(REGISTRY.keys())
    if group is None:
        return names
    return [n for n in names if _in_group(group_of(REGISTRY[n]), group)]


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


def run_one(name: str) -> Result:
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
                msg = f"silver table already exists: {t.silver_schema}.{t.table_name}"
                log.info("[%s] skipped — %s", name, msg)
                return Result(name, "skipped", 0, time.perf_counter() - start, msg)

            rows = t.run(conn)
        dur = time.perf_counter() - start
        log.info("[%s] succeeded — %s rows affected in %.2fs", name, rows, dur)
        return Result(name, "succeeded", rows, dur)

    except Exception as exc:  # noqa: BLE001 — isolate and report per transformation
        dur = time.perf_counter() - start
        log.exception("[%s] FAILED after %.2fs: %s", name, dur, exc)
        return Result(name, "failed", 0, dur, f"{type(exc).__name__}: {exc}")


def run_all() -> List[Result]:
    """Run every registered transformation; continue past failures."""
    results = [run_one(name) for name in list_transformations()]
    _summarize(results)
    return results


def run_group(group: str) -> List[Result]:
    """Run every transformation in one phase folder; continue past failures.

    An empty group is not an error — a phase folder that exists but holds no
    transformations yet (e.g. master_capacity) is a no-op, so scheduled jobs can
    reference it before the code lands without failing.
    """
    names = list_transformations(group)
    if not names:
        log.warning(
            "Group %r has no registered transformations - nothing to do. Known groups: %s",
            group, ", ".join(list_groups()) or "(none)",
        )
        return []
    log.info("Running group %r: %s", group, ", ".join(names))
    results = [run_one(name) for name in names]
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
