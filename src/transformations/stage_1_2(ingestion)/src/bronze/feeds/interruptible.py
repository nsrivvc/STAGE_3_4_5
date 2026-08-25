"""
interruptible.py
================
Interruptible transportation contracts -> bronze.gtran_it.

Structurally identical to the firm feed -- same envelope variants, same
renames -- differing only in the contract id (`InterruptibleId`) and the
quantity column (`ITQtyK` rather than `KQtyK`). The aliases and the extra
`Term` / `RecZones` / `DelZones` columns mirror firm.py for the same reason:
the live NatGasHub export spells them that way. See firm.py for the detail.
"""

from __future__ import annotations

from .spec import FeedDefinition

FEED = FeedDefinition(
    feed_type="gTRAN_IT",
    table="gtran_it",
    records_keys=("contracts", "Interruptibles"),
    parent_id_field="Id",
    parent_required=("Id", "InterruptibleId"),
    header_keys=("TspName", "TspDuns", "TspProp"),
    nested_sections=("locations", "rates"),
    # Alternative spellings accepted for the SAME column.
    aliases={
        "KQty": "ITQtyK",
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
        ("InterruptibleId", "varchar"),
        ("Cycle", "varchar"),
        ("AmendRptg", "varchar"),
        ("AmendRptgDesc", "varchar"),
        ("KHolderName", "varchar"),
        ("KHolder", "int"),
        ("KHolderProp", "varchar"),
        ("SvcReqK", "varchar"),
        ("RateSch", "varchar"),
        ("ITQtyK", "int"),
        ("KStat", "varchar"),
        ("KStatDesc", "varchar"),
        ("KBegDateTime", "datetime"),
        ("KEndDateTime", "datetime"),
        ("NgtdRateInd", "varchar"),
        ("NgtdRateIndDesc", "varchar"),
        ("PkgId", "varchar"),
        ("KRoll", "varchar"),
        ("KRollDesc", "varchar"),
        ("Affil", "varchar"),
        ("AffilDesc", "varchar"),
        ("TermsNotes", "varchar"),
        ("CreatedDateTime", "datetime"),
        ("RecLocs", "varchar"),
        ("DelLocs", "varchar"),
        ("MaxRateChgd", "varchar"),
        ("MaxTrfRate", "varchar"),
        ("OtherRates", "varchar"),
        ("OtherRatesDescription", "varchar"),
        ("OtherRatesBasis", "varchar"),
        ("DealType", "varchar"),
        ("locations", "json"),
        ("rates", "json"),
        ("Term", "int"),
        ("RecZones", "varchar"),
        ("DelZones", "varchar"),
    ],
)
