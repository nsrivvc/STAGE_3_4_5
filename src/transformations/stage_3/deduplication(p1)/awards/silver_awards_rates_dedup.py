"""
silver_awards_rates_dedup.py
============================
Explodes the AWARDS feed's nested `rates` arrays out of bronze.gawd -- one row
per rate element -- and deduplicates them.

There is no separate Bronze rates table: ingestion lands the whole awards feed
in gawd, with each award row carrying its rates as a JSON array inside
`raw_payload`. See ../dedup_base.py (NestedArrayDeduplication) for how the
explosion and the element-level hash dedupe work.

`element_keys` is the schema of one rate object in the payload, verbatim,
and matches the agreed awards rates column list. Every element carries its own
`GS_ID` and `Id` (e.g. "TCO-AWARD-2026-000001-RATE-01") plus the parent's
OfferNumber / BidNumber / AwardNumber, so the award is identifiable from the
element alone. `parent_columns` adds the four award-level datetimes that exist
only on the contract row.

Target: <DECOMP_SCHEMA>.awards_rates_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverAwardsRatesDedup(NestedArrayDeduplication):
    name = "silver_awards_rates_dedup"
    table_name = "awards_rates_dedup"
    feed = "awards"
    source_table = "gawd"
    section = "rates"

    # Award-level only -- absent from every element, so no name collides.
    parent_columns = ["postdatetime", "capacityawarddatetime", "releasetermstartdate", "releasetermenddate"]

    element_keys = [
        "GS_ID",
        "Id",
        "OfferNumber",
        "BidNumber",
        "AwardNumber",
        "BidderDuns",
        "ReleaserDuns",
        "TransportationServiceProviderPropCode",
        "LocationPurpose",
        "LocationPurposeCodeValue",
        "LocationName",
        "LocationPropCode",
        "IdentificationCodeQualifier",
        "ReservationRateBasis",
        "MarketBasedRateIndicator",
        "SurchargeIndicatorCodeValue",
        "SurchargeIndicator",
        "ChargeInformationReferenceNumber",
        "ChargeCode",
        "ChargeRate",
        "AwardRate",
        "AwardRateIdentificationCode",
        "MaximumTariffRate",
        "MaximumTariffRateIdentificationCode",
        "AwardPercentageOfMaximumTariffRate",
        "AwardPercentageOfMaximumTariffRateIdentificationCode",
        "MinimumVolumetricCommitmentPercentage",
        "IBRAllowableDifferential",
        "IBRAllowableDifferentialRateFloor",
        "IBRBidValuePercent",
        "CreatedDate",
        "Version_Status",
        "UpdatedDateTime",
    ]
