# Roadmap

> Feature-freeze / build-complete target: **June 18–19**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**
> Team: Victor (Role 1) · Gary (Role 2) · Christian (Role 3)
> Last updated: **June 3, 2026**

The build is sequenced slice-first: sneaker/streetwear end-to-end as a complete
demo-ready proof, then contemporary fashion adapted from the same pipeline.

---

## Current status

**Phase 1 complete.** Phase 2 in progress — ahead of schedule on frontend (mock
flow ships; live pipeline swap is Phase 3).

**Critical path:** Gary's seed corpus slice 1 (~75 images) blocks everything
downstream — Christian's batch extraction, the first live E2E run, Victor's
frontend-to-pipeline connect, and demo pre-warming.

| Layer | Status |
|---|---|
| Backend pipeline | Wired (`api.py` → `pipeline/run.py` → retrieval / extract / synthesize) |
| Frontend | Full mock flow (brief → agent log → report); not yet calling `POST /query` |
| Seed corpus | Not started — no curated image set in repo |
| Slice 2 plumbing | Publication lists + Are.na queries + synthesizer sub-slice context already in code; needs corpus + verification |

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

## Phase 2 — Slice 1 end-to-end (in progress · target June 15)

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
- [ ] Seed corpus slice 1: ~75 sneaker/streetwear images, hand-curated

**Role 3 — Christian**
- [ ] Seed corpus extraction: run extractor over all ~75 seed images, store results
- [x] Editorial synthesizer: aggregated schema + brief → 4–6 named saturation patterns
- [x] Synthesis prompt primed on Snarkitecture voice (dry, factual, material-specific)
- [x] Sneaker/streetwear reference patterns wired in
- [ ] Manual end-to-end run: verify full pipeline produces valid output
  - `scripts/run_e2e.py` ready; live keys configured — **blocked on seed corpus**
- [x] Write tests for synthesizer output structure

---

## Phase 3 — Integration + slice 2 (June 15–18)

**Role 1 — Victor**
- [ ] Connect frontend to live pipeline (`POST /query` at `localhost:8000`)
- [ ] Wire agent log to live retrieval reasoning log (`retrieval_log` in `/query` response; mock UI exists)
- [ ] Polish: typography, spacing, image attribution display
- [ ] Cross-browser / responsive check
- [x] Slice 2 UI: sub-slice selector (shipped early in Phase 2; mock results don't vary by slice yet)

**Role 2 — Gary**
- [ ] Seed corpus slice 2: ~75 contemporary fashion images, hand-curated
- [x] Publication list for slice 2 (Dezeen, Frame, Wallpaper, Sight Unseen) — wired in `retrieval/tavily.py`
- [ ] Verify caching works across both slices (keying exists; needs live runs with corpus)

**Role 3 — Christian**
- [ ] Seed corpus extraction: run extractor over slice 2 seed images
- [ ] Swap schema to contemporary fashion dimensions (shared v2.5 vocab today; slice-specific dims TBD)
- [ ] Update synthesis prompt with slice 2 reference patterns (sub-slice context block exists in `src/synthesizer.py`; dedicated calibration reference still needed)
- [ ] End-to-end test query for slice 2

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
