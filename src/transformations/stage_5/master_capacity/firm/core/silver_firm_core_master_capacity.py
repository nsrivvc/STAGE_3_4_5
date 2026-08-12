"""
silver_firm_core_master_capacity.py
===================================
Maps the FIRM feed's stage-3 `firm_core` onto the shared master capacity
model, producing `silver.firm_core_master_capacity`.

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
class SilverFirmCoreMasterCapacity(MasterCapacityTransformation):
    name = "silver_firm_core_master_capacity"
    table_name = "firm_core_master_capacity"
    feed = "firm"
    grain = "core"
    source_table = "firm_core"


    # SPEC: `ngh_contract_id` is the feed's CONTRACT key (firmid), not the row's
    # own `id`. In the locations and rates tables `id` identifies the location or
    # rate record and repeats across contracts -- using it collapsed 4,467
    # locations into 112. The contract key is also what ties core, locations and
    # rates together, which is the point of a shared master capacity model.
    column_map = {
        "ngh_contract_id": "firmid",
        "pipeline_duns": "tspduns",
        "pipeline_name": "tspname",
        "contract_number": "svcreqk",
        "posted_date": "NULLIF(posteddatetime, '')::TIMESTAMPTZ",
        "begin_date": "NULLIF(kbegdatetime, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(kenddatetime, '')::TIMESTAMPTZ",
        "contract_quantity": "NULLIF(kqtyk, '')::NUMERIC",
        "rate_schedule": "ratesch",
        "contract_holder": "kholdername",
        "contract_holder_duns": "kholder",
        "evergreen": "kroll",
        "term_notes": "termsnotes",
        "contract_type": "'FIRM'",
        "created_date": "NULLIF(createddatetime, '')::TIMESTAMPTZ",
        "update_date": "updated_ts",
        "source": "source_system",
    }
