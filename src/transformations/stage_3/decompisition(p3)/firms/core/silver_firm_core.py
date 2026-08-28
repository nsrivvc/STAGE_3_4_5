"""
silver_firm_core.py
===================
Decomposes the FIRM feed's core into `<DECOMP_SCHEMA>.firm_core`.

Source: `firm_amended` (ammendments(p2) output -- the folded contract
        header). That table is a VERSION HISTORY, so `source_where` narrows the
        read to each contract's Current row; the Void versions stay behind.
Key:    (firmid, tspduns)

`drop_columns` removes the nested `locations` / `rates` JSON (they become their
own grains) and the version bookkeeping, which is p2's concern, not a grain's.

Column list is explicit rather than introspected so `--show-sql` works without a
database. If the upstream table gains a column, add it here or it is not carried.
"""

from __future__ import annotations

from ...decomp_base import GrainDecomposition
from ......core.registry import register


@register
class SilverFirmCore(GrainDecomposition):
    name = "silver_firm_core"
    table_name = "firm_core"
    feed = "firm"
    grain = "core"
    source_table = "firm_amended"
    key_cols_list = ["firmid", "tspduns"]

    source_where = "amend_version_status = 'Current'"
    drop_columns = ["locations", "rates", "amend_version_status", "amend_voided_ts"]

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
        "amend_kind",
    ]
