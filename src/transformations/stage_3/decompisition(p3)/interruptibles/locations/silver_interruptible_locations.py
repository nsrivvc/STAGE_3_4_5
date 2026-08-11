"""
silver_interruptible_locations.py
=================================
Decomposes the INTERRUPTIBLE (IT) feed's Bronze locations into
`<DECOMP_SCHEMA>.interruptible_locations` — the table stage 4 rec-del pairing
reads.

Reads bronze.gtran_it_loc directly. Once deduplication(p1) and ammendments(p2)
have code and output tables, `source_table` (and `source_schema`) should point at
the ammendments output instead; the rest of the class needs no change.

Note gtran_it_loc is empty today, so this reports 0 rows until the IT feed lands.
"""

from __future__ import annotations

from ...decomp_base import LocationsDecomposition
from ......core.registry import register


@register
class SilverInterruptibleLocations(LocationsDecomposition):
    name = "silver_interruptible_locations"
    table_name = "interruptible_locations"
    feed = "interruptible"
    source_table = "gtran_it_loc"
    contract_id_col = "interruptibleid"
    qty_col = "itqtyloc"
