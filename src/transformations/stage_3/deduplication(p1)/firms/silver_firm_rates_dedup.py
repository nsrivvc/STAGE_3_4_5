"""
silver_firm_rates_dedup.py
==========================
Explodes the FIRM feed's nested `rates` arrays out of bronze.gtran_firm --
one row per rate element -- and deduplicates them.

There is no separate Bronze rates table: ingestion lands the whole firm feed
in gtran_firm, with each contract row carrying its rates as a JSON array
inside `raw_payload`. See ../dedup_base.py (NestedArrayDeduplication) for how
the explosion and the element-level hash dedupe work.

`element_keys` is the schema of one rate object in the payload, verbatim; each
key becomes the lowercase TEXT column decompisition(p3) expects. `firmid`,
`posteddatetime`, `tspduns` and `tspname` live on the contract row, not in the
element, so they are carried via `parent_columns`.

Target: <DECOMP_SCHEMA>.firm_rates_dedup
"""

from __future__ import annotations

from ..dedup_base import NestedArrayDeduplication
from .....core.registry import register


@register
class SilverFirmRatesDedup(NestedArrayDeduplication):
    name = "silver_firm_rates_dedup"
    table_name = "firm_rates_dedup"
    feed = "firm"
    source_table = "gtran_firm"
    section = "rates"

    parent_columns = ["firmid", "posteddatetime", "tspduns", "tspname"]

    element_keys = [
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
        "KQtyLoc",
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
