# Airflow + Snowflake: The Right Way

> A hands-on reference architecture for combining Apache Airflow with Snowflake, following the principle: **Airflow orchestrates, Snowflake executes.**

[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

---

## What This Is

A complete, runnable implementation of the **Snowflake Reference Architecture for Airflow Integration** — demonstrating how to build production-grade data pipelines where:

- **Airflow** is the control plane (fetch data, upload files, observe completion)
- **Snowflake** is the runtime (stage, stream, triggered task, dbt transform)
- **No data transformation happens in Airflow** — ever

This repo accompanies the Medium article series: **"Airflow + Snowflake: The Right Way"**

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────────┐
│  Docker Compose (Your Machine)                                          │
│                                                                         │
│  ┌──────────────┐     ┌──────────────────────────────────────────────┐ │
│  │  Mock API    │     │  Airflow (control plane only)                │ │
│  │  :8099       │────▶│  webserver :8080 │ scheduler │ triggerer     │ │
│  │  /docs (UI)  │     │                                              │ │
│  └──────────────┘     └─────────────────────┬────────────────────────┘ │
│                                             │                           │
│                                             │ PUT file (sync)           │
└─────────────────────────────────────────────┼───────────────────────────┘
                                              │
                                              ▼
┌─────────────────────────────────────────────────────────────────────────┐
│  Snowflake                                                              │
│                                                                         │
│  @STAGE ──▶ Directory Stream ──▶ Triggered Task ──▶ BRONZE (MERGE)     │
│                                                        │                │
│                                                        ▼                │
│                                               dbt (SILVER → GOLD)       │
└─────────────────────────────────────────────────────────────────────────┘
```

### The Core Principle

| Layer | Owner | Does | Does NOT |
|-------|-------|------|----------|
| Airflow | You (Docker) | Call APIs, handle pagination, PUT files, observe | Transform, join, deduplicate, aggregate |
| Snowflake | Snowflake | Stage → Stream → Task → Bronze → Silver → Gold | Call external APIs, manage schedules |

---

## Article Series

| # | Article | What You Learn | Code Tag |
|---|---------|---------------|----------|
| 1 | [Stop Using Airflow Wrong](#) | Architecture philosophy | `repo-live` |
| 2 | [Incremental CDC Pipeline](#) | Watermarks + triggered tasks | `v0.1` |
| 3 | [dbt: Bronze to Gold](#) | Incremental models + QUALIFY dedup | `v0.2` |
| 4 | [Multi-Source TaskGroups](#) | Parallel ingestion from 3 APIs | `v0.3` |
| 5 | [10 Gotchas](#) | War stories that save you days | `v0.4` |
| B1 | [Airflow on SPCS](#) | Enterprise self-hosted in Snowflake | `v1.0-spcs` |
| B2 | [Migrating to MWAA](#) | AWS managed Airflow + Snowpipe | `v1.0-mwaa` |

Each article builds on the previous one. Git tags mark the state of the repo at each article's publication.

---

## Quick Start

### Prerequisites

- Docker Desktop
- A Snowflake account (trial works fine)
- Private key (.p8) configured for your Snowflake user

### 1. Clone and Configure

```bash
git clone https://github.com/<your-username>/airflow-snowflake-how-to.git
cd airflow-snowflake-how-to
cp .env.example .env
# Edit .env with your Snowflake account details
```

### 2. Set Up Snowflake Objects

```bash
# Run scripts 01-05 in Snowsight or your SQL tool of choice
snowflake/01_setup_environment.sql
snowflake/02_create_stage_and_stream.sql
snowflake/03_create_bronze_objects.sql
snowflake/04_create_orch_objects.sql
snowflake/05_create_triggered_task.sql
```

### 3. Start the Stack

```bash
docker compose up --build -d
```

### 4. Trigger the Pipeline

Open http://localhost:8080 (admin/admin), find the DAG, unpause it, and trigger.

---

## Project Structure

```
airflow-snowflake-how-to/
├── docker-compose.yaml          # Full local stack
├── .env.example                 # Configuration template
├── mock-api/                    # Simulated vendor API (FastAPI)
├── airflow/                     # DAGs (control plane only)
│   └── dags/
│       ├── single_source_pipeline.py
│       └── multi_source_pipeline.py
├── snowflake/                   # DDL scripts (numbered, idempotent)
├── dbt/                         # Transformation models
│   └── models/{silver,gold}/
├── spcs/                        # Bonus: Enterprise SPCS deployment
├── mwaa/                        # Bonus: AWS MWAA migration guide
├── tests/                       # Unit + E2E tests
├── articles/                    # Medium article sources (markdown)
└── docs/                        # Architecture decisions + diagrams
```

---

## Design Decisions

| Decision | Rationale |
|----------|-----------|
| Internal stage (not S3) | Local dev — no cloud bucket needed |
| Key-pair auth (not password) | More secure, no password in env files |
| Triggered task (not scheduled) | Event-driven: runs only when files arrive |
| Reschedule sensor (not poke) | Frees Airflow worker while waiting |
| MERGE at Bronze | Idempotent: safe to replay any batch |
| QUALIFY at Silver | Deduplicate without separate staging table |
| Watermark in Snowflake table | Single source of truth (not XCom) |

For detailed ADRs, see [docs/DECISIONS.md](docs/DECISIONS.md).

---

## Running the Tests

```bash
pip install -r tests/requirements-test.txt
pytest tests/ -v
```

---

## Deployment Options (Covered in Bonus Articles)

| Option | Article | Best For |
|--------|---------|----------|
| **Docker Compose** | Articles 1-5 | Local dev, learning, demos |
| **SPCS (Snowflake)** | Bonus 1 | Enterprise: zero-egress, single bill, same RBAC |
| **Amazon MWAA** | Bonus 2 | AWS shops wanting fully managed |
| **Astronomer** | — | Teams wanting premium managed Airflow |
| **GCP Cloud Composer** | — | GCP-native shops |

---

## Contributing

This is a reference implementation, not a product. Issues and PRs welcome for:
- Bug fixes
- Documentation improvements
- Additional gotchas
- Language/framework-specific variations

---

## License

MIT — see [LICENSE](LICENSE)

---

## Author

**Marawen Charni** — Solutions Engineer at Snowflake, based in the Middle East. Building things that make data teams more productive.

- Medium: [@marawen](https://medium.com/@marawen)
- LinkedIn: [/in/marawen](https://linkedin.com/in/marawen)
