"""
silver_firm_core_dedup.py
=========================
Deduplicates bronze.gtran_firm for the FIRM feed.

Rows identical to ones already seen are dropped; new or changed rows pass
through to ammendments(p2). See ../dedup_base.py for how that comparison works.

Target: <DECOMP_SCHEMA>.firm_core_dedup
"""

from __future__ import annotations

from ..dedup_base import Deduplication
from .....core.registry import register


@register
class SilverFirmCoreDedup(Deduplication):
    name = "silver_firm_core_dedup"
    table_name = "firm_core_dedup"
    feed = "firm"
    source_table = "gtran_firm"
