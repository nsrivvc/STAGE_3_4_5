"""
router.py
=========
Decides which Bronze table(s) each part of a payload belongs to.

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

Adding a new feed = adding one entry to FEED_REGISTRY. No new code paths.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, Iterator, List, Optional

from . import coerce, validators


@dataclass
class ChildSpec:
    array_key: str          # key on the parent record holding the child list
    table: str              # target Bronze table
    id_field: str           # source key used as raw_record_id
    required: List[str]     # required fields for validation
    inherit: List[str]      # parent keys merged into each child if missing


@dataclass
class FeedSpec:
    feed_type: str
    records_key: str        # payload key holding the top-level record list
    parent_table: str       # target Bronze table for each top-level record
    parent_id_field: str
    parent_required: List[str]
    header_keys: List[str]  # payload-level keys merged into each record
    children: List[ChildSpec]


# Bronze is ONE raw table per feed. Nested arrays (locations/rates) are NOT
# fanned out here — they land as canonical JSON text columns on the parent row
# (plus the full original record in raw_payload). Exploding them into
# location/rate rows is the Silver layer's job.
FEED_REGISTRY: Dict[str, FeedSpec] = {
    "gTRAN_FIRM": FeedSpec(
        feed_type="gTRAN_FIRM",
        records_key="contracts",
        parent_table="gtran_firm",
        parent_id_field="Id",
        parent_required=["Id", "FirmId"],
        header_keys=["TspName", "TspDuns", "TspProp"],
        children=[],
    ),
    "gTRAN_IT": FeedSpec(
        feed_type="gTRAN_IT",
        records_key="contracts",
        parent_table="gtran_it",
        parent_id_field="Id",
        parent_required=["Id", "InterruptibleId"],
        header_keys=["TspName", "TspDuns", "TspProp"],
        children=[],
    ),
    "gINDEX": FeedSpec(
        feed_type="gINDEX",
        records_key="records",
        parent_table="gindex",
        parent_id_field="ID",
        parent_required=["ID", "Pipe"],
        header_keys=[],
        children=[],
    ),
    # Capacity-release awards. No TSP header at the payload level — each award
    # carries its own TSP fields.
    "gAWD": FeedSpec(
        feed_type="gAWD",
        records_key="awards",
        parent_table="gawd",
        parent_id_field="Id",
        parent_required=["Id", "AwardNumber"],
        header_keys=[],
        children=[],
    ),
}


@dataclass
class RoutedRecord:
    table: str
    record: Dict[str, Any]
    raw_record_id: str
    missing_fields: List[str]


def known_feeds() -> List[str]:
    return list(FEED_REGISTRY.keys())


def _merge_missing(base: Dict[str, Any], extra: Dict[str, Any], keys: List[str]) -> None:
    """Fill `base[k]` from `extra[k]` for each k in keys when base lacks it."""
    lower = {k.lower(): k for k in base}
    for key in keys:
        if key.lower() not in lower and key in extra:
            base[key] = extra[key]


def _get_id(record: Dict[str, Any], field: str) -> str:
    lower = {k.lower(): v for k, v in record.items()}
    val = lower.get(field.lower())
    return "" if val is None else str(val)


def route(payload: Dict[str, Any], feed_type: str) -> Iterator[RoutedRecord]:
    """Yield a RoutedRecord for every Bronze row implied by the payload."""
    spec = FEED_REGISTRY[feed_type]

    header = {k: payload[k] for k in spec.header_keys if k in payload}
    # Record lists and child arrays may arrive native or as embedded JSON text.
    records = coerce.as_record_list(payload.get(spec.records_key))

    for raw in records:
        record = dict(raw)
        _merge_missing(record, header, spec.header_keys)

        parent_id = _get_id(record, spec.parent_id_field)
        # The parent's typed columns ignore the nested child arrays automatically
        # (they aren't business columns), but we keep them on the record so the
        # parent's raw_payload preserves the FULL original contract.
        yield RoutedRecord(
            table=spec.parent_table,
            record=record,
            raw_record_id=parent_id,
            missing_fields=validators.validate_record(record, spec.parent_required),
        )

        for child in spec.children:
            for child_raw in coerce.as_record_list(record.get(child.array_key)):
                child_record = dict(child_raw)
                _merge_missing(child_record, record, child.inherit)
                yield RoutedRecord(
                    table=child.table,
                    record=child_record,
                    raw_record_id=_get_id(child_record, child.id_field),
                    missing_fields=validators.validate_record(
                        child_record, child.required
                    ),
                )
