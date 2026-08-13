"""
silver_firm_locations_master_capacity.py
========================================
Maps the FIRM feed's stage-3 `firm_locations` onto the shared master capacity
model, producing `silver.firm_locations_master_capacity`.

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
class SilverFirmLocationsMasterCapacity(MasterCapacityTransformation):
    name = "silver_firm_locations_master_capacity"
    table_name = "firm_locations_master_capacity"
    feed = "firm"
    grain = "locations"
    source_table = "firm_locations"


    # Mappings follow the agreed Locations sheet (gTRAN FIRM column):
    # Location <- Loc, Location Purpose Code <- LocPurpDesc, Capacity Type <-
    # CapTypeName, Quantity <- KQtyLoc, and so on. `ngh_contract_id` is the
    # contract key (firmid) tying this grain back to core; `group` has no firm
    # source and stays NULL.
    column_map = {
        "ngh_contract_id": "firmid",
        "location": "loc",
        "location_name": "locname",
        "zone": "loczn",
        "location_qti": "locqti",
        "location_purpose_code": "locpurpdesc",
        "capacity_type": "captypename",
        "quantity": "NULLIF(kqtyloc, '')::NUMERIC",
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
        "source": "'gTRAN FIRM'",
    }
