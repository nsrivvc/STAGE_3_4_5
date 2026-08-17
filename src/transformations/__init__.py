"""
transformations package
========================
Auto-discovers every transformation module in this folder *and its subfolders*
so that simply *creating a file* (with a @register-ed class) makes it available
to the runner. No central list to maintain.

Transformations are grouped by pipeline stage, then by component:

    stage_1_2(ingestion)/   the stage 1-2 subproject: mock NatGasHub API
                            (stage 1, src/mock_api) and JSON -> Bronze
                            ingestion (stage 2, src/bronze). NOT part of
                            discovery -- see the skip below.
    stage_3/    Silver staging: decompisition, standardization, deduplication,
                ammendments
    stage_4/    rec_del_pairing
    stage_5/    master_capacity

Folders are `stage_3` / `stage_4` rather than "stage 3" because they are Python
packages imported by name.

A file sitting directly in this folder works too (see
silver_firm_transport_rate.py). Shared helpers inside a subfolder are fine --
they get imported but register nothing unless decorated with @register.

`run.py --group` selects by folder at any depth: `--group stage_4` runs the whole
stage, `--group rec_del_pairing` runs just that component.
"""

from __future__ import annotations

import importlib
import pkgutil

#: Subfolders that live here for pipeline-layout uniformity but are their own
#: runtime, not transformation modules. The stage 1-2 ingestion subproject has
#: its own dependencies (psycopg 3, fastapi/uvicorn) that are NOT installed in
#: the stage 3-5 environments, so importing it would crash every run. It
#: registers nothing, so skipping it loses nothing.
_NOT_TRANSFORMATIONS = {"stage_1_2(ingestion)"}

# Two-level walk instead of one flat walk_packages over __path__: the top level
# is filtered by _NOT_TRANSFORMATIONS, then each surviving subpackage is walked
# recursively. walk_packages imports packages itself as it recurses, so the
# skipped subtree must never be handed to it at all.
for _finder, _name, _ispkg in pkgutil.iter_modules(__path__):
    if _name in _NOT_TRANSFORMATIONS:
        continue
    _full = f"{__name__}.{_name}"
    _pkg = importlib.import_module(_full)
    if _ispkg:
        for _module in pkgutil.walk_packages(_pkg.__path__, prefix=f"{_full}."):
            importlib.import_module(_module.name)
