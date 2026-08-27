"""
silver_awards_amended.py
========================
Resolves the AWARDS feed's posting history into one CURRENT row per award,
keyed on (awardnumber, transportationserviceproviderpropcode), with
superseded versions kept as Void (see amend_base.py for the whole flow --
the logic is identical to firm/interruptible; only column names differ):

  * awards carry NO AmendRptg/AmendRptgDesc columns (`desc_col = None`), so
    after the always-appended FIRST instance, every later posting takes the
    TSP's declared mode from the pipeline attributes table -- joined here on
    TransportationServiceProviderPropCode, the awards feed's TSP identifier
    (change `partner_col` if the attributes table ends up keyed differently
    for awards). A TSP with no attributes row defaults to All Data
    behaviour: the latest posting IS the award.
  * the posting timestamp is `postdatetime` (firm/it: posteddatetime);
  * the freshness marker is `record_status` -- gawd's `status` column is the
    award's own business status, and its `version_status` is business data
    too, which is exactly why this phase keeps its bookkeeping in
    amend_version_status / amend_voided_ts.

Reads the deduplication(p1) output `awards_dedup` (fresh rows only); writes
`<DECOMP_SCHEMA>.awards_amended`, which decompisition(p3)'s core reads
filtered to amend_version_status = 'Current'. Flips the consumed rows'
freshness marker to 'processed' in awards_dedup and bronze.gawd.

The column list below is the full shape of bronze.gawd (everything except
the 'record_status' freshness marker, which is bookkeeping, not data). It is
explicit rather than introspected so the SQL can be generated without a
database connection (`--show-sql` works offline).
"""

from __future__ import annotations

from ..amend_base import ContractAmendments
from .....core.registry import register


@register
class SilverAwardsAmended(ContractAmendments):
    name = "silver_awards_amended"
    table_name = "awards_amended"
    feed = "awards"
    source_table = "awards_dedup"
    raw_table = "gawd"
    contract_id_col = "awardnumber"
    partner_col = "transportationserviceproviderpropcode"

    status_col = "record_status"
    posted_col = "postdatetime"
    desc_col = None

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
        "locations",
        "rates",
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
