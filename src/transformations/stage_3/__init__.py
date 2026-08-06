"""
stage_3 -- Silver Staging (Bronze -> Silver)
============================================
Takes the raw Bronze tables and produces clean, per-type staging tables.

    decompisition/    split each feed into core / locations / rates per type
    standardization/  normalize codes, names, units and types
    deduplication/    collapse re-ingested and amended duplicates
    ammendments/      apply amendment records to the standing record

NO CODE YET: every folder here is scaffolding with an empty logic.txt and
per-type subdirectories. Stage 4 (rec-del pairing) reads this stage's locations
tables, so those are the first thing worth filling in.

Folder name is `stage_3`, not `stage 3`, because these are Python packages and
the runner imports them by name.
"""
