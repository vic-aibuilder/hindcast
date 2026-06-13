# Roadmap

> Feature-freeze / build-complete target: **June 18–19**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**
> Team: Victor (Role 1) · Gary (Role 2) · Christian (Role 3)
> Last updated: **June 12, 2026**

The build is sequenced slice-first: sneaker/streetwear end-to-end as a complete
demo-ready proof, then contemporary fashion adapted from the same pipeline.

---

## Current status

**Phase 1 complete. Phase 2 Role 3 tasks complete** (seed extraction, synthesizer,
E2E). Seed corpus extracted (108 images, 1,080 schema rows); synthesis **confirmed
data-grounded on both slices** (June 12 E2E — sneaker and fashion each return grounded
patterns from real extractions). P0/P0-assist resolved in PR #26. **This PR (#30)**
makes saturation/synthesis read the *extracted* set directly (`schema_extractions`),
dropping the old 500-row cap so seed images surface even when live-retrieval rows
dominate `images` — resolving **#27 Item 2** (full-extracted-corpus denominator;
**Gary-ratified**).

**Critical path to demo — not just hardening; open items remain:**

- **#27 Item 1 (docs, Victor):** README/ARCHITECTURE synced to the SQLite layer + real
  seed counts (PR #32); this roadmap updated here.
- **Attribution (#33, split from #27):** `year` was fabricated. **Display half done** —
  derives from title, omits when unknown (PR #31). **Data half — pending team call:**
  accept derived attribution for the demo, or capture real `designer/year/project`
  columns at retrieval (Gary).
- **P1s:** pattern-image term matching (Victor); retrieval junk filter (Gary).
- Then: cache pre-warm + demo hardening.

| Layer | Status |
|---|---|
| Backend pipeline | Wired, runs E2E. Round-trip fixed (#26). Saturation/synthesis denominate over the extracted set, not a 500-row window (#30, + denominator/isolation tests). ~108 extracted images → 6 grounded patterns/slice (June 12; sneaker re-verified on this branch). |
| Frontend | Live `POST /query`; renders `retrieval_log` + patterns. `corpus_size` now reflects analyzed (extracted) images; per-image `year` no longer fabricated (#27 item 3 display). **Open P1:** pattern images are a positional slice of retrieval, not matched to each pattern's terms. |
| Seed corpus | **Extracted (June 12):** 108 images, 1,080 schema rows, valid JSON round-trip confirmed. (~64–65 sneaker / ~43–44 fashion — split varies with the 1 failed image + per-source cap.) |
| Slice 2 plumbing | Publication lists + Are.na queries + synthesizer sub-slice context in code; seed extraction + synthesis E2E verified June 12. |

---

## Known issues / blockers (discovered June 9 — live E2E run)

Ranked. The first two severed the analytical core (output *looked* data-driven but
was not) — both are now resolved in #26; the two P1s remain open.

- **P0 — Schema never reaches synthesis (storage round-trip).** ✅ **Resolved in #26.**
  Owner: Gary (`pipeline/storage.py`). The extractor emits a *nested*
  `{category: {dimension: value}}` schema, but `save_extraction` was written for a
  *flat* schema and stored each category as `str(value)` → a stringified dict that
  `_aggregate` saw as a string and dropped. **Was:** 37 stored sneaker extractions →
  **0** non-zero term counts; patterns confabulated from priming, not data.
  **Fix (#26):** `json.dumps`/`json.loads` the nested category block on write/read so
  it round-trips (verified: 33 non-zero counts on a round-trip test). Legacy corrupt
  rows are cleared by `purge_legacy_extractions()` — re-extraction required to repopulate.
- **P0-assist — Aggregator fails silently.** ✅ **Resolved in #26.** Owner: Christian
  (`src/synthesizer.py`). `_aggregate` did `continue` on a shape mismatch instead of
  raising — which is *why* P0 went unnoticed. **Fix (#26):** it now raises `ValueError`
  on a non-dict category, surfacing this class of break on the first run.
- **P1 — Pattern images are unrelated to the pattern.** Owner: **Victor**
  (`frontend/src/api.ts`). `adaptQueryResponse` slices the global retrieved-image
  list by position (`offset = i * 8`) and bolts 8 images onto each pattern — no link
  to the pattern's `dominant_terms`. The synthesizer already matches images to terms
  in `_count_images_for_pattern`; it just discards *which* ones.
- **P1 — Retrieval returns unfiltered junk.** Owner: **Gary** (`retrieval/agent.py`,
  `retrieval/tavily.py`). Tavily `include_images=True` dumps every image on each
  result page (logos, related-article thumbnails, author headshots, non-NYC stores)
  with no relevance filter, plus a fallback that uses the page URL itself as an
  "image" (`agent.py:168`). This is what put a HYPEBEAST logo card, an IKEA Oxford
  St storefront, and a Nike Dubai store in the grid.

---

## Role split

| Role | Owner | Scope |
|---|---|---|
| **Role 1 — Victor** | Victor | Frontend (React UI) + repo oversight |
| **Role 2 — Gary** | Gary | Retrieval pipeline (agent loop, Tavily, Are.na, caching, seed corpus) |
| **Role 3 — Christian** | Christian | Claude integration (schema extractor, editorial synthesizer, prompt engineering) |

---

## Phase 1 — Foundation (complete)

**Role 1 — Victor**
- [x] Set up React project (Vite + TypeScript)
- [x] Wire `.env` and confirm API keys load
- [x] Branch protection + collaborator access on GitHub
- [x] Establish PR workflow for the team

**Role 2 — Gary**
- [x] Tavily integration: scoped queries against publication list
- [x] Are.na API integration: channel queries
- [x] Basic retrieval function: query in, image URLs + metadata out
- [x] Verify ArchDaily API status; fall back to scoped Tavily if dead

**Role 3 — Christian**
- [x] Claude client setup (Anthropic SDK, Sonnet 4.6)
- [x] Per-image schema extractor: image in, structured schema attributes out (sneaker/streetwear dimensions)
- [x] Schema output validated against `docs/schema.md` controlled vocabulary
- [x] Write tests for schema extractor

---

## Phase 2 — Slice 1 end-to-end (complete · Role 3)

**Role 1 — Victor**
- [x] Brief submission UI (sub-slice selector + free-text input)
- [x] Agent visibility log component (streaming reasoning during load)
- [x] Output layout: brief summary + pattern blocks stacked
- [x] Per-pattern component: title, description, image grid (project + designer + year)
- [x] Are.na-referenced visual style: clean, minimal, image-forward
  - All five built against mock data (PR #9). Live pipeline swap is Phase 3.
    Visual style implemented from the approved wireframe (`docs/wireframe.html`).

**Role 2 — Gary**
- [x] Retrieval agent loop (max 4 iterations): observe → decide → act → repeat
- [x] Self-assessment logic: corpus representative? gaps? off-context noise?
- [x] Caching layer: keyed by sub-slice + normalized brief
- [x] Seed corpus slice 1: 60 sneaker/streetwear images, hand-curated (PR #21)

**Role 3 — Christian**
- [x] Seed corpus extraction: 108/109 images extracted (64 sneaker, 44 fashion), 1,080 schema rows stored with valid JSON (June 12)
- [x] Editorial synthesizer: aggregated schema + brief → 4–6 named saturation patterns
- [x] Synthesis prompt primed on Snarkitecture voice (dry, factual, material-specific)
- [x] Sneaker/streetwear reference patterns wired in
- [x] Manual end-to-end run: seed-corpus synthesis verified on both slices — 6 grounded patterns each, non-zero aggregator term counts (June 12)
- [x] Write tests for synthesizer output structure

---

## Phase 3 — Integration + slice 2 (June 15–18)

**Role 1 — Victor**
- [x] Connect frontend to live pipeline (`POST /query` at `localhost:8000`) — live in `frontend/src/api.ts`
- [x] Wire agent log to live retrieval reasoning log (`retrieval_log` in `/query` response)
  - Captured + rendered from the live response. Note: **not streamed** — `/query` is a
    single blocking POST, so the loading view shows static placeholders until it returns.
- [ ] Polish: typography, spacing, image attribution display
- [ ] Cross-browser / responsive check
- [x] Slice 2 UI: sub-slice selector (shipped early in Phase 2; mock results don't vary by slice yet)

**Role 2 — Gary**
- [x] Seed corpus slice 2: 58 contemporary fashion images, hand-curated (PR #21, landed early)
- [x] Publication list for slice 2 (Dezeen, Frame, Wallpaper, Sight Unseen) — wired in `retrieval/tavily.py`
- [ ] Verify caching works across both slices (keying exists; needs live runs with corpus)
- [ ] Follow-ups from PR #21: re-source 29 dropped hs2architecture.com images (#22);
  Madhappy slice placement ✅ resolved in #28

**Role 3 — Christian**
- [x] Seed corpus extraction: run extractor over slice 2 seed images (44/44, June 12)
- [ ] Swap schema to contemporary fashion dimensions (shared v2.5 vocab today; slice-specific dims TBD)
  Note: calibration block work (above) may have addressed much of the gap this item was meant to solve — recommend team review before committing to vocab additions.
- [x] Update synthesis prompt with slice/category-specific calibration references for both sub-slices (sneaker_streetwear + contemporary_fashion baselines added to `_SUB_SLICE_CONTEXT` in `src/synthesizer.py`, tested via synthesis-only re-runs on existing seed extractions — both slices show category-aware contrast framing)
- [x] End-to-end test query for slice 2 — seed-corpus synthesis verified, 6 patterns (June 12)

> **Risk framing:** if timeline pressure hits, sneaker/streetwear (slice 1) is the
> committed deliverable. Slice 2 can be shown as an extension of the same approach.

---

## Phase 4 — Demo prep (June 19–23)

- [ ] Pre-warm 3–5 demo queries per slice (cache hits = fast load on the day)
- [ ] Harden demo path: one clean run, no edge cases exposed
- [ ] Build slide deck
- [ ] Write and rehearse presentation speech
- [ ] Dry run with full team

> Demo Day is the **performance** deadline. Build must be complete by June 18–19 to
> leave real time for prep.
