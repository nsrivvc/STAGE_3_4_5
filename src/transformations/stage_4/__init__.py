"""
stage_4 -- Pairing and Master Capacity
======================================
Builds the curated Silver model on top of stage 3's staging tables.

    rec_del_pairing/   pair receipts to deliveries, then apply the term transform
    master_capacity/   fold each type into the unified master capacity model

Each has its own scheduled workflow (.github/workflows/rec_del_pairing.yml and
master_capacity.yml), so they run and fail independently.

Folder name is `stage_4`, not `stage 4`, because these are Python packages and
the runner imports them by name.
"""
