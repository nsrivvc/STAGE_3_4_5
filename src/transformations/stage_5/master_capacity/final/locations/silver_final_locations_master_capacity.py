"""
silver_final_locations_master_capacity.py
=========================================
FINAL Locations — Master Capacity. Consolidates all four feeds' location master
capacity tables into one.

The column set follows the agreed Locations mapping sheet and lives in
../../models.py, shared with the per-feed transformations so the UNION can
never break on a column mismatch.
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

    # One row per contract/location/purpose per feed -- a location can serve
    # both receipt and delivery on one contract, so purpose is in the key,
    # mirroring the per-feed natural key in models.py.
    natural_key = ("source_type", "ngh_contract_id", "location", "location_purpose_code")

    dedupe_note = "one row per contract/location/purpose per feed"
