"""
silver_interruptible_amended.py
===============================
Resolves the INTERRUPTIBLE feed's contract posting history into one CURRENT
row per contract, keyed on (interruptibleid, tspduns), with superseded
versions kept as Void (see amend_base.py for the whole flow).

No "core" in the name: the contract is still WHOLE here -- the core /
locations / rates split does not happen until decompisition(p3).

Reads the deduplication(p1) output `interruptible_dedup` (fresh rows only);
writes `<DECOMP_SCHEMA>.interruptible_amended`, which decompisition(p3)
reads filtered to amend_version_status = 'Current'. Flips the consumed rows'
freshness marker to 'processed' in interruptible_dedup and bronze.gtran_it.

The column list below is the full 52-column shape of bronze.gtran_it
(everything except the 'status' freshness marker, which is bookkeeping, not
data). It is explicit rather than introspected so the SQL can be generated
without a database connection (`--show-sql` works offline). If the Bronze
schema gains a column, add it here or it will not be carried through the fold.
"""

from __future__ import annotations

from ..amend_base import ContractAmendments
from .....core.registry import register


@register
class SilverInterruptibleAmended(ContractAmendments):
    name = "silver_interruptible_amended"
    table_name = "interruptible_amended"
    feed = "interruptible"
    source_table = "interruptible_dedup"
    raw_table = "gtran_it"
    contract_id_col = "interruptibleid"

    columns = [
        "bronze_row_id",
        "id",
        "tspname",
        "tspduns",
        "tspprop",
        "posteddatetime",
        "interruptibleid",
        "cycle",
        "amendrptg",
        "amendrptgdesc",
        "kholdername",
        "kholder",
        "kholderprop",
        "svcreqk",
        "ratesch",
        "itqtyk",
        "kstat",
        "kstatdesc",
        "kbegdatetime",
        "kenddatetime",
        "ngtdrateind",
        "ngtdrateinddesc",
        "pkgid",
        "kroll",
        "krolldesc",
        "affil",
        "affildesc",
        "termsnotes",
        "createddatetime",
        "reclocs",
        "dellocs",
        "maxratechgd",
        "maxtrfrate",
        "otherrates",
        "otherratesdescription",
        "otherratesbasis",
        "dealtype",
        "locations",
        "rates",
        "term",
        "reczones",
        "delzones",
        "raw_record_id",
        "hash_key",
        "pipeline_run_id",
        "source_system",
        "source_api",
        "source_file_name",
        "ingestion_timestamp",
        "updated_ts",
        "ingestion_status",
        "raw_payload",
    ]
