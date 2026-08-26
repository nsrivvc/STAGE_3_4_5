"""
silver_firm_locations.py
========================
Decomposes the FIRM feed's locations into `<DECOMP_SCHEMA>.firm_locations`
— the table stage 4 rec-del pairing reads.

Reads `firm_dedup`, the one deduplicated contract table deduplication(p1)
produces, and explodes its nested `locations` JSON array: one row per location,
projected onto the agreed schema in a single statement. There is no Bronze
locations table and no intermediate exploded table.

`element_keys` is the schema of one location object in the payload, verbatim;
each becomes the lowercase column the agreed schema names. `firmid`,
`posteddatetime`, `kbegdatetime`/`kenddatetime` (the contract's transaction
term, which the agreed schema exposes as transactiontermbegin/enddatetime) and
`captypename` live on the contract row rather than in the element, so they are
carried via `parent_columns`.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverFirmLocations(LocationsDecomposition):
    name = "silver_firm_locations"
    table_name = "firm_locations"
    feed = "firm"
    source_table = "firm_dedup"
    contract_id_col = "firmid"
    qty_col = "kqtyloc"

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
