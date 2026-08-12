"""
silver_firm_rates_master_capacity.py
====================================
Maps the FIRM feed's stage-3 `firm_rates` onto the shared master capacity
model, producing `silver.firm_rates_master_capacity`.

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
class SilverFirmRatesMasterCapacity(MasterCapacityTransformation):
    name = "silver_firm_rates_master_capacity"
    table_name = "firm_rates_master_capacity"
    feed = "firm"
    grain = "rates"
    source_table = "firm_rates"


    # SPEC: `ngh_contract_id` is the feed's CONTRACT key (firmid), not the row's
    # own `id`. In the locations and rates tables `id` identifies the location or
    # rate record and repeats across contracts -- using it collapsed 4,467
    # locations into 112. The contract key is also what ties core, locations and
    # rates together, which is the point of a shared master capacity model.
    column_map = {
        "ngh_contract_id": "firmid",
        "pipeline_duns": "tspduns",
        "pipeline_name": "tspname",
        "rate_unique_id": "uniqueid",
        "rate_id": "rateid",
        "rate_form_type": "rateformtype",
        "rate_form_type_desc": "rateformtypedesc",
        "receipt_loc_code": "recloc",
        "delivery_loc_code": "delloc",
        "rate_charged": "NULLIF(ratechgd, '')::NUMERIC",
        "max_tariff_rate": "NULLIF(maxtrfrate, '')::NUMERIC",
        "total_surcharge": "NULLIF(totsurchg, '')::NUMERIC",
        "all_in_rate": "COALESCE(NULLIF(ratechgd, '')::NUMERIC, 0) + COALESCE(NULLIF(totsurchg, '')::NUMERIC, 0)",
        "is_market_based_rate": "CASE upper(NULLIF(mktbasedrateind, '')) WHEN 'Y' THEN TRUE WHEN 'N' THEN FALSE END",
        "season_start_date": "NULLIF(seasnlst, '')::DATE",
        "season_end_date": "NULLIF(seasnlend, '')::DATE",
        "begin_date": "NULLIF(kentbegdatetime, '')::TIMESTAMPTZ",
        "end_date": "NULLIF(kentenddatetime, '')::TIMESTAMPTZ",
        "posted_date": "NULLIF(posteddatetime, '')::TIMESTAMPTZ",
        "created_date": "NULLIF(createddatetime, '')::TIMESTAMPTZ",
        "source": "source_system",
    }
