"""
silver_interruptible_locations_dedup.py
=======================================
Explodes the INTERRUPTIBLE feed's nested `locations` arrays out of
bronze.gtran_it -- one row per location element -- and deduplicates them.

Mirror of the firm variant (see ../firms/silver_firm_locations_dedup.py):
ingestion lands the whole IT feed in gtran_it with locations nested in
`raw_payload`; there is no separate Bronze locations table. The only schema
differences from firm are the contract id (`interruptibleid`) and the quantity
key (`ItQtyLoc` instead of `KQtyLoc`).

gtran_it is empty today, so this reports 0 rows until the IT feed lands; the
key list follows the firm payload shape and the columns decompisition(p3)
expects. A key absent from the real payload simply yields NULL.

Target: <DECOMP_SCHEMA>.interruptible_locations_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverInterruptibleLocationsDedup(NestedArrayDeduplication):
    name = "silver_interruptible_locations_dedup"
    table_name = "interruptible_locations_dedup"
    feed = "interruptible"
    source_table = "gtran_it"
    section = "locations"

    # gtran_it has no captype* columns on the contract row (unlike gtran_firm),
    # so captypename is listed as an element key instead: NULL until the IT
    # feed lands and shows where it actually carries it.
    parent_columns = ["interruptibleid", "posteddatetime", "kbegdatetime", "kenddatetime"]

    element_keys = [
        "CapTypeName",
        "Index",
        "Segment",
        "UniqueId",
        "Pk",
        "ItQtyLoc",
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
