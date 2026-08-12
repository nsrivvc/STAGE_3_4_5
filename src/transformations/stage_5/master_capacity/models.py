"""
models.py
=========
The master capacity column model, defined once.

Both sides of stage 5 depend on these lists agreeing exactly:

    <feed>/<grain>/    maps a feed's stage-3 output onto the model
    final/<grain>/     UNIONs every feed's table into one

A UNION only works if every input has the same columns in the same order, so if
these lived in each subclass they could silently drift and the finals would break
at run time. They live here instead, and both sides import them.

CORE mirrors `public.final_core_master_capacity` (27 columns), snake_cased.
LOCATIONS and RATES have no existing table to mirror -- they are SPEC models
built from the fields this pipeline already carries, and should be replaced when
the real ones are agreed.
"""

from __future__ import annotations

from typing import List, Tuple

Column = Tuple[str, str]

#: Mirrors public.final_core_master_capacity, snake_cased.
CORE_COLUMNS: List[Column] = [
    ("ngh_contract_id", "TEXT"),
    ("pipeline_duns", "TEXT"),
    ("pipeline_name", "TEXT"),
    ("contract_number", "TEXT"),
    ("award_number", "TEXT"),
    ("offer_number", "TEXT"),
    ("bid_number", "TEXT"),
    ("releaser_contract_number", "TEXT"),
    ("posted_date", "TIMESTAMPTZ"),
    ("begin_date", "TIMESTAMPTZ"),
    ("end_date", "TIMESTAMPTZ"),
    ("contract_quantity", "NUMERIC"),
    ("rate_schedule", "TEXT"),
    ("contract_holder", "TEXT"),
    ("contract_holder_duns", "TEXT"),
    ("releaser_name", "TEXT"),
    ("releaser_duns", "TEXT"),
    # term fields -- what the rec-del term transform ultimately feeds
    ("evergreen", "TEXT"),
    ("notice_period_days", "INTEGER"),
    ("calculated_end_date", "TIMESTAMPTZ"),
    ("replacement_shipper_role_indicator", "TEXT"),
    ("term_notes", "TEXT"),
    ("contract_type", "TEXT"),
    ("created_date", "TIMESTAMPTZ"),
    ("update_date", "TIMESTAMPTZ"),
    ("source", "TEXT"),
]

#: SPEC: no real target table exists yet.
LOCATIONS_COLUMNS: List[Column] = [
    ("ngh_contract_id", "TEXT"),
    ("pipeline_duns", "TEXT"),
    ("pipeline_name", "TEXT"),
    ("contract_number", "TEXT"),
    ("loc_code", "TEXT"),
    ("loc_name", "TEXT"),
    ("loc_zone", "TEXT"),
    ("loc_purpose", "TEXT"),
    ("loc_quantity_type", "TEXT"),
    ("loc_quantity_dth", "NUMERIC"),
    ("begin_date", "TIMESTAMPTZ"),
    ("end_date", "TIMESTAMPTZ"),
    ("posted_date", "TIMESTAMPTZ"),
    ("created_date", "TIMESTAMPTZ"),
    ("update_date", "TIMESTAMPTZ"),
    ("source", "TEXT"),
]

#: SPEC: no real target table exists yet.
RATES_COLUMNS: List[Column] = [
    ("ngh_contract_id", "TEXT"),
    ("pipeline_duns", "TEXT"),
    ("pipeline_name", "TEXT"),
    ("contract_number", "TEXT"),
    ("rate_unique_id", "TEXT"),
    ("rate_id", "TEXT"),
    ("rate_schedule", "TEXT"),
    ("rate_form_type", "TEXT"),
    ("rate_form_type_desc", "TEXT"),
    ("receipt_loc_code", "TEXT"),
    ("delivery_loc_code", "TEXT"),
    ("rate_charged", "NUMERIC"),
    ("max_tariff_rate", "NUMERIC"),
    ("total_surcharge", "NUMERIC"),
    ("all_in_rate", "NUMERIC"),
    ("is_negotiated_rate", "BOOLEAN"),
    ("is_market_based_rate", "BOOLEAN"),
    ("season_start_date", "DATE"),
    ("season_end_date", "DATE"),
    ("begin_date", "TIMESTAMPTZ"),
    ("end_date", "TIMESTAMPTZ"),
    ("posted_date", "TIMESTAMPTZ"),
    ("created_date", "TIMESTAMPTZ"),
    ("update_date", "TIMESTAMPTZ"),
    ("source", "TEXT"),
]

COLUMNS_BY_GRAIN = {
    "core": CORE_COLUMNS,
    "locations": LOCATIONS_COLUMNS,
    "rates": RATES_COLUMNS,
}

#: Natural key per grain, used by both the per-feed tables and the finals.
NATURAL_KEY_BY_GRAIN = {
    "core": ("ngh_contract_id",),
    "locations": ("ngh_contract_id", "loc_code", "loc_purpose"),
    "rates": ("ngh_contract_id", "rate_unique_id"),
}
