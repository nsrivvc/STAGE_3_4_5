"""
silver_firm_locations.py
========================
Decomposes the FIRM feed's Bronze locations into `<DECOMP_SCHEMA>.firm_locations`
— the table stage 4 rec-del pairing reads.

Reads the deduplication(p1) output `firm_locations_dedup`, so only new or changed
rows reach this phase. When ammendments(p2) gains code, point `source_table`
at its output instead; nothing else changes.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverFirmLocations(LocationsDecomposition):
    name = "silver_firm_locations"
    table_name = "firm_locations"
    feed = "firm"
    source_table = "firm_locations_dedup"
    contract_id_col = "firmid"
    qty_col = "kqtyloc"
