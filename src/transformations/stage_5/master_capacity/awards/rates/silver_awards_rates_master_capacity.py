"""
silver_awards_rates_master_capacity.py
======================================
Maps the AWARDS feed's stage-3 `awards_rates` onto the shared master capacity
model, producing `silver.awards_rates_master_capacity`.

That model lives in ../../models.py and is shared with the FINAL
transformations, which UNION every feed's table for this grain into one.

DORMANT: stage 3 produces no awards tables yet -- deduplication(p1) covers
bronze.gawd, but there is no awards decomposition, so `awards_rates` does not
exist and the runner reports this as skipped. The mapping is left empty
until the awards stage-3 output is defined; gawd is award-shaped
(awardid, awdqty, awdbegdatetime), not contract-shaped.
"""

from __future__ import annotations

from ...master_base import MasterCapacityTransformation
from ......core.registry import register


@register
class SilverAwardsRatesMasterCapacity(MasterCapacityTransformation):
    name = "silver_awards_rates_master_capacity"
    table_name = "awards_rates_master_capacity"
    feed = "awards"
    grain = "rates"
    source_table = "awards_rates"

    column_map = {
        # SPEC: awaiting the awards stage-3 output shape.
    }
