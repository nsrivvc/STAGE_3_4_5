#!/usr/bin/env python3
"""
run.py
======
Batch entrypoint for the Bronze -> Silver transformations.

Examples:
    python run.py --list                              # show registered transformations
    python run.py --show-sql silver_awards_core       # print SQL (no DB needed)
    python run.py --table silver_awards_core          # run one
    python run.py --group rec_del_pairing             # run one phase folder
    python run.py --list-groups                       # show phase folders
    python run.py --shippers --source firm            # show the shipper scope for one feed
    python run.py --all                               # run everything

Exit code is non-zero if any transformation failed (so schedulers flag the job).
"""

from __future__ import annotations

import argparse
import sys

from src.logging_config import get_logger

log = get_logger("run")


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description="Bronze -> Silver batch runner")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="List registered transformations")
    group.add_argument("--inspect", action="store_true",
                       help="Read-only snapshot: existing Bronze/Silver tables + row counts (no transforms run)")
    group.add_argument("--table", metavar="NAME", help="Run a single transformation by name")
    group.add_argument("--group", metavar="FOLDER",
                       help="Run every transformation in one phase folder (e.g. rec_del_pairing)")
    group.add_argument("--list-groups", action="store_true", help="List phase folders that contain transformations")
    group.add_argument("--shippers", action="store_true",
                       help="Show the shipper scope currently configured in "
                            "<BRONZE_SCHEMA>.shipper_mapping (narrow with --source)")
    group.add_argument("--all", action="store_true", help="Run all transformations")
    group.add_argument("--show-sql", metavar="NAME", help="Print a transformation's SQL and exit")

    parser.add_argument("--source", metavar="FEED",
                        help="Only run transformations for one JSON source feed: "
                             "firm, interruptible (or it), awards, ioc, or final "
                             "(the cross-feed tables). Narrows --all and --group.")
    parser.add_argument("--reload", action="store_true",
                        help="Drop and rebuild tables that already exist, instead of skipping them")
    args = parser.parse_args(argv)

    # Import here so --help works without importing the DB stack.
    from src.core import runner
    from src.core.registry import REGISTRY

    if args.list:
        names = runner.list_transformations(source=args.source)
        header = "Registered transformations"
        if args.source:
            header += f" for source {args.source!r}"
        print(f"{header}:")
        for name in names:
            t = REGISTRY[name]
            print(f"  - {name}  [{runner.source_of(t)}]  "
                  f"(reads: {', '.join(t.bronze_sources)})")
        if not names:
            print(f"  (none — known sources: {', '.join(runner.list_sources())})")
        return 0

    if args.show_sql:
        t = REGISTRY.get(args.show_sql)
        if not t:
            log.error("Unknown transformation: %s", args.show_sql)
            return 2
        print("-- ===== CREATE TABLE =====")
        print(t.create_table_sql())
        print("\n-- ===== TRANSFORM =====")
        print(t.transform_sql())
        return 0

    if args.inspect:
        from src.core import inspect as inspect_mod
        inspect_mod.inspect()
        return 0

    if args.shippers:
        from src.config import settings
        from src.core import shipper_scope
        from src.db.connection import get_engine

        with get_engine().connect() as conn:
            print(shipper_scope.describe(conn, settings.bronze_schema, args.source))
        return 0

    if args.list_groups:
        groups = runner.list_groups()
        print("Phase folders with registered transformations:")
        for g in groups:
            for name in runner.list_transformations(g):
                print(f"  {g}/{name}")
        loose = runner.list_transformations("")
        if loose:
            print("  (top level)")
            for name in loose:
                print(f"    {name}")
        return 0

    if args.table:
        result = runner.run_one(args.table, args.reload)
        return 1 if result.status == "failed" else 0

    if args.group:
        results = runner.run_group(args.group, args.reload, args.source)
        return 1 if runner.any_failed(results) else 0

    if args.all:
        results = runner.run_all(args.reload, args.source)
        return 1 if runner.any_failed(results) else 0

    return 0


if __name__ == "__main__":
    sys.exit(main())
