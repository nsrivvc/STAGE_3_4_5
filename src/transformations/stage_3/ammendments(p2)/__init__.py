"""
ammendments (phase 2 of stage 3)
================================
Folds each contract's posting history into one current row.

A pipeline re-posts the same contract over time; AmendRptgDesc says whether a
posting is the original ("new"), a full restatement ("all data"), or a partial
update carrying only what changed ("changes only"). This phase resolves those
into the contract as it now stands.

    firm/           gtran_firm headers
    interruptibles/ gtran_it headers

HEADER-LEVEL ONLY: amendrptg/amendrptgdesc exist only on the contract header
tables, never on locations or rates. Those children skip this phase entirely
and go straight from deduplication(p1) to decompisition(p3).

The fold, and why it works the way it does, is documented in amend_base.py.
"""
