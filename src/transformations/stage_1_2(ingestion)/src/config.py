"""
config.py
=========
Centralised configuration. All secrets and connection details come from
environment variables — nothing is hardcoded. A local .env file is loaded
automatically if python-dotenv is installed (see .env.example).
"""

from __future__ import annotations

import os
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional

try:  # optional convenience for local runs
    from dotenv import load_dotenv

    load_dotenv()
except Exception:  # pragma: no cover - dotenv is optional
    pass


@dataclass
class Settings:
    """Application settings sourced from the environment."""

    # which writer implementation to use: "postgres" (now) or "azure_sql" (later)
    db_type: str = field(default_factory=lambda: os.getenv("DB_TYPE", "postgres"))

    # Postgres / Neon connection string, e.g.
    #   postgresql://user:pass@ep-xxx.neon.tech/dbname?sslmode=require
    # Stripped because the repo's DATABASE_URL secret carries a trailing
    # newline, which psycopg rejects ('invalid channel_binding value:
    # "require\n"').
    database_url: Optional[str] = field(
        default_factory=lambda: (os.getenv("DATABASE_URL") or "").strip() or None
    )

    # Azure SQL (used only when db_type == "azure_sql")
    azure_sql_connection_string: Optional[str] = field(
        default_factory=lambda: os.getenv("AZURE_SQL_CONNECTION_STRING")
    )

    bronze_schema: str = field(
        default_factory=lambda: os.getenv("BRONZE_SCHEMA", "bronze")
    )
    source_system: str = field(
        default_factory=lambda: os.getenv("SOURCE_SYSTEM", "NatGasHub")
    )
    pipeline_name: str = field(
        default_factory=lambda: os.getenv("PIPELINE_NAME", "pipeline_accelerator_bronze")
    )
    batch_size: int = field(
        default_factory=lambda: int(os.getenv("BATCH_SIZE", "500"))
    )
    # Directory for the pre-load Parquet export (see src/parquet_export.py).
    parquet_output_dir: str = field(
        default_factory=lambda: os.getenv("PARQUET_OUTPUT_DIR", "parquet_output")
    )

    def require_db(self) -> None:
        """Validate that the credentials for the chosen db_type are present."""
        if self.db_type == "postgres" and not self.database_url:
            raise RuntimeError(
                "DATABASE_URL is required when DB_TYPE=postgres. "
                "See .env.example."
            )
        if self.db_type == "azure_sql" and not self.azure_sql_connection_string:
            raise RuntimeError(
                "AZURE_SQL_CONNECTION_STRING is required when DB_TYPE=azure_sql."
            )


@dataclass
class RunContext:
    """Per-execution metadata stamped onto every Bronze row and the log."""

    source_system: str
    source_api: str
    source_file_name: str
    pipeline_name: str
    pipeline_layer: str = "bronze"
    pipeline_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    activity_name: str = "Write_to_bronze"
    activity_run_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    triggered_by: str = field(
        default_factory=lambda: os.getenv("TRIGGERED_BY", os.getenv("USER", "manual"))
    )
    pipeline_start_ts: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )
