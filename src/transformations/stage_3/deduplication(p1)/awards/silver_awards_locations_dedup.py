"""
silver_awards_locations_dedup.py
================================
Explodes the AWARDS feed's nested `locations` arrays out of bronze.gawd -- one row
per location element -- and deduplicates them.

There is no separate Bronze locations table: ingestion lands the whole awards feed
in gawd, with each award row carrying its locations as a JSON array inside
`raw_payload`. See ../dedup_base.py (NestedArrayDeduplication) for how the
explosion and the element-level hash dedupe work.

`element_keys` is the schema of one location object in the payload, verbatim,
and matches the agreed awards locations column list. Every element carries its own
`GS_ID` and `Id` (e.g. "TCO-AWARD-2026-000001-LOC-01") plus the parent's
OfferNumber / BidNumber / AwardNumber, so the award is identifiable from the
element alone. `parent_columns` adds the four award-level datetimes that exist
only on the contract row.

Target: <DECOMP_SCHEMA>.awards_locations_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverAwardsLocationsDedup(NestedArrayDeduplication):
    name = "silver_awards_locations_dedup"
    table_name = "awards_locations_dedup"
    feed = "awards"
    source_table = "gawd"
    section = "locations"

    # Award-level only -- absent from every element, so no name collides.
    parent_columns = ["postdatetime", "capacityawarddatetime", "releasetermstartdate", "releasetermenddate"]

    element_keys = [
        "GS_ID",
        "Id",
        "OfferNumber",
        "BidNumber",
        "AwardNumber",
        "TransportationServiceProviderPropCode",
        "IBRRateFloor",
        "IBRNameVolume",
        "MaximumVolumetricCommitmentQuantity",
        "SeasonalStartDate",
        "SeasonalEndDate",
        "LocationPurposeCode",
        "StdLocPropPurposeCode",
        "LocationPurposeCodeValue",
        "LocationName",
        "LocationPropCode",
        "LocationQuantityTypeIndicator",
        "LocationQuantityTypeIndicatorCodeValue",
        "CapacityTypeLocationIndicator",
        "CapacityTypeLocationIndicatorCodeValue",
        "Route",
        "AwardQuantityLocation",
        "SeasonalDateFormat",
        "BidderDuns",
        "ReleaserDuns",
        "CreatedDate",
        "Version_Status",
        "UpdatedDateTime",
    ]
