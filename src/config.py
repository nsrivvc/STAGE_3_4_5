"""
config.py
=========
All configuration comes from environment variables (loaded from a local .env
if python-dotenv is installed). Nothing is hardcoded.

WHERE TO CHANGE THINGS:
  * Point at a different database  -> DATABASE_URL (or the PG* parts) in .env
  * Rename the raw/curated schemas -> BRONZE_SCHEMA / SILVER_SCHEMA in .env
  * Rename the decomposition-output schema -> DECOMP_SCHEMA in .env
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field

try:  # optional convenience for local runs
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover
    pass


def _build_url() -> str:
    """Return a SQLAlchemy URL, either from DATABASE_URL or from PG* parts."""
    url = os.getenv("DATABASE_URL")
    if url:
        # SQLAlchemy wants the "postgresql://" scheme (not "postgres://").
        if url.startswith("postgres://"):
            url = url.replace("postgres://", "postgresql://", 1)
        return url

    # Fallback: assemble from individual parts (handy for a local/dummy DB).
    user = os.getenv("PGUSER", "postgres")
    pwd = os.getenv("PGPASSWORD", "postgres")
    host = os.getenv("PGHOST", "localhost")
    port = os.getenv("PGPORT", "5432")
    db = os.getenv("PGDATABASE", "pipeline")
    return f"postgresql://{user}:{pwd}@{host}:{port}/{db}"


@dataclass
class Settings:
    database_url: str = field(default_factory=_build_url)
    bronze_schema: str = field(default_factory=lambda: os.getenv("BRONZE_SCHEMA", "bronze"))
    silver_schema: str = field(default_factory=lambda: os.getenv("SILVER_SCHEMA", "silver"))
    # Where the decomposition phase lands its output tables. The rec-del pairing
    # transformations read from here rather than from Bronze. Set DECOMP_SCHEMA
    # once the decomposition phase exists and writes somewhere else.
    decomp_schema: str = field(default_factory=lambda: os.getenv("DECOMP_SCHEMA", "silver_staging"))
    # Parquet export. Every table's rows are written here before the transaction
    # commits. Set PARQUET_OUTPUT_DIR to "" to turn the export off entirely.
    parquet_output_dir: str = field(
        default_factory=lambda: os.getenv("PARQUET_OUTPUT_DIR", "parquet_output"))
    # Top-level folder each run's files land under. Stage numbering follows the
    # workflows (bronze_to_silver=stage3, rec_del_pairing=stage4,
    # master_capacity=stage5), so each workflow sets this. Left empty, it falls
    # back to the transformation's own folder (stage_3 / stage_4).
    parquet_stage: str = field(default_factory=lambda: os.getenv("PARQUET_STAGE", ""))
    log_level: str = field(default_factory=lambda: os.getenv("LOG_LEVEL", "INFO"))


# Single shared instance imported across the codebase.
settings = Settings()
