"""
silver_awards_core_master_capacity.py
=====================================
Maps the AWARDS feed's stage-3 `awards_core` onto the shared master capacity
model, producing `silver.awards_core_master_capacity`.

That model lives in ../../models.py and is shared with the FINAL
transformations, which UNION every feed's table for this grain into one.

`ngh_contract_id` is **AwardNumber** for all three awards grains. The award's own
`Id` identifies the core row, but the locations and rates elements do not carry
it -- they carry OfferNumber / BidNumber / AwardNumber. AwardNumber is the only
key present at every grain, so it is what lets the three join.

Unmapped target columns are emitted as typed NULLs. `SPEC:` markers flag the
mappings that are inferred rather than confirmed against the mapping sheet.

NOT MAPPED, because the awards feed has no equivalent: `pipeline_duns` (only a
TSP prop code and name are published), `evergreen`, `notice_period_days` and
`calculated_end_date` (the far-future placeholder the sheet defines applies to
the gTRAN feeds, not to a capacity release).
"""

from __future__ import annotations

from ...master_base import MasterCapacityTransformation
from ......core.registry import register


@register
class SilverAwardsCoreMasterCapacity(MasterCapacityTransformation):
    name = "silver_awards_core_master_capacity"
    table_name = "awards_core_master_capacity"
    feed = "awards"
    grain = "core"
    source_table = "awards_core"

    column_map = {
        "ngh_contract_id": "awardnumber",
        # No TSP DUNS in this feed -- only the prop code and the name.
        "pipeline_name": "transportationserviceprovidername",
        # SPEC: for a capacity release the acquiring contract is the replacement
        # shipper's; `releaser_contract_number` below keeps the releaser's own.
        "contract_number": "replacementshippercontractnumber",
        "award_number": "awardnumber",
        "offer_number": "offernumber",
        "bid_number": "bidnumber",
        "releaser_contract_number": "releasercontractnumber",
        "posted_date": "NULLIF(postdatetime, '')::TIMESTAMPTZ",
        # The release term is the award's contract window.
        "begin_date": "NULLIF(releasetermstartdate, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(releasetermenddate, '')::TIMESTAMPTZ",
        "contract_quantity": "NULLIF(awardquantitycontract, '')::NUMERIC",
        "rate_schedule": "rateschedule",
        # SPEC: the BIDDER acquires the released capacity, so the bidder is its
        # holder and the releaser is the original holder.
        "contract_holder": "biddername",
        "contract_holder_duns": "bidderduns",
        "releaser_name": "releasername",
        "releaser_duns": "releaserduns",
        "replacement_shipper_role_indicator": "replacementshipperroleindicator",
        "term_notes": "specialtermsandmiscellaneousnotes",
        "contract_type": "'AWARDS'",
        "created_date": "NULLIF(createddate, '')::TIMESTAMPTZ",
        "update_date": "updated_ts",
        # The sheet's Source row names the feed literally.
        "source": "'gAWD'",
    }
