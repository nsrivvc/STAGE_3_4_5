"""
rec_del_pairing
===============
Receipt/delivery pairing: turns each type's flat locations table (from the
decomposition phase) into one row per receipt->delivery path, then hangs the
term transform off each paired row.

    pairing_base.py                    shared logic + the two `SPEC:` hooks
    silver_firm_rec_del_pair.py        firm
    silver_interruptible_rec_del_pair.py   interruptible
    silver_awards_rec_del_pair.py      awards          (dormant: no feed yet)
    silver_ioc_rec_del_pair.py         ioc             (dormant: no feed yet)

The parent package discovers these automatically -- no imports needed here.
"""
