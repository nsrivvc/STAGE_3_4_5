"""
deduplication (phase 1 of stage 3)
==================================
First thing that happens to a freshly ingested batch: compare it against
everything already seen and drop the rows that are byte-identical, so only
new or changed data flows on to ammendments(p2), decompisition(p3) and
standardization(p4).

One module per grain. The core grain deduplicates its Bronze table row-for-row;
the locations and rates grains have no Bronze table of their own -- ingestion
nests them as JSON arrays inside the raw feed table -- so their modules explode
the nested arrays first, one row per element, then deduplicate:

    firms/          gtran_firm (core rows + nested locations / rates)
    interruptibles/ gtran_it   (core rows + nested locations / rates)
    awards/         gawd

Shared mechanics -- and the reasoning behind using hash_key -- are in
dedup_base.py (Deduplication for whole rows, NestedArrayDeduplication for the
exploded grains).
"""
