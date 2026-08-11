"""
silver_firm_rec_del_pair.py
===========================
Rec-del pairing for FIRM transport.

Source: the firm locations table produced by the decomposition phase.
All pairing and term logic lives in the shared base -- see pairing_base.py in this package,
where the two `SPEC:` hooks are waiting for the business rules.

TODO(confirm): `locations_table` and the `column_map` overrides below are set to
the expected decomposition output. Verify both once that phase lands.
"""

from __future__ import annotations

from ..pairing_base import RecDelPairingTransformation
from .....core.registry import register


@register
class SilverFirmRecDelPair(RecDelPairingTransformation):
    name = "silver_firm_rec_del_pair"
    table_name = "firm_rec_del_pair"
    entity = "firm"
    locations_table = "firm_locations"

    column_map = {
        **RecDelPairingTransformation.column_map,
        "contract_key": "firmid",
        "loc_qty": "kqtyloc",
    }
