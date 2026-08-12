"""
silver_firm_rates.py
====================
Decomposes the FIRM feed's rates into `<DECOMP_SCHEMA>.firm_rates`.

Source: `firm_rates_dedup` (deduplication(p1) output -- rates carry no amendment marker)
Key:    (firmid, uniqueid)

Column list is explicit rather than introspected so `--show-sql` works without a
database. If the upstream table gains a column, add it here or it is not carried.
"""

from __future__ import annotations

from ...decomp_base import GrainDecomposition
from ......core.registry import register


@register
class SilverFirmRates(GrainDecomposition):
    name = "silver_firm_rates"
    table_name = "firm_rates"
    feed = "firm"
    grain = "rates"
    source_table = "firm_rates_dedup"
    key_cols_list = ["firmid", "uniqueid"]

    columns = [
        "bronze_row_id",
        "seasnlst",
        "seasnlend",
        "firmid",
        "uniqueid",
        "pk",
        "rateformtype",
        "rateformtypedesc",
        "resratebasis",
        "resratebasisdesc",
        "lockmaxpress",
        "lockminpress",
        "minvolpctnoncaprel",
        "minvolqtynoncaprel",
        "captype",
        "captypename",
        "captypeloc",
        "captypelocdesc",
        "kqtyloc",
        "uniquekey",
        "id",
        "createddatetime",
        "posteddatetime",
        "kentbegdatetime",
        "kentenddatetime",
        "recloc",
        "reclocname",
        "reclocpurp",
        "reclocpurpdesc",
        "recloczn",
        "delloc",
        "dellocname",
        "dellocpurp",
        "dellocpurpdesc",
        "delloczn",
        "locqti",
        "locqtidesc",
        "rateid",
        "rateiddesc",
        "ratechgd",
        "ratechgdref",
        "ratechgdrefdesc",
        "maxtrfrate",
        "maxtrfrateref",
        "maxtrfraterefdesc",
        "mktbasedrateind",
        "surchgid",
        "surchgiddesc",
        "surchgind",
        "surchginddesc",
        "totsurchg",
        "discbegdatetime",
        "discenddatetime",
        "rptlvl",
        "rptlvldesc",
        "tspduns",
        "tspname",
        "ngtdrateindrates",
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
