"""
interruptible / rates -- master capacity
========================================

Builds interruptible_rates_master_capacity, which feeds
final_rates_master_capacity in ../../final/rates/.

EMPTY: drop a module here with a @register-ed SilverTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_interruptible_rates.yml
    python run.py --group master_capacity/interruptible/rates

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
