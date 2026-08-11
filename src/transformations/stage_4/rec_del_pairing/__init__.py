"""
rec_del_pairing
===============
Receipt/delivery pairing: turns a feed's flat locations table (from the
decomposition phase) into one row per receipt->delivery path, then hangs the
term transform off each paired row.

PAIRING APPLIES TO FIRM AND INTERRUPTIBLE ONLY. Awards and IOC have no
receipt/delivery path structure to pair, so they are not represented here and
have no stage-4 workflow. They pick up again at stage 5.

    pairing_base.py           shared mechanics + the two `SPEC:` hooks
    firm/                     firm pairing
    interruptible/            interruptible (IT) pairing

Each feed is its own package so their rules can diverge -- override
`pair_predicate_sql()` or `term_columns_sql()` on one subclass and the other is
untouched. The parent package discovers these automatically.
"""
