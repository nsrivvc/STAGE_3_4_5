"""
silver_awards_core_dedup.py
===========================
Deduplicates bronze.gawd for the AWARDS feed.

Rows identical to ones already seen are dropped; new or changed rows pass
through to ammendments(p2). See ../dedup_base.py for how that comparison works.

Target: <DECOMP_SCHEMA>.awards_core_dedup
"""

from __future__ import annotations

from ..dedup_base import Deduplication
from .....core.registry import register


@register
class SilverAwardsCoreDedup(Deduplication):
    name = "silver_awards_core_dedup"
    table_name = "awards_core_dedup"
    feed = "awards"
    source_table = "gawd"
