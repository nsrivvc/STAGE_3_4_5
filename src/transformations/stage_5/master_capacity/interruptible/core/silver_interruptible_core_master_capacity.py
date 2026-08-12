"""
silver_interruptible_core_master_capacity.py
============================================
Maps the INTERRUPTIBLE feed's stage-3 `interruptible_core` onto the shared master capacity
model, producing `silver.interruptible_core_master_capacity`.

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
class SilverInterruptibleCoreMasterCapacity(MasterCapacityTransformation):
    name = "silver_interruptible_core_master_capacity"
    table_name = "interruptible_core_master_capacity"
    feed = "interruptible"
    grain = "core"
    source_table = "interruptible_core"


    # SPEC: `ngh_contract_id` is the feed's CONTRACT key (interruptibleid), not the row's
    # own `id`. In the locations and rates tables `id` identifies the location or
    # rate record and repeats across contracts -- using it collapsed 4,467
    # locations into 112. The contract key is also what ties core, locations and
    # rates together, which is the point of a shared master capacity model.
    column_map = {
        "ngh_contract_id": "interruptibleid",
        "pipeline_duns": "tspduns",
        "pipeline_name": "tspname",
        "contract_number": "svcreqk",
        "posted_date": "NULLIF(posteddatetime, '')::TIMESTAMPTZ",
        "begin_date": "NULLIF(kbegdatetime, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(kenddatetime, '')::TIMESTAMPTZ",
        "contract_quantity": "NULLIF(itqtyk, '')::NUMERIC",
        "rate_schedule": "ratesch",
        "contract_holder": "kholdername",
        "contract_holder_duns": "kholder",
        "evergreen": "kroll",
        "term_notes": "termsnotes",
        "contract_type": "'INTERRUPTIBLE'",
        "created_date": "NULLIF(createddatetime, '')::TIMESTAMPTZ",
        "update_date": "updated_ts",
        "source": "source_system",
    }
