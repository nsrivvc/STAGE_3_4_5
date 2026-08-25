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
    """Validate top-level structure. Returns the normalised feed type.

    `feedType` is preferred when present. When it is absent the payload is
    identified by WHICH RECORD KEY IT CARRIES instead: the live NatGasHub export
    ships `{"PageNumber": 1, "Firms": [...]}` with no envelope metadata at all,
    and that is unambiguous because each feed declares its own record keys (see
    bronze/feeds/). Ambiguity -- a payload matching more than one feed -- is an
    error rather than a guess.
    """
    from . import feeds

    if not isinstance(payload, dict):
        raise PayloadValidationError("Top-level JSON must be an object.")

    declared = payload.get("feedType") or payload.get("feed_type")
    if declared:
        feed = str(declared).strip()
        if feed not in known_feeds:
            raise PayloadValidationError(
                f"Unknown feedType '{feed}'. Known feeds: {', '.join(known_feeds)}."
            )
        return feed

    matches = [f for f in feeds.FEEDS if f.matches_envelope(payload)]
    if len(matches) == 1:
        return matches[0].feed_type
    if not matches:
        raise PayloadValidationError(
            "Payload declares no 'feedType' and carries no recognised record "
            f"key. Top-level keys: {', '.join(map(str, payload)) or '(none)'}. "
            "Expected one of: "
            + "; ".join(f"{f.feed_type} -> {'/'.join(f.records_keys)}" for f in feeds.FEEDS)
        )
    raise PayloadValidationError(
        "Payload declares no 'feedType' and matches more than one feed "
        f"({', '.join(f.feed_type for f in matches)}). Add an explicit "
        "'feedType' to disambiguate."
    )


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
