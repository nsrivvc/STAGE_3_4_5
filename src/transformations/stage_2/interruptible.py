"""
interruptible.py — interruptible transportation contracts:
gTRAN_IT -> bronze.gtran_it.

Structurally the same as firm.py. It differs in three places: the records
arrive under "Interruptibles", the contract is identified by InterruptibleId,
and the quantity lands in itqtyk rather than kqtyk.

"contracts" is shared with firm, so a file using that envelope has to declare
a feedType (or be told which feed it is with --feed).
"""

NAME = "gTRAN_IT"
TABLE = "gtran_it"
RECORD_KEYS = ("Interruptibles", "contracts")
ID_FIELD = "Id"
REQUIRED = ("Id", "InterruptibleId")
HEADER_KEYS = ("TspName", "TspDuns", "TspProp")
ALIASES = {
    "kqty": "itqtyk",                      # KQty            -> itqtyk
    "amendrptdate": "amendrptgdesc",       # AmendRptDate    -> amendrptgdesc
    "netdrateind": "ngtdrateind",          # NetdRateInd     -> ngtdrateind
    "netdrateinddesc": "ngtdrateinddesc",  # NetdRateIndDesc -> ngtdrateinddesc
}
