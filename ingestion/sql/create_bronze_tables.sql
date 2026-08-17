-- Auto-generated from src/bronze/schemas.py — do not hand-edit.
-- Regenerate with:  python -m src.bronze.schemas

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
    CONSTRAINT "uq_gtran_firm_hash" UNIQUE (hash_key)
);
CREATE INDEX IF NOT EXISTS "ix_gtran_firm_run" ON bronze."gtran_firm" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gtran_firm_recid" ON bronze."gtran_firm" (raw_record_id);

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
    CONSTRAINT "uq_gtran_it_hash" UNIQUE (hash_key)
);
CREATE INDEX IF NOT EXISTS "ix_gtran_it_run" ON bronze."gtran_it" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gtran_it_recid" ON bronze."gtran_it" (raw_record_id);

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
    "raw_payload"                JSONB,
    CONSTRAINT "uq_gindex_hash" UNIQUE (hash_key)
);
CREATE INDEX IF NOT EXISTS "ix_gindex_run" ON bronze."gindex" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gindex_recid" ON bronze."gindex" (raw_record_id);

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
    CONSTRAINT "uq_gawd_hash" UNIQUE (hash_key)
);
CREATE INDEX IF NOT EXISTS "ix_gawd_run" ON bronze."gawd" (pipeline_run_id);
CREATE INDEX IF NOT EXISTS "ix_gawd_recid" ON bronze."gawd" (raw_record_id);

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

