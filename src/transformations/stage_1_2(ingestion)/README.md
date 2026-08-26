# Stage 1-2 — Mock NatGasHub API + Bronze Ingestion

This subproject of `nsrivvc/STAGE_3_4_5` (it was the standalone
`json--bronze--postgres` repo before the merge) is stages 1 and 2 of the
pipeline:

```
STAGE 1: mock NatGasHub API (src/mock_api) serves the JSON feeds over HTTP
STAGE 2: Python parse/validate/route/transform (src/bronze) -> Bronze tables on Neon
```

Bronze → Silver (stages 3-5) lives in the parent repo's `src/transformations/`
stage folders and is run by its own workflows.

The Bronze tables, columns, and metadata columns are derived from the
`Bronze Layer` and `Logging` sheets of `FT_Tracker2_0_Tables_Schema-Draft.xlsx`.

---

## Running the mock API (stage 1) and accessing the data

The API is a FastAPI app that impersonates NatGasHub by serving the JSON
fixtures in this subproject's `data/` folder verbatim. Run it **from this
subproject's folder** (the `src.mock_api.app` module path resolves against the
current directory):

```powershell
cd "src\transformations\stage_1_2(ingestion)"     # from the repo root
python -m uvicorn src.mock_api.app:app --host 127.0.0.1 --port 8000
```

(First time only: `pip install -r requirements.txt` for fastapi/uvicorn. Add
uvicorn's `--reload` flag to auto-restart while editing the API code.)

Then access the data:

| URL | Returns |
|---|---|
| `http://127.0.0.1:8000/health` | liveness check |
| `http://127.0.0.1:8000/docs` | interactive Swagger UI for all endpoints |
| `http://127.0.0.1:8000/api/firms` | `data/firms_test.json` (firm contracts, nested locations/rates) |
| `http://127.0.0.1:8000/api/interruptibles` | `data/interruptibles_test.json` (IT contracts) |
| `http://127.0.0.1:8000/api/ioc` | `data/ioc_test.json` (Index of Customers) |
| `http://127.0.0.1:8000/api/awards` | `data/awards_test.json` (capacity release awards) |

To change what the API serves, edit the fixture file — the endpoints return the
JSON unchanged. Browser consumers on localhost ports 3000/5173/8080 are allowed
by CORS out of the box; override with a comma-separated `MOCK_API_CORS_ORIGINS`
env var.

**In GitHub Actions you never start it yourself**: every `bronze_ingest_*.yml`
workflow boots its own copy inside the runner, fetches the feed into
`data/_fetched_*.json`, hands that file to `python -m src.main`, and the server
dies with the job. Pointing at the real NatGasHub later means replacing the
"Start mock" + fetch steps with a call to the live endpoint and an API-key
secret.

---

## Bronze tables

Four business tables plus a run log, all in the `bronze` schema:

| Table           | Grain                                     | Populated by feed |
|-----------------|-------------------------------------------|-------------------|
| `gtran_firm`    | one row per firm transportation contract  | `gTRAN_FIRM`      |
| `gtran_it`      | one row per interruptible contract        | `gTRAN_IT`        |
| `gindex`        | one row per Index-of-Customers record     | `gINDEX`          |
| `gawd`          | one row per capacity release award        | `gAWD`            |
| `ingestion_log` | one row per pipeline run                  | (all)             |

Each contract row carries its `locations` and `rates` **nested** — as text
columns and as arrays inside the `raw_payload` JSONB. There are no separate
location/rate tables in Bronze; stage 3's deduplication phase explodes the
nested arrays into `silver_staging.*_locations` / `*_rates`.

Every business table also carries these pipeline-owned metadata columns:
`raw_record_id`, `hash_key`, `pipeline_run_id`, `source_system`, `source_api`,
`source_file_name`, `ingestion_timestamp`, `updated_ts`, `ingestion_status`,
`raw_payload` (JSONB).

---

## Project layout

This subproject lives at `src/transformations/stage_1_2(ingestion)/` in the
parent repo. Its five workflows sit at the repo root (`.github/workflows/
bronze_ingest*.yml` — GitHub only runs root-level workflow files) with
`defaults.run.working-directory` pointed back here.

```
stage_1_2(ingestion)/
├── data/
│   ├── firms_test.json                  # feed fixtures the mock API serves
│   ├── interruptibles_test.json         #   (plus ioc/awards + older versions;
│   ├── ioc_test.json                    #   _fetched_*.json are gitignored
│   └── awards_test.json                 #   per-run downloads)
├── sql/
│   └── create_bronze_tables.sql         # generated DDL (schema + 4 tables + log)
├── src/
│   ├── config.py                        # env-driven settings + RunContext
│   ├── main.py                          # CLI orchestrator (python -m src.main)
│   ├── parquet_export.py                # pre-load Parquet export of every Bronze row
│   ├── mock_api/                        # STAGE 1: FastAPI mock of NatGasHub
│   │   ├── app.py                       #   endpoints (see "Running the mock API")
│   │   └── loader.py                    #   serves data/ fixtures verbatim
│   ├── db/
│   │   ├── connection.py                # writer factory keyed by DB_TYPE
│   │   └── writer.py                    # BronzeWriter ABC + Postgres impl + Azure stub
│   └── bronze/                          # STAGE 2: JSON -> Bronze
│       ├── schemas.py                   # single source of truth: columns + DDL generator
│       ├── validators.py                # payload + record validation
│       ├── router.py                    # feed registry -> target table
│       ├── coerce.py                    # tolerate structure delivered as JSON text
│       └── transformers.py              # flatten, map columns, add metadata + hash
├── .env.example                         # template; real .env is gitignored
├── requirements.txt                     # psycopg 3, pyarrow, fastapi, uvicorn
└── README.md
```

## Idempotency / duplicate loads

Bronze keeps every load, duplicates included — re-ingesting the same payload
lands the batch again. Stage 3's deduplication(p1) is the one place duplicate
rows are dropped: it compares the rows' own data fields itself, with no help
from this stage. (Each row still carries a `hash_key` content fingerprint,
stamped for traceability only.)

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
- **Input** — each `bronze_ingest_*.yml` workflow (at the parent repo's root)
  starts the in-repo mock API, fetches the feed into `data/_fetched_*.json`,
  and invokes `python -m src.main --file <path> --create-tables`. The
  `bronze_ingest.yml` fan-out runs all four feeds in parallel after applying
  the DDL once; the feed orchestrators (`firm(stage3_4_5).yml` etc.) call the
  same ingest workflow as their first job, then chain stages 3-4-5 and the
  finals after it. No schedules — every run is a manual dispatch or an
  orchestrator call.

Because every secret comes from the environment and nothing is hardcoded, the
script is portable across local, GitHub Actions, and any other runner without
modification.
