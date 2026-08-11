"""
stage_4 -- Rec-Del Pairing
==========================
Builds the curated Silver model on top of stage 3's staging tables.

    rec_del_pairing/   pair receipts to deliveries, then apply the term transform

One workflow per source feed -- (stage4)rec_del_pairing_<feed>.yml -- so the
feeds run and fail independently.

Master capacity used to live here; it moved to ../stage_5/ to match the stage
numbering the workflows use.

Folder name is `stage_4`, not `stage 4`, because these are Python packages and
the runner imports them by name.
"""
