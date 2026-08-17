# Pipeline Accelerator — Bronze Ingestion (Stage 1)

Stage 1 of the Pipeline Accelerator Program proof of concept:

```
NatGasHub JSON  ->  Python parse/validate  ->  Bronze tables  ->  Neon Postgres
```

This repo covers **only** the JSON → Bronze ingestion. Bronze → Silver and
Silver → destination export are intentionally out of scope.

The Bronze tables, columns, and metadata columns are derived from the
`Bronze Layer` and `Logging` sheets of `FT_Tracker2_0_Tables_Schema-Draft.xlsx`.

---

## Bronze tables

Seven business tables plus a run log, all in the `bronze` schema:

| Table                  | Grain                                  | Populated by feed |
|------------------------|----------------------------------------|-------------------|
| `gtran_firm`           | one row per firm transportation contract | `gTRAN_FIRM`    |
| `gtran_loc`            | one row per contract location          | `gTRAN_FIRM`      |
| `gtran_rates`          | one row per contract rate              | `gTRAN_FIRM`      |
| `gtran_it`             | one row per interruptible contract     | `gTRAN_IT`        |
| `gtran_it_loc`         | one row per IT contract location       | `gTRAN_IT`        |
| `gtran_it_rates`       | one row per IT contract rate           | `gTRAN_IT`        |
| `gindex`               | one row per Index-of-Customers record  | `gINDEX`          |
| `ingestion_log`        | one row per pipeline run               | (all)             |

A single firm payload fans out into **three** tables (`gtran_firm` +
`gtran_loc` + `gtran_rates`) because each contract carries nested `locations`
and `rates` arrays.

Every business table also carries these pipeline-owned metadata columns:
`raw_record_id`, `hash_key`, `pipeline_run_id`, `source_system`, `source_api`,
`source_file_name`, `ingestion_timestamp`, `updated_ts`, `ingestion_status`,
`raw_payload` (JSONB).

---

## Project layout

```
pipeline_accelerator_bronze/
├── data/
│   └── sample_natgashub_contract.json   # test payload (firm feed)
├── sql/
│   └── create_bronze_tables.sql         # generated DDL (schema + 7 tables + log)
├── src/
│   ├── config.py                        # env-driven settings + RunContext
│   ├── main.py                          # CLI orchestrator
│   ├── db/
│   │   ├── connection.py                # writer factory keyed by DB_TYPE
│   │   └── writer.py                    # BronzeWriter ABC + Postgres impl + Azure stub
│   └── bronze/
│       ├── schemas.py                   # single source of truth: columns + DDL generator
│       ├── validators.py                # payload + record validation
│       ├── router.py                    # feed registry / multi-table fan-out
│       └── transformers.py              # flatten, map columns, add metadata + hash
├── .github/workflows/bronze_ingest.yml  # sample CI workflow
├── .env.example
├── requirements.txt
└── README.md
```

## Idempotency / duplicate loads

Each row gets a `hash_key` = SHA-256 over its **business** field values (metadata
excluded). Every Bronze table has `UNIQUE (hash_key)`, and the Postgres writer
inserts with `ON CONFLICT (hash_key) DO NOTHING`. Re-ingesting the same payload
therefore inserts **zero** new rows — the load is idempotent. The run log
reports `rows_written` as the count of genuinely new rows.

To treat re-loads as updates instead of no-ops, change the writer's conflict
clause to `DO UPDATE SET updated_ts = now(), ingestion_status = EXCLUDED.ingestion_status`.

---

## Validation behaviour

- **Structural** problems (missing/unknown `feedType`, unreadable file) abort the
  run with exit code `2` and a clear message.
- **Record-level** missing required fields do **not** abort. The record is still
  landed in Bronze with `ingestion_status = 'INVALID'` (so nothing is lost) and
  counted under `rows_rejected` in the log. This is the standard "quarantine in
  place" raw-zone pattern.

---

## Swapping the database (Neon → Azure SQL later)

Nothing outside `src/db/` knows which database is in use. To migrate:

1. Implement `AzureSqlBronzeWriter` in `src/db/writer.py` (a documented stub is
   already there — use `pyodbc`, store `raw_payload` as `NVARCHAR(MAX)`, and
   replace `ON CONFLICT` with a `MERGE`).
2. Set `DB_TYPE=azure_sql` and `AZURE_SQL_CONNECTION_STRING` in the environment.

`main.py`, the router, transformers, and validators are unchanged.

---

## Running from GitHub Actions

This same `python -m src.main` command is what "GitHub Actions Workflow 1" in the
architecture diagram runs. The only differences from local execution are where
the secrets and the input file come from:

- **Secrets** — store the Neon connection string as a repo secret
  (`Settings → Secrets and variables → Actions`) named `DATABASE_URL`. The
  workflow exposes it as an env var; the code reads it exactly as it does
  locally, so no code changes are needed. The same pattern holds for a future
  `NATGASHUB_API_KEY` and, later, `AZURE_SQL_CONNECTION_STRING`.
- **Input** — in production an earlier workflow step calls the NatGasHub API
  (using the API-key secret) and writes the JSON into `data/`; this ingestion
  step then loads that file. The sample workflow in
  `.github/workflows/bronze_ingest.yml` runs on an hourly schedule and on manual
  dispatch, installs `requirements.txt`, and invokes
  `python -m src.main --file <path> --create-tables`.

Because every secret comes from the environment and nothing is hardcoded, the
script is portable across local, GitHub Actions, and any other runner without
modification.
