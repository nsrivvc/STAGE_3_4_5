"""
silver_interruptible_core_dedup.py
==================================
Deduplicates bronze.gtran_it for the INTERRUPTIBLE feed.

Rows identical to ones already seen are dropped; new or changed rows pass
through to ammendments(p2). See ../dedup_base.py for how that comparison works.

Target: <DECOMP_SCHEMA>.interruptible_core_dedup
"""

from __future__ import annotations

from ..dedup_base import Deduplication
from .....core.registry import register


@register
class SilverInterruptibleCoreDedup(Deduplication):
    name = "silver_interruptible_core_dedup"
    table_name = "interruptible_core_dedup"
    feed = "interruptible"
    source_table = "gtran_it"
