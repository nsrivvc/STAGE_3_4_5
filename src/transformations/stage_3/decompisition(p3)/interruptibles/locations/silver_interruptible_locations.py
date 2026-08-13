"""
silver_interruptible_locations.py
=================================
Decomposes the INTERRUPTIBLE (IT) feed's Bronze locations into
`<DECOMP_SCHEMA>.interruptible_locations` — the table stage 4 rec-del pairing
reads.

Reads the deduplication(p1) output `interruptible_locations_dedup`, so only new or changed
rows reach this phase. When ammendments(p2) gains code, point `source_table`
at its output instead; nothing else changes.

Note bronze.gtran_it is empty today, so this reports 0 rows until the IT feed lands.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverInterruptibleLocations(LocationsDecomposition):
    name = "silver_interruptible_locations"
    table_name = "interruptible_locations"
    feed = "interruptible"
    source_table = "interruptible_locations_dedup"
    contract_id_col = "interruptibleid"
    qty_col = "itqtyloc"
