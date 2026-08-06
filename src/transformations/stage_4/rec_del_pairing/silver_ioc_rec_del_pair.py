"""
silver_ioc_rec_del_pair.py
==========================
Rec-del pairing for IOC.

Source: the IOC locations table produced by the decomposition phase.
All pairing and term logic lives in the shared base -- see pairing_base.py in this package,
where the two `SPEC:` hooks are waiting for the business rules.

DORMANT: no IOC feed exists yet -- there is no IOC table in Bronze and no IOC
feed in the ingestion router. The runner will report this transformation as
skipped ("missing sources") until the decomposition phase produces
`ioc_locations`, at which point it starts working with no code change.

TODO(confirm): `locations_table` and the `column_map` overrides below are
guesses modelled on the firm feed, since no IOC data exists to check against.
Verify both before the first real run.
"""

from __future__ import annotations

from .pairing_base import RecDelPairingTransformation
from ....core.registry import register


@register
class SilverIocRecDelPair(RecDelPairingTransformation):
    name = "silver_ioc_rec_del_pair"
    table_name = "ioc_rec_del_pair"
    entity = "ioc"
    locations_table = "ioc_locations"

    column_map = {
        **RecDelPairingTransformation.column_map,
        "contract_key": "iocid",     # TODO(confirm): IOC contract key
        "loc_qty": "iocqtyloc",      # TODO(confirm): IOC location quantity
    }
