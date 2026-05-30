# Architecture

> For full product context, see [PRD.md](PRD.md).
> For the definition layer and controlled vocabulary, see [docs/schema.md](docs/schema.md).

## Three-layer stack

```
Tavily (live search)
Are.na API              →  Claude (extraction + synthesis)  →  React UI
Publication archives
Seed corpus + cache
```

**Layer 1 — Retrieval**
Tavily (live search), the Are.na API, design-publication archives, and a hand-curated
seed corpus. A caching layer sits across all sources.

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
5. Output rendered. New extractions written to cache.

## Retrieval architecture

A deliberate hybrid of static and live data:

- **Seed corpus** — ~150 images (~75 per sub-slice), hand-curated and schema-extracted
  at build time. Provides a stable baseline population so saturation reads against
  something consistent from the first query.
- **Live retrieval** — At query time, the agent retrieves additional images via Tavily,
  scoped to a curated publication list (not the open web). Keeps findings current.
- **Caching layer** — Keyed by sub-slice + normalized brief. First run hits live sources
  and stores results; similar later queries serve from cache. The cache grows over time,
  improving saturation precision without a separate ingestion pipeline.

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
