"""
silver_interruptible_locations_master_capacity.py
=================================================
Maps the INTERRUPTIBLE feed's stage-3 `interruptible_locations` onto the shared master capacity
model, producing `silver.interruptible_locations_master_capacity`.

That model lives in ../../models.py and is shared with the FINAL
transformations, which UNION every feed's table for this grain into one.

Unmapped target columns are emitted as typed NULLs -- this feed has no award,
offer, bid or capacity-release fields. `SPEC:` markers below flag mappings that
are inferred rather than confirmed.
"""

from __future__ import annotations

from ...master_base import MasterCapacityTransformation
from ......core.registry import register


@register
class SilverInterruptibleLocationsMasterCapacity(MasterCapacityTransformation):
    name = "silver_interruptible_locations_master_capacity"
    table_name = "interruptible_locations_master_capacity"
    feed = "interruptible"
    grain = "locations"
    source_table = "interruptible_locations"


    # SPEC: `ngh_contract_id` is the feed's CONTRACT key (interruptibleid), not the row's
    # own `id`. In the locations and rates tables `id` identifies the location or
    # rate record and repeats across contracts -- using it collapsed 4,467
    # locations into 112. The contract key is also what ties core, locations and
    # rates together, which is the point of a shared master capacity model.
    column_map = {
        "ngh_contract_id": "interruptibleid",
        "pipeline_duns": "tspduns",
        "pipeline_name": "tspname",
        "loc_code": "loc",
        "loc_name": "locname",
        "loc_zone": "loczn",
        "loc_purpose": "locpurp",
        "loc_quantity_type": "locqti",
        "begin_date": "NULLIF(kentbegdatetime, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(kentenddatetime, '')::TIMESTAMPTZ",
        "posted_date": "NULLIF(posteddatetime, '')::TIMESTAMPTZ",
        "created_date": "NULLIF(createddatetime, '')::TIMESTAMPTZ",
        "source": "source_system",
    }
