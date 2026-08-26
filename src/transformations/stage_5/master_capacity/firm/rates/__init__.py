"""
firm / rates -- master capacity
===============================

Builds firm_rates_master_capacity, which feeds
final_rates_master_capacity in ../../final/rates/.

EMPTY: drop a module here with a @register-ed PipelineTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_firm_rates.yml
    python run.py --group master_capacity/firm/rates

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
