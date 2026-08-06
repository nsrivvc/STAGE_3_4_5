"""
transformations package
========================
Auto-discovers every transformation module in this folder *and its subfolders*
so that simply *creating a file* (with a @register-ed class) makes it available
to the runner. No central list to maintain.

Transformations are grouped by pipeline stage, then by component:

    stage_3/    Silver staging: decompisition, standardization, deduplication,
                ammendments  (scaffolding only -- no code yet)
    stage_4/    rec_del_pairing, master_capacity

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

# walk_packages recurses into subpackages, so each phase folder is discovered
# without needing its own import boilerplate.
for _module in pkgutil.walk_packages(__path__, prefix=f"{__name__}."):
    importlib.import_module(_module.name)
