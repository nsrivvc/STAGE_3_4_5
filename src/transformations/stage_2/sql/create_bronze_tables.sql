-- The Bronze raw tables: the schema source of truth for this repo.
-- (Originally generated from the retired stage 1-2 subproject's
-- src/bronze/schemas.py; hand-maintained here since.)
--
-- Applied by json_to_raw.py --create-tables. Every statement is CREATE/ALTER
-- IF NOT EXISTS, so re-running is always safe. To add a column to a feed, add
-- an ALTER TABLE ... ADD COLUMN IF NOT EXISTS line under its table.

CREATE SCHEMA IF NOT EXISTS bronze;

CREATE TABLE IF NOT EXISTS bronze."gtran_firm" (
    bronze_row_id BIGSERIAL PRIMARY KEY,
    "id"                         TEXT,            -- source type: varchar
    "tspname"                    TEXT,            -- source type: varchar
    "tspduns"                    TEXT,            -- source type: int
    "tspprop"                    TEXT,            -- source type: varchar
    "posteddatetime"             TEXT,            -- source type: datetime
    "firmid"                     TEXT,            -- source type: varchar
    "cycle"                      TEXT,            -- source type: varchar
    "amendrptg"                  TEXT,            -- source type: varchar
    "amendrptgdesc"              TEXT,            -- source type: varchar
    "kholdername"                TEXT,            -- source type: varchar
    "kholder"                    TEXT,            -- source type: int
    "kholderprop"                TEXT,            -- source type: varchar
    "svcreqk"                    TEXT,            -- source type: varchar
    "ratesch"                    TEXT,            -- source type: varchar
    "kqtyk"                      TEXT,            -- source type: int
    "kstat"                      TEXT,            -- source type: varchar
    "kstatdesc"                  TEXT,            -- source type: varchar
    "kbegdatetime"               TEXT,            -- source type: datetime
    "kenddatetime"               TEXT,            -- source type: datetime
    "kendind"                    TEXT,            -- source type: varchar
    "ngtdrateind"                TEXT,            -- source type: varchar
    "ngtdrateinddesc"            TEXT,            -- source type: varchar
    "pkgid"                      TEXT,            -- source type: varchar
    "kroll"                      TEXT,            -- source type: varchar
    "krolldesc"                  TEXT,            -- source type: varchar
    "affil"                      TEXT,            -- source type: varchar
    "affildesc"                  TEXT,            -- source type: varchar
    "captype"                    TEXT,            -- source type: varchar
    "captypename"                TEXT,            -- source type: varchar
    "captypeloc"                 TEXT,            -- source type: varchar
    "captypelocdesc"             TEXT,            -- source type: varchar
    "osid"                       TEXT,            -- source type: varchar
    "rte"                        TEXT,            -- source type: varchar
    "termsnotes"                 TEXT,            -- source type: varchar
    "createddatetime"            TEXT,            -- source type: datetime
    "reclocs"                    TEXT,            -- source type: varchar
    "dellocs"                    TEXT,            -- source type: varchar
    "maxratechgd"                TEXT,            -- source type: varchar
    "maxtrfrate"                 TEXT,            -- source type: varchar
    "otherrates"                 TEXT,            -- source type: varchar
    "otherratesdescription"      TEXT,            -- source type: varchar
    "otherratesbasis"            TEXT,            -- source type: varchar
    "locations"                  TEXT,            -- source type: json
    "rates"                      TEXT,            -- source type: json
    "term"                       TEXT,            -- source type: int
    "reczones"                   TEXT,            -- source type: varchar
    "delzones"                   TEXT,            -- source type: varchar
    -- ---- pipeline metadata ----
    "raw_record_id"              VARCHAR(256),
    "hash_key"                   VARCHAR(64),
    "pipeline_run_id"            VARCHAR(64),
    "source_system"              VARCHAR(128),
    "source_api"                 VARCHAR(256),
    "source_file_name"           VARCHAR(512),
    "ingestion_timestamp"        TIMESTAMPTZ,
    "updated_ts"                 TIMESTAMPTZ,
    "ingestion_status"           VARCHAR(32),
    "raw_payload"                JSONB,
    "status"                     VARCHAR(16) DEFAULT 'fresh'
);
CREATE INDEX IF NOT EXISTS "ix_gtran_firm_run" ON bronze."gtran_firm" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gtran_firm_recid" ON bronze."gtran_firm" (raw_record_id);
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "id" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "tspname" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "tspduns" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "tspprop" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "posteddatetime" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "firmid" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "cycle" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "amendrptg" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "amendrptgdesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kholdername" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kholder" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kholderprop" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "svcreqk" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "ratesch" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kqtyk" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kstat" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kstatdesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kbegdatetime" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kenddatetime" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kendind" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "ngtdrateind" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "ngtdrateinddesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "pkgid" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "kroll" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "krolldesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "affil" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "affildesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "captype" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "captypename" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "captypeloc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "captypelocdesc" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "osid" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "rte" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "termsnotes" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "createddatetime" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "reclocs" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "dellocs" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "maxratechgd" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "maxtrfrate" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "otherrates" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "otherratesdescription" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "otherratesbasis" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "locations" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "rates" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "term" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "reczones" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "delzones" TEXT;
ALTER TABLE bronze."gtran_firm" ADD COLUMN IF NOT EXISTS "status" VARCHAR(16) DEFAULT 'fresh';

CREATE TABLE IF NOT EXISTS bronze."gtran_it" (
    bronze_row_id BIGSERIAL PRIMARY KEY,
    "id"                         TEXT,            -- source type: varchar
    "tspname"                    TEXT,            -- source type: varchar
    "tspduns"                    TEXT,            -- source type: int
    "tspprop"                    TEXT,            -- source type: varchar
    "posteddatetime"             TEXT,            -- source type: datetime
    "interruptibleid"            TEXT,            -- source type: varchar
    "cycle"                      TEXT,            -- source type: varchar
    "amendrptg"                  TEXT,            -- source type: varchar
    "amendrptgdesc"              TEXT,            -- source type: varchar
    "kholdername"                TEXT,            -- source type: varchar
    "kholder"                    TEXT,            -- source type: int
    "kholderprop"                TEXT,            -- source type: varchar
    "svcreqk"                    TEXT,            -- source type: varchar
    "ratesch"                    TEXT,            -- source type: varchar
    "itqtyk"                     TEXT,            -- source type: int
    "kstat"                      TEXT,            -- source type: varchar
    "kstatdesc"                  TEXT,            -- source type: varchar
    "kbegdatetime"               TEXT,            -- source type: datetime
    "kenddatetime"               TEXT,            -- source type: datetime
    "ngtdrateind"                TEXT,            -- source type: varchar
    "ngtdrateinddesc"            TEXT,            -- source type: varchar
    "pkgid"                      TEXT,            -- source type: varchar
    "kroll"                      TEXT,            -- source type: varchar
    "krolldesc"                  TEXT,            -- source type: varchar
    "affil"                      TEXT,            -- source type: varchar
    "affildesc"                  TEXT,            -- source type: varchar
    "termsnotes"                 TEXT,            -- source type: varchar
    "createddatetime"            TEXT,            -- source type: datetime
    "reclocs"                    TEXT,            -- source type: varchar
    "dellocs"                    TEXT,            -- source type: varchar
    "maxratechgd"                TEXT,            -- source type: varchar
    "maxtrfrate"                 TEXT,            -- source type: varchar
    "otherrates"                 TEXT,            -- source type: varchar
    "otherratesdescription"      TEXT,            -- source type: varchar
    "otherratesbasis"            TEXT,            -- source type: varchar
    "dealtype"                   TEXT,            -- source type: varchar
    "locations"                  TEXT,            -- source type: json
    "rates"                      TEXT,            -- source type: json
    "term"                       TEXT,            -- source type: int
    "reczones"                   TEXT,            -- source type: varchar
    "delzones"                   TEXT,            -- source type: varchar
    -- ---- pipeline metadata ----
    "raw_record_id"              VARCHAR(256),
    "hash_key"                   VARCHAR(64),
    "pipeline_run_id"            VARCHAR(64),
    "source_system"              VARCHAR(128),
    "source_api"                 VARCHAR(256),
    "source_file_name"           VARCHAR(512),
    "ingestion_timestamp"        TIMESTAMPTZ,
    "updated_ts"                 TIMESTAMPTZ,
    "ingestion_status"           VARCHAR(32),
    "raw_payload"                JSONB,
    "status"                     VARCHAR(16) DEFAULT 'fresh'
);
CREATE INDEX IF NOT EXISTS "ix_gtran_it_run" ON bronze."gtran_it" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gtran_it_recid" ON bronze."gtran_it" (raw_record_id);
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "id" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "tspname" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "tspduns" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "tspprop" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "posteddatetime" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "interruptibleid" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "cycle" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "amendrptg" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "amendrptgdesc" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kholdername" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kholder" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kholderprop" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "svcreqk" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "ratesch" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "itqtyk" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kstat" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kstatdesc" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kbegdatetime" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kenddatetime" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "ngtdrateind" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "ngtdrateinddesc" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "pkgid" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "kroll" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "krolldesc" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "affil" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "affildesc" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "termsnotes" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "createddatetime" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "reclocs" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "dellocs" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "maxratechgd" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "maxtrfrate" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "otherrates" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "otherratesdescription" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "otherratesbasis" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "dealtype" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "locations" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "rates" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "term" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "reczones" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "delzones" TEXT;
ALTER TABLE bronze."gtran_it" ADD COLUMN IF NOT EXISTS "status" VARCHAR(16) DEFAULT 'fresh';

CREATE TABLE IF NOT EXISTS bronze."gawd" (
    bronze_row_id BIGSERIAL PRIMARY KEY,
    "gs_id"                      TEXT,            -- source type: int
    "id"                         TEXT,            -- source type: varchar
    "transportationserviceprovidername" TEXT,            -- source type: varchar
    "transportationserviceproviderpropcode" TEXT,            -- source type: varchar
    "status"                     TEXT,            -- source type: varchar
    "statuscodevalue"            TEXT,            -- source type: varchar
    "offernumber"                TEXT,            -- source type: varchar
    "bidnumber"                  TEXT,            -- source type: varchar
    "awardnumber"                TEXT,            -- source type: varchar
    "awardquantitycontract"      TEXT,            -- source type: varchar
    "ibrindexbasedcapacityreleaseindicator" TEXT,            -- source type: varchar
    "ibrindexbasedcapacityreleaseindicatorcodevalue" TEXT,            -- source type: varchar
    "recallreputindicator"       TEXT,            -- source type: varchar
    "recallreputindicatorcodevalue" TEXT,            -- source type: varchar
    "allowablereleaseindicator"  TEXT,            -- source type: varchar
    "affiliatedindicator"        TEXT,            -- source type: varchar
    "affiliatedindicatorcodevalue" TEXT,            -- source type: varchar
    "righttoamendprimarypointsindicator" TEXT,            -- source type: varchar
    "righttoamendprimarypointsindicatorcodevalue" TEXT,            -- source type: varchar
    "rei_awardingaction"         TEXT,            -- source type: varchar
    "rei_storageinventorycondition" TEXT,            -- source type: varchar
    "capacityawarddatetime"      TEXT,            -- source type: datetime
    "releasetermstartdate"       TEXT,            -- source type: datetime
    "releasetermenddate"         TEXT,            -- source type: datetime
    "postdatetime"               TEXT,            -- source type: datetime
    "marketbasedrateindicator"   TEXT,            -- source type: varchar
    "marketbasedrateindicatorcodevalue" TEXT,            -- source type: varchar
    "prearrangeddealindicator"   TEXT,            -- source type: varchar
    "prearrangeddealindicatorcodevalue" TEXT,            -- source type: varchar
    "previouslyreleasedindicator" TEXT,            -- source type: varchar
    "previouslyreleasedindicatorcodevalue" TEXT,            -- source type: varchar
    "permanentreleaseindicator"  TEXT,            -- source type: varchar
    "permanentreleaseindicatorcodevalue" TEXT,            -- source type: varchar
    "replacementshipperroleindicator" TEXT,            -- source type: varchar
    "replacementshipperroleindicatorcodevalue" TEXT,            -- source type: varchar
    "storageinventoryconditionedreleaseindicator" TEXT,            -- source type: varchar
    "storageinventoryconditionedreleaseindicatorcodevalue" TEXT,            -- source type: varchar
    "overrunresponsibilityindicator" TEXT,            -- source type: varchar
    "overrunresponsibilityindicatorcodevalue" TEXT,            -- source type: varchar
    "businessdayindicator"       TEXT,            -- source type: varchar
    "biddername"                 TEXT,            -- source type: varchar
    "bidderduns"                 TEXT,            -- source type: int
    "releasername"               TEXT,            -- source type: varchar
    "releaserduns"               TEXT,            -- source type: int
    "bidderphonenumber"          TEXT,            -- source type: varchar
    "bidderemailaddress"         TEXT,            -- source type: varchar
    "rateformtypecode"           TEXT,            -- source type: varchar
    "rateformtypecodevalue"      TEXT,            -- source type: varchar
    "reservationratebasis"       TEXT,            -- source type: varchar
    "reservationratebasiscodevalue" TEXT,            -- source type: varchar
    "rateschedule"               TEXT,            -- source type: varchar
    "unitprice"                  TEXT,            -- source type: varchar
    "multiplier"                 TEXT,            -- source type: varchar
    "monetaryamount"             TEXT,            -- source type: varchar
    "releasedesignationacceptablebiddingbasis" TEXT,            -- source type: varchar
    "releasedesignationacceptablebiddingbasiscodevalue" TEXT,            -- source type: varchar
    "surchargeindicator"         TEXT,            -- source type: varchar
    "surchargeindicatorcodevalue" TEXT,            -- source type: varchar
    "chargeindicator"            TEXT,            -- source type: varchar
    "cycleindicator"             TEXT,            -- source type: varchar
    "cycleindicatorcodevalue"    TEXT,            -- source type: varchar
    "ibrformulaidentifier"       TEXT,            -- source type: varchar
    "ibrformulaidentifiercodevalue" TEXT,            -- source type: varchar
    "ibrindexmathematicaloperatorindicator" TEXT,            -- source type: varchar
    "ibrindexmathematicaloperatorindicatorcodevalue" TEXT,            -- source type: varchar
    "ibrindexreference1"         TEXT,            -- source type: varchar
    "ibrindexreference2"         TEXT,            -- source type: varchar
    "ibruniqueformulaspecialterms" TEXT,            -- source type: varchar
    "ibrvariablemathematicaloperatorindicator" TEXT,            -- source type: varchar
    "replacementshippercontractnumber" TEXT,            -- source type: varchar
    "agencyqualifiercode"        TEXT,            -- source type: varchar
    "recallreputtermrate"        TEXT,            -- source type: varchar
    "righttoamendprimarypointstermsnote" TEXT,            -- source type: varchar
    "specialtermsandmiscellaneousnotesandobligations" TEXT,            -- source type: varchar
    "specialtermsandmiscellaneousnotesstorageinventoryconditions" TEXT,            -- source type: varchar
    "specialtermsandmiscellaneousnotes" TEXT,            -- source type: varchar
    "measurementbasis"           TEXT,            -- source type: varchar
    "measurementbasiscodevalue"  TEXT,            -- source type: varchar
    "createddate"                TEXT,            -- source type: datetime
    "releasercontractnumber"     TEXT,            -- source type: varchar
    "releasefullname"            TEXT,            -- source type: varchar
    "bidderfullname"             TEXT,            -- source type: varchar
    "version_status"             TEXT,            -- source type: varchar
    "updateddatetime"            TEXT,            -- source type: datetime
    "locations"                  TEXT,            -- source type: json
    "rates"                      TEXT,            -- source type: json
    -- ---- pipeline metadata ----
    "raw_record_id"              VARCHAR(256),
    "hash_key"                   VARCHAR(64),
    "pipeline_run_id"            VARCHAR(64),
    "source_system"              VARCHAR(128),
    "source_api"                 VARCHAR(256),
    "source_file_name"           VARCHAR(512),
    "ingestion_timestamp"        TIMESTAMPTZ,
    "updated_ts"                 TIMESTAMPTZ,
    "ingestion_status"           VARCHAR(32),
    "raw_payload"                JSONB,
    "record_status"              VARCHAR(16) DEFAULT 'fresh'
);
CREATE INDEX IF NOT EXISTS "ix_gawd_run" ON bronze."gawd" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gawd_recid" ON bronze."gawd" (raw_record_id);
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "gs_id" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "id" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "transportationserviceprovidername" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "transportationserviceproviderpropcode" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "status" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "statuscodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "offernumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "bidnumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "awardnumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "awardquantitycontract" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexbasedcapacityreleaseindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexbasedcapacityreleaseindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "recallreputindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "recallreputindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "allowablereleaseindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "affiliatedindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "affiliatedindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "righttoamendprimarypointsindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "righttoamendprimarypointsindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rei_awardingaction" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rei_storageinventorycondition" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "capacityawarddatetime" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasetermstartdate" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasetermenddate" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "postdatetime" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "marketbasedrateindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "marketbasedrateindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "prearrangeddealindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "prearrangeddealindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "previouslyreleasedindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "previouslyreleasedindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "permanentreleaseindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "permanentreleaseindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "replacementshipperroleindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "replacementshipperroleindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "storageinventoryconditionedreleaseindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "storageinventoryconditionedreleaseindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "overrunresponsibilityindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "overrunresponsibilityindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "businessdayindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "biddername" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "bidderduns" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasername" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releaserduns" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "bidderphonenumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "bidderemailaddress" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rateformtypecode" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rateformtypecodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "reservationratebasis" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "reservationratebasiscodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rateschedule" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "unitprice" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "multiplier" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "monetaryamount" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasedesignationacceptablebiddingbasis" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasedesignationacceptablebiddingbasiscodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "surchargeindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "surchargeindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "chargeindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "cycleindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "cycleindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrformulaidentifier" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrformulaidentifiercodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexmathematicaloperatorindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexmathematicaloperatorindicatorcodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexreference1" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrindexreference2" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibruniqueformulaspecialterms" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "ibrvariablemathematicaloperatorindicator" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "replacementshippercontractnumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "agencyqualifiercode" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "recallreputtermrate" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "righttoamendprimarypointstermsnote" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "specialtermsandmiscellaneousnotesandobligations" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "specialtermsandmiscellaneousnotesstorageinventoryconditions" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "specialtermsandmiscellaneousnotes" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "measurementbasis" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "measurementbasiscodevalue" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "createddate" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasercontractnumber" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "releasefullname" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "bidderfullname" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "version_status" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "updateddatetime" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "locations" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "rates" TEXT;
ALTER TABLE bronze."gawd" ADD COLUMN IF NOT EXISTS "record_status" VARCHAR(16) DEFAULT 'fresh';

CREATE TABLE IF NOT EXISTS bronze."gindex" (
    bronze_row_id BIGSERIAL PRIMARY KEY,
    "id"                         TEXT,            -- source type: int
    "fercid"                     TEXT,            -- source type: varchar
    "pipe"                       TEXT,            -- source type: varchar
    "reportdate"                 TEXT,            -- source type: datetime
    "origrevised"                TEXT,            -- source type: int
    "tporuom"                    TEXT,            -- source type: varchar
    "storuom"                    TEXT,            -- source type: varchar
    "contact"                    TEXT,            -- source type: varchar
    "contactnumber"              TEXT,            -- source type: varchar
    "shipper"                    TEXT,            -- source type: varchar
    "shipperduns"                TEXT,            -- source type: int
    "ratesched"                  TEXT,            -- source type: varchar
    "k"                          TEXT,            -- source type: varchar
    "kstart"                     TEXT,            -- source type: date
    "kexp"                       TEXT,            -- source type: date
    "negrate"                    TEXT,            -- source type: varchar
    "tportmdq"                   TEXT,            -- source type: int
    "stormsq"                    TEXT,            -- source type: int
    "agentama"                   TEXT,            -- source type: varchar
    "agentamaaffiliation"        TEXT,            -- source type: varchar
    "ptidcode"                   TEXT,            -- source type: varchar
    "ptname"                     TEXT,            -- source type: varchar
    "ptidcodequal"               TEXT,            -- source type: varchar
    "ptidencode"                 TEXT,            -- source type: int
    "zone"                       TEXT,            -- source type: varchar
    "loctportmdq"                TEXT,            -- source type: int
    "locstormsq"                 TEXT,            -- source type: int
    "createddate"                TEXT,            -- source type: datetime
    "rateschedid"                TEXT,            -- source type: int
    "state"                      TEXT,            -- source type: varchar
    "county"                     TEXT,            -- source type: varchar
    "dunpce"                     TEXT,            -- source type: int
    -- ---- pipeline metadata ----
    "raw_record_id"              VARCHAR(256),
    "hash_key"                   VARCHAR(64),
    "pipeline_run_id"            VARCHAR(64),
    "source_system"              VARCHAR(128),
    "source_api"                 VARCHAR(256),
    "source_file_name"           VARCHAR(512),
    "ingestion_timestamp"        TIMESTAMPTZ,
    "updated_ts"                 TIMESTAMPTZ,
    "ingestion_status"           VARCHAR(32),
    "raw_payload"                JSONB
);
CREATE INDEX IF NOT EXISTS "ix_gindex_run" ON bronze."gindex" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gindex_recid" ON bronze."gindex" (raw_record_id);
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "id" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "fercid" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "pipe" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "reportdate" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "origrevised" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "tporuom" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "storuom" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "contact" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "contactnumber" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "shipper" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "shipperduns" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "ratesched" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "k" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "kstart" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "kexp" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "negrate" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "tportmdq" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "stormsq" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "agentama" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "agentamaaffiliation" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "ptidcode" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "ptname" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "ptidcodequal" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "ptidencode" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "zone" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "loctportmdq" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "locstormsq" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "createddate" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "rateschedid" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "state" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "county" TEXT;
ALTER TABLE bronze."gindex" ADD COLUMN IF NOT EXISTS "dunpce" TEXT;

CREATE TABLE IF NOT EXISTS bronze."ingestion_log" (
    log_id BIGSERIAL PRIMARY KEY,
    pipeline_name           VARCHAR(128),
    pipeline_layer          VARCHAR(32),
    pipeline_run_id         VARCHAR(64),
    activity_name           VARCHAR(128),
    activity_run_id         VARCHAR(64),
    source_system           VARCHAR(128),
    source_api              VARCHAR(256),
    source_file_name        VARCHAR(512),
    triggered_by            VARCHAR(256),
    pipeline_start_ts       TIMESTAMPTZ,
    pipeline_end_ts         TIMESTAMPTZ,
    activity_duration_secs  NUMERIC,
    objects_read            INTEGER,
    rows_written            INTEGER,
    rows_rejected           INTEGER,
    pipeline_status         VARCHAR(32),
    data_validation_status  VARCHAR(32),
    error_details           TEXT,
    logged_at_ts            TIMESTAMPTZ DEFAULT now()
);
CREATE INDEX IF NOT EXISTS "ix_ingestion_log_run"
    ON bronze."ingestion_log" (pipeline_run_id);

