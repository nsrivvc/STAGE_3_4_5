"""
connection.py
=============
Factory that returns the right BronzeWriter for the configured DB_TYPE. This is
the single place that knows about concrete database backends; everything else
depends only on the abstract BronzeWriter interface.
"""

from __future__ import annotations

from ..config import Settings
from .writer import (
    AzureSqlBronzeWriter,
    BronzeWriter,
    DryRunWriter,
    PostgresBronzeWriter,
)


def get_writer(settings: Settings, dry_run: bool = False) -> BronzeWriter:
    """Return a BronzeWriter based on settings.db_type (or a DryRunWriter)."""
    if dry_run:
        return DryRunWriter(schema=settings.bronze_schema)

    settings.require_db()

    if settings.db_type == "postgres":
        return PostgresBronzeWriter(
            dsn=settings.database_url,  # type: ignore[arg-type]
            schema=settings.bronze_schema,
        )
    if settings.db_type == "azure_sql":
        return AzureSqlBronzeWriter(
            connection_string=settings.azure_sql_connection_string,  # type: ignore[arg-type]
            schema=settings.bronze_schema,
        )
    raise ValueError(f"Unsupported DB_TYPE: {settings.db_type!r}")
