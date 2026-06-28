# Diagram Generation Prompts (Gemini / AI Image Gen)

> These prompts are used to generate the diagrams for the article series.
> Tool: Gemini image generation (or Excalidraw manual creation)
> Style: Hybrid — structured layout + hand-drawn/sketch aesthetic

---

## Article 1 Diagrams

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
