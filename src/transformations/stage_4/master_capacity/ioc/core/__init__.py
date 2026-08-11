"""
ioc / core -- master capacity
=============================

Builds ioc_core_master_capacity, which feeds
final_core_master_capacity in ../../final/core/.

EMPTY: drop a module here with a @register-ed SilverTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_ioc_core.yml
    python run.py --group master_capacity/ioc/core

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
