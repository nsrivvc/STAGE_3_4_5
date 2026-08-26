"""
silver_awards_core.py
=====================
Decomposes the AWARDS feed's core into `<DECOMP_SCHEMA>.awards_core`.

Source: `awards_dedup`
Key:    (id)

AWARDS SKIPS ammendments(p2): the feed carries no AmendRptg marker, so there
is no posting history to fold. This reads deduplication(p1) directly.

`drop_columns` removes the nested `locations` / `rates` JSON that Bronze keeps
on the award row -- they become their own grains, and the agreed core schema
excludes them.

Column list is explicit rather than introspected so `--show-sql` works without a
database. If the upstream table gains a column, add it here or it is not carried.
"""

from __future__ import annotations

from ...decomp_base import GrainDecomposition
from ......core.registry import register


@register
class SilverAwardsCore(GrainDecomposition):
    name = "silver_awards_core"
    table_name = "awards_core"
    feed = "awards"
    grain = "core"
    source_table = "awards_dedup"
    key_cols_list = ["id"]

    drop_columns = ["locations", "rates"]

    columns = [
        "bronze_row_id",
        "gs_id",
        "id",
        "transportationserviceprovidername",
        "transportationserviceproviderpropcode",
        "status",
        "statuscodevalue",
        "offernumber",
        "bidnumber",
        "awardnumber",
        "awardquantitycontract",
        "ibrindexbasedcapacityreleaseindicator",
        "ibrindexbasedcapacityreleaseindicatorcodevalue",
        "recallreputindicator",
        "recallreputindicatorcodevalue",
        "allowablereleaseindicator",
        "affiliatedindicator",
        "affiliatedindicatorcodevalue",
        "righttoamendprimarypointsindicator",
        "righttoamendprimarypointsindicatorcodevalue",
        "rei_awardingaction",
        "rei_storageinventorycondition",
        "capacityawarddatetime",
        "releasetermstartdate",
        "releasetermenddate",
        "postdatetime",
        "marketbasedrateindicator",
        "marketbasedrateindicatorcodevalue",
        "prearrangeddealindicator",
        "prearrangeddealindicatorcodevalue",
        "previouslyreleasedindicator",
        "previouslyreleasedindicatorcodevalue",
        "permanentreleaseindicator",
        "permanentreleaseindicatorcodevalue",
        "replacementshipperroleindicator",
        "replacementshipperroleindicatorcodevalue",
        "storageinventoryconditionedreleaseindicator",
        "storageinventoryconditionedreleaseindicatorcodevalue",
        "overrunresponsibilityindicator",
        "overrunresponsibilityindicatorcodevalue",
        "businessdayindicator",
        "biddername",
        "bidderduns",
        "releasername",
        "releaserduns",
        "bidderphonenumber",
        "bidderemailaddress",
        "rateformtypecode",
        "rateformtypecodevalue",
        "reservationratebasis",
        "reservationratebasiscodevalue",
        "rateschedule",
        "unitprice",
        "multiplier",
        "monetaryamount",
        "releasedesignationacceptablebiddingbasis",
        "releasedesignationacceptablebiddingbasiscodevalue",
        "surchargeindicator",
        "surchargeindicatorcodevalue",
        "chargeindicator",
        "cycleindicator",
        "cycleindicatorcodevalue",
        "ibrformulaidentifier",
        "ibrformulaidentifiercodevalue",
        "ibrindexmathematicaloperatorindicator",
        "ibrindexmathematicaloperatorindicatorcodevalue",
        "ibrindexreference1",
        "ibrindexreference2",
        "ibruniqueformulaspecialterms",
        "ibrvariablemathematicaloperatorindicator",
        "replacementshippercontractnumber",
        "agencyqualifiercode",
        "recallreputtermrate",
        "righttoamendprimarypointstermsnote",
        "specialtermsandmiscellaneousnotesandobligations",
        "specialtermsandmiscellaneousnotesstorageinventoryconditions",
        "specialtermsandmiscellaneousnotes",
        "measurementbasis",
        "measurementbasiscodevalue",
        "createddate",
        "releasercontractnumber",
        "releasefullname",
        "bidderfullname",
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
