"""
writer.py
=========
The database-agnostic write layer.

`BronzeWriter` is an abstract interface. `PostgresBronzeWriter` implements it for
Neon / any Postgres. `AzureSqlBronzeWriter` is a documented stub showing exactly
where the Azure SQL implementation slots in later — the rest of the codebase
(main, router, transformers) never imports a concrete driver, so switching
databases means adding one writer class and flipping DB_TYPE.

Idempotency is implemented in the writer via dialect-specific upsert:
  * Postgres:  INSERT ... ON CONFLICT (hash_key) DO NOTHING
  * Azure SQL: MERGE ... WHEN NOT MATCHED THEN INSERT   (see stub)
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from typing import Any, Dict, List, Optional, Sequence

from ..bronze import schemas


class BronzeWriter(ABC):
    """Database-agnostic contract used by the ingestion pipeline."""

    @abstractmethod
    def ensure_schema(self, ddl: str) -> None:
        """Create the Bronze schema/tables if they do not already exist."""

    @abstractmethod
    def write_rows(self, table: str, rows: List[Dict[str, Any]]) -> int:
        """Insert rows into `schema.table`, skipping duplicate hash_keys.

        Returns the number of rows actually inserted (new content).
        """

    @abstractmethod
    def write_log(self, log_row: Dict[str, Any]) -> None:
        """Append one row to the ingestion_log table."""

    @abstractmethod
    def close(self) -> None:
        ...

    # context-manager sugar
    def __enter__(self) -> "BronzeWriter":
        return self

    def __exit__(self, *exc) -> None:
        self.close()


class PostgresBronzeWriter(BronzeWriter):
    """Bronze writer for Neon / vanilla Postgres using psycopg 3."""

    def __init__(self, dsn: str, schema: str = "bronze") -> None:
        # Imported lazily so that --dry-run and unit tests need no driver.
        import psycopg
        from psycopg.types.json import Jsonb

        self._psycopg = psycopg
        self._Jsonb = Jsonb
        self._schema = schema
        self._conn = psycopg.connect(dsn, autocommit=False)

    # -- helpers ------------------------------------------------------------
    @staticmethod
    def _q(identifier: str) -> str:
        return '"' + identifier.replace('"', '""') + '"'

    def _adapt(self, column: str, value: Any) -> Any:
        if column == "raw_payload" and value is not None:
            return self._Jsonb(value)
        return value

    # -- interface ----------------------------------------------------------
    def ensure_schema(self, ddl: str) -> None:
        with self._conn.cursor() as cur:
            cur.execute(ddl)
        self._conn.commit()

    def write_rows(self, table: str, rows: List[Dict[str, Any]]) -> int:
        if not rows:
            return 0

        columns = schemas.all_db_columns(table)
        col_sql = ", ".join(self._q(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        stmt = (
            f"INSERT INTO {self._q(self._schema)}.{self._q(table)} "
            f"({col_sql}) VALUES ({placeholders}) "
            f"ON CONFLICT (hash_key) DO NOTHING"
        )

        params: List[Sequence[Any]] = [
            [self._adapt(c, row.get(c)) for c in columns] for row in rows
        ]

        # executemany pipelines the whole batch to the server in a few network
        # round trips instead of one per row — the difference between minutes
        # and seconds when the database is remote (e.g. Neon from a CI runner).
        # rowcount after executemany is the cumulative number of rows actually
        # inserted (conflict-skipped duplicates are not counted).
        with self._conn.cursor() as cur:
            cur.executemany(stmt, params)
            inserted = max(cur.rowcount, 0)
        self._conn.commit()
        return inserted

    def write_log(self, log_row: Dict[str, Any]) -> None:
        columns = list(log_row.keys())
        col_sql = ", ".join(self._q(c) for c in columns)
        placeholders = ", ".join(["%s"] * len(columns))
        stmt = (
            f"INSERT INTO {self._q(self._schema)}.\"ingestion_log\" "
            f"({col_sql}) VALUES ({placeholders})"
        )
        with self._conn.cursor() as cur:
            cur.execute(stmt, [log_row[c] for c in columns])
        self._conn.commit()

    def close(self) -> None:
        try:
            self._conn.close()
        except Exception:
            pass


class AzureSqlBronzeWriter(BronzeWriter):
    """
    Placeholder for the future Azure SQL Database target.

    When you migrate, implement these methods with pyodbc/pymssql. The only
    real differences from Postgres are:

      * Connect with the ODBC connection string (AZURE_SQL_CONNECTION_STRING).
      * Replace JSONB with NVARCHAR(MAX) holding json.dumps(raw_payload), and
        store ingestion timestamps as DATETIME2.
      * Replace `INSERT ... ON CONFLICT (hash_key) DO NOTHING` with a MERGE:

            MERGE bronze.<table> AS tgt
            USING (VALUES (...)) AS src (...columns...)
               ON tgt.hash_key = src.hash_key
            WHEN NOT MATCHED THEN
               INSERT (...) VALUES (...);

    Because every caller depends only on the BronzeWriter interface, no other
    file changes when this class is filled in.
    """

    def __init__(self, connection_string: str, schema: str = "bronze") -> None:
        raise NotImplementedError(
            "AzureSqlBronzeWriter is a stub. Implement with pyodbc when migrating."
        )

    def ensure_schema(self, ddl: str) -> None: ...
    def write_rows(self, table: str, rows: List[Dict[str, Any]]) -> int: ...
    def write_log(self, log_row: Dict[str, Any]) -> None: ...
    def close(self) -> None: ...


class DryRunWriter(BronzeWriter):
    """No-op writer that prints a summary. Lets you exercise the full parse /
    validate / route / transform path with no database (used by --dry-run)."""

    def __init__(self, schema: str = "bronze") -> None:
        self._schema = schema
        self.counts: Dict[str, int] = {}

    def ensure_schema(self, ddl: str) -> None:
        print(f"[dry-run] would ensure schema/tables ({len(ddl)} chars of DDL)")

    def write_rows(self, table: str, rows: List[Dict[str, Any]]) -> int:
        self.counts[table] = self.counts.get(table, 0) + len(rows)
        sample = rows[0] if rows else {}
        keys = [k for k in ("raw_record_id", "hash_key", "ingestion_status") if k in sample]
        preview = {k: sample[k] for k in keys}
        print(f"[dry-run] {self._schema}.{table}: +{len(rows)} rows  e.g. {preview}")
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
