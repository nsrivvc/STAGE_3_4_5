"""
awards.py — capacity release awards: gAWD -> bronze.gawd.

No header keys: unlike firm and interruptible, an awards payload declares no
TSP at the top. Every award carries its own TSP fields, so there is nothing to
copy down.

No aliases either -- the award field names already match their columns
case-insensitively. Awards do carry nested Locations/Rates, which land as JSON
text on the row for stage 3 to fan out.
"""

NAME = "gAWD"
TABLE = "gawd"
#: Pipeline freshness marker (fresh -> processed). Named record_status here
#: because gawd already has a business column "status" -- the award's own
#: status from the JSON -- which stage 3 reads and must not be overwritten.
STATUS_COLUMN = "record_status"
FILE_WORDS = ("award", "awards")
RECORD_KEYS = ("Awards", "awards")
ID_FIELD = "Id"
REQUIRED = ("Id", "AwardNumber")
HEADER_KEYS = ()
ALIASES = {}
