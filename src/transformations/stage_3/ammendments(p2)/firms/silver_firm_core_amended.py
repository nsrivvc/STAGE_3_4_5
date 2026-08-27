"""
silver_firm_core_amended.py
===========================
Resolves the FIRM feed's contract posting history into one CURRENT row per
contract, keyed on (firmid, tspduns), with superseded versions kept as Void
(see amend_base.py for the whole flow).

Reads the deduplication(p1) output `firm_dedup` (fresh rows only); writes
`<DECOMP_SCHEMA>.firm_core_amended`, which decompisition(p3) reads filtered to
version_status = 'Current'. Flips the consumed rows' freshness marker to
'processed' in firm_dedup and bronze.gtran_firm.

The column list below is the full 58-column shape of bronze.gtran_firm
(everything except the 'status' freshness marker, which is bookkeeping, not
data). It is explicit rather than introspected so the SQL can be generated
without a database connection (`--show-sql` works offline). If the Bronze
schema gains a column, add it here or it will not be carried through the fold.
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
    raw_table = "gtran_firm"
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
