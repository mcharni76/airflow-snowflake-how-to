# Stop Using Airflow Wrong

*Your Airflow DAGs shouldn't be doing what you think they should be doing.*

![Hero Image](../docs/diagrams/Fig01_control_plane.png)

**Reading Time:** 8 minutes
**Difficulty:** Intermediate
**Coffee Required:** One strong espresso. This might challenge some habits.

---

> **Side note:** This article exists because I've reviewed dozens of Airflow + Snowflake implementations, and roughly 80% of them make the same architectural mistake. They treat Airflow as a data processing engine. It isn't. It never was. After the 30th code review where I found pandas DataFrames inside PythonOperators doing transforms that Snowflake handles in milliseconds, I decided to write this down. Consider this my attempt to save your team from debugging memory-killed Airflow workers at 3 AM.

---

## The Pattern Everyone Uses (and Why It's Wrong)

You're a data engineer. You need to pull data from a vendor API and land it in Snowflake. So you write a DAG that looks something like this:

```python
@task
def extract():
    response = requests.get("https://api.vendor.com/data")
    return response.json()

@task
def transform(data):
    df = pd.DataFrame(data)
    df["amount"] = df["amount"].astype(float)
    df["created_at"] = pd.to_datetime(df["created_at"])
    df = df.drop_duplicates(subset=["id"])
    return df

@task
def load(df):
    write_pandas(conn, df, "TARGET_TABLE")
```

Extract. Transform. Load. Classic ETL in Airflow.

Here's the problem: **every line in that `transform` function is work that Snowflake does better, faster, and cheaper than your Airflow worker.**

Type casting? Snowflake does it at read time. Deduplication? `QUALIFY ROW_NUMBER()` is a single-pass operation on columnar storage. Date parsing? Built-in. And it does all of this on dedicated compute, not on the same 2-CPU container that's also running your scheduler.

![The Anti-Pattern](../docs/diagrams/Fig02_antipattern.png)

---

## The Right Mental Model: Control Plane vs Runtime

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

![Control Plane vs Runtime](../docs/diagrams/Fig03_conductor.png)

---

## What the Architecture Actually Looks Like

Here's the pattern that works at scale:

```
┌─────────────────────────┐         ┌─────────────────────────────┐
│   Airflow (Control)     │         │   Snowflake (Runtime)       │
│                         │         │                             │
│  1. Call vendor API     │         │                             │
│  2. Write JSON to file  │         │                             │
│  3. PUT file to stage   │────────▶│  @STAGE (landing zone)      │
│  4. Register batch      │         │      │                      │
│  5. Wait (reschedule)   │         │      ▼                      │
│                         │         │  Stream detects file        │
│         ┌───────────────│◀────────│  Triggered Task fires       │
│         │               │         │  MERGE INTO Bronze          │
│  6. Confirm complete    │         │      │                      │
│  7. Advance watermark   │────────▶│      ▼                      │
│  8. Trigger dbt         │────────▶│  dbt: Silver (dedup)        │
│                         │         │  dbt: Gold (aggregate)      │
│  9. Cleanup temp files  │         │                             │
└─────────────────────────┘         └─────────────────────────────┘
```

Notice what Airflow does: 9 steps, all lightweight. No data manipulation. No DataFrames. No memory pressure.

Notice what Snowflake does: all the heavy lifting. MERGE for idempotency. Streams for CDC detection. Triggered tasks for event-driven execution. dbt for transformation.

---

## The Async Pattern: Don't Block

The second mistake teams make is blocking Airflow workers while Snowflake processes data. Your DAG calls `COPY INTO`, then sits there waiting. The worker slot is occupied. If you have 16 workers and 20 DAGs, you're now queuing.

The fix: **async with reschedule sensors and deferrable operators.**

```
  SYNC (fast)              ASYNC (frees the worker)
  ──────────               ────────────────────────
  extract API ──▶ PUT ──▶  [Snowflake task runs autonomously]
                           [Airflow sensor: reschedule mode]
                           [Worker slot freed immediately]
                           [Sensor re-checks every 15 seconds]
                           [dbt via deferrable operator]
```

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

![The Right Way](../docs/diagrams/Fig04_right_way.png)

---

*Next up: [Article 2 — Building an Incremental CDC Pipeline (Locally)](#). We write actual code. Docker Compose, a mock vendor API, watermark-based extraction, and a Snowflake triggered task that fires when files land. See you Tuesday.*

---

*About the Author: Marawen Charni is a Solutions Engineer at Snowflake, based in the Middle East. He's spent the last year reviewing Airflow implementations and gently suggesting that maybe, just maybe, pandas doesn't belong inside a DAG.*

---

### A Note on How This Article Came to Be

> **Figures:** Generated by **Bannerbear Pro**, because architecture diagrams drawn in Mermaid don't get Medium engagement.

> **Content:** Assisted by **[Snowflake Cortex Code](https://docs.snowflake.com/en/user-guide/snowflake-cortex/cortex-code)**, which helped structure the series and refactor 2,000 lines of production code into a publishable format.

> **Experience:** Based on a real production pipeline (redacted and genericized) that ingests 100k+ records daily from multiple vendor APIs into Snowflake.

---

## Diagrams (Excalidraw Hybrid Style)

> **Style Guide:** All diagrams use Excalidraw with hand-drawn line style enabled.
> Font: Virgil (hand-written). Background: white/light. Lines: slightly wobbly.
> Palette: Snowflake Blue (#29B5E8), Dark Gray (#374151), Green (#10B981), Warning Amber (#F59E0B), Error Red (#EF4444).
> Layout: Structured and organized (grid/columns), but rendered with sketch aesthetics.
> Export: PNG @2x for Medium (1200px wide minimum).

### Figure 01: The Control Plane (Cover Image)

```
File: docs/diagrams/01-control-plane.excalidraw
Dimensions: 1200x630 (Medium cover ratio)

Layout:
┌─────────────────────────────────────────────────────┐
│                                                     │
│   ┌──────────┐    thin dashed     ┌──────────────┐ │
│   │ AIRFLOW  │    arrow →→→       │  SNOWFLAKE   │ │
│   │          │   "signals only"   │              │ │
│   │ [toggle] │                    │ ⚙ Stage      │ │
│   │ [toggle] │                    │ ⚙ Stream     │ │
│   │ [toggle] │                    │ ⚙ Task       │ │
│   │          │                    │ ⚙ dbt        │ │
│   └──────────┘                    └──────────────┘ │
│       small                           LARGE        │
│                                                     │
│   "Control Plane vs Runtime"                        │
│   "Orchestrate. Don't Execute."                     │
└─────────────────────────────────────────────────────┘

Style notes:
- Airflow box: small, thin border (#374151), toggle switches drawn as simple rectangles
- Snowflake box: 3x wider, thick border (#29B5E8), gears are simple hand-drawn circles with dots
- Connecting arrow: thin dashed line, hand-drawn wobble, labeled "signals only"
- Title text: large Virgil font, centered below
- Background: white with very subtle grid dots
```

### Figure 02: The Anti-Pattern (Before/After)

```
File: docs/diagrams/02-anti-pattern.excalidraw
Dimensions: 1200x800 (inline)

Layout:
┌────────────────────────┐  ┌────────────────────────┐
│  ❌ THE WRONG WAY      │  │  ✓ THE RIGHT WAY       │
│                        │  │                        │
│  ┌──────────────────┐  │  │  ┌──────────────────┐  │
│  │  AIRFLOW WORKER  │  │  │  │  AIRFLOW WORKER  │  │
│  │  ┈┈┈┈┈┈┈┈┈┈┈┈┈┈  │  │  │  │                  │  │
│  │  [pandas] [spark] │  │  │  │  → PUT file      │  │
│  │  [transform]      │  │  │  │  → check status  │  │
│  │  [memory: 95%]    │  │  │  │  [memory: 12%]   │  │
│  │  [CPU: maxed]     │  │  │  │  [CPU: idle]     │  │
│  └──────────────────┘  │  │  └──────────────────┘  │
│                        │  │          │              │
│  "2 CPU, 4GB RAM"     │  │          ▼ signal       │
│  "handles 3 sources"  │  │  ┌──────────────────┐  │
│                        │  │  │  SNOWFLAKE       │  │
│                        │  │  │  (does the work) │  │
│                        │  │  └──────────────────┘  │
│                        │  │  "Same HW, 10x thru"  │
└────────────────────────┘  └────────────────────────┘

Style notes:
- Left panel: red-tinted border (#EF4444), worker box stuffed with scribbled icons
- Right panel: blue-tinted border (#29B5E8), worker box mostly empty, clean
- Memory bars: hand-drawn rectangles, filled proportionally (red=full, green=low)
- Cross mark (❌) and checkmark (✓) hand-drawn, not emoji
- Bottom labels: Virgil font, contrasting sizes
```

### Figure 03: The Orchestra Metaphor

```
File: docs/diagrams/03-conductor-orchestra.excalidraw
Dimensions: 1200x800 (inline)

Layout:
┌─────────────────────────────────────────────────────┐
│                                                     │
│              🎵  (hand-drawn notes)                  │
│                                                     │
│         ┌─────────┐                                 │
│         │CONDUCTOR│  ← stick figure with baton      │
│         │(Airflow)│     hands: EMPTY (just baton)   │
│         └────┬────┘                                 │
│              │ waves baton                           │
│              ▼                                      │
│   ┌─────┬─────┬─────┬─────┬─────┐                 │
│   │Stage│Strm │Task │ dbt │Gold │  ← orchestra     │
│   │  ♪  │  ♪  │  ♪  │  ♪  │  ♪  │    (Snowflake)  │
│   └─────┴─────┴─────┴─────┴─────┘                 │
│                                                     │
│   "The conductor never plays an instrument."        │
│   "Airflow never transforms data."                  │
└─────────────────────────────────────────────────────┘

Style notes:
- Conductor: simple stick figure, large baton (emphasized), Virgil label
- Orchestra pit: 5 rounded boxes in a row, each labeled with a Snowflake object
- Musical notes: hand-drawn squiggles floating up (representing data flowing)
- Key emphasis: conductor's hands are drawn EMPTY except for baton
- Color: conductor in #374151, orchestra in #29B5E8, notes in #10B981
- Quote at bottom: italic Virgil, centered
```

### Figure 04: The Reference Architecture

```
File: docs/diagrams/04-reference-architecture.excalidraw
Dimensions: 1200x800 (inline)

Layout:
┌─────────────────────────────────────────────────────────────┐
│                                                             │
│  AIRFLOW (control)          SNOWFLAKE (runtime)             │
│  ┌───────────────┐          ┌─────────────────────────────┐│
│  │ 1. check wm   │─signal─→│                             ││
│  │ 2. call API   │          │  ┌─────┐   ┌──────┐        ││
│  │ 3. PUT file   │─file───→│  │STAGE│──▶│STREAM│        ││
│  │ 4. observe    │          │  └─────┘   └──┬───┘        ││
│  │ 5. update wm  │          │               │ trigger     ││
│  │               │          │               ▼             ││
│  │               │          │  ┌──────┐  ┌──────┐        ││
│  │               │          │  │ TASK │─▶│BRONZE│        ││
│  │               │          │  └──────┘  └──┬───┘        ││
│  │               │          │               │ dbt run     ││
│  │               │          │               ▼             ││
│  │               │          │  ┌──────┐  ┌──────┐        ││
│  │               │          │  │SILVER│─▶│ GOLD │        ││
│  │               │          │  └──────┘  └──────┘        ││
│  └───────────────┘          └─────────────────────────────┘│
│       ▲ thin                        ▲ WIDE                  │
│                                                             │
│  ← "Signals, not data" →                                   │
└─────────────────────────────────────────────────────────────┘

Style notes:
- Airflow column: narrow (25% width), thin gray border (#374151)
- Snowflake column: wide (70% width), thick blue border (#29B5E8)
- Arrows between columns: thin dashed lines (signals) — NOT thick data pipes
- Internal Snowflake arrows: solid, hand-drawn, with flow direction
- Stage→Stream→Task→Bronze: green arrows (#10B981)
- Bronze→Silver→Gold: blue arrows (#29B5E8)
- Size contrast is THE key visual message (small orchestrator, large runtime)
- Label at bottom: "Signals, not data" with hand-drawn underline
```
