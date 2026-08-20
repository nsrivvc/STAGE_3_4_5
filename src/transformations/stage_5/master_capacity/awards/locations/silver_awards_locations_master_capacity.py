"""
silver_awards_locations_master_capacity.py
==========================================
Maps the AWARDS feed's stage-3 `awards_locations` onto the shared master capacity
model, producing `silver.awards_locations_master_capacity`.

That model lives in ../../models.py and is shared with the FINAL
transformations, which UNION every feed's table for this grain into one.

`ngh_contract_id` is **AwardNumber** for all three awards grains. The award's own
`Id` identifies the core row, but the locations and rates elements do not carry
it -- they carry OfferNumber / BidNumber / AwardNumber. AwardNumber is the only
key present at every grain, so it is what lets the three join.

Unmapped target columns are emitted as typed NULLs. `SPEC:` markers flag the
mappings that are inferred rather than confirmed against the mapping sheet.

NOT MAPPED: `zone`, `segment` and `index` -- the awards locations schema has no
zone, no segment and no index, where firm/IT have loczn / segment / Index.
"""

from __future__ import annotations

from ...master_base import MasterCapacityTransformation
from ......core.registry import register


@register
class SilverAwardsLocationsMasterCapacity(MasterCapacityTransformation):
    name = "silver_awards_locations_master_capacity"
    table_name = "awards_locations_master_capacity"
    feed = "awards"
    grain = "locations"
    source_table = "awards_locations"

    column_map = {
        "ngh_contract_id": "awardnumber",
        "location": "locationpropcode",
        "location_name": "locationname",
        "location_qti": "locationquantitytypeindicator",
        "location_purpose_code": "locationpurposecode",
        "capacity_type": "capacitytypelocationindicator",
        "quantity": "NULLIF(awardquantitylocation, '')::NUMERIC",
        # Elements carry only a SEASONAL window; the contract window is the
        # award-level release term, carried down as a parent column.
        "beg_date": "NULLIF(releasetermstartdate, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(releasetermenddate, '')::TIMESTAMPTZ",
        "season_beg_date": "NULLIF(seasonalstartdate, '')::TIMESTAMPTZ",
        "season_end_date": "NULLIF(seasonalenddate, '')::TIMESTAMPTZ",
        "transaction_term_begin_datetime": "NULLIF(releasetermstartdate, '')::TIMESTAMPTZ",
        "transaction_term_end_datetime": "NULLIF(releasetermenddate, '')::TIMESTAMPTZ",
        "posted_date": "NULLIF(postdatetime, '')::TIMESTAMPTZ",
        "update_date": "updated_ts",
        "source": "'gAWD'",
    }
