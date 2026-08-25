"""
main.py — the ENTIRE NatGasHub JSON -> Bronze ingestion in one file.
====================================================================

Run it:
    python -m src.main --file data/firms_test.json --dry-run
    python -m src.main --file data/firms_test.json --create-tables

What happens, top to bottom (the file is laid out in this same order):

    1. FEED DEFINITIONS   what each of the four JSON feeds looks like
    2. SETTINGS / CONTEXT env-var config + per-run identity (run id, source)
    3. JSON TOLERANCE     helpers for arrays delivered as JSON *strings*
    4. VALIDATE           which feed is this payload? which records incomplete?
    5. ROUTE              payload -> one record dict per Bronze row
    6. TRANSFORM          record dict -> DB row (columns + hash + metadata)
    7. DDL                CREATE TABLE statements generated from the feed defs
    8. WRITERS            Postgres writer + dry-run writer
    9. PARQUET EXPORT     optional pre-load snapshot of the rows
   10. PIPELINE + CLI     run() ties 1-9 together; main() parses the flags

Why it isn't a 50-line script: the source data is messy in specific ways.
The same feed arrives from two producers with different envelopes
({"contracts": [...]} vs {"PageNumber": 1, "Firms": [...]} with no feedType),
several fields are spelled differently between them (KQty vs KQtyK), arrays
sometimes arrive as JSON-encoded *strings*, and the pipeline must be
idempotent (re-running a file must not duplicate rows) and lossless (bad
records land flagged INVALID instead of vanishing). Each section below exists
to absorb exactly one of those problems.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import sys
import traceback
import uuid
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Iterator, List, Mapping, Optional, Tuple

try:  # optional convenience: load a local .env file if python-dotenv is present
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


# ===========================================================================
# 1. FEED DEFINITIONS
# ===========================================================================
# A "feed" is one kind of JSON input. Four exist, each landing in exactly one
# Bronze table, one row per source record:
#
#     gTRAN_FIRM  firm transportation contracts    -> bronze.gtran_firm
#     gTRAN_IT    interruptible transport contracts-> bronze.gtran_it
#     gAWD        capacity awards                  -> bronze.gawd
#     gINDEX      index of customers               -> bronze.gindex
#
# Everything the pipeline needs to know about a feed is declared here as data:
# its envelope key(s), its columns, its required fields, and the alternative
# spellings ("aliases") the live NatGasHub export uses. Adding a feed = adding
# one Feed(...) entry to FEEDS. No code changes.
#
# Nested arrays inside a record (locations, rates) are NOT exploded here —
# they land on the row as JSON text columns, and the Silver layer (stage 3)
# fans them out into per-location / per-rate rows.

@dataclass(frozen=True)
class Feed:
    feed_type: str                    # canonical name, as in payload "feedType"
    table: str                        # Bronze table it lands in
    records_keys: Tuple[str, ...]     # envelope key(s) that may hold the list
    id_field: str                     # source key used as raw_record_id
    required: Tuple[str, ...]         # missing any of these => row flagged INVALID
    header_keys: Tuple[str, ...]      # payload-level keys copied onto every record
    columns: Tuple[Tuple[str, str], ...]  # (source key, declared type). The DB
    #                                   column is source_key.lower(); the type is
    #                                   documentation only — Bronze lands TEXT.
    aliases: Tuple[Tuple[str, str], ...] = ()  # (alternative spelling, canonical)

    def source_key_map(self) -> Dict[str, str]:
        """lowercased source key -> DB column, aliases included."""
        m = {src.lower(): src.lower() for src, _ in self.columns}
        for alt, canonical in self.aliases:
            m[alt.lower()] = canonical.lower()
        return m

    def records_from(self, payload: Mapping) -> Any:
        """Pull the record list out of the payload, whichever envelope key it used."""
        lower = {str(k).lower(): v for k, v in payload.items()}
        for key in self.records_keys:
            if key.lower() in lower:
                return lower[key.lower()]
        return None


FEEDS: Tuple[Feed, ...] = (
    # ---- Firm transportation contracts ------------------------------------
    # Two envelopes: mock fixture {"feedType": ..., "contracts": [...]} and
    # live export {"PageNumber": 1, "Firms": [...]}. Four fields are spelled
    # differently in the live export — declared as aliases, same columns.
    Feed(
        feed_type="gTRAN_FIRM",
        table="gtran_firm",
        records_keys=("contracts", "Firms"),
        id_field="Id",
        required=("Id", "FirmId"),
        header_keys=("TspName", "TspDuns", "TspProp"),
        aliases=(
            ("KQty", "KQtyK"),
            ("AmendRptDate", "AmendRptgDesc"),
            ("NetdRateInd", "NgtdRateInd"),
            ("NetdRateIndDesc", "NgtdRateIndDesc"),
        ),
        columns=(
            ("Id", "varchar"), ("TspName", "varchar"), ("TspDuns", "int"),
            ("TspProp", "varchar"), ("PostedDateTime", "datetime"),
            ("FirmId", "varchar"), ("Cycle", "varchar"), ("AmendRptg", "varchar"),
            ("AmendRptgDesc", "varchar"), ("KHolderName", "varchar"),
            ("KHolder", "int"), ("KHolderProp", "varchar"), ("SvcReqK", "varchar"),
            ("RateSch", "varchar"), ("KQtyK", "int"), ("KStat", "varchar"),
            ("KStatDesc", "varchar"), ("KBegDateTime", "datetime"),
            ("KEndDateTime", "datetime"), ("KEndInd", "varchar"),
            ("NgtdRateInd", "varchar"), ("NgtdRateIndDesc", "varchar"),
            ("PkgId", "varchar"), ("KRoll", "varchar"), ("KRollDesc", "varchar"),
            ("Affil", "varchar"), ("AffilDesc", "varchar"), ("CapType", "varchar"),
            ("CapTypeName", "varchar"), ("CapTypeLoc", "varchar"),
            ("CapTypeLocDesc", "varchar"), ("OSId", "varchar"), ("Rte", "varchar"),
            ("TermsNotes", "varchar"), ("CreatedDateTime", "datetime"),
            ("RecLocs", "varchar"), ("DelLocs", "varchar"),
            ("MaxRateChgd", "varchar"), ("MaxTrfRate", "varchar"),
            ("OtherRates", "varchar"), ("OtherRatesDescription", "varchar"),
            ("OtherRatesBasis", "varchar"),
            ("locations", "json"), ("rates", "json"),   # nested arrays as JSON text
            ("Term", "int"), ("RecZones", "varchar"), ("DelZones", "varchar"),
        ),
    ),
    # ---- Interruptible transportation contracts ---------------------------
    # Structurally identical to firm; differs in id (InterruptibleId) and
    # quantity column (ITQtyK).
    Feed(
        feed_type="gTRAN_IT",
        table="gtran_it",
        records_keys=("contracts", "Interruptibles"),
        id_field="Id",
        required=("Id", "InterruptibleId"),
        header_keys=("TspName", "TspDuns", "TspProp"),
        aliases=(
            ("KQty", "ITQtyK"),
            ("AmendRptDate", "AmendRptgDesc"),
            ("NetdRateInd", "NgtdRateInd"),
            ("NetdRateIndDesc", "NgtdRateIndDesc"),
        ),
        columns=(
            ("Id", "varchar"), ("TspName", "varchar"), ("TspDuns", "int"),
            ("TspProp", "varchar"), ("PostedDateTime", "datetime"),
            ("InterruptibleId", "varchar"), ("Cycle", "varchar"),
            ("AmendRptg", "varchar"), ("AmendRptgDesc", "varchar"),
            ("KHolderName", "varchar"), ("KHolder", "int"),
            ("KHolderProp", "varchar"), ("SvcReqK", "varchar"),
            ("RateSch", "varchar"), ("ITQtyK", "int"), ("KStat", "varchar"),
            ("KStatDesc", "varchar"), ("KBegDateTime", "datetime"),
            ("KEndDateTime", "datetime"), ("NgtdRateInd", "varchar"),
            ("NgtdRateIndDesc", "varchar"), ("PkgId", "varchar"),
            ("KRoll", "varchar"), ("KRollDesc", "varchar"), ("Affil", "varchar"),
            ("AffilDesc", "varchar"), ("TermsNotes", "varchar"),
            ("CreatedDateTime", "datetime"), ("RecLocs", "varchar"),
            ("DelLocs", "varchar"), ("MaxRateChgd", "varchar"),
            ("MaxTrfRate", "varchar"), ("OtherRates", "varchar"),
            ("OtherRatesDescription", "varchar"), ("OtherRatesBasis", "varchar"),
            ("DealType", "varchar"),
            ("locations", "json"), ("rates", "json"),
            ("Term", "int"), ("RecZones", "varchar"), ("DelZones", "varchar"),
        ),
    ),
    # ---- Capacity release awards ------------------------------------------
    # No TSP header at the payload level: each award carries its own TSP
    # fields, so header_keys is empty.
    Feed(
        feed_type="gAWD",
        table="gawd",
        records_keys=("awards", "Awards"),
        id_field="Id",
        required=("Id", "AwardNumber"),
        header_keys=(),
        columns=(
            ("GS_ID", "int"), ("Id", "varchar"),
            ("TransportationServiceProviderName", "varchar"),
            ("TransportationServiceProviderPropCode", "varchar"),
            ("Status", "varchar"), ("StatusCodeValue", "varchar"),
            ("OfferNumber", "varchar"), ("BidNumber", "varchar"),
            ("AwardNumber", "varchar"), ("AwardQuantityContract", "varchar"),
            ("IBRIndexBasedCapacityReleaseIndicator", "varchar"),
            ("IBRIndexBasedCapacityReleaseIndicatorCodeValue", "varchar"),
            ("RecallReputIndicator", "varchar"),
            ("RecallReputIndicatorCodeValue", "varchar"),
            ("AllowableReleaseIndicator", "varchar"),
            ("AffiliatedIndicator", "varchar"),
            ("AffiliatedIndicatorCodeValue", "varchar"),
            ("RightToAmendPrimaryPointsIndicator", "varchar"),
            ("RightToAmendPrimaryPointsIndicatorCodeValue", "varchar"),
            ("REI_AwardingAction", "varchar"),
            ("REI_StorageInventoryCondition", "varchar"),
            ("CapacityAwardDateTime", "datetime"),
            ("ReleaseTermStartDate", "datetime"),
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
            ("BidderDuns", "int"), ("ReleaserName", "varchar"),
            ("ReleaserDuns", "int"), ("BidderPhoneNumber", "varchar"),
            ("BidderEmailAddress", "varchar"), ("RateFormTypeCode", "varchar"),
            ("RateFormTypeCodeValue", "varchar"),
            ("ReservationRateBasis", "varchar"),
            ("ReservationRateBasisCodeValue", "varchar"),
            ("RateSchedule", "varchar"), ("UnitPrice", "varchar"),
            ("Multiplier", "varchar"), ("MonetaryAmount", "varchar"),
            ("ReleaseDesignationAcceptableBiddingBasis", "varchar"),
            ("ReleaseDesignationAcceptableBiddingBasisCodeValue", "varchar"),
            ("SurchargeIndicator", "varchar"),
            ("SurchargeIndicatorCodeValue", "varchar"),
            ("ChargeIndicator", "varchar"), ("CycleIndicator", "varchar"),
            ("CycleIndicatorCodeValue", "varchar"),
            ("IBRFormulaIdentifier", "varchar"),
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
            ("MeasurementBasis", "varchar"),
            ("MeasurementBasisCodeValue", "varchar"), ("CreatedDate", "datetime"),
            ("ReleaserContractNumber", "varchar"), ("ReleaseFullName", "varchar"),
            ("BidderFullName", "varchar"), ("Version_Status", "varchar"),
            ("UpdatedDateTime", "datetime"),
            ("locations", "json"), ("rates", "json"),
        ),
    ),
    # ---- Index of customers -----------------------------------------------
    # Flat rows, no nested arrays. (Ingests to Bronze; no stage 3+ registered.)
    Feed(
        feed_type="gINDEX",
        table="gindex",
        records_keys=("records", "Records", "IndexOfCustomers"),
        id_field="ID",
        required=("ID", "Pipe"),
        header_keys=(),
        columns=(
            ("ID", "int"), ("FercID", "varchar"), ("Pipe", "varchar"),
            ("ReportDate", "datetime"), ("OrigRevised", "int"),
            ("TporUOM", "varchar"), ("StorUOM", "varchar"),
            ("Contact", "varchar"), ("ContactNumber", "varchar"),
            ("Shipper", "varchar"), ("ShipperDuns", "int"),
            ("RateSched", "varchar"), ("K", "varchar"), ("KStart", "date"),
            ("KExp", "date"), ("NegRate", "varchar"), ("TportMDQ", "int"),
            ("StorMSQ", "int"), ("AgentAMA", "varchar"),
            ("AgentAMAAffiliation", "varchar"), ("PtIDCode", "varchar"),
            ("PtName", "varchar"), ("PtIDCodeQual", "varchar"),
            ("PtIdenCode", "int"), ("Zone", "varchar"), ("LocTportMDQ", "int"),
            ("LocStorMSQ", "int"), ("CreatedDate", "datetime"),
            ("RateSchedID", "int"), ("State", "varchar"), ("County", "varchar"),
            ("DUNPCE", "int"),
        ),
    ),
)

BY_FEED_TYPE: Dict[str, Feed] = {f.feed_type: f for f in FEEDS}

# Pipeline-owned metadata columns appended to EVERY Bronze table.
METADATA_COLUMNS: Tuple[Tuple[str, str], ...] = (
    ("raw_record_id", "VARCHAR(256)"),       # natural/source id of the record
    ("hash_key", "VARCHAR(64)"),             # SHA-256 content hash -> idempotency
    ("pipeline_run_id", "VARCHAR(64)"),      # one value per pipeline execution
    ("source_system", "VARCHAR(128)"),       # e.g. "NatGasHub"
    ("source_api", "VARCHAR(256)"),          # e.g. "natgashub/gTRAN_FIRM"
    ("source_file_name", "VARCHAR(512)"),    # input file the record came from
    ("ingestion_timestamp", "TIMESTAMPTZ"),
    ("updated_ts", "TIMESTAMPTZ"),
    ("ingestion_status", "VARCHAR(32)"),     # LOADED | INVALID
    ("raw_payload", "JSONB"),                # original JSON fragment, untouched
)

SCHEMA = "bronze"


def all_db_columns(feed: Feed) -> List[str]:
    """Business columns then metadata columns — the DB column order."""
    return [src.lower() for src, _ in feed.columns] + [c for c, _ in METADATA_COLUMNS]


# ===========================================================================
# 2. SETTINGS + RUN CONTEXT
# ===========================================================================

@dataclass
class Settings:
    """Configuration from environment variables (see .env.example)."""

    # .strip() because the repo's DATABASE_URL secret carries a trailing
    # newline, which psycopg rejects.
    database_url: Optional[str] = field(
        default_factory=lambda: (os.getenv("DATABASE_URL") or "").strip() or None
    )
    source_system: str = field(default_factory=lambda: os.getenv("SOURCE_SYSTEM", "NatGasHub"))
    pipeline_name: str = field(default_factory=lambda: os.getenv("PIPELINE_NAME", "pipeline_accelerator_bronze"))
    batch_size: int = field(default_factory=lambda: int(os.getenv("BATCH_SIZE", "500")))
    parquet_output_dir: str = field(default_factory=lambda: os.getenv("PARQUET_OUTPUT_DIR", "parquet_output"))


@dataclass
class RunContext:
    """Per-execution identity stamped onto every Bronze row and the log row —
    this is what lets any landed row be traced back to its exact run + file."""

    source_system: str
    source_api: str
    source_file_name: str
    pipeline_name: str
    pipeline_layer: str = "bronze"
    pipeline_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    activity_name: str = "Write_to_bronze"
    activity_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    triggered_by: str = field(default_factory=lambda: os.getenv("TRIGGERED_BY", os.getenv("USER", "manual")))
    pipeline_start_ts: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


# ===========================================================================
# 3. JSON TOLERANCE
# ===========================================================================
# The source is inconsistent about structure-vs-text. The same field can be
#     "rates": [ {...} ]              <- native array
#     "rates": "[{\"RateId\": ...}]"  <- the SAME thing as a JSON *string*
# These helpers absorb that. Only strings delimited by {} / [] are parsed —
# plain values like "0.4500" must land verbatim, never re-typed.

def canonical_json(value: Any) -> str:
    """Compact JSON with sorted keys -> same content always hashes the same."""
    return json.dumps(value, sort_keys=True, separators=(",", ":"), default=str)


def parse_embedded_json(value: Any) -> Any:
    """Parse a string holding a JSON object/array; pass anything else through."""
    if not isinstance(value, str):
        return value
    text = value.strip()
    if len(text) < 2 or text[0] not in "{[" or text[-1] not in "}]":
        return value
    try:
        return json.loads(text)
    except ValueError:
        return value  # looks like JSON, isn't — land the source text as-is


def as_record_list(value: Any) -> List[Dict[str, Any]]:
    """Normalise a record-list field (native list / single object / JSON string)
    into a list of dicts. Unusable entries are dropped, not crashed on."""
    value = parse_embedded_json(value)
    if value is None or value == "":
        return []
    if isinstance(value, dict):
        return [value]
    if isinstance(value, list):
        return [p for item in value if isinstance(p := parse_embedded_json(item), dict)]
    return []


# ===========================================================================
# 4. VALIDATE
# ===========================================================================

class PayloadValidationError(Exception):
    """Structural problems that make a payload unprocessable (aborts the run)."""


def resolve_feed(payload: Dict[str, Any]) -> Feed:
    """Which feed is this payload? Trust "feedType" when declared; otherwise
    identify it by WHICH record key it carries (the live export ships
    {"PageNumber": 1, "Firms": [...]} with no envelope metadata at all).
    Ambiguity is an error, never a guess."""
    if not isinstance(payload, dict):
        raise PayloadValidationError("Top-level JSON must be an object.")

    declared = payload.get("feedType") or payload.get("feed_type")
    if declared:
        feed = BY_FEED_TYPE.get(str(declared).strip())
        if feed is None:
            raise PayloadValidationError(
                f"Unknown feedType '{declared}'. Known: {', '.join(BY_FEED_TYPE)}."
            )
        return feed

    matches = [f for f in FEEDS if f.records_from(payload) is not None]
    if len(matches) == 1:
        return matches[0]
    if not matches:
        raise PayloadValidationError(
            "Payload declares no 'feedType' and carries no recognised record key. "
            f"Top-level keys: {', '.join(map(str, payload)) or '(none)'}. Expected one of: "
            + "; ".join(f"{f.feed_type} -> {'/'.join(f.records_keys)}" for f in FEEDS)
        )
    raise PayloadValidationError(
        "Payload matches more than one feed "
        f"({', '.join(f.feed_type for f in matches)}). Add an explicit 'feedType'."
    )


def missing_required(record: Dict[str, Any], required: Tuple[str, ...]) -> List[str]:
    """Required keys that are absent/blank (case-insensitive). A record missing
    some still LANDS — flagged ingestion_status='INVALID', never dropped."""
    lower = {k.lower(): v for k, v in record.items()}
    return [
        key for key in required
        if (v := lower.get(key.lower())) is None or (isinstance(v, str) and not v.strip())
    ]


# ===========================================================================
# 5. ROUTE
# ===========================================================================

def route(payload: Dict[str, Any], feed: Feed) -> Iterator[Dict[str, Any]]:
    """Yield one record dict per Bronze row: pull the record list out of the
    envelope and copy payload-header fields (TspName...) onto every record so
    each row is self-describing. Nested locations/rates stay on the record."""
    header = {k: payload[k] for k in feed.header_keys if k in payload}
    for raw in as_record_list(feed.records_from(payload)):
        record = dict(raw)
        present = {k.lower() for k in record}
        for key, val in header.items():
            if key.lower() not in present:
                record[key] = val
        yield record


def record_id(record: Dict[str, Any], id_field: str) -> str:
    lower = {k.lower(): v for k, v in record.items()}
    val = lower.get(id_field.lower())
    return "" if val is None else str(val)


# ===========================================================================
# 6. TRANSFORM
# ===========================================================================

def _scalarize(value: Any) -> Any:
    """Make a JSON value fit a TEXT column. Structure (native or embedded-string)
    becomes canonical JSON text — same content, same text, same hash — while
    plain strings/numbers land verbatim."""
    if value is None:
        return None
    if isinstance(value, str):
        parsed = parse_embedded_json(value)
        return canonical_json(parsed) if isinstance(parsed, (dict, list)) else value
    if isinstance(value, (dict, list)):
        return canonical_json(value)
    if isinstance(value, bool):
        return "true" if value else "false"
    return str(value)


def build_row(feed: Feed, record: Dict[str, Any], raw_id: str,
              ctx: RunContext, status: str) -> Dict[str, Any]:
    """Record dict -> DB row: map JSON keys onto columns (aliases included,
    case-insensitive), compute the idempotency hash over the business values,
    attach run metadata, and preserve the untouched record in raw_payload.
    Unrecognised source keys aren't lost — they ride along in raw_payload."""
    key_map = feed.source_key_map()
    business = {
        col: _scalarize(value)
        for key, value in record.items()
        if (col := key_map.get(key.lower())) is not None
    }

    # Same business content -> same hash -> UNIQUE(hash_key) makes re-ingesting
    # a file a no-op instead of duplicating rows.
    hash_key = hashlib.sha256(
        json.dumps(business, sort_keys=True, default=str).encode("utf-8")
    ).hexdigest()

    now = datetime.now(timezone.utc)
    row = dict(business)
    row.update(
        raw_record_id=raw_id or None,
        hash_key=hash_key,
        pipeline_run_id=ctx.pipeline_run_id,
        source_system=ctx.source_system,
        source_api=ctx.source_api,
        source_file_name=ctx.source_file_name,
        ingestion_timestamp=now,
        updated_ts=now,
        ingestion_status=status,
        raw_payload=record,  # original fragment; writer adapts to JSONB
    )
    return row


# ===========================================================================
# 7. DDL — generated from the SAME feed definitions the mapper uses, so the
#    database and the Python code can never drift apart.
# ===========================================================================

def _q(identifier: str) -> str:
    return '"' + identifier.replace('"', '""') + '"'


def generate_ddl() -> str:
    """Full Bronze DDL: schema + one table per feed + ingestion_log."""
    parts = [f"CREATE SCHEMA IF NOT EXISTS {SCHEMA};", ""]
    for feed in FEEDS:
        t = feed.table
        cols = ["    bronze_row_id BIGSERIAL PRIMARY KEY,"]
        # every business column lands as TEXT (raw-zone pattern: never fail on a
        # dirty source value; Silver enforces real types). The declared type is
        # kept as a comment so Silver knows the intended target.
        for src, declared in feed.columns:
            cols.append(f"    {_q(src.lower()):<28} TEXT,            -- source type: {declared}")
        cols.append("    -- ---- pipeline metadata ----")
        for col, pgtype in METADATA_COLUMNS:
            cols.append(f"    {_q(col):<28} {pgtype},")
        cols.append(f"    CONSTRAINT {_q('uq_' + t + '_hash')} UNIQUE (hash_key)")

        parts.append(f"CREATE TABLE IF NOT EXISTS {SCHEMA}.{_q(t)} (\n" + "\n".join(cols) + "\n);")
        parts.append(f"CREATE INDEX IF NOT EXISTS {_q('ix_' + t + '_run')} ON {SCHEMA}.{_q(t)} (pipeline_run_id);")
        parts.append(f"CREATE INDEX IF NOT EXISTS {_q('ix_' + t + '_recid')} ON {SCHEMA}.{_q(t)} (raw_record_id);")
        # forward migration: CREATE TABLE IF NOT EXISTS no-ops on an existing
        # table, so columns added to a feed later would never reach the DB.
        # ADD COLUMN IF NOT EXISTS closes that gap. Additive only — dropped
        # feed columns are left in place (dropping destroys landed data).
        for src, _ in feed.columns:
            parts.append(f"ALTER TABLE {SCHEMA}.{_q(t)} ADD COLUMN IF NOT EXISTS {_q(src.lower())} TEXT;")
        parts.append("")

    parts.append(f"""CREATE TABLE IF NOT EXISTS {SCHEMA}."ingestion_log" (
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
    ON {SCHEMA}."ingestion_log" (pipeline_run_id);""")
    return "\n".join(parts)


# ===========================================================================
# 8. WRITERS
# ===========================================================================

class PostgresWriter:
    """Writes to Neon / any Postgres via psycopg 3. Idempotency lives here:
    INSERT ... ON CONFLICT (hash_key) DO NOTHING."""

    def __init__(self, dsn: str) -> None:
        # imported lazily so --dry-run needs no driver installed
        import psycopg
        from psycopg.types.json import Jsonb

        self._Jsonb = Jsonb
        self._conn = psycopg.connect(dsn, autocommit=False)

    def ensure_schema(self, ddl: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(ddl)
        self._conn.commit()

    def write_rows(self, feed: Feed, rows: List[Dict[str, Any]]) -> int:
        """Insert a batch; returns only genuinely NEW rows (duplicates skipped)."""
        if not rows:
            return 0
        columns = all_db_columns(feed)
        stmt = (
            f"INSERT INTO {_q(SCHEMA)}.{_q(feed.table)} "
            f"({', '.join(_q(c) for c in columns)}) "
            f"VALUES ({', '.join(['%s'] * len(columns))}) "
            f"ON CONFLICT (hash_key) DO NOTHING"
        )
        params = [
            [self._Jsonb(row.get(c)) if c == "raw_payload" and row.get(c) is not None
             else row.get(c) for c in columns]
            for row in rows
        ]
        # executemany pipelines the whole batch in a few network round trips —
        # the difference between minutes and seconds against a remote DB.
        with self._conn.cursor() as cur:
            cur.executemany(stmt, params)
            inserted = max(cur.rowcount, 0)
        self._conn.commit()
        return inserted

    def write_log(self, log_row: Dict[str, Any]) -> None:
        columns = list(log_row)
        stmt = (
            f"INSERT INTO {_q(SCHEMA)}.\"ingestion_log\" "
            f"({', '.join(_q(c) for c in columns)}) "
            f"VALUES ({', '.join(['%s'] * len(columns))})"
        )
        with self._conn.cursor() as cur:
            cur.execute(stmt, [log_row[c] for c in columns])
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


class DryRunWriter:
    """--dry-run: exercise the full parse/validate/route/transform path and
    print what WOULD be written, touching no database."""

    def ensure_schema(self, ddl: str) -> None:
        print(f"[dry-run] would ensure schema/tables ({len(ddl)} chars of DDL)")

    def write_rows(self, feed: Feed, rows: List[Dict[str, Any]]) -> int:
        sample = rows[0] if rows else {}
        preview = {k: sample[k] for k in ("raw_record_id", "hash_key", "ingestion_status") if k in sample}
        print(f"[dry-run] {SCHEMA}.{feed.table}: +{len(rows)} rows  e.g. {preview}")
        return len(rows)

    def write_log(self, log_row: Dict[str, Any]) -> None:
        print(
            f"[dry-run] ingestion_log: run={log_row.get('pipeline_run_id')} "
            f"status={log_row.get('pipeline_status')} "
            f"written={log_row.get('rows_written')} "
            f"rejected={log_row.get('rows_rejected')}"
        )

    def close(self) -> None:
        pass


def get_writer(settings: Settings, dry_run: bool):
    if dry_run:
        return DryRunWriter()
    if not settings.database_url:
        raise RuntimeError("DATABASE_URL is required (see .env.example).")
    return PostgresWriter(settings.database_url)


# ===========================================================================
# 9. PARQUET EXPORT — optional snapshot of the exact rows the writer would
#    insert, taken BEFORE any database write. Layout is Hive-partitioned so
#    repeated runs never clobber each other:
#    <dir>/<feed_type>/<table>/ingest_date=YYYY-MM-DD/<run_id>.parquet
# ===========================================================================

def export_parquet(feed: Feed, rows: List[Dict[str, Any]],
                   ctx: RunContext, output_dir: str) -> List[str]:
    if not rows:
        return []
    import pyarrow as pa            # lazy: only needed when exporting
    import pyarrow.parquet as pq

    def parquet_safe(column: str, value: Any) -> Any:
        # raw_payload is the one non-scalar column; store it as JSON text
        if column == "raw_payload" and value is not None and not isinstance(value, str):
            return json.dumps(value, sort_keys=True, default=str)
        return value

    columns = all_db_columns(feed)
    records = [{c: parquet_safe(c, row.get(c)) for c in columns} for row in rows]
    target_dir = (Path(output_dir) / feed.feed_type / feed.table
                  / f"ingest_date={ctx.pipeline_start_ts.strftime('%Y-%m-%d')}")
    target_dir.mkdir(parents=True, exist_ok=True)
    file_path = target_dir / f"{ctx.pipeline_run_id}.parquet"
    pq.write_table(pa.Table.from_pylist(records), file_path, compression="snappy")
    return [str(file_path)]


# ===========================================================================
# 10. THE PIPELINE + CLI
# ===========================================================================

def run(file_path: str, settings: Settings, *, create_tables: bool,
        dry_run: bool, parquet_dir: str | None = None) -> int:
    # STEP 1 — LOAD: JSON file -> dict.
    with open(file_path, "r", encoding="utf-8") as fh:
        payload = json.load(fh)

    # STEP 2 — VALIDATE: which of the four feeds is this file?
    feed = resolve_feed(payload)

    # STEP 3 — RUN CONTEXT: mint this run's identity (run id, source labels).
    ctx = RunContext(
        source_system=payload.get("sourceSystem", settings.source_system),
        source_api=(payload.get("sourceApi") or payload.get("source_api")
                    or f"natgashub/{feed.feed_type}"),
        source_file_name=os.path.basename(file_path),
        pipeline_name=settings.pipeline_name,
    )
    print(f"Feed type      : {feed.feed_type}")
    print(f"Pipeline run id: {ctx.pipeline_run_id}")
    print(f"Source file    : {ctx.source_file_name}")

    # STEP 4 — ROUTE + TRANSFORM (in memory, nothing written yet).
    rows: List[Dict[str, Any]] = []
    rejected = 0
    for record in route(payload, feed):
        raw_id = record_id(record, feed.id_field)
        missing = missing_required(record, feed.required)
        if missing:
            rejected += 1
            print(f"  ! [{feed.table}] record '{raw_id}' missing required "
                  f"field(s): {', '.join(missing)}")
        rows.append(build_row(feed, record, raw_id, ctx,
                              status="INVALID" if missing else "LOADED"))
    objects_read = len(rows)

    # STEP 5 — PARQUET EXPORT (optional, before any DB write).
    if parquet_dir:
        for path in export_parquet(feed, rows, ctx, parquet_dir):
            print(f"  parquet: {path}")

    # STEP 6 — WRITE: ensure tables, insert in batches, log the run.
    status, error_details, rows_written = "Succeeded", "", 0
    writer = get_writer(settings, dry_run)
    try:
        if create_tables or dry_run:
            writer.ensure_schema(generate_ddl())
        for i in range(0, len(rows), settings.batch_size):
            rows_written += writer.write_rows(feed, rows[i:i + settings.batch_size])
        writer.write_log(_log_row(ctx, status, objects_read, rows_written, rejected, ""))
    except Exception as exc:  # noqa: BLE001 — any write failure must reach the log
        status = "Failed"
        error_details = f"{type(exc).__name__}: {exc}"
        traceback.print_exc()
        try:
            writer.write_log(_log_row(ctx, status, objects_read, rows_written,
                                      rejected, error_details))
        except Exception:
            pass
        return 1
    finally:
        writer.close()

    # STEP 7 — SUMMARY.
    print(f"\nDone. objects_read={objects_read} rows_written(new)={rows_written} "
          f"rejected={rejected} status={status}")
    return 0


def _log_row(ctx: RunContext, status: str, objects_read: int,
             rows_written: int, rejected: int, error_details: str) -> Dict[str, Any]:
    """The single bronze.ingestion_log row for this run."""
    end_ts = datetime.now(timezone.utc)
    return {
        "pipeline_name": ctx.pipeline_name,
        "pipeline_layer": ctx.pipeline_layer,
        "pipeline_run_id": ctx.pipeline_run_id,
        "activity_name": ctx.activity_name,
        "activity_run_id": ctx.activity_run_id,
        "source_system": ctx.source_system,
        "source_api": ctx.source_api,
        "source_file_name": ctx.source_file_name,
        "triggered_by": ctx.triggered_by,
        "pipeline_start_ts": ctx.pipeline_start_ts,
        "pipeline_end_ts": end_ts,
        "activity_duration_secs": (end_ts - ctx.pipeline_start_ts).total_seconds(),
        "objects_read": objects_read,
        "rows_written": rows_written,
        "rows_rejected": rejected,
        "pipeline_status": status,
        "data_validation_status": "Pass" if rejected == 0 else "Warn",
        "error_details": error_details,
    }


def main(argv: List[str] | None = None) -> int:
    p = argparse.ArgumentParser(description="NatGasHub JSON -> Bronze ingestion")
    p.add_argument("--file", required=True, help="Path to the NatGasHub JSON file")
    p.add_argument("--create-tables", action="store_true",
                   help="Run the Bronze DDL (CREATE IF NOT EXISTS) before loading")
    p.add_argument("--dry-run", action="store_true",
                   help="Parse/validate/route/transform without touching a database")
    p.add_argument("--parquet-dir", default=None,
                   help="Directory for the pre-load Parquet export "
                        "(default: PARQUET_OUTPUT_DIR or 'parquet_output')")
    p.add_argument("--no-parquet", action="store_true",
                   help="Skip the Parquet export entirely")
    args = p.parse_args(argv)

    settings = Settings()
    try:
        return run(
            args.file,
            settings,
            create_tables=args.create_tables,
            dry_run=args.dry_run,
            parquet_dir=None if args.no_parquet
            else (args.parquet_dir or settings.parquet_output_dir),
        )
    except FileNotFoundError:
        print(f"ERROR: input file not found: {args.file}", file=sys.stderr)
        return 2
    except PayloadValidationError as exc:
        print(f"ERROR: payload validation failed: {exc}", file=sys.stderr)
        return 2
    except RuntimeError as exc:  # e.g. missing DATABASE_URL
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    sys.exit(main())
