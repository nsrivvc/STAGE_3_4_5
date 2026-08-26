"""
ioc.py — index of customers: gINDEX -> bronze.gindex.

The simplest of the four. The rows are flat: no nested arrays to carry as JSON
text, no header fields to copy down, no re-spelled fields. A record is
identified by ID and must name the Pipe it belongs to.

Called IOC in the workflows and gINDEX in the payloads; both names reach it
(--feed ioc, --feed index, --feed gINDEX).
"""

NAME = "gINDEX"
TABLE = "gindex"
#: IOC skips the staging phases, so it carries no freshness marker.
STATUS_COLUMN = None
FILE_WORDS = ("ioc", "index")
RECORD_KEYS = ("Records", "records", "IndexOfCustomers")
ID_FIELD = "ID"
REQUIRED = ("ID", "Pipe")
HEADER_KEYS = ()
ALIASES = {}
