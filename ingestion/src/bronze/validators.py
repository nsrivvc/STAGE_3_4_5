"""
validators.py
=============
Validation for NatGasHub-style payloads.

Two levels:
  * Payload-level (structural): the feed must be recognised and the records
    array must be present. A structural failure aborts the whole payload.
  * Record-level (required fields): each record routed to a Bronze table must
    contain that table's required keys. A record-level failure does NOT abort
    the run — Bronze still lands the record (so nothing is silently lost) but
    flags it with ingestion_status = "INVALID".
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


class PayloadValidationError(Exception):
    """Raised for structural problems that make a payload unprocessable."""


@dataclass
class RecordIssue:
    table: str
    raw_record_id: str
    missing_fields: List[str] = field(default_factory=list)

    def message(self) -> str:
        return (
            f"[{self.table}] record '{self.raw_record_id}' "
            f"missing required field(s): {', '.join(self.missing_fields)}"
        )


def validate_payload(payload: Dict[str, Any], known_feeds: List[str]) -> str:
    """Validate top-level structure. Returns the normalised feed type."""
    if not isinstance(payload, dict):
        raise PayloadValidationError("Top-level JSON must be an object.")

    feed = payload.get("feedType") or payload.get("feed_type")
    if not feed:
        raise PayloadValidationError("Missing required top-level field 'feedType'.")

    feed = str(feed).strip()
    if feed not in known_feeds:
        raise PayloadValidationError(
            f"Unknown feedType '{feed}'. Known feeds: {', '.join(known_feeds)}."
        )
    return feed


def validate_record(record: Dict[str, Any], required: List[str]) -> List[str]:
    """Return the list of required keys that are missing/blank for a record."""
    missing = []
    # case-insensitive presence check
    lower = {k.lower(): v for k, v in record.items()}
    for key in required:
        val = lower.get(key.lower())
        if val is None or (isinstance(val, str) and val.strip() == ""):
            missing.append(key)
    return missing
