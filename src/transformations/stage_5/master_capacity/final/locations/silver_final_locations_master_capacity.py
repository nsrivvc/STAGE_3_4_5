"""
silver_final_locations_master_capacity.py
=========================================
FINAL Locations — Master Capacity. Consolidates all four feeds' location master
capacity tables into one.

NO EXISTING TARGET TO MIRROR: unlike the core grain, there is no
`final_locations_master_capacity` table in the database yet, so the column set
below is a SPEC placeholder built from the location fields this pipeline already
handles (bronze.gtran_loc and the stage-4 rec-del pairing output). Replace it
with the real model when it's settled — the DDL and the UNION both follow from
this list, so nothing else needs touching.
"""

from __future__ import annotations

from ..final_base import FinalMasterCapacityTransformation
from ...models import LOCATIONS_COLUMNS
from ......core.registry import register


@register
class SilverFinalLocationsMasterCapacity(FinalMasterCapacityTransformation):
    name = "silver_final_locations_master_capacity"
    table_name = "final_locations_master_capacity"
    grain = "locations"

    # Shared with the per-feed transformations so the UNION can never break
    # on a column mismatch. Single definition lives in ../../models.py.
    columns = LOCATIONS_COLUMNS

    # SPEC: one row per contract per location per feed. If a location can serve
    # both receipt and delivery on one contract, loc_purpose belongs in the key.
    natural_key = ("source_type", "ngh_contract_id", "loc_code")

    dedupe_note = (
        "one row per contract/location per feed; add loc_purpose to the key if "
        "a location can be both receipt and delivery on the same contract"
    )

    # SPEC: placeholder model — no real target table exists yet.
