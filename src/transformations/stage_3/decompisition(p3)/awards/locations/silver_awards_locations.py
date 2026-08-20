"""
silver_awards_locations.py
==========================
Decomposes the AWARDS feed's locations into `<DECOMP_SCHEMA>.awards_locations`.

Source: `awards_locations_dedup`
Key:    (id, locationpropcode, locationpurposecode)

Awards locations do NOT use LocationsDecomposition: that class is typed to the
firm/IT agreed schema (index / uniqueid / pk / seasnlst / loczn), which the
awards feed does not have. Awards has its own agreed column list, carried here
through the generic keyed passthrough.

This is the table stage 4 rec-del pairing reads.

Column list is explicit rather than introspected so `--show-sql` works without a
database. If the upstream table gains a column, add it here or it is not carried.
"""

from __future__ import annotations

from ...decomp_base import GrainDecomposition
from ......core.registry import register


@register
class SilverAwardsLocations(GrainDecomposition):
    name = "silver_awards_locations"
    table_name = "awards_locations"
    feed = "awards"
    grain = "locations"
    source_table = "awards_locations_dedup"
    key_cols_list = ["id", "locationpropcode", "locationpurposecode"]

    columns = [
        "bronze_row_id",
        "postdatetime",
        "capacityawarddatetime",
        "releasetermstartdate",
        "releasetermenddate",
        "gs_id",
        "id",
        "offernumber",
        "bidnumber",
        "awardnumber",
        "transportationserviceproviderpropcode",
        "ibrratefloor",
        "ibrnamevolume",
        "maximumvolumetriccommitmentquantity",
        "seasonalstartdate",
        "seasonalenddate",
        "locationpurposecode",
        "stdlocproppurposecode",
        "locationpurposecodevalue",
        "locationname",
        "locationpropcode",
        "locationquantitytypeindicator",
        "locationquantitytypeindicatorcodevalue",
        "capacitytypelocationindicator",
        "capacitytypelocationindicatorcodevalue",
        "route",
        "awardquantitylocation",
        "seasonaldateformat",
        "bidderduns",
        "releaserduns",
        "createddate",
        "version_status",
        "updateddatetime",
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
