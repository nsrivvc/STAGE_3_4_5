"""
router.py
=========
Turns a payload into one RoutedRecord per Bronze row.

Each feed lands in exactly ONE Bronze raw table, one row per source record:

    gTRAN_FIRM  contracts[] -> bronze.gtran_firm
    gTRAN_IT    contracts[] -> bronze.gtran_it
    gINDEX      records[]   -> bronze.gindex
    gAWD        awards[]    -> bronze.gawd

Nested arrays inside a record (locations, rates) are kept on the row as
canonical JSON text columns — flattening/exploding them into per-location and
per-rate rows is the Silver layer's job, not Bronze's.

Header propagation
------------------
TSP-level fields (TspName, TspDuns, ...) declared once at the payload header
are merged into every record, so each Bronze row is self-describing.

Everything about a feed (table, envelope keys, required fields, header keys)
comes from its FeedDefinition in bronze/feeds/ — adding a feed changes nothing
here.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List

from . import coerce, feeds, validators


@dataclass
class RoutedRecord:
    table: str
    record: Dict[str, Any]
    raw_record_id: str
    missing_fields: List[str]


def known_feeds() -> List[str]:
    return list(feeds.feed_types())


def _merge_missing(base: Dict[str, Any], extra: Dict[str, Any], keys) -> None:
    """Fill `base[k]` from `extra[k]` for each k in keys when base lacks it."""
    lower = {k.lower() for k in base}
    for key in keys:
        if key.lower() not in lower and key in extra:
            base[key] = extra[key]


def _get_id(record: Dict[str, Any], field: str) -> str:
    lower = {k.lower(): v for k, v in record.items()}
    val = lower.get(field.lower())
    return "" if val is None else str(val)


def route(payload: Dict[str, Any], feed_type: str) -> Iterator[RoutedRecord]:
    """Yield a RoutedRecord for every Bronze row implied by the payload."""
    feed = feeds.for_feed_type(feed_type)

    header = {k: payload[k] for k in feed.header_keys if k in payload}
    # Record lists may arrive native or as embedded JSON text, and envelope
    # keys vary by producer (the fixture's "contracts" vs the live export's
    # "Firms") — the feed decides which key holds its records.
    for raw in coerce.as_record_list(feed.records_from(payload)):
        record = dict(raw)
        _merge_missing(record, header, feed.header_keys)

        # Nested arrays (locations/rates) stay on the record: they land as
        # JSON text columns and the FULL original record goes to raw_payload.
        yield RoutedRecord(
            table=feed.table,
            record=record,
            raw_record_id=_get_id(record, feed.parent_id_field),
            missing_fields=validators.validate_record(record, list(feed.parent_required)),
        )
