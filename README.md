Contact-Centre Analytics Platform

A contact-centre analytics pipeline demonstrating multi-source ingestion, dbt transformation, and self-serve BI on a conformed dimensional model.

Problem

Contact-centre data rarely arrives in one shape. This project models a common reality: two ticketing systems that describe the same events differently — one ticket-based, one conversation-based — with mismatched field casing and time units (seconds vs milliseconds). Agents are identified differently in each source, and every campaign carries its own SLA target.

The goal is a single conformed model that answers "are we hitting SLA, per campaign?" without writing bespoke logic for each new source or campaign.

Architecture
Sources                         Load / Landing        Warehouse        Transform              BI
─────────────────────────────   ───────────────       ─────────        ───────────────────    ─────────
Zendesk-shape JSON (sec) ─┐
Intercom-shape JSON (ms) ─┤
Agent roster CSV ─────────┼──►  Python load+dedupe ──► Postgres (raw) ─► dbt                ─► Metabase
SLA targets CSV ──────────┘     (idempotent, PK)                          staging (views)
                                                                          marts   (tables)

In production the Python load step is replaced by an orchestrator (e.g. Azure Data Factory or Airflow) and the landing zone is object storage (Parquet/JSON), not the warehouse. Everything downstream of the raw layer is identical — that boundary is deliberate.

Key design decisions
Staging = views, marts = tables. Staging holds the conforming logic (renames, unit conversion, source alignment) and stays live as views. Marts are materialised as tables so the dashboard reads fast.
Marts are the semantic layer. Joins are resolved in SQL inside the marts, not as relationships in the BI tool. The BI layer reads a flat, query-ready fact table.
SLA targets are config, not code. Targets live in a raw_sla_targets table. Adding a campaign is a config row, not a code change — the same within_sla logic scales to N campaigns.
Normalise units once. The millisecond→second conversion happens a single time, in staging, so nothing downstream has to know a source's original unit.
Agent identity resolution. Source-specific agent IDs are resolved to a single employee ID via a mapping in the agent dimension. SCD Type 2 is designed but not built here — the dimension is a current snapshot — because in production agents move between campaigns and you'd want history preserved.
Idempotent load. The load step dedupes on primary key, so re-running it is safe and produces no drift.
Data model
Model	Type	Purpose
stg_zendesk	view	Conforms ticket-shaped source to the common contact model
stg_intercom	view	Conforms conversation-shaped source; converts ms→sec
dim_agent	table	Resolves source agent IDs to employee ID
dim_date	table	Calendar dimension (built as a dbt model — semantic layer is dbt, not BI)
fct_contacts	table	Unions both sources; joins SLA targets, agent, date; computes within_sla per campaign target and resolution_minutes
Quickstart

Requires Docker and Python 3.

bash
# 1. Start Postgres + Metabase
docker compose up -d

# 2. Generate synthetic source data
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python generate_data.py

# 3. Load raw sources into Postgres (idempotent)
python load_to_postgres.py

# 4. Build the dbt models
cd orion_dbt
export DBT_PROFILES_DIR=$(pwd)
dbt run

# 5. Open Metabase
# http://localhost:3000  — connect to the Postgres container and explore the dashboard
Project structure
.
├── docker-compose.yml       # Postgres + Metabase
├── generate_data.py         # Synthetic multi-source generator (seeded, injects realistic mess)
├── load_to_postgres.py      # Raw load + PK dedupe
├── requirements.txt
└── orion_dbt/
    ├── models/
    │   ├── staging/         # stg_zendesk, stg_intercom (views)
    │   └── marts/           # dim_agent, dim_date, fct_contacts (tables)
    └── dbt_project.yml
Synthetic data

generate_data.py is seeded for reproducibility and deliberately produces two different source shapes — snake_case ticket records with waits in seconds, and camelCase conversation records with waits in milliseconds — plus an agent roster and SLA config. It also injects realistic data-quality issues (duplicate rows, whitespace in agent IDs, null and negative wait times) so the pipeline's dedupe, conforming, and quarantine logic have something real to handle.

Production considerations

What would change moving this from a local demo to production:

Orchestration — replace the Python load scripts with ADF or Airflow; the landing zone becomes object storage (Parquet for file/CRM sources, raw JSON from ticketing APIs).
SCD Type 2 on the agent dimension to preserve history as agents change campaigns.
Change data capture for near-real-time ingestion where source systems support it.
Data contracts at each source boundary and formal incident postmortems for pipeline failures.
