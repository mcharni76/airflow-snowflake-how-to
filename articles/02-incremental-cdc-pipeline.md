# Building an Incremental CDC Pipeline (Locally)

*You don't need S3 or a cloud account to simulate production patterns. Here's a full pipeline running on your laptop.*

![Article 2 Cover](../docs/diagrams/art2-00-cover.png)

**Reading Time:** 12 minutes
**Difficulty:** Intermediate
**Prerequisites:** Article 1 (the mental model), Docker installed, a Snowflake trial account
**Coffee Required:** Double shot. We're writing real code today.

---

> **What we're building:** A complete CDC pipeline that extracts data from a vendor API, lands it in Snowflake Bronze, and does it all incrementally — every 5 minutes, forever. The entire local stack runs in Docker. Snowflake handles the heavy lifting. Airflow touches the data for about 5 seconds per run.

---

## The Setup: What's Running Where

Before we write a single line of code, let's understand the architecture of our local development environment.

![Docker Stack](../docs/diagrams/art2-01-docker-stack.png)

Three containers. One cloud service. That's it.

| Component | What It Does | Port |
|-----------|-------------|------|
| **Mock API** | Simulates "EventHub" vendor — generates new tickets every 5 min | `:8099` |
| **Airflow** | Webserver + Scheduler + Triggerer — orchestrates the pipeline | `:8080` |
| **PostgreSQL** | Airflow's metadata database (not your data) | `:5432` |
| **Snowflake** | Stage → Stream → Triggered Task → Bronze table (cloud) | — |

The mock API is our stand-in for a real vendor. In production, this would be Ticketmaster, Eventbrite, or your internal ticketing system. We simulate it because:

1. **No rate limits** — we can hit it 100 times/second without getting banned
2. **No cost** — no API keys, no billing
3. **Reproducible** — same seed, same data, every time
4. **CDC-aware** — it supports the `since` parameter for incremental pulls

---

## The Mock API: A Vendor That Never Sleeps

Our mock vendor, "EventHub," is a FastAPI app that generates event tickets continuously. Every 5-minute interval produces 10–25 new tickets. The key feature: it supports a `since` timestamp parameter that returns only records created *after* that point.

```python
@app.get("/api/v1/tickets")
def get_tickets(
    page: int = Query(1, ge=1),
    per_page: int = Query(50, ge=1, le=500),
    since: Optional[str] = Query(None),  # ← the watermark
    authorization: Optional[str] = Header(None),
):
```

The `since` parameter is the entire foundation of our incremental pattern. Without it, we'd have to pull everything and diff — expensive, slow, and fragile.

**What the API returns:**

```json
{
  "data": [
    {
      "ticket_id": "EVH-20260628-000142",
      "event_id": "EVT-2026-001",
      "event_name": "Music Festival 2026",
      "venue": "Stadium Arena",
      "category": "VIP",
      "price": 425.50,
      "currency": "USD",
      "status": "confirmed",
      "purchase_timestamp": "2026-06-28T14:23:17+00:00",
      "attendee_email_hash": "a1b2c3d4e5f6g7h8"
    }
  ],
  "meta": {
    "page": 1,
    "total": 847,
    "has_more": true,
    "current_server_time": "2026-06-28T15:00:00+00:00"
  }
}
```

Notice `current_server_time` in the meta. That becomes our next watermark. Not the latest record's timestamp — the *server's* timestamp at query time. This is important. If we used the latest record's timestamp, we'd miss records that were created between query execution and the last record in the response.

---

## Watermarks: The State That Survives Failures

A watermark is a bookmark. It says: "I've successfully processed everything up to this point. Next time, start here."

![Watermark Flow](../docs/diagrams/art2-02-watermark-flow.png)

**Where NOT to store it:**

| Storage | Problem |
|---------|---------|
| Airflow XCom | Tied to a DAG run. Clear history = lose state. |
| A file on disk | Containers are ephemeral. Lost on restart. |
| Environment variable | Doesn't persist. Can't be shared across tasks. |
| Airflow Variable | Works, but now Airflow *is* the source of truth for data state. Coupling. |

**Where to store it: Snowflake.**

```sql
CREATE TABLE EVENTS_DEV.ORCH.WATERMARKS (
  ENTITY_NAME    STRING PRIMARY KEY,
  LAST_WATERMARK STRING,
  LAST_BATCH_ID  STRING,
  UPDATED_AT     TIMESTAMP_NTZ DEFAULT CURRENT_TIMESTAMP()
);
```

One row per entity. Our ticketing pipeline has one entity: `tickets`. When we add more sources (Article 4), they each get a row.

**The read pattern** (start of every DAG run):

```python
def get_watermark(**context):
    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT LAST_WATERMARK FROM EVENTS_DEV.ORCH.WATERMARKS "
                "WHERE ENTITY_NAME = %s",
                ("tickets",),
            )
            row = cur.fetchone()

    watermark = row[0] if row and row[0] else None
    is_backfill = watermark is None
    context["ti"].xcom_push(key="watermark", value=watermark)
    context["ti"].xcom_push(key="is_backfill", value=is_backfill)
```

First run? No watermark exists. That's a backfill — pull the last 7 days. Every subsequent run uses the watermark and only pulls new data.

**The advance pattern** (end of every successful run):

```python
def advance_watermark(**context):
    new_watermark = context["ti"].xcom_pull(
        task_ids="extract_tickets", key="new_watermark"
    )
    batch_id = context["ti"].xcom_pull(
        task_ids="extract_tickets", key="batch_id"
    )

    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                MERGE INTO EVENTS_DEV.ORCH.WATERMARKS t
                USING (SELECT %s AS entity, %s AS wm, %s AS bid) s
                ON t.ENTITY_NAME = s.entity
                WHEN MATCHED THEN UPDATE SET
                    LAST_WATERMARK = s.wm, LAST_BATCH_ID = s.bid,
                    UPDATED_AT = CURRENT_TIMESTAMP()
                WHEN NOT MATCHED THEN INSERT
                    (ENTITY_NAME, LAST_WATERMARK, LAST_BATCH_ID, UPDATED_AT)
                    VALUES (s.entity, s.wm, s.bid, CURRENT_TIMESTAMP())
            """, ("tickets", new_watermark, batch_id))
```

MERGE, not UPDATE. If the row doesn't exist yet (first run), it inserts. If it does, it updates. Idempotent.

**Key insight:** The watermark only advances *after* Bronze is confirmed loaded. If the triggered task fails, the watermark stays put. Next run retries from the same point. No data loss. No gaps.

---

## The DAG: Seven Tasks, All Lightweight

Here's the complete task flow:

```
get_watermark → extract_tickets → upload_to_stage → register_batch → wait_for_bronze → advance_watermark → cleanup_local
```

Let me walk through each task and what it costs in Airflow resources:

| Task | What It Does | Duration | Memory |
|------|-------------|----------|--------|
| `get_watermark` | One SQL query to Snowflake | ~200ms | ~5MB |
| `extract_tickets` | HTTP GET (paginated) + write JSON file | 1–3s | ~20MB |
| `upload_to_stage` | PUT file + ALTER STAGE REFRESH | ~1s | ~5MB |
| `register_batch` | One CALL to stored procedure | ~200ms | ~5MB |
| `wait_for_bronze` | Polls every 15s (reschedule mode) | 15–60s | **0 when waiting** |
| `advance_watermark` | One MERGE statement | ~200ms | ~5MB |
| `cleanup_local` | Delete temp file from disk | ~10ms | ~1MB |

**Total active worker time: ~5 seconds.** The rest is Snowflake doing its thing while Airflow's worker is free to run other DAGs.

---

## PUT to Stage: The File-Based Pattern

This is where most teams go wrong. They do:

```python
# ❌ The wrong way
write_pandas(conn, df, "RAW_TICKETS")  # Airflow worker builds, compresses, uploads
```

We do:

```python
# ✅ The right way
def upload_to_stage(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    local_file = context["ti"].xcom_pull(task_ids="extract_tickets", key="local_file")
    stage_path = f"{CONFIG['named_stage']}/batch_id={batch_id}"

    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"PUT file://{local_file} @{stage_path} "
                f"AUTO_COMPRESS=FALSE OVERWRITE=TRUE"
            )
            cur.execute(f"ALTER STAGE {CONFIG['named_stage']} REFRESH")
```

**Why JSON files instead of DataFrames?**

1. No pandas dependency. No memory spike for large payloads.
2. The JSON is the contract. Snowflake parses it with `LATERAL FLATTEN` — zero Python involvement.
3. The file sits on the internal stage forever (until you clean it). Replay any batch by re-running the triggered task.

**Why `AUTO_COMPRESS=FALSE`?**

Internal stages compress by default (gzip). For small incremental batches (50–200 records), compression overhead isn't worth it. For backfill (thousands of records), you might flip this to TRUE. We keep it simple.

**Why `ALTER STAGE REFRESH`?**

Directory tables (and streams on stages) need a refresh signal to detect new files. Without this, the stream won't see the file until the next automatic refresh (which could be minutes).

---

## Stream + Triggered Task: Snowflake's Event-Driven Magic

This is where the architecture shines. After the PUT, three things happen *inside Snowflake* with zero Airflow involvement:

![PUT → Stage → Stream → Task](../docs/diagrams/art2-03-put-stage-stream.png)

**Step 1: The stream detects the file.**

```sql
CREATE STREAM EVENTS_DEV.RAW.TICKETING_STAGE_STREAM
  ON STAGE EVENTS_DEV.RAW.TICKETING_STAGE;
```

A stream on a stage is like a `tail -f` on a directory. The moment a file lands, the stream captures its metadata (path, size, timestamp).

**Step 2: The triggered task fires automatically.**

```sql
CREATE TASK EVENTS_DEV.RAW.LAND_TICKETS_BRONZE
  WAREHOUSE = COMPUTE_WH
  WHEN SYSTEM$STREAM_HAS_DATA('EVENTS_DEV.RAW.TICKETING_STAGE_STREAM')
AS
BEGIN
  -- Cursor loops through each new file in the stream
  FOR rec IN (SELECT RELATIVE_PATH FROM EVENTS_DEV.RAW.TICKETING_STAGE_STREAM
              WHERE METADATA$ACTION = 'INSERT') DO

    -- MERGE: idempotent load into Bronze
    MERGE INTO EVENTS_DEV.BRONZE.RAW_TICKETS tgt
    USING (
      SELECT t.VALUE AS ticket_data,
             t.VALUE:ticket_id::STRING AS ticket_id
      FROM @EVENTS_DEV.RAW.TICKETING_STAGE/... AS s,
      LATERAL FLATTEN(input => s.$1:data) t
    ) src
    ON tgt.TICKET_DATA:ticket_id::STRING = src.ticket_id
    WHEN NOT MATCHED THEN INSERT (BATCH_ID, TICKET_DATA, SOURCE_FILE)
      VALUES (...);
  END FOR;
END;
```

The `WHEN SYSTEM$STREAM_HAS_DATA(...)` clause is the magic. The task doesn't run on a schedule — it runs *when data arrives*. If no files land for an hour, the task sleeps. If 10 files land in a minute, it processes them all in one execution.

**Step 3: The MERGE guarantees idempotency.**

`ON tgt.TICKET_DATA:ticket_id::STRING = src.ticket_id` — if a ticket already exists in Bronze (maybe from a retry), it won't be duplicated. MERGE is the safety net that lets us replay any batch without fear.

---

## The Reschedule Sensor: Don't Block, Observe

After registering the batch, Airflow needs to wait for Snowflake's triggered task to complete. This is the observation pattern.

![Reschedule vs Poke](../docs/diagrams/art2-04-reschedule-sensor.png)

```python
t_wait_bronze = PythonSensor(
    task_id="wait_for_bronze",
    python_callable=check_bronze_ready,
    poke_interval=15,      # check every 15 seconds
    timeout=600,           # give up after 10 minutes
    mode="reschedule",     # ← THIS IS THE KEY
)
```

**The difference between `mode="poke"` and `mode="reschedule"`:**

| | Poke Mode | Reschedule Mode |
|--|-----------|-----------------|
| Worker slot | Held for entire wait | Released between checks |
| Memory | Sensor sits in RAM | Sensor is evicted, rescheduled |
| Parallelism | Blocks other DAGs | Frees slot for other work |
| Suitable for | Short waits (< 30s) | Long waits (minutes) |

With reschedule mode, our sensor fires, checks the batch status, and if it's not done, *releases the worker*. Fifteen seconds later, Airflow's scheduler picks it back up, runs the check again, and releases again. The worker is occupied for milliseconds per check.

**What `check_bronze_ready` looks like:**

```python
def check_bronze_ready(**context):
    batch_id = context["ti"].xcom_pull(task_ids="extract_tickets", key="batch_id")
    with _sf_conn() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT STATUS, ERROR_MESSAGE "
                "FROM EVENTS_DEV.ORCH.BATCH_AUDIT WHERE BATCH_ID = %s",
                (batch_id,),
            )
            row = cur.fetchone()

    if not row:
        return False  # not registered yet, retry

    status, error = row[0], row[1]
    if status == "FAILED":
        raise AirflowFailException(f"Bronze load FAILED: {error}")
    return status == "BRONZE_COMPLETE"  # True = sensor satisfied
```

The triggered task updates `BATCH_AUDIT.STATUS` to `BRONZE_COMPLETE` when it finishes. Our sensor polls that status. Clean separation — Snowflake signals completion through a table update, Airflow observes it.

---

## Running It: From Zero to Data in 3 Minutes

### Prerequisites

1. Docker + Docker Compose installed
2. A Snowflake account (trial works fine)
3. Key-pair authentication configured ([Snowflake docs](https://docs.snowflake.com/en/user-guide/key-pair-auth))

### Step 1: Clone and configure

```bash
git clone https://github.com/mcharni76/airflow-snowflake-how-to.git
cd airflow-snowflake-how-to
git checkout v0.1

cp .env.example .env
# Edit .env with your Snowflake account, user, and key path
```

### Step 2: Run the Snowflake setup scripts

Execute scripts 01–05 in order in your Snowflake worksheet (or via SnowSQL):

```bash
# In Snowflake UI or SnowSQL:
# Run snowflake/01_setup_environment.sql  (as ACCOUNTADMIN)
# Run snowflake/02_create_stage_and_stream.sql
# Run snowflake/03_create_bronze_objects.sql
# Run snowflake/04_create_orch_objects.sql
# Run snowflake/05_create_triggered_task.sql
```

### Step 3: Start the stack

```bash
docker compose up -d
```

Wait ~30 seconds for Airflow to initialize. Then:

- Mock API Swagger: http://localhost:8099/docs
- Airflow UI: http://localhost:8080 (admin/admin)

### Step 4: Trigger the DAG

In the Airflow UI, find `eventhub_single_source_pipeline` and toggle it ON. It runs every 5 minutes, but you can trigger it manually.

### Step 5: Watch the flow

1. `get_watermark` — first run finds no watermark (backfill mode)
2. `extract_tickets` — pulls 7 days of historical data (~2000 tickets)
3. `upload_to_stage` — PUTs a JSON file to `@EVENTS_DEV.RAW.TICKETING_STAGE`
4. `register_batch` — writes audit record with status `UPLOADED`
5. `wait_for_bronze` — polls `BATCH_AUDIT` every 15 seconds
6. Meanwhile, Snowflake's triggered task fires, MERGEs data, updates status to `BRONZE_COMPLETE`
7. `advance_watermark` — stores the server timestamp as the new watermark
8. `cleanup_local` — removes the temp JSON file

### Step 6: Verify

```sql
-- Check Bronze landed
SELECT COUNT(*) FROM EVENTS_DEV.BRONZE.RAW_TICKETS;

-- Check watermark advanced
SELECT * FROM EVENTS_DEV.ORCH.WATERMARKS;

-- Check batch audit trail
SELECT BATCH_ID, STATUS, RECORD_COUNT_EXPECTED, RECORD_COUNT_LOADED
FROM EVENTS_DEV.ORCH.BATCH_AUDIT
ORDER BY CREATED_AT DESC;
```

---

## What Just Happened: The Complete Flow

Let's recap the full sequence:

1. **Airflow scheduler** wakes the DAG (every 5 min)
2. **`get_watermark`** reads the last checkpoint from Snowflake → finds "2026-06-28T14:55:00Z"
3. **`extract_tickets`** calls the mock API with `since=2026-06-28T14:55:00Z` → gets 18 new tickets
4. **`extract_tickets`** writes them to `/opt/airflow/tmp/api_extracts/batch_id=<uuid>/tickets.json`
5. **`upload_to_stage`** runs `PUT file://... @EVENTS_DEV.RAW.TICKETING_STAGE/batch_id=<uuid>/`
6. **`upload_to_stage`** runs `ALTER STAGE ... REFRESH` → stream now sees the file
7. **`register_batch`** calls `EVENTS_DEV.ORCH.REGISTER_BATCH(...)` → audit trail created
8. **Snowflake task** `LAND_TICKETS_BRONZE` fires → MERGE INTO Bronze → updates audit to `BRONZE_COMPLETE`
9. **`wait_for_bronze`** sensor sees `BRONZE_COMPLETE` → returns True
10. **`advance_watermark`** MERGE into watermarks table → "2026-06-28T15:00:00Z"
11. **`cleanup_local`** deletes the temp file
12. **Next run** starts at step 2 with the new watermark

**Total Airflow worker time: ~5 seconds.** Total Snowflake compute: ~2 seconds. Total data in motion: ~18 records × 200 bytes = 3.6KB.

This is what "control plane" means in practice.

---

## What's Next

We have raw JSON sitting in Bronze. It's there, it's safe, it's idempotent. But it's not queryable in a useful way.

In **Article 3**, we add the transformation layer with dbt:
- **Silver**: Deduplicate (QUALIFY), type cast, flatten the VARIANT into typed columns
- **Gold**: Aggregate by event, calculate revenue metrics, build the star schema

The Bronze → Silver → Gold medallion pattern — but done *inside Snowflake* using dbt, not pandas.

---

**Repository:** [github.com/mcharni76/airflow-snowflake-how-to](https://github.com/mcharni76/airflow-snowflake-how-to) — tag `v0.1`

---

*About the Author: [Marawen Charni](https://www.linkedin.com/in/mcharni) is a Solutions Engineer at Snowflake, based in the Middle East. He believes the best pipeline is one where Airflow does almost nothing.*

*Follow on Medium: [@marawen.cherni](https://medium.com/@marawen.cherni)*

---

### A Note on How This Article Came to Be

> **Figures:** Generated with **Gemini** in infographic style.
> **Content:** Assisted by **Snowflake Cortex Code**.
> **Experience:** Based on a real production pipeline (redacted and genericized).
