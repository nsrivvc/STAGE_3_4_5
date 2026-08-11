"""
awards / rates -- master capacity
=================================

Builds awards_rates_master_capacity, which feeds
final_rates_master_capacity in ../../final/rates/.

EMPTY: drop a module here with a @register-ed SilverTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_awards_rates.yml
    python run.py --group master_capacity/awards/rates

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
