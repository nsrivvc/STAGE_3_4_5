"""
silver_awards_rec_del_pair.py
=============================
Rec-del pairing for AWARDS.

Source: the awards locations table produced by the decomposition phase.
All pairing and term logic lives in the shared base -- see ../pairing_base.py,
where the two `SPEC:` hooks are waiting for the business rules.

DORMANT: no awards feed exists yet -- there is no awards table in Bronze and no
awards feed in the ingestion router, so decomposition produces no
`awards_locations`. The runner reports this as skipped ("missing sources") until
that lands, then it starts working with no code change.

TODO(confirm): `locations_table` and the `column_map` overrides below are guesses
modelled on the firm feed, since no awards data exists to check against. Verify
both before the first real run.
"""

from __future__ import annotations

from ..pairing_base import RecDelPairingTransformation
from .....core.registry import register


@register
class SilverAwardsRecDelPair(RecDelPairingTransformation):
    name = "silver_awards_rec_del_pair"
    table_name = "awards_rec_del_pair"
    entity = "awards"
    locations_table = "awards_locations"

    column_map = {
        **RecDelPairingTransformation.column_map,
        "contract_key": "awardid",   # TODO(confirm): awards contract key
        "loc_qty": "awardqtyloc",    # TODO(confirm): awards location quantity
    }
