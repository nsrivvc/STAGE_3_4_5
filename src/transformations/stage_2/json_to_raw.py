"""
json_to_raw.py — Stage 2: a JSON file -> its raw table.
=======================================================
Take the JSON, shape each record to the raw table, write it. That is the whole
job: no API calls, no Parquet, no Silver logic, no deduplication (stage 3).

    python src/transformations/stage_2/json_to_raw.py --file data/firms.json
    python src/transformations/stage_2/json_to_raw.py --file <path> --feed ioc --dry-run

One module per feed sits next to this one and declares the little the database
cannot tell us -- the envelope its records arrive in, which key is the record
id, and any field spelled differently from its column:

    firm.py  gTRAN_FIRM -> gtran_firm     awards.py  gAWD   -> gawd
    interruptible.py  gTRAN_IT -> gtran_it     ioc.py  gINDEX -> gindex

THE TABLE OWNS THE SCHEMA. Columns come from information_schema at run time,
not from a list in here, so this cannot drift from the database: a column added
there is filled on the next run, and a JSON key with nowhere to land is
reported rather than dropped -- it is kept whole in raw_payload.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import uuid
from datetime import datetime, timezone
from typing import Any, Dict, Iterator, List, Optional, Tuple

try:  # convenience for local runs; CI passes DATABASE_URL as an env var
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass

import awards
import firm
import interruptible
import ioc

SCHEMA = "bronze"
BATCH_SIZE = int(os.getenv("BATCH_SIZE", "500"))

#: --feed name -> feed module.
FEEDS = {
    "firm": firm,
    "interruptible": interruptible,
    "awards": awards,
    "ioc": ioc,
}

#: Columns stage 2 fills itself. Everything else on the table comes from JSON.
METADATA_COLUMNS: Tuple[str, ...] = (
    "raw_record_id", "hash_key", "pipeline_run_id", "source_system",
    "source_api", "source_file_name", "ingestion_timestamp", "updated_ts",
    "ingestion_status", "raw_payload",
)


class PayloadError(Exception):
    """The file cannot be routed to a raw table (aborts the run)."""


# --- 1. WHICH FEED IS THIS? --------------------------------------------------

def by_name(name: str):
    """Look a feed up by --feed value, canonical name, or a common synonym."""
    key = name.strip().lower()
    key = {"index": "ioc", "gindex": "ioc", "it": "interruptible"}.get(key, key)
    if key in FEEDS:
        return FEEDS[key]
    for feed in FEEDS.values():
        if feed.NAME.lower() == key:
            return feed
    raise PayloadError(f"Unknown feed {name!r}. Known: {', '.join(FEEDS)}.")


def records_of(payload: Dict[str, Any], feed) -> Any:
    """The record list under whichever envelope key this payload used."""
    lower = {str(k).lower(): v for k, v in payload.items()}
    for key in feed.RECORD_KEYS:
        if key.lower() in lower:
            return lower[key.lower()]
    return None


def pick_feed(payload: Dict[str, Any], override: Optional[str] = None):
    """--feed wins, then a declared "feedType", then the envelope key.
    Ambiguity is an error, never a guess: "contracts" is used by both the firm
    and interruptible exports, so a file carrying it has to say which it is."""
    if override:
        return by_name(override)

    declared = payload.get("feedType") or payload.get("feed_type")
    if declared:
        return by_name(str(declared))

    matches = [f for f in FEEDS.values() if records_of(payload, f) is not None]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise PayloadError(
            "No 'feedType' and no recognised record key. Top-level keys: "
            f"{', '.join(map(str, payload)) or '(none)'}. Expected one of: "
            + "; ".join(f"{f.NAME} -> {'/'.join(f.RECORD_KEYS)}" for f in FEEDS.values())
        )
    raise PayloadError(
        f"Payload matches {', '.join(f.NAME for f in matches)}. "
        "Pass --feed to say which one it is."
    )


# --- 2. RECORDS --------------------------------------------------------------

def load_payload(file_path: str) -> Dict[str, Any]:
    with open(file_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)
    if not isinstance(payload, dict):
        raise PayloadError("Top-level JSON must be an object.")
    return payload


def parse_embedded_json(value: Any) -> Any:
    """Parse a string holding a JSON object/array; pass anything else through.
    The source sends the same field as a native array on one record and as a
    JSON-encoded string on the next. Only {} / [] delimited strings are
    parsed, so a plain "0.4500" lands verbatim and is never re-typed."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if len(text) < 2 or text[0] not in "{[" or text[-1] not in "}]":
        return value
    try:
        return json.loads(text)
    except ValueError:
        return value  # looks like JSON, isn't — land the source text as-is


def iter_records(payload: Dict[str, Any], feed) -> Iterator[Dict[str, Any]]:
    """One dict per raw row, with any payload-level header fields copied down
    so every row is self-describing. Nested arrays stay on the record: they
    land as JSON text and stage 3 fans them out."""
    records = parse_embedded_json(records_of(payload, feed))
    if isinstance(records, dict):
        records = [records]
    if not isinstance(records, list):
        raise PayloadError(
            f"{feed.NAME}: expected a list under {'/'.join(feed.RECORD_KEYS)}, "
            f"got {type(records).__name__}."
        )

    header = {k: payload[k] for k in feed.HEADER_KEYS if k in payload}
    for raw in records:
        record = parse_embedded_json(raw)
        if not isinstance(record, dict):
            continue  # an unusable entry is skipped, not crashed on
        present = {k.lower() for k in record}
        yield {**{k: v for k, v in header.items() if k.lower() not in present}, **record}


# --- 3. COLUMNS — read from the table, never declared here -------------------

def table_columns(conn, table: str) -> List[Tuple[str, str]]:
    """(name, type) per column of bronze.<table>, in table order, minus the
    ones the database fills itself (bronze_row_id and any other serial key)."""
    with conn.cursor() as cur:
        cur.execute(
            """SELECT column_name, data_type
                 FROM information_schema.columns
                WHERE table_schema = %s AND table_name = %s
                  AND is_identity = 'NO'
                  AND COALESCE(column_default, '') NOT LIKE 'nextval%%'
                ORDER BY ordinal_position""",
            (SCHEMA, table),
        )
        columns = [(name, dtype) for name, dtype in cur.fetchall()]
    if not columns:
        raise PayloadError(
            f"Table {SCHEMA}.{table} does not exist. Stage 2 writes into the raw "
            "tables; it does not create them."
        )
    return columns


def key_to_column(feed, columns: List[Tuple[str, str]]) -> Dict[str, str]:
    """json key (lowercased) -> column. Keys match their column directly; the
    re-spelled ones come in through the feed's ALIASES."""
    business = {name for name, _ in columns if name not in METADATA_COLUMNS}
    mapping = {name: name for name in business}
    mapping.update({k.lower(): v for k, v in feed.ALIASES.items() if v in business})
    return mapping


# --- 4. ROWS -----------------------------------------------------------------

def to_text(value: Any) -> Any:
    """Fit a JSON value into a text column: structure — native, or arriving as
    an embedded JSON string — becomes compact sorted-key JSON, so the same
    content always renders the same text; plain scalars land verbatim."""
    if value is None:
        return None
    if isinstance(value, str):
        parsed = parse_embedded_json(value)
        return _canonical(parsed) if isinstance(parsed, (dict, list)) else value
    if isinstance(value, (dict, list)):
        return _canonical(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def _canonical(value: Any) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def missing_required(record: Dict[str, Any], feed) -> List[str]:
    """Required keys that are absent or blank. A record missing some still
    lands, flagged INVALID — stage 2 drops nothing on the floor."""
    lower = {k.lower(): v for k, v in record.items()}
    return [
        key for key in feed.REQUIRED
        if (v := lower.get(key.lower())) is None or (isinstance(v, str) and not v.strip())
    ]


def to_row(record: Dict[str, Any], feed, key_map: Dict[str, str],
           meta: Dict[str, Any], status: str) -> Dict[str, Any]:
    """One record -> one row shaped like the table."""
    row = {
        column: to_text(value)
        for key, value in record.items()
        if (column := key_map.get(key.lower())) is not None
    }

    # Fingerprint of the business values. Stage 3's deduplication compares rows
    # on it (see stage_3/deduplication(p1)/dedup_base.py), and the raw tables
    # carry UNIQUE (hash_key), so bronze has to stamp it.
    hash_key = hashlib.sha256(
        json.dumps(row, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    raw_id = {k.lower(): v for k, v in record.items()}.get(feed.ID_FIELD.lower())
    row.update(
        meta,
        raw_record_id=None if raw_id is None else str(raw_id),
        hash_key=hash_key,
        ingestion_status=status,
        raw_payload=record,
    )
    return row


# --- 5. WRITE ----------------------------------------------------------------

def connect():
    # .strip() because the repo's DATABASE_URL secret carries a trailing
    # newline, which the driver rejects.
    dsn = (os.getenv("DATABASE_URL") or "").strip()
    if not dsn:
        raise RuntimeError("DATABASE_URL is not set.")
    import psycopg2  # imported here so --help needs no driver

    return psycopg2.connect(dsn)


def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def write_rows(conn, table: str, columns: List[Tuple[str, str]],
               rows: List[Dict[str, Any]]) -> int:
    """Insert the rows and return how many landed. ON CONFLICT DO NOTHING
    because the raw tables carry UNIQUE (hash_key): re-running a file skips
    records already there instead of raising."""
    if not rows:
        return 0
    from psycopg2.extras import Json, execute_values

    def value(row, name, data_type):
        v = row.get(name)
        return Json(v) if v is not None and data_type in ("json", "jsonb") else v

    stmt = (
        f"INSERT INTO {_q(SCHEMA)}.{_q(table)} "
        f"({', '.join(_q(name) for name, _ in columns)}) VALUES %s "
        f"ON CONFLICT (hash_key) DO NOTHING RETURNING 1"
    )
    params = [tuple(value(row, name, dtype) for name, dtype in columns) for row in rows]

    # execute_values sends the batch as a few multi-row INSERTs instead of one
    # statement per row — the difference between minutes and seconds against a
    # remote database. RETURNING 1 comes back only for rows actually inserted.
    with conn.cursor() as cur:
        landed = execute_values(cur, stmt, params, page_size=BATCH_SIZE, fetch=True)
    conn.commit()
    return len(landed)


def write_log(conn, meta: Dict[str, Any], started: datetime, read: int,
              written: int, invalid: int, status: str, error: str = "") -> None:
    """One bronze.ingestion_log row per run — the same log stage 1-2 writes."""
    ended = datetime.now(timezone.utc)
    row = {
        "pipeline_name": os.getenv("PIPELINE_NAME", "pipeline_accelerator_bronze"),
        "pipeline_layer": "bronze",
        "pipeline_run_id": meta["pipeline_run_id"],
        "activity_name": "Stage2_json_to_raw",
        "activity_run_id": str(uuid.uuid4()),
        "source_system": meta["source_system"],
        "source_api": meta["source_api"],
        "source_file_name": meta["source_file_name"],
        "triggered_by": os.getenv("TRIGGERED_BY", os.getenv("USER", "manual")),
        "pipeline_start_ts": started,
        "pipeline_end_ts": ended,
        "activity_duration_secs": (ended - started).total_seconds(),
        "objects_read": read,
        "rows_written": written,
        "rows_rejected": invalid,
        "pipeline_status": status,
        "data_validation_status": "Pass" if invalid == 0 else "Warn",
        "error_details": error,
    }
    stmt = (
        f"INSERT INTO {_q(SCHEMA)}.\"ingestion_log\" "
        f"({', '.join(_q(c) for c in row)}) "
        f"VALUES ({', '.join(['%s'] * len(row))})"
    )
    with conn.cursor() as cur:
        cur.execute(stmt, list(row.values()))
    conn.commit()


# --- 6. THE RUN + CLI --------------------------------------------------------

def run(file_path: str, feed_override: Optional[str] = None,
        dry_run: bool = False) -> int:
    started = datetime.now(timezone.utc)
    payload = load_payload(file_path)
    feed = pick_feed(payload, feed_override)

    # Stamped onto every row, so any landed row traces back to this run + file.
    meta = {
        "pipeline_run_id": str(uuid.uuid4()),
        "source_system": payload.get("sourceSystem", os.getenv("SOURCE_SYSTEM", "NatGasHub")),
        "source_api": payload.get("sourceApi") or f"natgashub/{feed.NAME}",
        "source_file_name": os.path.basename(file_path),
        "ingestion_timestamp": started,
        "updated_ts": started,
    }
    print(f"Feed         : {feed.NAME}")
    print(f"Target table : {SCHEMA}.{feed.TABLE}")
    print(f"Source file  : {meta['source_file_name']}")
    print(f"Run id       : {meta['pipeline_run_id']}")

    conn = connect()
    try:
        columns = table_columns(conn, feed.TABLE)
        key_map = key_to_column(feed, columns)
        print(f"Columns      : {len(columns)} read from {SCHEMA}.{feed.TABLE}")

        rows: List[Dict[str, Any]] = []
        invalid = 0
        unmapped: set = set()
        for record in iter_records(payload, feed):
            unmapped.update(k for k in record if k.lower() not in key_map)
            missing = missing_required(record, feed)
            if missing:
                invalid += 1
                print(f"  ! record missing required field(s): {', '.join(missing)}")
            rows.append(to_row(record, feed, key_map, meta,
                               "INVALID" if missing else "LOADED"))

        # Not a failure: the key is still kept whole in raw_payload. It means
        # the source grew a field the table has no column for.
        if unmapped:
            print(f"  note: no column for {', '.join(sorted(unmapped))} "
                  "- kept in raw_payload only")

        if dry_run:
            print(f"\n[dry-run] {len(rows)} row(s) ready for {SCHEMA}.{feed.TABLE}; "
                  "nothing written.")
            return 0

        try:
            written = write_rows(conn, feed.TABLE, columns, rows)
            write_log(conn, meta, started, len(rows), written, invalid, "Succeeded")
        except Exception as exc:  # noqa: BLE001 — any failure must reach the log
            conn.rollback()
            details = f"{type(exc).__name__}: {exc}"
            print(f"ERROR: write failed: {details}", file=sys.stderr)
            try:
                write_log(conn, meta, started, len(rows), 0, invalid, "Failed", details)
            except Exception:
                pass
            return 1

        summary = f"\nDone. records={len(rows)} written={written} invalid={invalid}"
        if len(rows) - written:
            summary += f" (already in the table: {len(rows) - written})"
        print(summary)
        return 0
    finally:
        conn.close()


def main(argv: Optional[List[str]] = None) -> int:
    parser = argparse.ArgumentParser(
        description="Stage 2: write a JSON file into its raw table."
    )
    parser.add_argument("--file", required=True, help="Path to the JSON file")
    parser.add_argument("--feed", default=None,
                        help=f"Force the target feed ({', '.join(FEEDS)}). Only "
                             "needed when the file cannot be identified on its own.")
    parser.add_argument("--dry-run", action="store_true",
                        help="Convert and report without writing (still reads the "
                             "table's columns, so DATABASE_URL is required)")
    args = parser.parse_args(argv)

    try:
        return run(args.file, args.feed, args.dry_run)
    except FileNotFoundError:
        print(f"ERROR: input file not found: {args.file}", file=sys.stderr)
        return 2
    except (PayloadError, RuntimeError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
