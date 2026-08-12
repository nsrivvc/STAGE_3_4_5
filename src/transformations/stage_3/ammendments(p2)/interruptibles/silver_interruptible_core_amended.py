"""
silver_interruptible_core_amended.py
====================================
Resolves the INTERRUPTIBLE feed's contract posting history into one current row per
contract, keyed on (interruptibleid, tspduns).

Reads the deduplication(p1) output `interruptible_core_dedup`; writes
`<DECOMP_SCHEMA>.interruptible_core_amended`, which decompisition(p3) can then use as the
authoritative contract header.

The column list below is the full 47-column shape of bronze.gtran_it. It is
explicit rather than introspected so the SQL can be generated without a database
connection (`--show-sql` works offline). If the Bronze schema gains a column,
add it here or it will not be carried through the fold.
"""

from __future__ import annotations

from ..amend_base import ContractAmendments
from .....core.registry import register


@register
class SilverInterruptibleCoreAmended(ContractAmendments):
    name = "silver_interruptible_core_amended"
    table_name = "interruptible_core_amended"
    feed = "interruptible"
    source_table = "interruptible_core_dedup"
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
