# dbt on Snowflake: From Bronze to Gold

*Your Bronze table is a giant VARIANT blob. Let's turn it into something an analyst can actually query — in 3 SQL files.*

![Article 3 Cover](../docs/diagrams/art3-00-cover.png)

**Reading Time:** 10 minutes
**Difficulty:** Intermediate
**Prerequisites:** Article 2 (working Bronze pipeline), dbt CLI installed, data in `EVENTS_DEV.BRONZE.RAW_TICKETS`
**Coffee Required:** One flat white. The SQL is elegant today.

---

> **What we're building:** A complete dbt project that transforms raw VARIANT JSON into typed Silver records, deduplicates them with QUALIFY, and aggregates them into Gold dimensions and facts. Three SQL files. Zero stored procedures.

---

## Why dbt (and Not Stored Procedures)

I used to write stored procedures for everything. "It runs inside Snowflake" was the justification. And it does. But here's what else it does:

- **No version control.** Your transformation logic lives in a Snowflake worksheet or a `CREATE OR REPLACE PROCEDURE` buried somewhere.
- **No lineage.** Which downstream tables break when you rename a column? Good luck finding out.
- **No tests.** You find out about data issues when the CFO asks why revenue dropped 40%.
- **No DRY.** The same QUALIFY dedup pattern copy-pasted across 12 procedures.

dbt solves all of this. Same SQL. Same Snowflake compute. But wrapped in a framework that gives you:

| Feature | Stored Procedure | dbt Model |
|---------|-----------------|-----------|
| Version control | Manual export/import | Git-native |
| Lineage | None | Auto-generated DAG |
| Testing | Write your own | Declarative YAML |
| Documentation | Comments (maybe) | Auto-generated site |
| Incremental logic | Hand-rolled IF/ELSE | `is_incremental()` macro |
| Idempotency | You build it | Built-in |

**The principle:** dbt models are SELECT statements. That's it. No DDL, no DML, no control flow. You write the query, dbt handles the materialization. It's the same separation of concerns we applied in Article 1 — but for transformations.

---

## Project Setup

Here's what our dbt project looks like:

```
dbt/
├── dbt_project.yml       # Project config: name, paths, schema routing
├── profiles.yml          # Connection config (no auth — Snowflake handles it)
├── profiles.yml.example  # Template for local dev (key-pair auth)
└── models/
    ├── silver/
    │   ├── schema.yml    # Source definition + model tests
    │   └── fact_tickets.sql
    └── gold/
        ├── schema.yml    # Model tests
        ├── dim_events.sql
        └── fact_revenue.sql
```

**Key difference from "normal" dbt:** This project runs *inside Snowflake* as a native dbt project. No local CLI. No worker machine running `dbt run`. Snowflake's compute executes the SQL directly. The `profiles.yml` has no password or key-pair — authentication is handled by the Snowflake session.

### `dbt_project.yml`

```yaml
name: 'events_pipeline'
version: '1.0.0'
config-version: 2

profile: 'events_pipeline'

models:
  events_pipeline:
    silver:
      +schema: SILVER
      +tags: ["tickets"]
    gold:
      +schema: GOLD
      +tags: ["gold"]
```

Two things to notice:
1. **Schema routing** — Silver models go to `EVENTS_DEV.SILVER`, Gold to `EVENTS_DEV.GOLD`. No hardcoding in the SQL.
2. **Tags** — We can run just Silver (`dbt run --select tag:tickets`) or just Gold (`dbt run --select tag:gold`) independently.

### Source Definition (in `silver/schema.yml`)

```yaml
sources:
  - name: bronze
    database: EVENTS_DEV
    schema: BRONZE
    tables:
      - name: raw_tickets
        description: Raw ticket records from EventHub API, stored as VARIANT.
```

This tells dbt: "When I reference `{{ source('bronze', 'raw_tickets') }}`, I mean `EVENTS_DEV.BRONZE.RAW_TICKETS`." One place to update if the table moves. One place for documentation. One place for freshness checks.

---

## The Silver Layer: Typing and Deduplication

This is where the real work happens. We take a VARIANT blob and produce a typed, deduplicated table that analysts can `SELECT *` from without a Snowflake semi-structured tutorial.

### `fact_tickets.sql` — Line by Line

```sql
{{ config(
    materialized='incremental',
    schema='SILVER',
    unique_key='ticket_id',
    tags=['tickets']
) }}

SELECT
    TICKET_DATA:ticket_id::STRING           AS ticket_id,
    TICKET_DATA:event_id::STRING            AS event_id,
    TICKET_DATA:event_name::STRING          AS event_name,
    TICKET_DATA:venue::STRING               AS venue,
    TICKET_DATA:category::STRING            AS category,
    TICKET_DATA:price::NUMBER(10,2)         AS price,
    TICKET_DATA:currency::STRING            AS currency,
    TICKET_DATA:status::STRING              AS ticket_status,
    TICKET_DATA:purchase_timestamp::TIMESTAMP_NTZ AS purchase_timestamp,
    TICKET_DATA:attendee_email_hash::STRING AS attendee_email_hash,
    BATCH_ID,
    LOADED_AT
FROM {{ source('bronze', 'raw_tickets') }}
WHERE TICKET_DATA:ticket_id IS NOT NULL

{% if is_incremental() %}
  AND LOADED_AT > (SELECT MAX(LOADED_AT) FROM {{ this }})
{% endif %}

QUALIFY ROW_NUMBER() OVER (PARTITION BY TICKET_DATA:ticket_id::STRING ORDER BY LOADED_AT DESC) = 1
```

Let me walk through what's happening.

### Flattening VARIANT

`TICKET_DATA:ticket_id::STRING` — this is Snowflake's semi-structured access syntax. `TICKET_DATA` is the VARIANT column. The colon (`:`) navigates into JSON keys. The double-colon (`::`) casts to a SQL type.

Why not `TICKET_DATA['ticket_id']`? Both work. The colon syntax is cleaner, and importantly, it's case-insensitive by default. Less brittle when upstream JSON changes casing.

### Incremental Materialization

![Incremental Logic](../docs/diagrams/art3-01-incremental-logic.png)

```yaml
materialized='incremental'
unique_key='ticket_id'
```

This tells dbt:
- **First run:** Execute the full SELECT, CREATE TABLE AS.
- **Subsequent runs:** Only process rows where the incremental predicate is true, then MERGE into the existing table using `ticket_id` as the match key.

The `is_incremental()` macro is the gate:

```sql
{% if is_incremental() %}
  AND LOADED_AT > (SELECT MAX(LOADED_AT) FROM {{ this }})
{% endif %}
```

On first run, `is_incremental()` returns false. The WHERE clause is just `WHERE TICKET_DATA:ticket_id IS NOT NULL`. The table doesn't exist yet, so `{{ this }}` would error — but it never gets evaluated.

On run 2+, it returns true. We only scan rows loaded *after* the last batch we processed. On a table with 10M rows, this means scanning 50 rows instead of 10M. The difference is real money at Snowflake scale.

**Why LOADED_AT and not purchase_timestamp?** Because LOADED_AT is monotonically increasing (set by our pipeline). Purchase_timestamp can be backdated — someone buys a ticket at 2pm but the API batches it at 3pm. If we used purchase_timestamp, we'd miss it.

### QUALIFY for Deduplication

![QUALIFY Dedup](../docs/diagrams/art3-02-qualify-dedup.png)

```sql
QUALIFY ROW_NUMBER() OVER (
    PARTITION BY TICKET_DATA:ticket_id::STRING
    ORDER BY LOADED_AT DESC
) = 1
```

This is Snowflake-specific syntax (PostgreSQL doesn't have QUALIFY). It filters *after* window functions are evaluated. Think of it as a WHERE clause that can reference window results.

**What it does:** If the same `ticket_id` appears in multiple batches (API retry, status update, correction), keep only the *most recent* version based on `LOADED_AT`.

**Why not DISTINCT?** DISTINCT deduplicates on all columns. If price changes from $100 to $110 (partial refund), DISTINCT keeps both rows. QUALIFY keeps only the latest.

**Why not a separate staging model?** Some teams create a `stg_tickets` model for dedup and a `fact_tickets` model for typing. That works, but it's an extra table scan for simple cases. QUALIFY handles both in one pass.

---

## The Gold Layer: Business-Ready Aggregations

Gold is where we serve analysts. Clean dimensions, pre-aggregated facts, no VARIANT in sight.

### `dim_events.sql`

```sql
{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold']
) }}

WITH events AS (
    SELECT DISTINCT
        event_id,
        event_name,
        venue
    FROM {{ ref('fact_tickets') }}
    WHERE event_id IS NOT NULL
)

SELECT
    ROW_NUMBER() OVER (ORDER BY event_id) AS event_key,
    event_id,
    event_name,
    venue,
    CURRENT_TIMESTAMP() AS created_at
FROM events
```

Simple. Distinct events from Silver, with a surrogate key. In Article 4, when we add TicketFlow and LivePass as additional sources, this dimension will grow a `source_platforms` array and cross-platform matching logic. For now, it's one source, one dimension.

**Why `materialized='table'` and not `incremental`?** Dimensions are small. Our events table has maybe 20–50 rows. Full refresh costs nothing and ensures consistency. Save incremental for the big fact tables.

### `fact_revenue.sql`

```sql
{{ config(
    materialized='table',
    schema='GOLD',
    tags=['gold']
) }}

SELECT
    purchase_timestamp::DATE AS revenue_date,
    event_id,
    event_name,
    category,
    COUNT(*) AS total_tickets,
    SUM(price) AS total_revenue,
    ROUND(AVG(price), 2) AS avg_ticket_price
FROM {{ ref('fact_tickets') }}
WHERE ticket_status NOT IN ('cancelled', 'refunded')
GROUP BY
    purchase_timestamp::DATE,
    event_id,
    event_name,
    category
```

Three decisions here:

1. **Exclude cancelled/refunded** — revenue means money that actually came in. The WHERE filter is the business rule.
2. **Group by date + event + category** — this is the grain. One row = one day × one event × one category. Fine for dashboards. If you need ticket-level, query Silver.
3. **Three metrics** — `total_tickets`, `total_revenue`, `avg_ticket_price`. Enough to answer "how did VIP do last week?" without a 30-second query.

---

## Testing: Your Data Contract

Tests in dbt are YAML declarations that run as queries. If a test fails, `dbt test` exits non-zero. In production, that blocks the pipeline.

```yaml
models:
  - name: fact_tickets
    columns:
      - name: ticket_id
        tests:
          - not_null
          - unique
      - name: category
        tests:
          - accepted_values:
              values: ["VIP", "Premium", "Standard", "General Admission"]
      - name: ticket_status
        tests:
          - accepted_values:
              values: ["confirmed", "pending", "cancelled", "refunded"]
      - name: currency
        tests:
          - accepted_values:
              values: ["USD"]
```

What each test does:

| Test | Generated SQL | What It Catches |
|------|--------------|-----------------|
| `not_null` | `SELECT * WHERE ticket_id IS NULL` | Missing IDs from bad upstream data |
| `unique` | `SELECT ticket_id HAVING COUNT(*) > 1` | Dedup logic failure |
| `accepted_values` | `SELECT * WHERE category NOT IN (...)` | Schema drift, new categories |

**Tests are a data contract.** When the API starts sending a new category "Early Bird" that we don't handle, the `accepted_values` test fails. We find out in CI, not in the dashboard. We decide: add "Early Bird" to the list, or filter it. Either way, it's a conscious decision.

---

## Running It: Native dbt on Snowflake

### Step 1: Deploy the Project

We deploy the dbt project to Snowflake using the `snow` CLI. This uploads the models, schema files, and profiles as a **native Snowflake object** — no external compute required.

```bash
snow dbt deploy EVENTS_PIPELINE \
  --source ./dbt \
  --database EVENTS_DEV \
  --schema ORCH
```

That's it. The project now lives inside Snowflake. You can see it:

```sql
SHOW DBT PROJECTS IN EVENTS_DEV.ORCH;
```

### Step 2: Run Models

```bash
# Run all models (Silver → Gold)
snow dbt execute --database EVENTS_DEV --schema ORCH EVENTS_PIPELINE run

# Silver only
snow dbt execute --database EVENTS_DEV --schema ORCH EVENTS_PIPELINE run --select tag:tickets

# Gold only
snow dbt execute --database EVENTS_DEV --schema ORCH EVENTS_PIPELINE run --select tag:gold

# Full refresh (rebuilds incremental tables from scratch)
snow dbt execute --database EVENTS_DEV --schema ORCH EVENTS_PIPELINE run --full-refresh
```

### Step 3: Run Tests

```bash
snow dbt execute --database EVENTS_DEV --schema ORCH EVENTS_PIPELINE test
```

### Or via SQL (for Airflow integration)

```sql
-- Run models
EXECUTE DBT PROJECT EVENTS_DEV.ORCH.EVENTS_PIPELINE ARGS = 'run';

-- Run tests
EXECUTE DBT PROJECT EVENTS_DEV.ORCH.EVENTS_PIPELINE ARGS = 'test';

-- Silver only
EXECUTE DBT PROJECT EVENTS_DEV.ORCH.EVENTS_PIPELINE ARGS = 'run --select tag:tickets';
```

### Expected Output

```
Running with dbt=1.9.4
Found 3 models, 15 data tests, 1 source, 475 macros

Concurrency: 4 threads (target='dev')

1 of 3 START sql incremental model SILVER.fact_tickets ................... [RUN]
1 of 3 OK created sql incremental model SILVER.fact_tickets .............. [SUCCESS 0 in 1.48s]
2 of 3 START sql table model GOLD.dim_events ............................. [RUN]
3 of 3 START sql table model GOLD.fact_revenue ........................... [RUN]
2 of 3 OK created sql table model GOLD.dim_events ....................... [SUCCESS 1 in 0.62s]
3 of 3 OK created sql table model GOLD.fact_revenue ..................... [SUCCESS 1 in 0.66s]

Finished running 1 incremental model, 2 table models in 0 hours 0 minutes and 3.56 seconds

Completed successfully

Done. PASS=3 WARN=0 ERROR=0 SKIP=0 TOTAL=3
```

**Notice:** dbt ran inside Snowflake's compute — not on your laptop, not on an Airflow worker. Zero data left the cloud.

---

## The Medallion Architecture: What Just Happened

![Medallion Flow](../docs/diagrams/art3-03-medallion-flow.png)

Let's trace one record through the full pipeline:

1. **API** → EventHub returns `{"ticket_id": "EVH-20260628-000142", "price": 425.50, ...}`
2. **Bronze** → Landed as a VARIANT blob in `RAW_TICKETS`. No transformation. Just a raw backup.
3. **Silver** → dbt flattens, types, and deduplicates. Now it's `ticket_id STRING, price NUMBER(10,2)`. Analysts can query it.
4. **Gold** → dbt aggregates into `fact_revenue`. "VIP tickets for Music Festival 2026 on June 28: 14 tickets, $5,957 revenue."

Each layer has a purpose:
- **Bronze:** Immutable landing zone. Never transform here. This is your insurance policy.
- **Silver:** Typed, deduplicated, queryable. The "source of truth" for detailed analysis.
- **Gold:** Pre-aggregated, business-ready. Fast dashboards, no complex joins.

---

## Connecting to the DAG: What Comes Next

The project is deployed. In production, Airflow triggers it after Bronze confirms — with a single SQL statement:

```python
t_dbt_run = SnowflakeSqlApiOperator(
    task_id="dbt_run_silver",
    sql="EXECUTE DBT PROJECT EVENTS_DEV.ORCH.EVENTS_PIPELINE ARGS = 'run --select tag:tickets';",
    snowflake_conn_id="snowflake_default",
)

t_dbt_test = SnowflakeSqlApiOperator(
    task_id="dbt_test",
    sql="EXECUTE DBT PROJECT EVENTS_DEV.ORCH.EVENTS_PIPELINE ARGS = 'test';",
    snowflake_conn_id="snowflake_default",
)
```

No BashOperator. No `pip install dbt-snowflake` on the worker. No `profiles.yml` secrets in Airflow. Snowflake handles compute, authentication, and execution. Airflow sends one SQL command and observes the result.

The key insight: **the DAG doesn't care about SQL.** It cares about completion and failure. `EXECUTE DBT PROJECT` succeeds or fails. Airflow routes on that signal.

---

## What's Next

In **Article 4**, we add two more sources (TicketFlow and LivePass), run them in parallel with TaskGroups, and build a unified Gold layer that matches events across platforms. The dbt models grow from 3 to 8. The DAG grows from sequential to concurrent. Production complexity, still under control.

---

**Repository:** [github.com/mcharni76/airflow-snowflake-how-to](https://github.com/mcharni76/airflow-snowflake-how-to) — tag `v0.2`

---

*About the Author: [Marawen Charni](https://www.linkedin.com/in/mcharni) is a Solutions Engineer at Snowflake, based in the Middle East. He believes the best pipeline is one where Airflow does almost nothing.*

*Follow on Medium: [@marawen.cherni](https://medium.com/@marawen.cherni)*

---

### A Note on How This Article Came to Be

> **Figures:** Generated with **Gemini** in infographic style.
> **Content:** Assisted by **Snowflake Cortex Code**.
> **Experience:** Based on a real production pipeline (redacted and genericized).
