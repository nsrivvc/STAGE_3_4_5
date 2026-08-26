"""
transformers.py
===============
Turns a single source record (a plain dict pulled out of the JSON by the router)
into a fully-formed Bronze row: business columns mapped onto DB column names,
pipeline metadata attached, a content hash computed for idempotency, and the
original fragment preserved in raw_payload.

Mapping rule
------------
JSON keys are matched to DB columns case-insensitively (source "TspName" ->
column "tspname"). Any JSON key that does not correspond to a Bronze column is
ignored for the typed columns but is STILL preserved inside raw_payload, so no
source detail is lost (schema-on-read tolerance).

Idempotency hash
----------------
hash_key = SHA-256 over the canonical JSON of the record's *business* values
only (metadata excluded). Re-ingesting byte-identical data therefore produces
the same hash, which stage 3's deduplication(p1) uses to drop duplicates.
(The sheet's sample hashes are SHA-1/40-char; SHA-256 is used here for lower
collision risk. Swap hashlib.sha256 -> hashlib.sha1 to match those exactly.)
"""

from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from typing import Any, Dict

from . import coerce, schemas


def _scalarize(value: Any) -> Any:
    """Coerce a JSON value into something a TEXT column can hold.

    Structure destined for a scalar column (e.g. KStatDesc arriving as
    {"code":"A","desc":"Active"}) is kept as JSON text so Silver can still parse
    it. The text is *canonical* (sorted keys, no whitespace) whether the source
    sent a native object or an embedded JSON string, so the same logical content
    yields the same hash_key either way and re-ingestion stays idempotent.
    """
    if value is None:
        return None
    if isinstance(value, str):
        parsed = coerce.parse_embedded_json(value)
        # Only rewrite when the string really was structure; plain text, numeric
        # strings and malformed JSON pass through verbatim.
        return coerce.dumps(parsed) if isinstance(parsed, (dict, list)) else value
    if isinstance(value, (dict, list)):
        return coerce.dumps(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def compute_hash(business_values: Dict[str, Any]) -> str:
    """Deterministic content hash over business values (order-independent)."""
    canonical = json.dumps(business_values, sort_keys=True, default=str)
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def build_row(
    *,
    table: str,
    record: Dict[str, Any],
    raw_record_id: str,
    run_context: "RunContext",
    ingestion_status: str = "LOADED",
) -> Dict[str, Any]:
    """Build a dict keyed by DB column name, ready for the writer."""
    valid_cols = schemas.source_key_map(table)  # lower-source -> db col

    business: Dict[str, Any] = {}
    for key, value in record.items():
        db_col = valid_cols.get(key.lower())
        if db_col is not None:
            business[db_col] = _scalarize(value)

    now = datetime.now(timezone.utc)
    row: Dict[str, Any] = dict(business)
    row.update(
        {
            "raw_record_id": str(raw_record_id) if raw_record_id is not None else None,
            "hash_key": compute_hash(business),
            "pipeline_run_id": run_context.pipeline_run_id,
            "source_system": run_context.source_system,
            "source_api": run_context.source_api,
            "source_file_name": run_context.source_file_name,
            "ingestion_timestamp": now,
            "updated_ts": now,
            "ingestion_status": ingestion_status,
            "raw_payload": record,  # original fragment; writer adapts to JSONB
        }
    )
    return row
