# Diagram Generation Prompts (Gemini / AI Image Gen)

> These prompts are used to generate the diagrams for the article series.
> Tool: Gemini image generation (or Excalidraw manual creation)
> Style: Hybrid — structured layout + hand-drawn/sketch aesthetic

---

## Article 1 Diagrams

### 00-series-cover.png (Medium Cover Image)

```
Create a wide cover image in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written Virgil font). White background. Dimensions: 1400x750 pixels.

CENTER COMPOSITION:
- A large hand-drawn title in bold sketch font: "Airflow + Snowflake: The Right Way"
- Below the title, a subtitle in smaller hand-written text: "A 7-Part Series on Building Production Pipelines"

LEFT SIDE (~30%):
- A small, thin, almost empty box labeled "Airflow" with a simple toggle switch icon inside
- Hand-written labels floating around it: "orchestrate", "signal", "observe"
- Overall feel: lightweight, minimal, calm

RIGHT SIDE (~60%):
- A large, thick-bordered box labeled "Snowflake" in blue (#29B5E8)
- Inside, a vertical cascade of hand-drawn boxes connected by arrows:
  - "Stage" → "Stream" → "Task" → "Bronze" → "Silver" → "Gold"
- Small gear/cog icons spinning next to each box
- Overall feel: powerful, busy, doing the heavy lifting

CONNECTING ELEMENT (between left and right):
- A single thin dashed arrow from Airflow to Snowflake
- Label on arrow: "signals, not data"
- A small hand-drawn "X" over a thick arrow (representing "no data transfer through Airflow")

BOTTOM STRIP (series overview, like a film strip or timeline):
- 7 small numbered circles in a horizontal row: ①②③④⑤⑥⑦
- Below each circle, a 2-word label:
  1. "Architecture"
  2. "CDC Pipeline"  
  3. "dbt Models"
  4. "Multi-Source"
  5. "Gotchas"
  6. "SPCS Deploy"
  7. "MWAA Migrate"
- A hand-drawn progress arrow running underneath all 7 circles

CORNER ELEMENTS:
- Top-right: small hand-drawn Docker whale icon
- Bottom-left: small hand-drawn Python logo (two snakes)
- These are subtle, not dominant

Color palette: 
- Snowflake Blue (#29B5E8) for Snowflake elements
- Dark Gray (#374151) for Airflow elements and text
- Green (#10B981) for the flow arrows inside Snowflake
- Amber (#F59E0B) for the series timeline circles
- White background throughout

Style: The overall impression should be "a thoughtful technical series about doing things the right way." Professional but approachable. The hand-drawn aesthetic makes it feel human and practical, not corporate. The size contrast between Airflow (small) and Snowflake (large) reinforces the core message.
```

---

### 01-control-plane.png (Cover Image)

```
Create a technical diagram in a hand-drawn sketch style (like Excalidraw with slightly wobbly lines and hand-written font). White background. Dimensions: 1200x630 pixels.

Layout: Two boxes side by side with a dashed arrow connecting them.

LEFT BOX (small, ~25% width):
- Label: "AIRFLOW"
- Thin gray border (#374151)
- Inside: 3 simple toggle switches drawn as small rectangles
- Overall feel: minimal, lightweight

RIGHT BOX (large, ~70% width):
- Label: "SNOWFLAKE"
- Thick blue border (#29B5E8)
- Inside: 4 items listed vertically with small gear icons: Stage, Stream, Task, dbt
- Overall feel: powerful, heavy

CONNECTING ELEMENT:
- A thin dashed arrow from left box to right box
- Label on the arrow: "signals only"

TEXT BELOW (centered):
- Large hand-written text: "Control Plane vs Runtime"
- Smaller subtitle: "Orchestrate. Don't Execute."

Color palette: Snowflake Blue (#29B5E8), Dark Gray (#374151), white background.
No emojis, no logos. Clean but hand-drawn aesthetic. The size contrast between the two boxes is the key visual message.
```

---

### 02-anti-pattern.png

```
Create a side-by-side comparison diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x800 pixels.

TWO PANELS SIDE BY SIDE:

LEFT PANEL (bordered in red #EF4444):
- Header: hand-drawn X mark + "THE WRONG WAY"
- Inside: a box labeled "AIRFLOW WORKER" that looks stuffed/overloaded
- Inside the worker box, scribbled icons: "pandas", "spark", "transform"
- A memory bar drawn at 95% full (red fill)
- A CPU indicator showing "maxed"
- Below the box: "2 CPU, 4GB RAM" and "handles 3 sources"
- Overall feel: cramped, stressed, overloaded

RIGHT PANEL (bordered in blue #29B5E8):
- Header: hand-drawn checkmark + "THE RIGHT WAY"
- Inside: a box labeled "AIRFLOW WORKER" that looks mostly empty/clean
- Inside the worker box, only 2 lines: "→ PUT file" and "→ check status"
- A memory bar at 12% (green fill)
- CPU: "idle"
- Below the worker, a thin arrow pointing down labeled "signal"
- Below the arrow: a second box labeled "SNOWFLAKE (does the work)"
- Below everything: "Same hardware, 10x throughput"
- Overall feel: spacious, calm, efficient

Color palette: Red (#EF4444) for wrong side, Blue (#29B5E8) for right side, Gray (#374151) for text, Green (#10B981) for healthy indicators. White background. Hand-drawn sketch style throughout.
```

---

### 03-conductor-orchestra.png

```
Create a metaphor diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x800 pixels.

Layout: A conductor figure at top, orchestra below.

TOP (center):
- A simple stick figure of a conductor holding a baton
- Label: "CONDUCTOR (Airflow)"
- Key detail: the conductor's hands are EMPTY except for the baton — no instruments
- The baton is emphasized/larger than normal
- Color: dark gray (#374151)

MIDDLE:
- A wavy line or arrow going down from conductor, labeled "waves baton"

BOTTOM:
- 5 rounded boxes in a horizontal row (like an orchestra pit)
- Each box labeled: "Stage", "Stream", "Task", "dbt", "Gold"
- Each box has a small musical note symbol inside
- All boxes colored in blue (#29B5E8)
- Small hand-drawn musical notes floating upward from the boxes (in green #10B981)
- Label to the right: "(Snowflake)"

QUOTE (centered at very bottom, italic hand-written):
- "The conductor never plays an instrument."
- "Airflow never transforms data."

Color palette: Dark Gray (#374151) for conductor, Snowflake Blue (#29B5E8) for orchestra boxes, Green (#10B981) for musical notes. White background. The visual metaphor should be immediately obvious.
```

---

### 04-reference-architecture.png

```
Create a technical architecture diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x800 pixels.

Layout: Two columns — narrow left column and wide right column.

LEFT COLUMN (narrow, ~25% width, thin gray border #374151):
- Header: "AIRFLOW (control)"
- 5 numbered steps listed vertically:
  1. check watermark
  2. call API
  3. PUT file
  4. observe
  5. update watermark
- Two thin dashed arrows exit this box going right (labeled "signal" and "file")

RIGHT COLUMN (wide, ~70% width, thick blue border #29B5E8):
- Header: "SNOWFLAKE (runtime)"
- Inside, a vertical flow chart with hand-drawn arrows:
  - Box "STAGE" → arrow → Box "STREAM"
  - STREAM → arrow labeled "trigger" → Box "TASK"
  - TASK → arrow → Box "BRONZE"
  - BRONZE → arrow labeled "dbt run" → Box "SILVER"
  - SILVER → arrow → Box "GOLD"
- Flow arrows from Stage to Bronze: green (#10B981)
- Flow arrows from Bronze to Gold: blue (#29B5E8)

BOTTOM (centered):
- Text with hand-drawn underline: "Signals, not data"
- Small arrows indicating the thin connections between left and right columns

KEY VISUAL MESSAGE: The Airflow column is intentionally narrow and minimal. The Snowflake column is intentionally wide and full of activity. The size difference tells the story — the orchestrator is lightweight, the runtime does all the heavy lifting.

Color palette: Gray (#374151) for Airflow side, Blue (#29B5E8) for Snowflake side, Green (#10B981) for data flow arrows. White background.
```

---

### 05-end-to-end-flow.png

```
Create a technical architecture diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x800 pixels.

Title at top: "The Pattern That Works at Scale"

Layout: Two tall columns side by side — a narrow left column (Airflow) and a wide right column (Snowflake). Steps flow top-to-bottom with arrows crossing between columns.

LEFT COLUMN (narrow, ~30% width, thin gray border #374151):
- Header: "Airflow (Control)" in hand-written font
- 9 numbered steps listed vertically:
  1. Call vendor API
  2. Write JSON to file
  3. PUT file to stage  →  (arrow exits right to Snowflake)
  4. Register batch
  5. Wait (reschedule)
  6. Confirm complete    ←  (arrow comes from Snowflake)
  7. Advance watermark   →  (arrow exits right)
  8. Trigger dbt         →  (arrow exits right)
  9. Cleanup temp files

RIGHT COLUMN (wide, ~65% width, thick blue border #29B5E8):
- Header: "Snowflake (Runtime)" in hand-written font
- Vertical flow starting where step 3's arrow arrives:
  - Box "@STAGE (landing zone)" with file icon
  - ↓ arrow
  - Box "Stream detects file" with eye icon
  - ↓ arrow labeled "trigger"
  - Box "Triggered Task fires" with lightning bolt
  - ↓ arrow
  - Box "MERGE INTO Bronze" with merge icon
  - ↓ arrow (after step 7/8 arrows arrive)
  - Box "dbt: Silver (dedup)" 
  - ↓ arrow
  - Box "dbt: Gold (aggregate)"

CROSSING ARROWS (key visual element):
- Step 3 → @STAGE: thick solid arrow labeled "file"
- Stream/Task → Step 6: thin dashed arrow labeled "done signal" (going left)
- Step 7 → Snowflake: thin arrow labeled "watermark"
- Step 8 → dbt: thin arrow labeled "run"

BOTTOM (centered below both columns):
- Hand-drawn text: "Airflow: 9 steps, all lightweight. No DataFrames. No memory pressure."

Style notes:
- The left column should feel empty/lightweight (lots of whitespace between steps)
- The right column should feel busy/active (boxes stacked close together, flow arrows)
- Arrows crossing between columns are the key storytelling element
- Color palette: Gray (#374151) for Airflow, Blue (#29B5E8) for Snowflake, Green (#10B981) for flow arrows, Amber (#F59E0B) for signal arrows going left
```

---

### 06-sync-async-pattern.png

```
Create a timeline/sequence diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x600 pixels.

Title at top: "The Async Pattern: Don't Block Your Workers"

Layout: A horizontal timeline divided into two sections — SYNC (short) and ASYNC (long). A worker slot indicator shows when it's occupied vs free.

TOP SECTION (timeline):
- A horizontal time arrow going left to right
- LEFT PORTION (short, ~20% of timeline): 
  - Labeled "SYNC (fast)" with green border (#10B981)
  - Three small boxes in sequence: "extract API" → "write file" → "PUT"
  - Total time label: "~5 seconds"
  - Worker slot bar below: FILLED (amber #F59E0B)

- RIGHT PORTION (long, ~75% of timeline):
  - Labeled "ASYNC (frees the worker)" with blue border (#29B5E8)
  - A large bracket spanning the section with items listed inside:
    - "Snowflake task runs autonomously"
    - "Airflow sensor: reschedule mode" 
    - "Worker slot freed immediately"
    - "Sensor re-checks every 15 seconds" (with small clock icons)
    - "dbt via deferrable operator"
  - Worker slot bar below: EMPTY (light gray, with text "freed")
  - Total time label: "30s → 30min (Snowflake handles it)"

BOTTOM SECTION (comparison):
- Two small comparison boxes:
  - LEFT box (red border #EF4444): "BLOCKING: Worker occupied entire time = queue builds"
  - RIGHT box (green border #10B981): "ASYNC: Worker free in 5s = handles 100x more DAGs"

KEY VISUAL:
- A hand-drawn "release" moment where the worker slot goes from filled to empty
- This is the central dramatic point of the diagram
- Maybe a small breaking-chain or unlock icon at the transition point

Style notes:
- The contrast between the short SYNC section and long ASYNC section tells the story
- Worker slot visualization is like a Gantt bar (filled vs empty)
- Color palette: Green (#10B981) for sync/good, Blue (#29B5E8) for async/Snowflake, Amber (#F59E0B) for worker occupied, Red (#EF4444) for blocking pattern, Gray (#374151) for text
- Keep it scannable — the visual should be understood in 3 seconds
```

---

## README Diagrams

### 07-local-dev-stack.png

```
Create a technical architecture diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x800 pixels.

Title at top: "Local Development Stack (Docker Compose)"

Layout: A large rounded rectangle labeled "Docker Compose (Your Machine)" containing 3 boxes inside, with an arrow going out to a cloud shape below.

INSIDE THE DOCKER COMPOSE BOX (3 containers in a row):
1. Box labeled "Mock API" with subtitle ":8099" and small text "/docs (Swagger)"
2. Box labeled "Airflow" with subtitle ":8080" and 3 small components listed: "webserver | scheduler | triggerer"
3. Box labeled "PostgreSQL" with subtitle "(metadata)" and a small lock icon

- An arrow from "Mock API" to "Airflow" labeled "HTTP response"
- An arrow from "Airflow" to "PostgreSQL" labeled "state"

BELOW (outside the Docker box):
- A cloud shape labeled "Snowflake" with thick blue border (#29B5E8)
- Inside the cloud: "Stage → Stream → Task → Bronze → dbt → Gold"
- A thick arrow from Airflow down to the cloud labeled "PUT file + SQL (key-pair auth)"

Style notes:
- Docker box: thick dashed dark gray border (#374151), rounded corners
- Internal boxes: solid borders, slightly different colors (green for API, amber for Airflow, gray for Postgres)
- Cloud: blue (#29B5E8), hand-drawn fluffy shape
- Arrow from Docker to Cloud: emphasized, thick, labeled
- Font: hand-written style throughout
- Color palette: #29B5E8 (Snowflake), #374151 (Docker), #10B981 (API), #F59E0B (Airflow)
```

---

### 08-deployment-options.png

```
Create an infographic comparison diagram in hand-drawn sketch style (Excalidraw aesthetic with wobbly lines and hand-written font). White background. Dimensions: 1200x900 pixels.

Title at top: "Where Should You Run Airflow?"

Layout: 6 boxes arranged in a 3x2 grid, each representing a deployment option. Each box has a header, a small icon/symbol, and 3 key bullet points.

ROW 1 (left to right):

Box 1 - "Docker Compose"
- Icon: small laptop sketch
- Bullets: "Free", "Local only", "Learning & demos"
- Border: gray (#374151)
- Tag: "Articles 1-5"

Box 2 - "SPCS (Snowflake)"
- Icon: snowflake symbol
- Bullets: "Zero egress", "Single bill", "Native RBAC"
- Border: blue (#29B5E8)
- Tag: "Bonus 1"

Box 3 - "Amazon MWAA"
- Icon: cloud with "AWS" text
- Bullets: "Fully managed", "S3 native", "Auto-scaling"
- Border: amber (#F59E0B)
- Tag: "Bonus 2"

ROW 2 (left to right):

Box 4 - "Astronomer"
- Icon: rocket sketch
- Bullets: "Multi-cloud", "Premium support", "$$$"
- Border: purple (#8B5CF6)
- Tag: "Commercial"

Box 5 - "Cloud Composer"
- Icon: cloud with "GCP" text
- Bullets: "GKE-based", "BigQuery native", "GCP only"
- Border: green (#10B981)
- Tag: "GCP"

Box 6 - "Self-Hosted K8s"
- Icon: wheel/helm symbol
- Bullets: "Full control", "Max flexibility", "You own ops"
- Border: dark gray (#374151)
- Tag: "DIY"

BOTTOM (centered):
A horizontal spectrum line from "Less Control / Less Ops" on left to "Full Control / Full Ops" on right, with dots marking where each option falls:
- Docker (far left)
- MWAA, Astronomer, Composer (middle-left)
- SPCS (middle)
- Self-Hosted K8s (far right)

Style notes:
- Each box has rounded corners, hand-drawn borders
- Tags are small badges in the top-right corner of each box
- The spectrum line at bottom is a hand-drawn line with labeled dots
- Font: hand-written throughout
- Keep it scannable — max 3 bullets per box, short phrases only
```

---

## Article 2 Diagrams

### art2-00-cover.png (Article 2 Cover — Full Pipeline Overview)

```
Create a professional infographic in flat design style. Clean vectors, sharp edges, NO hand-drawn aesthetic. White background. Dimensions: 1200x1500 portrait.

Title at top (bold, dark #1F2937): "Building an Incremental CDC Pipeline (Locally)"
Subtitle (lighter, #6B7280): "API → PUT → Stage → Stream → Triggered Task → Bronze"

PRIMARY VISUAL (center, ~60% of image):
A numbered step-flow diagram showing the complete pipeline path:

Step cards (rounded rectangles with numbered circles):
① "Mock API" — icon: server/API symbol — color: green (#10B981)
② "Extract (paginated)" — icon: download arrow — color: green (#10B981)
③ "Write JSON file" — icon: file/document — color: gray (#374151)
④ "PUT to Stage" — icon: upload arrow — color: blue (#2563EB)
⑤ "Stream detects" — icon: eye/radar — color: teal (#0D9488)
⑥ "Triggered Task fires" — icon: lightning bolt — color: teal (#0D9488)
⑦ "MERGE INTO Bronze" — icon: merge/combine arrows — color: teal (#0D9488)

Connectors between steps: dashed lines with small arrows.

SECTION LABELS (pill-shaped badges):
- Steps 1-3: "AIRFLOW (control plane)" pill in gray
- Steps 4-7: "SNOWFLAKE (runtime)" pill in teal

SIDE ANNOTATIONS:
- Near step 1: "Watermark: since=2026-06-28T14:55Z"
- Near step 4: "~5 seconds of worker time"
- Near step 7: "Idempotent MERGE (safe to replay)"

BOTTOM STRIP:
- Three stat boxes in a row:
  - "5s" / "Active worker time per run"
  - "15s" / "Sensor poll interval"
  - "0" / "DataFrames used"

Color palette: Primary Blue (#2563EB), Teal (#0D9488) for Snowflake, Green (#10B981) for extraction, Gray (#374151) for text, Orange (#F97316) for warnings/highlights. White background.
```

---

### art2-01-docker-stack.png (Local Stack Architecture)

```
Create a professional infographic in flat design style. Clean vectors, sharp edges. White background. Dimensions: 1200x800 landscape.

Title (top-left, bold): "Local Development Stack"

MAIN LAYOUT:
A large rounded rectangle labeled "Docker Compose (your laptop)" with a dashed dark gray border.

Inside the Docker rectangle, THREE service boxes in a horizontal row:

Box 1 — "Mock API (EventHub)"
- Subtitle: ":8099"
- Small text: "FastAPI + /docs"
- Color: green fill (#ECFDF5), green border (#10B981)
- Icon: small API/server symbol

Box 2 — "Airflow"
- Subtitle: ":8080"
- Three sub-components listed: "webserver | scheduler | triggerer"
- Color: amber fill (#FFFBEB), amber border (#F59E0B)
- Icon: airflow logo / workflow symbol

Box 3 — "PostgreSQL"
- Subtitle: ":5432"
- Small text: "metadata only"
- Color: gray fill (#F3F4F6), gray border (#6B7280)
- Icon: database cylinder

ARROWS INSIDE DOCKER:
- Mock API → Airflow: labeled "HTTP response"
- Airflow → PostgreSQL: labeled "state"

BELOW THE DOCKER BOX (cloud shape):
- A blue cloud shape (#29B5E8 border) labeled "Snowflake (cloud)"
- Inside: "Stage → Stream → Task → Bronze"
- A thick arrow from Airflow box DOWN to the cloud:
  - Label: "PUT file + SQL commands"
  - Sub-label: "key-pair auth (no passwords)"

BOTTOM NOTE:
"Everything runs locally except Snowflake. No S3, no cloud infra, no IAM roles."

Color palette: Green (#10B981) for API, Amber (#F59E0B) for Airflow, Blue (#29B5E8) for Snowflake, Gray (#6B7280) for Postgres. White background.
```

---

### art2-02-watermark-flow.png (Watermark Timeline)

```
Create a professional infographic in flat design style. Clean vectors, sharp edges. White background. Dimensions: 1200x600 landscape.

Title (top-left, bold): "Watermark-Based Incremental Extraction"

MAIN VISUAL — A horizontal timeline:

TIME ARROW running left to right, with time labels:
- "14:50" ... "14:55" ... "15:00" ... "15:05"

THREE LABELED RUNS on the timeline:

Run 1 (at 14:55):
- Blue dot on timeline
- Above: card labeled "Run 1"
- Inside card: 
  - "Read watermark: 14:50"
  - "Extract since 14:50"
  - "Got 18 records"
  - "Advance to 14:55"
- Arrow pointing from 14:50 to 14:55 on timeline, labeled "window"

Run 2 (at 15:00):
- Blue dot on timeline
- Above: card labeled "Run 2"
- Inside card:
  - "Read watermark: 14:55"
  - "Extract since 14:55"
  - "Got 22 records"
  - "Advance to 15:00"
- Arrow pointing from 14:55 to 15:00 on timeline, labeled "window"

Run 3 (at 15:05):
- Blue dot on timeline
- Above: card labeled "Run 3"
- Inside card:
  - "Read watermark: 15:00"
  - "Extract since 15:00"
  - "Got 0 records → SKIP"
- No advance arrow (skipped)

KEY INSIGHT BOX (bottom-right):
Orange border (#F97316), contains:
"Watermark only advances AFTER Bronze is confirmed loaded.
If the task fails → watermark stays → next run retries from same point.
Zero data loss. Zero gaps."

Color palette: Blue (#2563EB) for timeline/runs, Orange (#F97316) for insights, Gray (#374151) for text. White background.
```

---

### art2-03-put-stage-stream.png (File → Stage → Stream → Task → MERGE)

```
Create a professional infographic in flat design style. Clean vectors, sharp edges. White background. Dimensions: 1200x800 landscape.

Title (top-left, bold): "From File to Bronze: The Event-Driven Path"

MAIN VISUAL — A left-to-right flow with 5 numbered stages:

Stage 1: "PUT file"
- Icon: upload arrow into a folder
- Label below: "Airflow uploads JSON"
- Color: gray (#374151)
- Annotation: "~1 second"

→ (dashed arrow)

Stage 2: "@TICKETING_STAGE"
- Icon: folder with snowflake symbol
- Label below: "Internal stage (encrypted)"
- Color: blue (#2563EB)
- File icon inside showing "tickets.json"

→ (solid arrow labeled "ALTER STAGE REFRESH")

Stage 3: "Directory Stream"
- Icon: eye/radar watching the stage
- Label below: "Detects new file metadata"
- Color: teal (#0D9488)
- Small annotation: "METADATA$ACTION = 'INSERT'"

→ (lightning bolt arrow labeled "SYSTEM$STREAM_HAS_DATA → TRUE")

Stage 4: "Triggered Task"
- Icon: lightning bolt / gear
- Label below: "Fires automatically"
- Color: teal (#0D9488)
- Annotation: "No schedule — event-driven"

→ (solid arrow)

Stage 5: "MERGE INTO Bronze"
- Icon: merge/combine symbol
- Label below: "Idempotent load"
- Color: teal (#0D9488)
- Annotation: "Dedup on ticket_id"

SEPARATION LINE:
A vertical dashed line between Stage 1 and Stage 2, with labels:
- Left of line: "AIRFLOW (done in 1s)"
- Right of line: "SNOWFLAKE (autonomous)"

BOTTOM BOX (blue fill #EFF6FF):
"After PUT, Airflow's job is done. Snowflake's stream + task handle the rest.
No polling needed from Airflow to trigger the load — it's event-driven inside Snowflake."

Color palette: Gray (#374151) for Airflow steps, Blue (#2563EB) for stage, Teal (#0D9488) for Snowflake automation. White background.
```

---

### art2-04-reschedule-sensor.png (Poke vs Reschedule Comparison)

```
Create a professional infographic in flat design style. Clean vectors, sharp edges. White background. Dimensions: 1200x700 landscape.

Title (top-left, bold): "Sensor Modes: Poke vs Reschedule"

LAYOUT — Two horizontal timelines stacked vertically:

TOP TIMELINE — "mode='poke'" (bad):
- Header: "❌ Poke Mode" with red (#EF4444) accent
- Horizontal bar representing worker slot: SOLID RED fill for entire duration
- Time labels: "0s" ... "15s" ... "30s" ... "45s" ... "60s (done)"
- Small "check" markers at 0s, 15s, 30s, 45s, 60s on the bar
- Between checks: bar still RED (worker occupied)
- Label below bar: "Worker BLOCKED for 60 seconds (even though checks take 200ms each)"
- Stats: "5 checks × 200ms = 1 second of useful work. 59 seconds wasted."

BOTTOM TIMELINE — "mode='reschedule'" (good):
- Header: "✅ Reschedule Mode" with green (#10B981) accent
- Horizontal bar: SHORT green blocks (200ms each) at 0s, 15s, 30s, 45s, 60s
- Between blocks: WHITE/empty (worker freed)
- Small "release" icons between blocks showing worker is returned to pool
- Label below bar: "Worker freed between checks. Available for other DAGs."
- Stats: "Same 5 checks, same 200ms each. But worker free for 59 seconds."

COMPARISON BOX (bottom center):
Two-column comparison:
| | Poke | Reschedule |
| Worker time held | 60s | ~1s |
| Other DAGs can run? | No | Yes |
| 16 workers, 20 sensors | Queue builds | All fit |

Color palette: Red (#EF4444) for poke/bad, Green (#10B981) for reschedule/good, Blue (#2563EB) for highlights, Gray (#374151) for text. White background.
```
