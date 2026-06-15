# Roadmap

> **June 17 — Blackstone rehearsal (full presentation dry-run)**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**
> Team: Victor (Role 1) · Gary (Role 2) · Christian (Role 3)
> Last updated: **June 15, 2026**

The build is sequenced slice-first: sneaker/streetwear end-to-end as a complete
demo-ready proof, then contemporary fashion adapted from the same pipeline.

---

## Current status

Pipeline runs end-to-end on **both slices**; synthesis is data-grounded on real
extractions (June 12 E2E — 6 grounded patterns/slice). Every analytical-core blocker is
now resolved (see [CHANGELOG](CHANGELOG.md) for the list). A June 14 sneaker test run was
solid but surfaced two new **demo-visible** issues (#55, #56), now on the essential list
below.

| Layer | Status |
|---|---|
| Backend pipeline | Runs E2E. Denominates over the extracted set (#30). ~108 extracted images → 6 grounded patterns/slice. |
| Frontend | Live `POST /query`; renders `retrieval_log` + patterns with term-matched evidence images (#41). |
| Seed corpus | 108 images, 1,080 schema rows, valid JSON round-trip (June 12). |
| Slice 2 plumbing | Publication lists + Are.na queries + synthesizer sub-slice context in code; E2E verified June 12. |

---

## Essential for June 17 (Blackstone rehearsal)

Full presentation dry-run — slides + spoken walkthrough + **live demo of slice 1
(sneaker)**. Only the work required for that lands here; everything else is tracked as a
GitHub issue.

**Role 1 — Victor**
- [ ] **#29** — frontend polish: pipeline log redesign + pattern paragraph spacing
- [ ] **#55** — group pattern evidence images by store (display ordering; fix in `pipeline/run.py`)
- [ ] Cross-browser / responsive check — the hosted demo must render correctly on the day
- [ ] Deploy backend (FastAPI) + frontend (Vite build) to a hosted URL — set Tavily/Anthropic
  keys on the host, open CORS, and point the frontend API base off `localhost:8000`
  (with team; no host chosen yet)
  - ⚠️ Hosting exposes **#54** (blocking event loop): a concurrent request or a health
    probe freezes the server mid-query. Decide whether #54 must be fixed before the 17th.

**Role 2 — Gary**
- [ ] **#56** — enforce 2025–present window + uncapped subject filter; drop pre-2025 stores and off-subject junk (`retrieval/`)
- [ ] Pre-warm a clean sneaker demo query and confirm it serves from cache on reload —
  verifies **slice-1 caching** works for the day's fast load

**Role 3 — Christian**
- [ ] Build slide deck — ⚠️ **top schedule risk: nothing exists yet**
- [ ] Write the speech — ⚠️ **net-new, risk**

**Team**
- [ ] Harden the demo path: one clean run, no edge cases exposed
- [ ] Full-team dry run / rehearsal

> Slice 1 (sneaker) is what goes on screen on the 17th. Slice 2 is the stretch; its
> work (#40 + #53) is deferred.

**Tracked separately as [GitHub issues](https://github.com/vic-aibuilder/hindcast/issues),
not demo-blocking:** #22, #34, #35, #40, #53, #54.

---

## Slice 2 — stretch (deferred past June 17)

Slice 1 (sneaker) is the committed June 17 deliverable; slice 2 (contemporary fashion) is
an extension of the same pipeline — **not on screen at the rehearsal.** The plumbing is
already built (seed corpus, publication list, sub-slice calibration, slice-2 E2E — all
verified June 12; see Phase 3 for detail).

Deferred work:

**Role 2 — Gary**
- [ ] Verify caching works for **slice 2** (keying exists; needs live runs with the fashion
  corpus) — slice-1 caching is covered by the June 17 pre-warm

**Role 3 — Christian**
- [ ] **#40** — swap extraction schema to contemporary-fashion dimensions (paired with **#53**)

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

## Phase 2 — Slice 1 end-to-end (complete)

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

## Phase 3 — Integration (complete)

**Role 1 — Victor**
- [x] Connect frontend to live pipeline (`POST /query` at `localhost:8000`) — live in `frontend/src/api.ts`
- [x] Wire agent log to live retrieval reasoning log (`retrieval_log` in `/query` response)
  - Captured + rendered from the live response. Note: **not streamed** — `/query` is a
    single blocking POST, so the loading view shows static placeholders until it returns.
- [x] Slice 2 UI: sub-slice selector (shipped early in Phase 2; mock results don't vary by slice yet)

**Role 2 — Gary**
- [x] Seed corpus slice 2: 58 contemporary fashion images, hand-curated (PR #21, landed early)
- [x] Publication list for slice 2 (Dezeen, Frame, Wallpaper, Sight Unseen) — wired in `retrieval/tavily.py`

**Role 3 — Christian**
- [x] Seed corpus extraction: run extractor over slice 2 seed images (44/44, June 12)
- [x] Update synthesis prompt with slice/category-specific calibration references for both sub-slices (sneaker_streetwear + contemporary_fashion baselines added to `_SUB_SLICE_CONTEXT` in `src/synthesizer.py`, tested via synthesis-only re-runs on existing seed extractions — both slices show category-aware contrast framing)
- [x] End-to-end test query for slice 2 — seed-corpus synthesis verified, 6 patterns (June 12)

> Open work that used to live here has moved to its proper bucket:
> **#29** (polish) and the cross-browser check → [Essential for June 17](#essential-for-june-17-blackstone-rehearsal);
> **#40** (fashion schema) and cross-slice caching → [Slice 2 — stretch](#slice-2--stretch-deferred-past-june-17);
> **#22** (re-source seed images) → tracked as a GitHub issue.

---

## Phase 4 — Demo prep & buffer

All demo-prep work (deck, speech, pre-warmed query, demo hardening, cross-browser check)
is pulled forward into [Essential for June 17](#essential-for-june-17-blackstone-rehearsal)
above — the rehearsal is a full presentation dry-run, so it all has to hold this week.

After the rehearsal, **June 18–23 is buffer**: fix whatever the 17th surfaces, then final
polish before Demo Day (Wednesday, June 24).

> The **June 17 rehearsal** is the near-term forcing function — treat the 17th as the
> deadline that matters. Demo Day on the 24th is the final performance; the rehearsal is
> what we build toward this week.
