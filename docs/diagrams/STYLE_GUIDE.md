# Diagram Style Guide

## Tool
[Excalidraw](https://excalidraw.com/) — free, open-source, exports PNG/SVG.

## Style Settings
- **Line style:** Hand-drawn (not straight/sharp)
- **Font:** Virgil (Excalidraw's hand-written font)
- **Roughness:** 1 (default hand-drawn wobble)
- **Stroke width:** 2 for boxes, 1 for arrows
- **Background:** White (#FFFFFF) — NOT dark mode (optimized for Medium)
- **Grid:** Subtle dots (for alignment), hidden in export

## Color Palette
| Color | Hex | Usage |
|-------|-----|-------|
| Snowflake Blue | `#29B5E8` | Primary, Snowflake objects, success states |
| Dark Gray | `#374151` | Borders, labels, Airflow objects |
| Green | `#10B981` | Success flows, data movement |
| Amber | `#F59E0B` | Warnings, attention |
| Red | `#EF4444` | Errors, anti-patterns |
| White | `#FFFFFF` | Background |

## Layout Rules
1. **Structured grid** — boxes aligned, consistent spacing
2. **Size = importance** — Snowflake boxes 3x wider than Airflow boxes
3. **Flow direction** — left-to-right (orchestrator → runtime)
4. **Arrows** — thin dashed = signals, solid thick = data flow
5. **Labels** — always present, Virgil font, inside or below boxes

## Export Settings
- Format: PNG
- Scale: 2x (retina)
- Padding: 20px
- Min width: 1200px (Medium optimization)
- Cover images: 1200x630
- Inline diagrams: 1200x800

## File Naming
```
{article_number}-{slug}.excalidraw    # Source (committed)
{article_number}-{slug}.png           # Export (committed)
```

## Creating Diagrams
1. Open https://excalidraw.com/
2. Set background to white, turn on hand-drawn mode
3. Follow the ASCII layout in the article's diagram section
4. Apply colors from the palette above
5. Export as PNG @2x
6. Save both .excalidraw (source) and .png (export) to this directory
