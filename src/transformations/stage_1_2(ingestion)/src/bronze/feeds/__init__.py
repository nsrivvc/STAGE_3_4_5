"""
feeds
=====
One module per JSON feed. Each owns EVERYTHING about that feed: its Bronze
table, the envelope(s) it arrives in, its business columns, the alternative
field spellings it accepts, and its nested sections.

    firm.py           gTRAN_FIRM  -> bronze.gtran_firm
    interruptible.py  gTRAN_IT    -> bronze.gtran_it
    awards.py         gAWD        -> bronze.gawd
    index.py          gINDEX      -> bronze.gindex

`schemas.py` and `router.py` build their registries from FEEDS below, so adding
a feed is: write the module, add it to FEEDS. Nothing else changes -- the DDL,
the JSON->column mapping, the routing and the validator all follow.
"""

from __future__ import annotations

from typing import Dict, Tuple

from . import awards, firm, index, interruptible
from .spec import ChildSpec, FeedDefinition

#: Every feed the ingestion knows about. Order is the order they appear in
#: generated DDL and in `--list`-style output.
FEEDS: Tuple[FeedDefinition, ...] = (
    firm.FEED,
    interruptible.FEED,
    awards.FEED,
    index.FEED,
)

#: feed_type -> definition ("gTRAN_FIRM" -> ...)
BY_FEED_TYPE: Dict[str, FeedDefinition] = {f.feed_type: f for f in FEEDS}

#: bronze table -> definition ("gtran_firm" -> ...)
BY_TABLE: Dict[str, FeedDefinition] = {f.table: f for f in FEEDS}


def feed_types() -> Tuple[str, ...]:
    return tuple(BY_FEED_TYPE)


def tables() -> Tuple[str, ...]:
    return tuple(BY_TABLE)


def for_table(table: str) -> FeedDefinition:
    try:
        return BY_TABLE[table]
    except KeyError:
        raise KeyError(
            f"Unknown Bronze table {table!r}. Known: {', '.join(BY_TABLE)}"
        ) from None


def for_feed_type(feed_type: str) -> FeedDefinition:
    try:
        return BY_FEED_TYPE[feed_type]
    except KeyError:
        raise KeyError(
            f"Unknown feed type {feed_type!r}. Known: {', '.join(BY_FEED_TYPE)}"
        ) from None


__all__ = [
    "FEEDS", "BY_FEED_TYPE", "BY_TABLE", "FeedDefinition", "ChildSpec",
    "feed_types", "tables", "for_table", "for_feed_type",
]
