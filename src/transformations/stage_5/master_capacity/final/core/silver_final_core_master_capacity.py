"""
silver_final_core_master_capacity.py
====================================
FINAL Core — Master Capacity. Consolidates all four feeds' core master capacity
tables into one.

The column set below mirrors the model that already exists in the database as
`public.final_core_master_capacity` (27 columns, 20 rows), converted to the
snake_case this repo uses everywhere else.

TWO THINGS TO SETTLE (see the note in ../../__init__.py):
  * That existing table lives in `public` with PascalCase columns. This writes
    to the Silver schema instead, so it does NOT overwrite those 20 rows. If the
    dashboard should read what this produces, either point it at
    silver.final_core_master_capacity or change the target here.
  * `natural_key` is set to (source_type, ngh_contract_id) — one row per
    contract per feed. Change it if a contract can legitimately appear more than
    once within a single feed.
"""

from __future__ import annotations

from ..final_base import FinalMasterCapacityTransformation
from ...models import CORE_COLUMNS
from ......core.registry import register


@register
class SilverFinalCoreMasterCapacity(FinalMasterCapacityTransformation):
    name = "silver_final_core_master_capacity"
    table_name = "final_core_master_capacity"
    grain = "core"

    # Shared with the per-feed transformations so the UNION can never break
    # on a column mismatch. Single definition lives in ../../models.py.
    columns = CORE_COLUMNS

    # SPEC: one row per contract per feed. Revisit if a feed can restate a
    # contract (amendments may make this a versioned key).
    natural_key = ("source_type", "ngh_contract_id")

    dedupe_note = (
        "one row per contract per feed; a contract present in two feeds yields "
        "two rows, told apart by source_type"
    )

    # Mirrors public.final_core_master_capacity, snake_cased.
