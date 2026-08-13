"""
silver_firm_locations_dedup.py
==============================
Explodes the FIRM feed's nested `locations` arrays out of bronze.gtran_firm --
one row per location element -- and deduplicates them.

There is no separate Bronze locations table: ingestion lands the whole firm
feed in gtran_firm, with each contract row carrying its locations as a JSON
array inside `raw_payload`. See ../dedup_base.py (NestedArrayDeduplication)
for how the explosion and the element-level hash dedupe work.

`element_keys` is the schema of one location object in the payload, verbatim;
each key becomes the lowercase TEXT column decompisition(p3) expects. `firmid`,
`posteddatetime`, `kbegdatetime`/`kenddatetime` (the contract's transaction
term, which the agreed locations schema exposes as
transactiontermbegin/enddatetime) and `captypename` live on the contract row,
not in the element, so they are carried via `parent_columns`.

Target: <DECOMP_SCHEMA>.firm_locations_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverFirmLocationsDedup(NestedArrayDeduplication):
    name = "silver_firm_locations_dedup"
    table_name = "firm_locations_dedup"
    feed = "firm"
    source_table = "gtran_firm"
    section = "locations"

    parent_columns = ["firmid", "posteddatetime", "kbegdatetime", "kenddatetime", "captypename"]

    element_keys = [
        "Index",
        "Segment",
        "UniqueId",
        "Pk",
        "KQtyLoc",
        "SeasnlSt",
        "SeasnlEnd",
        "UniqueKey",
        "Id",
        "KEntBegDateTime",
        "KEntEndDateTime",
        "Loc",
        "LocName",
        "LocPurp",
        "LocPurpDesc",
        "LocZn",
        "LocQTI",
        "LocQTIDesc",
        "TspDuns",
        "TspName",
        "TspPropCode",
        "CreatedDateTime",
    ]
