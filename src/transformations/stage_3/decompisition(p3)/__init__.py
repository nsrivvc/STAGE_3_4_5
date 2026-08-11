"""
decompisition (phase 3 of stage 3)
==================================
Splits each feed into typed staging tables in DECOMP_SCHEMA (default
`silver_staging`) -- which is exactly where stage 4 rec-del pairing reads from.

    <feed>/locations/   -> <feed>_locations   IMPLEMENTED
    <feed>/core/        -> <feed>_core        schema pending
    <feed>/rates/       -> <feed>_rates       schema pending

Shared mechanics in decomp_base.py.

PHASE ORDER: the folder suffixes give it -- deduplication(p1), ammendments(p2),
decompisition(p3), standardization(p4). Decomposition therefore ought to read
the ammendments output, but p1/p2 have no code and no output tables yet, so it
reads Bronze directly for now. `source_table` on each subclass is the one line
to change when they land.

NOTE ON THE FOLDER NAMES: `(p3)` is not a valid Python identifier, so these
packages can only be imported the way the runner does it -- importlib by name
string, plus relative imports inside. Never write a literal
`import ...decompisition(p3)...` statement; it is a syntax error.
"""
