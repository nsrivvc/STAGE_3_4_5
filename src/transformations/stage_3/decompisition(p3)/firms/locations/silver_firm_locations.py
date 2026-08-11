"""
silver_firm_locations.py
========================
Decomposes the FIRM feed's Bronze locations into `<DECOMP_SCHEMA>.firm_locations`
— the table stage 4 rec-del pairing reads.

Reads bronze.gtran_loc directly. Once deduplication(p1) and ammendments(p2) have
code and output tables, `source_table` (and `source_schema`) should point at the
ammendments output instead; the rest of the class needs no change.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverFirmLocations(LocationsDecomposition):
    name = "silver_firm_locations"
    table_name = "firm_locations"
    feed = "firm"
    source_table = "gtran_loc"
    contract_id_col = "firmid"
    qty_col = "kqtyloc"
