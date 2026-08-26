"""
silver_interruptible_locations.py
=================================
Decomposes the INTERRUPTIBLE feed's locations into
`<DECOMP_SCHEMA>.interruptible_locations` — the table stage 4 rec-del pairing
reads.

Reads `interruptible_dedup`, the one deduplicated contract table
deduplication(p1) produces, and explodes its nested `locations` JSON array: one
row per location, projected onto the agreed schema in a single statement. There
is no Bronze locations table and no intermediate exploded table.

gtran_it has no captype* columns on the contract row (unlike gtran_firm), so
`captypename` is listed as an element key instead: NULL until the IT feed lands
and shows where it actually carries it.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverInterruptibleLocations(LocationsDecomposition):
    name = "silver_interruptible_locations"
    table_name = "interruptible_locations"
    feed = "interruptible"
    source_table = "interruptible_dedup"
    contract_id_col = "interruptibleid"
    qty_col = "itqtyloc"

    section = "locations"
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
