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


    # Mirror of the firm map (see ../../firm/locations/), per the agreed
    # Locations sheet's gTRAN IT column: contract key interruptibleid,
    # quantity itqtyloc; everything else shares the firm feed's names.
    column_map = {
        "ngh_contract_id": "interruptibleid",
        "location": "loc",
        "location_name": "locname",
        "zone": "loczn",
        "location_qti": "locqti",
        "location_purpose_code": "locpurpdesc",
        "capacity_type": "captypename",
        "quantity": "NULLIF(itqtyloc, '')::NUMERIC",
        "beg_date": "NULLIF(kentbegdatetime, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(kentenddatetime, '')::TIMESTAMPTZ",
        "season_beg_date": "NULLIF(seasnlst, '')::TIMESTAMPTZ",
        "season_end_date": "NULLIF(seasnlend, '')::TIMESTAMPTZ",
        "transaction_term_begin_datetime": "NULLIF(transactiontermbegindatetime, '')::TIMESTAMPTZ",
        "transaction_term_end_datetime": "NULLIF(transactiontermenddatetime, '')::TIMESTAMPTZ",
        "segment": "segment",
        "index": '"index"',
        "posted_date": "NULLIF(posteddatetime, '')::TIMESTAMPTZ",
        "update_date": "ingestion_timestamp",
        "source": "'gTRAN IT'",
    }
