# Architecture

> For full product context, see [PRD.md](PRD.md).
> For the definition layer and controlled vocabulary, see [docs/schema.md](docs/schema.md).

## Three-layer stack

```
Tavily (live search)
Are.na API              →  Claude (extraction + synthesis)  →  React UI
Publication archives
Seed corpus

(corpus, extractions, and brief cache persisted in SQLite — hindcast.db)
```

**Layer 1 — Retrieval**
Tavily (live search), the Are.na API, design-publication archives, and a hand-curated
seed corpus. State persists in a local SQLite store (`hindcast.db`) — the image corpus,
schema extractions, and brief cache (see [Storage](#storage)).

**Layer 2 — Analysis and synthesis**
Claude Sonnet 4.6 handles both per-image schema extraction and editorial synthesis. No
separate vision model required.

**Layer 3 — Output**
A React UI styled on Are.na's aesthetic — clean, minimal, image-forward. An image grid
with editorial framing; 4–6 named saturation patterns per query.

## The pipeline

1. User submits brief: sub-slice selection + free-text brief.
2. Retrieval agent checks the seed corpus and cache, then runs live queries to fill gaps.
   Loops to refine if needed (see [AGENTS.md](AGENTS.md)).
3. Claude extracts schema attributes per image (single-shot). Seed-corpus images are
   pre-extracted at build time.
4. Aggregated schema data + original brief feeds the synthesis prompt; Claude returns
   4–6 saturation observations.
5. Output rendered (image grid + patterns + per-query `source_breakdown`). New
   extractions are written to `schema_extractions`; the brief → image-set mapping is
   cached in `brief_cache` for repeat queries.

## Retrieval architecture

A deliberate hybrid of static and live data:

- **Seed corpus** — 118 hand-curated images (≈108 effective after the per-source cap,
  PR #21; ≈69 sneaker/streetwear, ≈49 contemporary fashion), schema-extracted at build
  time. Provides a stable baseline population so saturation reads against something
  consistent from the first query.
- **Live retrieval** — At query time, the agent retrieves additional images via Tavily,
  scoped to a curated publication list (not the open web). Keeps findings current.
- **Caching layer** — The `brief_cache` table maps a normalized brief (+ sub-slice) to
  its image set. First run hits live sources and stores results; similar later queries
  serve from cache. This only speeds repeat briefs — it does **not** affect saturation.
- **Saturation sharpens as the corpus grows** — synthesis denominates over the full
  *extracted* corpus (`schema_extractions`), so each newly analyzed image refines the
  read. (Pre-#30 this query was capped at 500 raw image rows by insertion order, which
  silently dropped newer extractions; #30 removed the cap and reads `schema_extractions`
  directly.)

## Storage

State lives in a single **SQLite** database at the project root (`hindcast.db`, WAL
mode), accessed through `pipeline/storage.py`. Three tables:

- **`images`** — every retrieved image with metadata (URL, source, title, sub-slice,
  retrieval method, brief hash).
- **`schema_extractions`** — per-image schema attributes, one row per category with the
  nested `{dimension: value}` block JSON-encoded. This is the *analyzed* corpus that
  synthesis and saturation read from (distinct from the larger `images` table, most of
  which is retrieved but not yet extracted).
- **`brief_cache`** — normalized brief → image-set mapping for cache lookups.

SQLite is appropriate for prototype scale; swap for PostgreSQL post-demo if query volume
grows.

## Definition layer

Every retrieved image is scored against a structured schema with controlled vocabulary —
the data that makes saturation quantifiable. See [docs/schema.md](docs/schema.md) for the
full schema: seven shared base categories (Material, Form/Geometry, Color, Lighting,
Texture, Opacity, Atmosphere/Warmth) plus sub-slice-specific dimensions for
sneaker/streetwear and contemporary fashion.

## Open questions

- ArchDaily API status (fallback: scoped Tavily search).
- Tavily plan/tier and rate limits — verify at build time.
- Final publication lists for each sub-slice.
- URL display in output (retained in underlying data regardless of display decision).
