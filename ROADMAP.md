# Roadmap

> Feature-freeze / build-complete target: **June 18–19**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**
> Team: Victor (Role 1) · Gary (Role 2) · Christian (Role 3)
> Last updated: **June 13, 2026**

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
- **P1s:** pattern-image term matching → #41 (Victor); retrieval junk filter → #38 (Gary).
- Then: cache pre-warm + demo hardening.

| Layer | Status |
|---|---|
| Backend pipeline | Wired, runs E2E. Round-trip fixed (#26). Saturation/synthesis denominate over the extracted set, not a 500-row window (#30, + denominator/isolation tests). ~108 extracted images → 6 grounded patterns/slice (June 12; sneaker re-verified on this branch). |
| Frontend | Live `POST /query`; renders `retrieval_log` + patterns. `corpus_size` now reflects analyzed (extracted) images; per-image `year` no longer fabricated (#27 item 3 display). **Open P1:** pattern images are a positional slice of retrieval, not matched to each pattern's terms (#41). |
| Seed corpus | **Extracted (June 12):** 108 images, 1,080 schema rows, valid JSON round-trip confirmed. (~64–65 sneaker / ~43–44 fashion — split varies with the 1 failed image + per-source cap.) |
| Slice 2 plumbing | Publication lists + Are.na queries + synthesizer sub-slice context in code; seed extraction + synthesis E2E verified June 12. |

---

## Known issues / blockers (discovered June 9 — live E2E run)

The first two severed the analytical core (output *looked* data-driven but was not) —
both **resolved in #26**. The two P1s remain open; full detail and discussion live in
the linked issues. (Post-mortem write-ups for the resolved P0s belong in `CHANGELOG.md`.)

- **P0 — Schema round-trip (storage).** ✅ Resolved in #26 (Gary, `pipeline/storage.py`).
  Nested schema was stored as a stringified dict and dropped by `_aggregate`; fixed with a
  `json.dumps`/`loads` round-trip. Legacy rows purged via `purge_legacy_extractions()` —
  re-extraction required.
- **P0-assist — Aggregator failed silently.** ✅ Resolved in #26 (Christian,
  `src/synthesizer.py`). `_aggregate` now raises `ValueError` on a non-dict category
  instead of `continue`-ing.
- **P1 — Pattern images not matched to pattern → [#41](https://github.com/vic-aibuilder/hindcast/issues/41)**
  (Victor, `frontend/src/api.ts`). Positional slicing (`offset = i * 8`) instead of
  term-matched images; `_count_images_for_pattern` already matches but discards which.
- **P1 — Retrieval returns unfiltered junk → [#38](https://github.com/vic-aibuilder/hindcast/issues/38)**
  (Gary, `retrieval/`). Tavily `include_images=True` dumps logos/headshots/non-NYC stores
  with no relevance filter, plus a URL-as-image fallback (`agent.py:168`) — what put a
  HYPEBEAST logo card and a Nike Dubai store in the grid. #39 was a partial URL-pattern
  mitigation only. *(Root-cause detail still to be added to #38.)*

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
- [ ] Swap schema to contemporary fashion dimensions (shared v2.5 vocab today; slice-specific dims TBD) → #40
  Note: this is the *extraction-vocab* layer — distinct from the synthesis-time calibration added in #37 (next item). Calibration changes how findings are *interpreted*, not what gets *extracted*, so it does not close this. Tracked in #40.
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
