"""
silver_interruptible_rates_dedup.py
===================================
Deduplicates bronze.gtran_it_rates for the INTERRUPTIBLE feed.

Rows identical to ones already seen are dropped; new or changed rows pass
through to ammendments(p2). See ../dedup_base.py for how that comparison works.

Target: <DECOMP_SCHEMA>.interruptible_rates_dedup
"""

from __future__ import annotations

from ..dedup_base import Deduplication
from .....core.registry import register


@register
class SilverInterruptibleRatesDedup(Deduplication):
    name = "silver_interruptible_rates_dedup"
    table_name = "interruptible_rates_dedup"
    feed = "interruptible"
    source_table = "gtran_it_rates"
