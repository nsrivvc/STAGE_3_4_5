"""
deduplication (phase 1 of stage 3)
==================================
First thing that happens to a freshly ingested batch: compare it against
everything already seen and drop the rows that are byte-identical, so only
new or changed data flows on to ammendments(p2), decompisition(p3) and
standardization(p4).

One module per Bronze table, since each is deduplicated independently:

    firms/          gtran_firm, gtran_loc, gtran_rates
    interruptibles/ gtran_it, gtran_it_loc, gtran_it_rates
    awards/         gawd

Shared mechanics -- and the reasoning behind using hash_key -- are in
dedup_base.py.
"""
