"""
firm / core -- master capacity
==============================

Builds firm_core_master_capacity, which feeds
final_core_master_capacity in ../../final/core/.

EMPTY: drop a module here with a @register-ed SilverTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_firm_core.yml
    python run.py --group master_capacity/firm/core

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
