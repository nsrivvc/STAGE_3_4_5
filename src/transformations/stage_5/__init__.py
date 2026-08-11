"""
stage_5 -- Master Capacity
==========================
Folds every source feed into the unified master capacity model, then ties them
together into the three FINAL tables.

    master_capacity/<feed>/<grain>/   per-feed assembly
                                      feeds:  firm, interruptible, awards, ioc, index
                                      grains: core, locations, rates
    master_capacity/final/<grain>/    the cross-feed consolidation

Each of those 18 folders has its own workflow, named to match:

    (stage5)master_capacity_<feed>_<grain>.yml
    -> python run.py --group master_capacity/<feed>/<grain>

Workflows target folders rather than transformation names, so dropping a module
into one of these folders is all that's needed to make its workflow do work.

Folder name is `stage_5`, not `stage 5`, because these are Python packages
imported by name.
"""
