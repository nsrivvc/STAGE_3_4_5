"""
firm.py
=======
Firm transportation contracts -> bronze.gtran_firm.

TWO ENVELOPES ARE ACCEPTED
--------------------------
The mock fixture wraps its records as

    {"feedType": "gTRAN_FIRM", "sourceSystem": ..., "contracts": [...]}

while the live NatGasHub export omits the metadata entirely and keys the list
differently:

    {"PageNumber": 1, "Firms": [...]}

`records_keys` lists both, so either loads with no pre-processing. A payload
carrying no `feedType` is identified by its record key instead -- see
validators.resolve_feed.

FIELD ALIASES
-------------
The live export renames four fields. They are the same columns, so they are
declared as aliases rather than duplicated:

    KQty            -> KQtyK
    AmendRptDate    -> AmendRptgDesc     (carries the amendment SCOPE, e.g.
                                          "All Data" -- stage 3's p2 fold
                                          classifies on exactly this)
    NetdRateInd     -> NgtdRateInd       (letter transposition in the source)
    NetdRateIndDesc -> NgtdRateIndDesc

THREE COLUMNS THE FIXTURE NEVER HAD
-----------------------------------
`Term`, `RecZones` and `DelZones` appear only in the live export. They are added
here rather than left to raw_payload so they land in typed columns like
everything else; a fixture that omits them simply leaves them NULL.
"""

from __future__ import annotations

from .spec import FeedDefinition

FEED = FeedDefinition(
    feed_type="gTRAN_FIRM",
    table="gtran_firm",
    records_keys=("contracts", "Firms"),
    parent_id_field="Id",
    parent_required=("Id", "FirmId"),
    header_keys=("TspName", "TspDuns", "TspProp"),
    nested_sections=("locations", "rates"),
    # Alternative spellings accepted for the SAME column.
    aliases={
        "KQty": "KQtyK",
        "AmendRptDate": "AmendRptgDesc",
        "NetdRateInd": "NgtdRateInd",
        "NetdRateIndDesc": "NgtdRateIndDesc",
    },
    columns=[
        ("Id", "varchar"),
        ("TspName", "varchar"),
        ("TspDuns", "int"),
        ("TspProp", "varchar"),
        ("PostedDateTime", "datetime"),
        ("FirmId", "varchar"),
        ("Cycle", "varchar"),
        ("AmendRptg", "varchar"),
        ("AmendRptgDesc", "varchar"),
        ("KHolderName", "varchar"),
        ("KHolder", "int"),
        ("KHolderProp", "varchar"),
        ("SvcReqK", "varchar"),
        ("RateSch", "varchar"),
        ("KQtyK", "int"),
        ("KStat", "varchar"),
        ("KStatDesc", "varchar"),
        ("KBegDateTime", "datetime"),
        ("KEndDateTime", "datetime"),
        ("KEndInd", "varchar"),
        ("NgtdRateInd", "varchar"),
        ("NgtdRateIndDesc", "varchar"),
        ("PkgId", "varchar"),
        ("KRoll", "varchar"),
        ("KRollDesc", "varchar"),
        ("Affil", "varchar"),
        ("AffilDesc", "varchar"),
        ("CapType", "varchar"),
        ("CapTypeName", "varchar"),
        ("CapTypeLoc", "varchar"),
        ("CapTypeLocDesc", "varchar"),
        ("OSId", "varchar"),
        ("Rte", "varchar"),
        ("TermsNotes", "varchar"),
        ("CreatedDateTime", "datetime"),
        ("RecLocs", "varchar"),
        ("DelLocs", "varchar"),
        ("MaxRateChgd", "varchar"),
        ("MaxTrfRate", "varchar"),
        ("OtherRates", "varchar"),
        ("OtherRatesDescription", "varchar"),
        ("OtherRatesBasis", "varchar"),
        ("locations", "json"),
        ("rates", "json"),
        ("Term", "int"),
        ("RecZones", "varchar"),
        ("DelZones", "varchar"),
    ],
)
