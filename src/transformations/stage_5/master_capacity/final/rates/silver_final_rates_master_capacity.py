"""
silver_final_rates_master_capacity.py
=====================================
FINAL Rates — Master Capacity. Consolidates all four feeds' rate master capacity
tables into one.

NO EXISTING TARGET TO MIRROR: there is no `final_rates_master_capacity` table in
the database yet, so the column set below is a SPEC placeholder built from the
rate fields this pipeline already handles (bronze.gtran_rates and
silver.firm_transport_rate). Replace it with the real model when it's settled —
the DDL and the UNION both follow from this list.
"""

from __future__ import annotations

from ..final_base import FinalMasterCapacityTransformation
from ......core.registry import register


@register
class SilverFinalRatesMasterCapacity(FinalMasterCapacityTransformation):
    name = "silver_final_rates_master_capacity"
    table_name = "final_rates_master_capacity"
    grain = "rates"

    # SPEC: one row per contract per rate record per feed.
    natural_key = ("source_type", "ngh_contract_id", "rate_unique_id")

    dedupe_note = (
        "one row per contract/rate per feed; seasonal rates may need the season "
        "window in the key rather than a single row per rate_unique_id"
    )

    # SPEC: placeholder model — no real target table exists yet.
    columns = [
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
