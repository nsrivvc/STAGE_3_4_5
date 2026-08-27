"""
sources.py
==========
Canonical names for the JSON source feeds, and the alias table that maps every
spelling seen across the feeds, the dashboard, the CLI (`--source`) and the
Bronze table names onto them. Used by the runner's source filtering and by
shipper_scope's feed matching.
"""

from __future__ import annotations

from typing import Optional

from ..logging_config import get_logger

log = get_logger(__name__)

FIRM = "firm"
INTERRUPTIBLE = "interruptible"
AWARDS = "awards"
IOC = "ioc"
INDEX = "index"

#: The source feeds, in pipeline order. `index` is the gindex feed
#: (bronze.gindex), which carries contract index records rather than a transport
#: type; it gets its own name for the same reason as the others.
SOURCES = (FIRM, INTERRUPTIBLE, AWARDS, IOC, INDEX)

#: Bucket for rows that span feeds or never declared one.
COMBINED = "_combined"

#: Spellings seen across the feeds, the dashboard and the Bronze table names.
_SOURCE_ALIASES = {
    "firm": FIRM,
    "firms": FIRM,
    "gtran_firm": FIRM,
    "it": INTERRUPTIBLE,
    "interruptible": INTERRUPTIBLE,
    "interruptibles": INTERRUPTIBLE,
    "gtran_it": INTERRUPTIBLE,
    "award": AWARDS,
    "awards": AWARDS,
    "ioc": IOC,
    "index": INDEX,
    "gindex": INDEX,
    # Cross-feed output (the master capacity finals). Spelled several ways so
    # `--source final` works as naturally as `--source _combined`.
    "final": COMBINED,
    "finals": COMBINED,
    "combined": COMBINED,
    COMBINED: COMBINED,
}


def normalize_source(source: Optional[str]) -> str:
    """Map any known spelling of a feed to its canonical name.

    Never raises: an unrecognised or missing source becomes COMBINED and is
    logged, because a labelling mistake should not fail a run that otherwise
    succeeded.
    """
    if not source:
        return COMBINED
    key = str(source).strip().lower()
    resolved = _SOURCE_ALIASES.get(key)
    if resolved is None:
        log.warning("unrecognised source %r — filing under %s", source, COMBINED)
        return COMBINED
    return resolved
