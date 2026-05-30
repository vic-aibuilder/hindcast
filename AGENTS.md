# Agents

Hindcast uses three Claude Sonnet 4.6 agents. All three run on the same model; no
separate vision model is required. For the schema and controlled vocabulary used by the
extractor, see [docs/schema.md](docs/schema.md).

## 1 — Retrieval agent

Runs as a tool-use loop (not a fixed query template): observe → decide → act → repeat.

**Loop behavior**
1. Read the brief. Check seed corpus and cache. Propose initial search strategy across
   available sources.
2. Execute searches via tool calls.
3. Self-assess the corpus: representative of the brief? Gaps (style, sub-context)?
   Off-context noise?
4. Refine queries and search again if needed.
5. Stop when corpus is judged sufficient or max iteration count is reached.

**Constraints**
- Hard ceiling: **4 iterations**.
- Tools exposed: Tavily search query, Are.na API query, per-publication search (where
  APIs exist).
- Agent reasoning is logged and surfaced in the UI during loading — visible while the
  query runs, hidden once results render.

## 2 — Per-image schema extractor

Runs single-shot per image. Takes an image and returns structured schema attributes
against the sub-slice's controlled vocabulary (see [docs/schema.md](docs/schema.md)).
Seed-corpus images are pre-extracted at build time; live-retrieved images are extracted
at query time and written to cache.

## 3 — Editorial synthesizer

Reads aggregated schema data plus the original brief. Returns 4–6 named saturation
patterns. Each pattern: a title (Title Case, names the move), a 2–3 sentence description
(last sentence is a data observation about what's rare or absent in the corpus), and an
evidence set of 8–15 images with project + designer + year attribution.

Synthesis prompts are primed with sub-slice-specific reference patterns so output reads
as written by someone who knows the category. Full voice spec is in [PRD.md](PRD.md).
