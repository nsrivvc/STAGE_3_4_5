"""
final
=====
The three FINAL master capacity tables — each ties all four source feeds into
one consolidated table for its grain.

    final_base.py   shared UNION-across-feeds logic + the `SPEC:` hooks
    core/           final_core_master_capacity
    locations/      final_locations_master_capacity
    rates/          final_rates_master_capacity

Each grain has its own module with its own column model, natural key and dedupe
rule, so their logic can diverge freely.
"""
