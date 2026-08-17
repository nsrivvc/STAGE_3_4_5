"""
schemas.py
==========
Single source of truth for the Bronze-layer table definitions.

The column lists below are transcribed directly from the "Bronze Layer" sheet of
FT_Tracker2_0_Tables_Schema-Draft.xlsx. They are used in two places:

  1. To generate the CREATE SCHEMA / CREATE TABLE DDL (see generate_ddl()).
  2. To map incoming JSON keys onto database columns (see bronze.transformers).

Keeping both the SQL and the Python mapping derived from this one module avoids
schema drift between the database and the ingestion code.

Design decision — Bronze lands business fields as TEXT
------------------------------------------------------
The sheet declares native types (int, datetime, date) for each business column.
In the Bronze layer we deliberately land every *business* column as TEXT and
preserve the source value verbatim. This is a common raw-zone pattern: it keeps
ingestion resilient to dirty/ambiguous source values (the sheet's own validation
tab mixes "13/4/2026" with Excel serials like 46360), and defers type
enforcement to the Silver transformation. The originally-declared type is kept
as an inline SQL comment so Silver knows the intended target type.

Metadata columns (timestamps, status, hash, payload) are owned by the pipeline
and therefore use proper native types.
"""

from __future__ import annotations

from typing import Dict, List

# ---------------------------------------------------------------------------
# Business columns per Bronze table (verbatim from the spreadsheet).
# (db_column is always source_key.lower(); declared_type is the sheet's type,
#  retained only as documentation since Bronze lands everything as TEXT.)
# ---------------------------------------------------------------------------

# Each entry: (source_json_key, declared_type)
BUSINESS_COLUMNS: Dict[str, List[tuple]] = {
    "gtran_firm": [
        ("Id", "varchar"), ("TspName", "varchar"), ("TspDuns", "int"),
        ("TspProp", "varchar"), ("PostedDateTime", "datetime"), ("FirmId", "varchar"),
        ("Cycle", "varchar"), ("AmendRptg", "varchar"), ("AmendRptgDesc", "varchar"),
        ("KHolderName", "varchar"), ("KHolder", "int"), ("KHolderProp", "varchar"),
        ("SvcReqK", "varchar"), ("RateSch", "varchar"), ("KQtyK", "int"),
        ("KStat", "varchar"), ("KStatDesc", "varchar"), ("KBegDateTime", "datetime"),
        ("KEndDateTime", "datetime"), ("KEndInd", "varchar"), ("NgtdRateInd", "varchar"),
        ("NgtdRateIndDesc", "varchar"), ("PkgId", "varchar"), ("KRoll", "varchar"),
        ("KRollDesc", "varchar"), ("Affil", "varchar"), ("AffilDesc", "varchar"),
        ("CapType", "varchar"), ("CapTypeName", "varchar"), ("CapTypeLoc", "varchar"),
        ("CapTypeLocDesc", "varchar"), ("OSId", "varchar"), ("Rte", "varchar"),
        ("TermsNotes", "varchar"), ("CreatedDateTime", "datetime"), ("RecLocs", "varchar"),
        ("DelLocs", "varchar"), ("MaxRateChgd", "varchar"), ("MaxTrfRate", "varchar"),
        ("OtherRates", "varchar"), ("OtherRatesDescription", "varchar"),
        ("OtherRatesBasis", "varchar"),
        # nested arrays, landed as canonical JSON text (exploded in Silver)
        ("locations", "json"), ("rates", "json"),
    ],
    "gtran_it": [
        ("Id", "varchar"), ("TspName", "varchar"), ("TspDuns", "int"),
        ("TspProp", "varchar"), ("PostedDateTime", "datetime"),
        ("InterruptibleId", "varchar"), ("Cycle", "varchar"), ("AmendRptg", "varchar"),
        ("AmendRptgDesc", "varchar"), ("KHolderName", "varchar"), ("KHolder", "int"),
        ("KHolderProp", "varchar"), ("SvcReqK", "varchar"), ("RateSch", "varchar"),
        ("ITQtyK", "int"), ("KStat", "varchar"), ("KStatDesc", "varchar"),
        ("KBegDateTime", "datetime"), ("KEndDateTime", "datetime"),
        ("NgtdRateInd", "varchar"), ("NgtdRateIndDesc", "varchar"), ("PkgId", "varchar"),
        ("KRoll", "varchar"), ("KRollDesc", "varchar"), ("Affil", "varchar"),
        ("AffilDesc", "varchar"), ("TermsNotes", "varchar"),
        ("CreatedDateTime", "datetime"), ("RecLocs", "varchar"), ("DelLocs", "varchar"),
        ("MaxRateChgd", "varchar"), ("MaxTrfRate", "varchar"), ("OtherRates", "varchar"),
        ("OtherRatesDescription", "varchar"), ("OtherRatesBasis", "varchar"),
        ("DealType", "varchar"),
        # nested arrays, landed as canonical JSON text (exploded in Silver)
        ("locations", "json"), ("rates", "json"),
    ],
    "gindex": [
        ("ID", "int"), ("FercID", "varchar"), ("Pipe", "varchar"),
        ("ReportDate", "datetime"), ("OrigRevised", "int"), ("TporUOM", "varchar"),
        ("StorUOM", "varchar"), ("Contact", "varchar"), ("ContactNumber", "varchar"),
        ("Shipper", "varchar"), ("ShipperDuns", "int"), ("RateSched", "varchar"),
        ("K", "varchar"), ("KStart", "date"), ("KExp", "date"), ("NegRate", "varchar"),
        ("TportMDQ", "int"), ("StorMSQ", "int"), ("AgentAMA", "varchar"),
        ("AgentAMAAffiliation", "varchar"), ("PtIDCode", "varchar"), ("PtName", "varchar"),
        ("PtIDCodeQual", "varchar"), ("PtIdenCode", "int"), ("Zone", "varchar"),
        ("LocTportMDQ", "int"), ("LocStorMSQ", "int"), ("CreatedDate", "datetime"),
        ("RateSchedID", "int"), ("State", "varchar"), ("County", "varchar"),
        ("DUNPCE", "int"),
    ],
    # Capacity-release awards feed. NOT in the source spreadsheet — these
    # columns are derived from the union of keys in data/awards_test.json
    # (one row per award, plus nested location/rate arrays like the gTRAN
    # feeds). Regenerate if the source layout changes.
    "gawd": [
        ("GS_ID", "int"), ("Id", "varchar"),
        ("TransportationServiceProviderName", "varchar"),
        ("TransportationServiceProviderPropCode", "varchar"), ("Status", "varchar"),
        ("StatusCodeValue", "varchar"), ("OfferNumber", "varchar"),
        ("BidNumber", "varchar"), ("AwardNumber", "varchar"),
        ("AwardQuantityContract", "varchar"),
        ("IBRIndexBasedCapacityReleaseIndicator", "varchar"),
        ("IBRIndexBasedCapacityReleaseIndicatorCodeValue", "varchar"),
        ("RecallReputIndicator", "varchar"),
        ("RecallReputIndicatorCodeValue", "varchar"),
        ("AllowableReleaseIndicator", "varchar"), ("AffiliatedIndicator", "varchar"),
        ("AffiliatedIndicatorCodeValue", "varchar"),
        ("RightToAmendPrimaryPointsIndicator", "varchar"),
        ("RightToAmendPrimaryPointsIndicatorCodeValue", "varchar"),
        ("REI_AwardingAction", "varchar"), ("REI_StorageInventoryCondition", "varchar"),
        ("CapacityAwardDateTime", "datetime"), ("ReleaseTermStartDate", "datetime"),
        ("ReleaseTermEndDate", "datetime"), ("PostDateTime", "datetime"),
        ("MarketBasedRateIndicator", "varchar"),
        ("MarketBasedRateIndicatorCodeValue", "varchar"),
        ("PrearrangedDealIndicator", "varchar"),
        ("PrearrangedDealIndicatorCodeValue", "varchar"),
        ("PreviouslyReleasedIndicator", "varchar"),
        ("PreviouslyReleasedIndicatorCodeValue", "varchar"),
        ("PermanentReleaseIndicator", "varchar"),
        ("PermanentReleaseIndicatorCodeValue", "varchar"),
        ("ReplacementShipperRoleIndicator", "varchar"),
        ("ReplacementShipperRoleIndicatorCodeValue", "varchar"),
        ("StorageInventoryConditionedReleaseIndicator", "varchar"),
        ("StorageInventoryConditionedReleaseIndicatorCodeValue", "varchar"),
        ("OverrunResponsibilityIndicator", "varchar"),
        ("OverrunResponsibilityIndicatorCodeValue", "varchar"),
        ("BusinessDayIndicator", "varchar"), ("BidderName", "varchar"),
        ("BidderDuns", "int"), ("ReleaserName", "varchar"), ("ReleaserDuns", "int"),
        ("BidderPhoneNumber", "varchar"), ("BidderEmailAddress", "varchar"),
        ("RateFormTypeCode", "varchar"), ("RateFormTypeCodeValue", "varchar"),
        ("ReservationRateBasis", "varchar"),
        ("ReservationRateBasisCodeValue", "varchar"), ("RateSchedule", "varchar"),
        ("UnitPrice", "varchar"), ("Multiplier", "varchar"),
        ("MonetaryAmount", "varchar"),
        ("ReleaseDesignationAcceptableBiddingBasis", "varchar"),
        ("ReleaseDesignationAcceptableBiddingBasisCodeValue", "varchar"),
        ("SurchargeIndicator", "varchar"), ("SurchargeIndicatorCodeValue", "varchar"),
        ("ChargeIndicator", "varchar"), ("CycleIndicator", "varchar"),
        ("CycleIndicatorCodeValue", "varchar"), ("IBRFormulaIdentifier", "varchar"),
        ("IBRFormulaIdentifierCodeValue", "varchar"),
        ("IBRIndexMathematicalOperatorIndicator", "varchar"),
        ("IBRIndexMathematicalOperatorIndicatorCodeValue", "varchar"),
        ("IBRIndexReference1", "varchar"), ("IBRIndexReference2", "varchar"),
        ("IBRUniqueFormulaSpecialTerms", "varchar"),
        ("IBRVariableMathematicalOperatorIndicator", "varchar"),
        ("ReplacementShipperContractNumber", "varchar"),
        ("AgencyQualifierCode", "varchar"), ("RecallReputTermRate", "varchar"),
        ("RightToAmendPrimaryPointsTermsNote", "varchar"),
        ("SpecialTermsAndMiscellaneousNotesAndObligations", "varchar"),
        ("SpecialTermsAndMiscellaneousNotesStorageInventoryConditions", "varchar"),
        ("SpecialTermsAndMiscellaneousNotes", "varchar"),
        ("MeasurementBasis", "varchar"), ("MeasurementBasisCodeValue", "varchar"),
        ("CreatedDate", "datetime"), ("ReleaserContractNumber", "varchar"),
        ("ReleaseFullName", "varchar"), ("BidderFullName", "varchar"),
        ("Version_Status", "varchar"), ("UpdatedDateTime", "datetime"),
        # nested arrays, landed as canonical JSON text (exploded in Silver)
        ("locations", "json"), ("rates", "json"),
    ],
}

# ---------------------------------------------------------------------------
# Pipeline-owned metadata columns appended to EVERY Bronze business table.
# (column_name, postgres_type)
# ---------------------------------------------------------------------------
METADATA_COLUMNS: List[tuple] = [
    ("raw_record_id", "VARCHAR(256)"),       # natural/source id of the record
    ("hash_key", "VARCHAR(64)"),             # SHA-256 content hash -> idempotency key
    ("pipeline_run_id", "VARCHAR(64)"),      # one value per pipeline execution
    ("source_system", "VARCHAR(128)"),       # e.g. "NatGasHub"
    ("source_api", "VARCHAR(256)"),          # e.g. "natgashub/v1/.../firm"
    ("source_file_name", "VARCHAR(512)"),    # input file the record came from
    ("ingestion_timestamp", "TIMESTAMPTZ"),  # == sheet's "ingestion_ts"
    ("updated_ts", "TIMESTAMPTZ"),           # last time this hash_key was touched
    ("ingestion_status", "VARCHAR(32)"),     # LOADED | INVALID
    ("raw_payload", "JSONB"),                # original JSON fragment for this row
]

SCHEMA_NAME = "bronze"

# Convenience lookups -------------------------------------------------------

def business_db_columns(table: str) -> List[str]:
    """Lowercased DB column names for a table's business fields."""
    return [src.lower() for src, _ in BUSINESS_COLUMNS[table]]


def all_db_columns(table: str) -> List[str]:
    """Business columns followed by metadata columns (DB order)."""
    return business_db_columns(table) + [c for c, _ in METADATA_COLUMNS]


def source_key_map(table: str) -> Dict[str, str]:
    """Map lowercased-source-key -> db column, for case-insensitive matching."""
    return {src.lower(): src.lower() for src, _ in BUSINESS_COLUMNS[table]}


# ---------------------------------------------------------------------------
# DDL generation
# ---------------------------------------------------------------------------

def _q(identifier: str) -> str:
    """Quote a Postgres identifier (lowercased)."""
    return '"' + identifier.replace('"', '""') + '"'


def generate_table_ddl(table: str) -> str:
    lines = [f"CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}.{_q(table)} ("]
    col_lines = ["    bronze_row_id BIGSERIAL PRIMARY KEY,"]

    for src, declared in BUSINESS_COLUMNS[table]:
        col_lines.append(f"    {_q(src.lower()):<28} TEXT,            -- source type: {declared}")

    col_lines.append("    -- ---- pipeline metadata ----")
    for col, pgtype in METADATA_COLUMNS:
        col_lines.append(f"    {_q(col):<28} {pgtype},")

    # idempotency: content hash is unique within the table
    col_lines.append(f"    CONSTRAINT {_q('uq_' + table + '_hash')} UNIQUE (hash_key)")

    lines.append("\n".join(col_lines))
    lines.append(");")
    # helpful lookup indexes
    lines.append(
        f"CREATE INDEX IF NOT EXISTS {_q('ix_' + table + '_run')} "
        f"ON {SCHEMA_NAME}.{_q(table)} (pipeline_run_id);"
    )
    lines.append(
        f"CREATE INDEX IF NOT EXISTS {_q('ix_' + table + '_recid')} "
        f"ON {SCHEMA_NAME}.{_q(table)} (raw_record_id);"
    )
    return "\n".join(lines)


def generate_log_ddl() -> str:
    """Pipeline run/activity log table (from the Logging + Validation sheets)."""
    return f"""CREATE TABLE IF NOT EXISTS {SCHEMA_NAME}."ingestion_log" (
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
    ON {SCHEMA_NAME}."ingestion_log" (pipeline_run_id);"""


def generate_ddl() -> str:
    """Full Bronze DDL: schema + all business tables + log table."""
    parts = [
        "-- Auto-generated from src/bronze/schemas.py — do not hand-edit.",
        "-- Regenerate with:  python -m src.bronze.schemas",
        "",
        f"CREATE SCHEMA IF NOT EXISTS {SCHEMA_NAME};",
        "",
    ]
    for table in BUSINESS_COLUMNS:
        parts.append(generate_table_ddl(table))
        parts.append("")
    parts.append(generate_log_ddl())
    parts.append("")
    return "\n".join(parts)


if __name__ == "__main__":
    # `python -m src.bronze.schemas` prints the DDL to stdout.
    print(generate_ddl())
