"""
firm.py — firm transportation contracts: gTRAN_FIRM -> bronze.gtran_firm.

TWO ENVELOPES
    The mock fixture ships {"feedType": "gTRAN_FIRM", "contracts": [...]}; the
    live export ships {"PageNumber": 1, "Firms": [...]} with no feed metadata
    at all. "Firms" identifies this feed on its own; "contracts" never can,
    because interruptible arrives under that key too.

HEADERS
    Some exports declare the TSP once at the top of the payload, others repeat
    it on every record. HEADER_KEYS are copied down onto records that lack
    them, so a row is self-describing either way.

ALIASES
    The few fields spelled differently from the column they fill. Everything
    else matches its column case-insensitively -- "Locations" fills locations,
    "KStat" fills kstat -- which is why this list is so short.

Nested Locations/Rates are not exploded here: they land as JSON text on the
row and stage 3 fans them out.
"""

NAME = "gTRAN_FIRM"
TABLE = "gtran_firm"
RECORD_KEYS = ("Firms", "contracts")
ID_FIELD = "Id"
REQUIRED = ("Id", "FirmId")
HEADER_KEYS = ("TspName", "TspDuns", "TspProp")
ALIASES = {
    "kqty": "kqtyk",                       # KQty            -> kqtyk
    "amendrptdate": "amendrptgdesc",       # AmendRptDate    -> amendrptgdesc
    "netdrateind": "ngtdrateind",          # NetdRateInd     -> ngtdrateind
    "netdrateinddesc": "ngtdrateinddesc",  # NetdRateIndDesc -> ngtdrateinddesc
}
