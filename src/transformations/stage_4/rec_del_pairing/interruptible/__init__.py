"""
interruptible -- rec-del pairing
=================================

Receipt/delivery pairing for the INTERRUPTIBLE (IT) feed.

Its own package so this feed's pairing rules can diverge from the
other's: override `pair_predicate_sql()` and `term_columns_sql()` on
the subclass here and it affects only interruptible. Shared mechanics stay in
../pairing_base.py.

Workflow:  (stage4)rec_del_pairing_interruptible.yml
           python run.py --group rec_del_pairing/interruptible
"""
