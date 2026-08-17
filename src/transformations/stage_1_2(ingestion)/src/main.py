"""
main.py
=======
Entry point for the NatGasHub JSON -> Bronze ingestion.

Pipeline:
  1. Load the JSON file.
  2. Validate the payload structure and resolve the feed type.
  3. Route records to their Bronze tables (multi-table fan-out).
  4. Transform each record into a Bronze row (+ metadata + content hash).
  5. Write rows idempotently to the configured database.
  6. Record one ingestion_log row for traceability.

Usage:
  python -m src.main --file data/sample_natgashub_contract.json
  python -m src.main --file data/sample_natgashub_contract.json --create-tables
  python -m src.main --file data/sample_natgashub_contract.json --dry-run
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import traceback
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List

from . import parquet_export
from .bronze import router, schemas, transformers, validators
from .config import RunContext, Settings
from .db.connection import get_writer


def load_payload(path: str) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as fh:
        return json.load(fh)


def resolve_source_api(payload: Dict[str, Any], feed_type: str) -> str:
    return (
        payload.get("sourceApi")
        or payload.get("source_api")
        or f"natgashub/{feed_type}"
    )


def run(
    file_path: str,
    settings: Settings,
    *,
    create_tables: bool,
    dry_run: bool,
    parquet_dir: str | None = None,
) -> int:
    payload = load_payload(file_path)

    feed_type = validators.validate_payload(payload, router.known_feeds())

    ctx = RunContext(
        source_system=payload.get("sourceSystem", settings.source_system),
        source_api=resolve_source_api(payload, feed_type),
        source_file_name=os.path.basename(file_path),
        pipeline_name=settings.pipeline_name,
    )

    print(f"Feed type      : {feed_type}")
    print(f"Pipeline run id: {ctx.pipeline_run_id}")
    print(f"Source file    : {ctx.source_file_name}")

    # ---- route + transform, grouping rows per target table ----------------
    rows_by_table: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    rejected = 0
    for routed in router.route(payload, feed_type):
        status = "LOADED"
        if routed.missing_fields:
            status = "INVALID"
            rejected += 1
            print(f"  ! {validators.RecordIssue(routed.table, routed.raw_record_id, routed.missing_fields).message()}")
        row = transformers.build_row(
            table=routed.table,
            record=routed.record,
            raw_record_id=routed.raw_record_id,
            run_context=ctx,
            ingestion_status=status,
        )
        rows_by_table[routed.table].append(row)

    objects_read = sum(len(v) for v in rows_by_table.values())

    # ---- parquet export (before any database write) -----------------------
    if parquet_dir:
        for path in parquet_export.export_tables(
            rows_by_table, ctx, feed_type, parquet_dir
        ):
            print(f"  parquet: {path}")

    # ---- write ------------------------------------------------------------
    status = "Succeeded"
    error_details = ""
    rows_written = 0
    writer = get_writer(settings, dry_run=dry_run)
    try:
        if create_tables or dry_run:
            writer.ensure_schema(schemas.generate_ddl())

        for table in schemas.BUSINESS_COLUMNS:  # deterministic order
            batch = rows_by_table.get(table, [])
            for i in range(0, len(batch), settings.batch_size):
                rows_written += writer.write_rows(
                    table, batch[i : i + settings.batch_size]
                )

        end_ts = datetime.now(timezone.utc)
        writer.write_log(
            _log_row(ctx, end_ts, status, objects_read, rows_written, rejected, "")
        )
    except Exception as exc:  # noqa: BLE001 - we want to log any failure
        status = "Failed"
        error_details = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
        try:
            writer.write_log(
                _log_row(ctx, datetime.now(timezone.utc), status,
                         objects_read, rows_written, rejected, error_details)
            )
        except Exception:
            pass
        return 1
    finally:
        writer.close()

    print(
        f"\nDone. tables={len(rows_by_table)} objects_read={objects_read} "
        f"rows_written(new)={rows_written} rejected={rejected} status={status}"
    )
    return 0


def _log_row(
    ctx: RunContext,
    end_ts: datetime,
    status: str,
    objects_read: int,
    rows_written: int,
    rejected: int,
    error_details: str,
) -> Dict[str, Any]:
    duration = (end_ts - ctx.pipeline_start_ts).total_seconds()
    return {
        "pipeline_name": ctx.pipeline_name,
        "pipeline_layer": ctx.pipeline_layer,
        "pipeline_run_id": ctx.pipeline_run_id,
        "activity_name": ctx.activity_name,
        "activity_run_id": ctx.activity_run_id,
        "source_system": ctx.source_system,
        "source_api": ctx.source_api,
        "source_file_name": ctx.source_file_name,
        "triggered_by": ctx.triggered_by,
        "pipeline_start_ts": ctx.pipeline_start_ts,
        "pipeline_end_ts": end_ts,
        "activity_duration_secs": duration,
        "objects_read": objects_read,
        "rows_written": rows_written,
        "rows_rejected": rejected,
        "pipeline_status": status,
        "data_validation_status": "Pass" if rejected == 0 else "Warn",
        "error_details": error_details,
    }


def build_arg_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="NatGasHub JSON -> Bronze ingestion")
    p.add_argument("--file", required=True, help="Path to the NatGasHub JSON file")
    p.add_argument("--create-tables", action="store_true",
                   help="Run the Bronze DDL (CREATE IF NOT EXISTS) before loading")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse/validate/route/transform without touching a database")
    p.add_argument("--parquet-dir", default=None,
                   help="Directory for the pre-load Parquet export "
                        "(default: PARQUET_OUTPUT_DIR or 'parquet_output')")
    p.add_argument("--no-parquet", action="store_true",
                   help="Skip the Parquet export entirely")
    return p


def main(argv: List[str] | None = None) -> int:
    args = build_arg_parser().parse_args(argv)
    settings = Settings()
    try:
        return run(
            args.file,
            settings,
            create_tables=args.create_tables,
            dry_run=args.dry_run,
            parquet_dir=None if args.no_parquet
            else (args.parquet_dir or settings.parquet_output_dir),
        )
    except FileNotFoundError:
        print(f"ERROR: input file not found: {args.file}", file=sys.stderr)
        return 2
    except validators.PayloadValidationError as exc:
        print(f"ERROR: payload validation failed: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:  # e.g. missing DATABASE_URL
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
