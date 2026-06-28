# Stop Using Airflow Wrong

*Your Airflow DAGs shouldn't be doing what you think they should be doing.*

![Series Cover](../docs/diagrams/00-series-cover.png)

**Reading Time:** 8 minutes
**Difficulty:** Intermediate
**Coffee Required:** One strong espresso. This might challenge some habits.

---

> **Side note:** This article exists because I've reviewed dozens of Airflow + Snowflake implementations, and roughly 80% of them make the same architectural mistake. They treat Airflow as a data processing engine. It isn't. It never was. After the 30th code review where I found pandas DataFrames inside PythonOperators doing transforms that Snowflake handles in milliseconds, I decided to write this down. Consider this my attempt to save your team from debugging memory-killed Airflow workers at 3 AM.

---

## The Pattern Everyone Uses (and Why It's Wrong)

You're a data engineer. You need to pull data from a vendor API and land it in Snowflake. So you write a DAG that looks something like this:

```python
from airflow.decorators import dag, task
from snowflake.connector.pandas_tools import write_pandas
import pandas as pd
import requests

@dag(schedule="@hourly", catchup=False)
def vendor_etl():

    @task
    def extract():
        """Pull everything from the vendor API into memory."""
        response = requests.get(
            "https://api.vendor.com/data",
            params={"since": "2024-01-01"}  # no incremental logic
        )
        response.raise_for_status()
        return response.json()  # entire payload sits in XCom

    @task
    def transform(data):
        """Parse, cast, deduplicate — all in Python, all in RAM."""
        df = pd.DataFrame(data)                         # full dataset in memory
        df["amount"] = df["amount"].astype(float)       # type casting
        df["created_at"] = pd.to_datetime(df["created_at"])  # date parsing
        df = df.drop_duplicates(subset=["id"])          # deduplication
        df["revenue_bucket"] = pd.cut(                  # business logic
            df["amount"], bins=[0, 50, 200, 1000, float("inf")],
            labels=["small", "medium", "large", "enterprise"]
        )
        return df  # serialized back into XCom (again, full dataset)

    @task
    def load(df):
        """Bulk insert into Snowflake using write_pandas."""
        conn = snowflake.connector.connect(...)
        write_pandas(conn, df, "TARGET_TABLE")  # full table overwrite each run

    # DAG wiring
    raw = extract()
    cleaned = transform(raw)
    load(cleaned)

vendor_etl()
```

Look familiar? This is the most common pattern I see in production Airflow deployments. Extract. Transform. Load. Classic ETL — textbook, clean, and **fundamentally wrong** when Snowflake is your target.

Let's break down what's actually happening at runtime:

| Step | What Happens in Memory | Problem |
|------|----------------------|---------|
| `extract()` | Entire API response loaded into Python dict → serialized to XCom (Airflow metadata DB) | XCom has a size limit. Large payloads crash the metadata DB or silently truncate. |
| `transform(data)` | Dict deserialized → pandas DataFrame created → every row processed in Python | Your 2-CPU, 4GB Airflow worker is now doing compute work. For 10K rows? Fine. For 1M? OOM kill. |
| `df.astype(float)` | Python iterates every value, casting one by one | Snowflake does this at read time on columnar storage — orders of magnitude faster. |
| `pd.to_datetime()` | Python parses date strings row by row | Snowflake's `TRY_TO_TIMESTAMP` handles thousands of date formats natively. |
| `drop_duplicates()` | Pandas hashes every row, builds a set, filters | Snowflake's `QUALIFY ROW_NUMBER()` is a single-pass window function on compressed data. |
| `pd.cut()` | Python bins values with conditionals | A SQL `CASE WHEN` runs on Snowflake's vectorized engine without data movement. |
| `load(df)` | `write_pandas` converts DataFrame → Parquet → PUT → COPY INTO | The only step that *actually* needs to talk to Snowflake — but by now you've wasted minutes of worker time on transforms. |

**The total cost:** your Airflow worker is occupied for the entire duration — extract, transform, AND load. If the API is slow (30 seconds), the transform is heavy (2 minutes), and the load takes another minute, that's **3.5 minutes of a worker slot blocked** per DAG run.

Now multiply: 10 sources × hourly × 24 hours = **840 blocked worker-minutes per day.** And you're wondering why DAGs are queuing.

Here's the uncomfortable truth: **every line in that `transform` function is work that Snowflake does better, faster, and cheaper than your Airflow worker.**

Type casting? Snowflake does it at read time on columnar storage — no Python iteration required. Deduplication? `QUALIFY ROW_NUMBER() OVER (PARTITION BY id ORDER BY _loaded_at DESC) = 1` is a single-pass window function that handles billions of rows. Date parsing? `TRY_TO_TIMESTAMP_NTZ` with `AUTO` detection handles any format. Binning? A SQL `CASE WHEN` expression runs on Snowflake's vectorized engine without moving a single byte out of the warehouse.

And all of this happens on **dedicated, elastic compute** — not on the same container that's running your scheduler, your webserver, and 15 other DAGs.

![The Anti-Pattern](../docs/diagrams/02-anti-pattern.png)

---

## The Right Mental Model: Control Plane vs Runtime

![Control Plane vs Runtime](../docs/diagrams/01-control-plane.png)

The fix isn't complicated. It's a mindset shift.

**Airflow is a control plane.** It decides *when* things happen, *what* to trigger, and *whether* they succeeded. It does not do the work itself.

**Snowflake is the runtime.** It stores, transforms, deduplicates, and serves data. It has the compute. It has the storage. It has the SQL engine optimized for exactly this.

| Airflow Should | Airflow Should NOT |
|----------------|-------------------|
| Call vendor APIs | Parse JSON into DataFrames |
| Upload files to a stage | Cast data types |
| Trigger Snowflake tasks | Deduplicate records |
| Poll for completion | Join tables |
| Advance watermarks | Aggregate metrics |
| Handle retries and alerting | Run pandas/spark transforms |

Think of it like a conductor and an orchestra. The conductor doesn't play the violin. The conductor tells the violinist *when* to play, *how fast*, and *when to stop*. If your conductor is also playing three instruments, something has gone wrong.

![The Orchestra Metaphor](../docs/diagrams/03-conductor-orchestra.png)

---

## What the Architecture Actually Looks Like

![End-to-End Flow](../docs/diagrams/05-end-to-end-flow.png)

Notice what Airflow does: 9 steps, all lightweight. No data manipulation. No DataFrames. No memory pressure.

Notice what Snowflake does: all the heavy lifting. MERGE for idempotency. Streams for CDC detection. Triggered tasks for event-driven execution. dbt for transformation.

---

## The Async Pattern: Don't Block

The second mistake teams make is blocking Airflow workers while Snowflake processes data. Your DAG calls `COPY INTO`, then sits there waiting. The worker slot is occupied. If you have 16 workers and 20 DAGs, you're now queuing.

The fix: **async with reschedule sensors and deferrable operators.**

![Sync vs Async Pattern](../docs/diagrams/06-sync-async-pattern.png)

Your Airflow worker touches the data for maybe 5 seconds (API call + file write + PUT command). Then it lets go. Snowflake can take 30 seconds or 30 minutes. Airflow doesn't care. It checks back periodically using almost zero resources.

---

## Why This Matters at Scale

With one DAG, the anti-pattern is fine. You won't notice. But pipelines multiply.

| Scenario | ETL-in-Airflow | Control-Plane Pattern |
|----------|---------------|----------------------|
| 10 sources, 5-min schedule | 10 workers blocked continuously | 10 PUT commands (2s each), workers free |
| Backfill 1M records | OOM kill on worker (pandas) | Snowflake handles it natively |
| Source API is slow (30s) | Worker blocked 30s per page | Same (unavoidable), but no transform overhead |
| Retry after failure | Re-process entire DataFrame | Re-PUT file, Snowflake MERGE is idempotent |
| Add a new source | Copy-paste 200-line DAG | Add config entry, same DAG pattern |

The control-plane pattern also makes your DAGs trivially testable. Each task is a thin wrapper around an API call or a SQL command. No business logic to unit test in Python.

---

## Where to Run Airflow

Before you build, choose your deployment:

| Option | Best For | Cost |
|--------|----------|------|
| **Docker Compose** | Local dev, this series | Free |
| **SPCS (Snowflake)** | Enterprise: zero-egress, single RBAC | Snowflake credits |
| **Amazon MWAA** | AWS shops wanting managed | ~$0.49/hr+ |
| **Cloud Composer** | GCP shops | ~$0.35/hr+ |
| **Astronomer (Astro)** | Best managed Airflow experience | ~$350/mo+ |
| **Self-hosted K8s** | Full control, auto-scaling | Your infra team's time |

This series uses Docker Compose for learning. Bonus articles cover SPCS (enterprise) and MWAA (managed) for production.

---

## What We're Building in This Series

Over the next 6 articles, we'll build a complete pipeline step by step:

1. **Article 2** — A single-source incremental CDC pipeline. Mock API, watermarks, triggered tasks, Bronze loading. All running locally in Docker.

2. **Article 3** — dbt transformation layer. Silver (dedup + type cast) and Gold (aggregation + cross-source matching). Deployed as a native Snowflake dbt project.

3. **Article 4** — Scale to 3 concurrent API sources using Airflow TaskGroups. Different ID formats, date formats, and normalization rules. Parallel execution.

4. **Article 5** — Every gotcha we hit during development. SQL Scripting quirks, Docker volume permissions, task suspension, dbt schema naming. The war stories that save you days.

5. **Bonus 1** — Deploy Airflow itself on Snowflake SPCS. Multi-container, auto-scaling, zero-trust networking, OAuth authentication. The "keep everything in Snowflake" enterprise play.

6. **Bonus 2** — Migrate from Docker to Amazon MWAA. Swap internal stage for S3, add Snowpipe, configure IAM. The "we're already on AWS" path.

Each article has a corresponding git tag. Clone the repo, checkout the tag, and you have the exact state of the code for that article.

**Repository:** [github.com/marawen/airflow-snowflake-how-to](https://github.com/marawen/airflow-snowflake-how-to)

---

## The Bottom Line

Airflow is not a data processing engine. It's a scheduler with a nice UI. The moment you put business logic, transforms, or heavy computation inside a DAG task, you're fighting the tool instead of using it.

Let Airflow do what it's good at: orchestrating. Let Snowflake do what it's good at: computing.

**"The best Airflow DAG is one where every task finishes in under 10 seconds."**

![Reference Architecture](../docs/diagrams/04-reference-architecture.png)

---

*Next up: [Article 2 — Building an Incremental CDC Pipeline (Locally)](#). We write actual code. Docker Compose, a mock vendor API, watermark-based extraction, and a Snowflake triggered task that fires when files land. See you Tuesday.*

---

*About the Author: Marawen Charni is a Solutions Engineer at Snowflake, based in the Middle East. He's spent the last year reviewing Airflow implementations and gently suggesting that maybe, just maybe, pandas doesn't belong inside a DAG.*

---

### A Note on How This Article Came to Be

> **Figures:** Generated with **Gemini** in Excalidraw hybrid style (structured layout + hand-drawn aesthetic).

> **Content:** Assisted by **[Snowflake Cortex Code](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code)**, which helped structure the series and refactor 2,000 lines of production code into a publishable format.

> **Experience:** Based on a real production pipeline (redacted and genericized) that ingests 100k+ records daily from multiple vendor APIs into Snowflake.


