"""
deduplication (phase 1 of stage 3)
==================================
Drops the rows we have already seen, so only new or changed data flows on to
ammendments(p2), decompisition(p3) and standardization(p4).

It is one file: dedup.py. One class holds the rule, and the three feeds under
it are four declarations each.
"""
