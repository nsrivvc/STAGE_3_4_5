"""
spec.py
=======
The shape of a feed definition. One `FeedDefinition` per JSON feed, each living
in its own module in this package -- firm.py, interruptible.py, awards.py,
index.py.

WHY THIS EXISTS
---------------
The four feeds used to be split across two shared dictionaries: BUSINESS_COLUMNS
in schemas.py and FEED_REGISTRY in router.py. Adding or changing a feed meant
editing both, in two different files, with nothing tying the halves together.
Now each feed is one module that owns everything about itself -- its table, its
envelope, its columns, its aliases -- and schemas.py / router.py assemble the
registry from whatever this package exports.

Adding a feed is: drop a module in here, list it in __init__.FEEDS. Nothing else.

ALIASES ARE THE POINT
---------------------
The same feed arrives from more than one producer with the same fields under
different names -- the mock fixtures use one spelling, the live NatGasHub export
another (`KQty` vs `KQtyK`, `NetdRateInd` vs `NgtdRateInd`, and an envelope of
`{"Firms": [...]}` rather than `{"feedType": ..., "contracts": [...]}`).

Rather than fork the schema or pre-process the file, a feed declares the
alternative spellings it accepts:

    records_keys  -- envelope keys that may hold the record list
    aliases       -- {alternative source key: canonical source key}

Both are matched case-insensitively, so a producer that also changes case costs
nothing. Anything still unrecognised is not lost: it stays in `raw_payload`.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Dict, List, Mapping, Sequence, Tuple


@dataclass(frozen=True)
class ChildSpec:
    """A nested array fanned out into its own Bronze table.

    Unused today -- every feed lands as ONE Bronze row per record, with nested
    locations/rates kept on the row (as JSON text columns and inside
    raw_payload) and exploded in Silver by stage 3. Kept because the router
    still supports it and a future feed may need it.
    """

    array_key: str
    table: str
    id_field: str
    required: Sequence[str] = ()
    inherit: Sequence[str] = ()


@dataclass(frozen=True)
class FeedDefinition:
    #: Canonical feed type, as it appears in a payload's `feedType`.
    feed_type: str

    #: Bronze table this feed lands in.
    table: str

    #: Envelope keys that may hold the record list, most canonical first.
    #: Matched case-insensitively. The first one found in the payload wins.
    records_keys: Tuple[str, ...]

    #: Source key used as `raw_record_id`.
    parent_id_field: str

    #: Keys a record must carry. A record missing one is still landed, flagged
    #: `ingestion_status = 'INVALID'` -- nothing is silently dropped.
    parent_required: Tuple[str, ...]

    #: Payload-level keys merged into every record so each Bronze row is
    #: self-describing (TSP fields declared once at the top of the payload).
    header_keys: Tuple[str, ...]

    #: (source_json_key, declared_type) per business column, in sheet order.
    #: The DB column is always source_key.lower(); the declared type is retained
    #: as documentation because Bronze lands every business column as TEXT.
    columns: List[Tuple[str, str]]

    #: {alternative source key: canonical source key}. Case-insensitive.
    aliases: Mapping[str, str] = field(default_factory=dict)

    #: Nested array sections carried on the row and exploded in Silver. Declared
    #: so a feed can state them once; stage 3 finds them case-insensitively.
    nested_sections: Tuple[str, ...] = ()

    children: Tuple[ChildSpec, ...] = ()

    # ------------------------------------------------------------------ views
    @property
    def db_columns(self) -> List[str]:
        """Business column names as they exist in Postgres."""
        return [src.lower() for src, _ in self.columns]

    @property
    def source_key_map(self) -> Dict[str, str]:
        """lowercased-source-key -> db column, including every alias.

        This is what the transformer matches incoming JSON keys against, which
        is why aliasing needs no code anywhere else: an aliased key simply
        resolves to the same column its canonical spelling would.
        """
        mapping = {src.lower(): src.lower() for src, _ in self.columns}
        for alt, canonical in self.aliases.items():
            mapping[alt.lower()] = canonical.lower()
        return mapping

    def records_from(self, payload: Mapping) -> object:
        """The record list out of `payload`, whichever envelope key it used."""
        lower = {str(k).lower(): v for k, v in payload.items()}
        for key in self.records_keys:
            if key.lower() in lower:
                return lower[key.lower()]
        return None

    def matches_envelope(self, payload: Mapping) -> bool:
        """True when this payload looks like this feed, with no `feedType`.

        Used only as a fallback: a live export that omits the envelope metadata
        is still identifiable by which record key it carries.
        """
        return self.records_from(payload) is not None
