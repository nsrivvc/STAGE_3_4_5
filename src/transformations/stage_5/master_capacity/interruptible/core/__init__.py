"""
interruptible / core -- master capacity
=======================================

Builds interruptible_core_master_capacity, which feeds
final_core_master_capacity in ../../final/core/.

EMPTY: drop a module here with a @register-ed PipelineTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_interruptible_core.yml
    python run.py --group master_capacity/interruptible/core

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
