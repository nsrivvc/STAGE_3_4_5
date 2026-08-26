"""
silver_firm_core_amended.py
===========================
Resolves the FIRM feed's contract posting history into one current row per
contract, keyed on (firmid, tspduns).

Reads the deduplication(p1) output `firm_dedup`; writes
`<DECOMP_SCHEMA>.firm_core_amended`, which decompisition(p3) can then use as the
authoritative contract header.

The column list below is the full 53-column shape of bronze.gtran_firm. It is
explicit rather than introspected so the SQL can be generated without a database
connection (`--show-sql` works offline). If the Bronze schema gains a column,
add it here or it will not be carried through the fold.
"""

from __future__ import annotations

from ..amend_base import ContractAmendments
from .....core.registry import register


@register
class SilverFirmCoreAmended(ContractAmendments):
    name = "silver_firm_core_amended"
    table_name = "firm_core_amended"
    feed = "firm"
    source_table = "firm_dedup"
    contract_id_col = "firmid"

    columns = [
        "bronze_row_id",
        "id",
        "tspname",
        "tspduns",
        "tspprop",
        "posteddatetime",
        "firmid",
        "cycle",
        "amendrptg",
        "amendrptgdesc",
        "kholdername",
        "kholder",
        "kholderprop",
        "svcreqk",
        "ratesch",
        "kqtyk",
        "kstat",
        "kstatdesc",
        "kbegdatetime",
        "kenddatetime",
        "kendind",
        "ngtdrateind",
        "ngtdrateinddesc",
        "pkgid",
        "kroll",
        "krolldesc",
        "affil",
        "affildesc",
        "captype",
        "captypename",
        "captypeloc",
        "captypelocdesc",
        "osid",
        "rte",
        "termsnotes",
        "createddatetime",
        "reclocs",
        "dellocs",
        "maxratechgd",
        "maxtrfrate",
        "otherrates",
        "otherratesdescription",
        "otherratesbasis",
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
