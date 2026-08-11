"""
awards / locations -- master capacity
=====================================

Builds awards_locations_master_capacity, which feeds
final_locations_master_capacity in ../../final/locations/.

EMPTY: drop a module here with a @register-ed SilverTransformation
subclass. Its workflow already exists and targets this exact folder:
    (stage5)master_capacity_awards_locations.yml
    python run.py --group master_capacity/awards/locations

See ../../final/final_base.py for how a family of near-identical
transformations shares one base class.
"""
