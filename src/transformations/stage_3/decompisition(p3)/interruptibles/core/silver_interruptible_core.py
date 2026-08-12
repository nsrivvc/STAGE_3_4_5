"""
silver_interruptible_core.py
============================
Decomposes the INTERRUPTIBLE feed's core into `<DECOMP_SCHEMA>.interruptible_core`.

Source: `interruptible_core_amended` (ammendments(p2) output -- the folded contract header)
Key:    (interruptibleid, tspduns)

Column list is explicit rather than introspected so `--show-sql` works without a
database. If the upstream table gains a column, add it here or it is not carried.
"""

from __future__ import annotations

from ...decomp_base import GrainDecomposition
from ......core.registry import register


@register
class SilverInterruptibleCore(GrainDecomposition):
    name = "silver_interruptible_core"
    table_name = "interruptible_core"
    feed = "interruptible"
    grain = "core"
    source_table = "interruptible_core_amended"
    key_cols_list = ["interruptibleid", "tspduns"]

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
        "amend_kind",
        "amend_postings_applied",
        "amend_baseline_ts",
    ]
