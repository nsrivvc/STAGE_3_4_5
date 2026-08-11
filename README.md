# Silver Staging (Stages 3–4)

A modular batch system that reads **Bronze** tables from a data source, applies
transformation logic, and writes curated **Silver** tables. This repo handles
**only** Bronze → Silver. Ingestion (JSON → Bronze) and export (Silver →
downstream) live elsewhere.

Each Silver table is its own self-registering module, so new transformations are
added by dropping in a file — no central list to edit.

## Pipeline stages

Transformations are grouped by stage, then by component. **Most of this is
scaffolding**: the folders and the runner wiring exist, the business logic does
not. Current state:

| Stage | Component | Status |
|---|---|---|
| — | `silver_firm_transport_rate` | **Implemented** — the worked example |
| 3 | `decompisition/` | Scaffolded, empty `logic.txt` |
| 3 | `standardization/` | Scaffolded, empty `logic.txt` |
| 3 | `deduplication/` | Scaffolded, empty `logic.txt` |
| 3 | `ammendments/` | Scaffolded, empty `logic.txt` |
| 4 | `rec_del_pairing/` | **Wired end-to-end**, two business rules pending |
| 4 | `master_capacity/` | Scaffolded, empty `logic.txt` |

Stage 3 splits each feed into core / locations / rates per type, standardizes and
deduplicates it, and applies amendments. Stage 4 pairs receipts to deliveries and
assembles master capacity.

> The stage-3 folders contain no `.py` files, so `find -name "*.py"` won't show
> them and git won't track the empty directories. They exist.

### What still needs business rules

- **Stage 3 in full.** Nothing is written. Rec-del pairing reads stage 3's
  locations tables, so those are the first thing worth filling in.
- **Rec-del pairing: two hooks**, marked `SPEC:` in
  `src/transformations/stage_4/rec_del_pairing/pairing_base.py`:
  - `pair_predicate_sql()` — how a receipt matches a delivery. The placeholder
    pairs every receipt with every delivery on the same contract.
  - `term_columns_sql()` — the term transform. The placeholder passes the raw
    window through and leaves `term_days` / `term_category` NULL.
- **Master capacity in full.** The target model already exists as
  `public.final_core_master_capacity` (27 columns). Note it lives in `public`
  with PascalCase columns, unlike everything else this repo writes — worth
  deciding whether to target it as-is or a Silver-schema equivalent.

Only **firm** and **interruptible** have ingestion feeds today. The **awards**
and **IOC** pairing transformations are written but dormant: the runner reports
them as skipped until their source tables appear, then they start working with no
code change.

## Architecture

```
run.py                        CLI: --list / --table / --group / --all / --show-sql / --inspect
src/
  config.py                   env-driven settings (DB URL, schema names, log level)
  logging_config.py           logging setup (stdout)
  db/connection.py            SQLAlchemy engine factory (the only driver-aware file)
  core/
    base.py                   SilverTransformation base class (the shared pattern)
    registry.py               @register decorator + REGISTRY
    runner.py                 run one / group / all: per-table transaction, checks, logging
    inspect.py                read-only Bronze/Silver snapshot + readiness
  transformations/
    __init__.py               auto-discovers every module, recursively
    silver_firm_transport_rate.py   implemented example
    stage_3/
      decompisition/ standardization/ deduplication/ ammendments/
    stage_4/
      rec_del_pairing/
        pairing_base.py       shared pairing logic + the two SPEC hooks
        silver_{firm,interruptible,awards,ioc}_rec_del_pair.py
      master_capacity/
        awards/ firms/ index/ interruptibles/    per-type assembly
        final/{core,locations,rates}/            the three FINAL tables
```

Folders are named `stage_3` / `stage_4`, not `stage 3`, because they are imported
as Python packages.

- **One file per Silver table.** Each subclasses `SilverTransformation` and
  provides `table_name`, `create_table_sql()`, and `transform_sql()`.
- **Per-table transactions.** The runner runs each transformation in its own
  `engine.begin()` block, so a failure rolls back cleanly and doesn't stop the
  others. It also checks the required source tables exist first (skips with a
  clear message if not).
- **Sources aren't always Bronze.** A transformation declares `source_schema`;
  it defaults to Bronze, and rec-del pairing overrides it to read the
  decomposition phase's output instead. `--inspect` follows this, so readiness
  is reported against the right schema.
- **Load-once, then skip.** Before doing anything, the runner checks whether
  `silver_schema.table_name` already exists. If it does, the transformation is
  skipped entirely — no `CREATE TABLE`, no `INSERT`/`UPDATE`. A table is only
  ever populated on the run that creates it; reruns after that are a deliberate
  no-op, even if the underlying Bronze rows have changed. The SQL itself is
  still written idempotently (`CREATE TABLE IF NOT EXISTS` + a `UNIQUE` natural
  key + `ON CONFLICT DO UPDATE`) so a single first run can't produce duplicates,
  but that's the only protection — see [Reloading a table](#reloading-a-table)
  to force a refresh.
- **Driver-isolated.** Only `db/connection.py` imports the driver, so
  `--list` / `--show-sql` work with no database, and swapping databases later is
  contained to one file.

## Setup

```bash
python -m venv .venv && source .venv/bin/activate    # Windows: .venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env          # then edit DATABASE_URL to point at your Postgres
```

Schema names are all env-driven: `BRONZE_SCHEMA` (default `bronze`),
`SILVER_SCHEMA` (default `silver`), and `DECOMP_SCHEMA` (default
`silver_staging`) — the last is where rec-del pairing looks for the decomposition
phase's output, and must match wherever that phase actually writes.

For a local/dummy Postgres, the quickest option is Docker:

```bash
docker run --name pa-postgres -e POSTGRES_PASSWORD=postgres \
  -e POSTGRES_DB=pipeline -p 5432:5432 -d postgres:16
```

(That matches the default `DATABASE_URL` in `.env.example`.) This codebase
assumes the **Bronze tables already exist**; it reads them and writes Silver.

> Rec-del pairing uses `UNIQUE NULLS NOT DISTINCT`, which requires **Postgres
> 15+**, so that image tag is a floor for running stage 4 locally.

## Run

```bash
python run.py --list                                 # what's registered
python run.py --list-groups                          # what's registered, by folder
python run.py --inspect                              # snapshot tables + row counts (no transforms)
python run.py --show-sql silver_firm_transport_rate  # inspect SQL (no DB needed)
python run.py --table silver_firm_transport_rate     # run one transformation
python run.py --group rec_del_pairing                # run one component
python run.py --group stage_4                        # run a whole stage
python run.py --all                                  # run all of them
```

`--group` matches on any folder segment, so a component can be selected by its
own name (`rec_del_pairing`), by its stage (`stage_4`), or by the full path
(`stage_4/rec_del_pairing`). A folder that exists but holds no transformations
yet logs a warning and exits 0, so scheduled jobs can reference it before the
code lands.

Run `--inspect` before transforming to confirm which source tables exist and how
many rows they hold, and whether each transformation is READY (will run),
BLOCKED (missing a source), or SKIP (its Silver table already exists, so the run
would be a no-op). It's read-only — it never writes or alters data — so it's safe
to run anytime to check the state as data flows through. Run it again afterward
to see the new Silver row counts.

The run commands exit non-zero if any transformation fails, so a scheduler can
flag the job.

## Add a new Silver table

1. Copy `src/transformations/silver_firm_transport_rate.py` into the folder for
   its stage/component, e.g. `stage_4/master_capacity/final/core/`.
2. Change five things (each is commented in the example):
   - the class name and `name` (registry key / CLI name)
   - `table_name` (the bare table name created in the Silver schema — the
     runner checks for exactly this table to decide whether to skip the run)
   - `bronze_sources` (the tables you read)
   - `create_table_sql()` (your columns/types — must create `table_name`)
   - `transform_sql()` (your column mapping + business rules)
3. If it reads something other than Bronze, override `source_schema`.
4. Keep the idempotency pieces: `CREATE TABLE IF NOT EXISTS` with a `UNIQUE`
   natural key, and `INSERT … SELECT … ON CONFLICT (key) DO UPDATE`. They
   protect a single first run from producing duplicates; they do not cause
   later reruns to refresh anything, since the runner skips once the table
   exists.

That's it — `python run.py --list` will show it immediately. Discovery is
recursive, so no imports or registration boilerplate are needed in any folder.

> Most transformations are pure SQL. If one needs real Python logic, override
> `run(self, conn)` in your subclass instead of using the two SQL methods.

> For a family of near-identical transformations (one per transport type), put
> the shared SQL in a base class and keep the subclasses to just names — see
> `stage_4/rec_del_pairing/` for the pattern.

## Reloading a table

Because a transformation is skipped once its Silver table exists, picking up
new or corrected Bronze rows means dropping the table first:

```sql
DROP TABLE silver.firm_transport_rate;
```

Then rerun it:

```bash
python run.py --table silver_firm_transport_rate
```

`--inspect` will show `SKIP` for any transformation whose table is already
present — that's the signal a drop is needed before it will load again.

> This bites hardest while iterating on unfinished business rules: once a table
> is created, editing its SQL changes nothing until you drop it.

## Running it on a schedule

`run.py` is a plain batch command that reads all config from environment
variables, which makes it portable to any scheduler without code changes.

Three ready-to-use workflows are included, sequenced by cron offset so each
consumes freshly-built upstream tables:

| Workflow | File | Cron | Runs |
|---|---|---|---|
| `bronze-to-silver` | `.github/workflows/bronze_to_silver.yml` | `:30` | `--all` |
| `rec-del-pairing` | `.github/workflows/rec_del_pairing.yml` | `:45` | `--group rec_del_pairing` |
| `master-capacity` | `.github/workflows/master_capacity.yml` | `:55` | `--group master_capacity` |

(Bronze ingestion runs at `:00` in the upstream repo.) Each workflow:

- runs on its `cron` schedule and on manual dispatch;
- lets you pick `all` or a single transformation at dispatch time;
- reads the Neon connection string from the `DATABASE_URL` repo secret (the same
  secret used by the ingestion repo — Settings → Secrets and variables →
  Actions), and fails fast with a clear error if it isn't set;
- runs `python run.py --inspect` before and after, so the run log shows inputs
  and the resulting Silver row counts.

The two stage-4 workflows each have their own `concurrency` group, so a run never
collides with itself but the two stages don't block each other. They select work
by folder rather than by a hardcoded list, so modules added to those folders are
picked up with no workflow change.

`master-capacity` is safe to enable now: with nothing registered in that folder
it logs a warning and exits 0.

Because the two stage-4 workflows are separate, they relate only through the
clock — `:55` gives pairing a 10-minute window. If pairing ever outgrows it,
widen the offset or switch master capacity to a `workflow_run` trigger keyed on
pairing completing.

To run any of them: push the repo, add the `DATABASE_URL` secret, then Actions →
pick the workflow → **Run workflow**.

For other schedulers:

- **Azure Container Apps job** — build a small image (`python:3.11-slim`,
  `pip install -r requirements.txt`, `CMD ["python","run.py","--all"]`) and set
  `DATABASE_URL` as a secret/env var on the job.

Because nothing is hardcoded and logs go to stdout, the same command works
locally, in CI, and in a cloud job.
