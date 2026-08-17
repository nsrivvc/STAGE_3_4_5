"""
coerce.py
=========
Tolerance for source payloads that deliver structure as *embedded JSON text*
instead of native JSON.

NatGasHub-style feeds are not consistent about this. The same logical field can
arrive either way, sometimes within a single posting:

    "rates": [ { "RateId": "FT-1-RES", ... } ]        <- native array
    "rates": "[{\"RateId\":\"FT-1-RES\", ... }]"      <- JSON *string*
    "KStatDesc": "Active"                             <- plain text
    "KStatDesc": "{\"code\":\"A\",\"desc\":\"Active\"}"  <- JSON *string*

Without this module the router iterates a string character-by-character and
`dict("[")` raises ValueError, aborting the whole payload.

Two rules
---------
1. `parse_embedded_json` only treats a string as JSON when it is delimited by
   {} or []. That guard matters: business values like "0.4500", "610778256" and
   "Active" are valid JSON scalars, and parsing them would silently retype
   source data (0.45 loses the trailing zero, and Bronze's promise is to land
   the source value verbatim). Object/array delimiters are unambiguous.
2. A string that *looks* like JSON but does not parse is returned untouched —
   malformed source text lands as-is in Bronze rather than failing the load.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List

_JSON_OPENERS = ("{", "[")
_JSON_CLOSERS = ("}", "]")


def dumps(value: Any) -> str:
    """Canonical compact JSON text (stable key order -> stable content hash)."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def parse_embedded_json(value: Any) -> Any:
    """Parse a string holding a JSON object/array; pass anything else through."""
    if not isinstance(value, str):
        return value

    text = value.strip()
    if len(text) < 2 or text[0] not in _JSON_OPENERS or text[-1] not in _JSON_CLOSERS:
        return value

    try:
        return json.loads(text)
    except ValueError:
        # Looks like JSON, isn't. Preserve the source text.
        return value


def as_record_list(value: Any) -> List[Dict[str, Any]]:
    """Normalise a child-array field into a list of record dicts.

    Accepts a native list, a single object, or either of those delivered as an
    embedded JSON string. Non-dict entries (and anything unusable) are dropped
    rather than crashing the run — the parent row's raw_payload still holds the
    original value verbatim, so nothing is lost.
    """
    value = parse_embedded_json(value)

    if value is None or value == "":
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [parsed for item in value
                if isinstance(parsed := parse_embedded_json(item), dict)]
    return []
