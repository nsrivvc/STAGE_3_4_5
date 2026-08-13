"""
silver_interruptible_rates_dedup.py
===================================
Explodes the INTERRUPTIBLE feed's nested `rates` arrays out of bronze.gtran_it
-- one row per rate element -- and deduplicates them.

Mirror of the firm variant (see ../firms/silver_firm_rates_dedup.py):
ingestion lands the whole IT feed in gtran_it with rates nested in
`raw_payload`; there is no separate Bronze rates table. Schema differences
from firm: contract id `interruptibleid`, quantity key `ItQtyLoc` instead of
`KQtyLoc`, plus the IT-only `MaxDQ` / `MinDQ` daily-quantity bounds.

gtran_it is empty today, so this reports 0 rows until the IT feed lands; the
key list follows the firm payload shape and the columns decompisition(p3)
expects. A key absent from the real payload simply yields NULL.

Target: <DECOMP_SCHEMA>.interruptible_rates_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverInterruptibleRatesDedup(NestedArrayDeduplication):
    name = "silver_interruptible_rates_dedup"
    table_name = "interruptible_rates_dedup"
    feed = "interruptible"
    source_table = "gtran_it"
    section = "rates"

    parent_columns = ["interruptibleid", "posteddatetime", "tspduns", "tspname"]

    element_keys = [
        "MaxDQ",
        "MinDQ",
        "SeasnlSt",
        "SeasnlEnd",
        "UniqueId",
        "Pk",
        "RateFormType",
        "RateFormTypeDesc",
        "ResRateBasis",
        "ResRateBasisDesc",
        "LocKMaxPress",
        "LocKMinPress",
        "MinVolPctNonCapRel",
        "MinVolQtyNonCapRel",
        "CapType",
        "CapTypeName",
        "CapTypeLoc",
        "CapTypeLocDesc",
        "ItQtyLoc",
        "UniqueKey",
        "Id",
        "CreatedDateTime",
        "KEntBegDateTime",
        "KEntEndDateTime",
        "RecLoc",
        "RecLocName",
        "RecLocPurp",
        "RecLocPurpDesc",
        "RecLocZn",
        "DelLoc",
        "DelLocName",
        "DelLocPurp",
        "DelLocPurpDesc",
        "DelLocZn",
        "LocQTI",
        "LocQTIDesc",
        "RateId",
        "RateIdDesc",
        "RateChgd",
        "RateChgdRef",
        "RateChgdRefDesc",
        "MaxTrfRate",
        "MaxTrfRateRef",
        "MaxTrfRateRefDesc",
        "MktBasedRateInd",
        "SurchgId",
        "SurchgIdDesc",
        "SurchgInd",
        "SurchgIndDesc",
        "TotSurchg",
        "DiscBegDateTime",
        "DiscEndDateTime",
        "RptLvl",
        "RptLvlDesc",
        "NgtdRateIndRates",
    ]
