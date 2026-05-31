# Roadmap

> Feature-freeze / build-complete target: **June 18–19**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**
> Team: Victor (Role 1) · Gary (Role 2) · Christian (Role 3)

The build is sequenced slice-first: sneaker/streetwear end-to-end as a complete
demo-ready proof, then contemporary fashion adapted from the same pipeline.

---

## Role split

| Role | Owner | Scope |
|---|---|---|
| **Role 1 — Victor** | Victor | Frontend (React UI) + repo oversight |
| **Role 2 — Gary** | Gary | Retrieval pipeline (agent loop, Tavily, Are.na, caching, seed corpus) |
| **Role 3 — Christian** | Christian | Claude integration (schema extractor, editorial synthesizer, prompt engineering) |

---

## Phase 1 — Foundation (now → June 9)

**Role 1 — Victor**
- [ ] Set up React project (Vite + TypeScript)
- [ ] Wire `.env` and confirm API keys load
- [ ] Branch protection + collaborator access on GitHub
- [ ] Establish PR workflow for the team
- [ ] Write tests for frontend components (React Testing Library)

**Role 2 — Gary**
- [ ] Tavily integration: scoped queries against publication list
- [ ] Are.na API integration: channel queries
- [ ] Basic retrieval function: query in, image URLs + metadata out
- [ ] Verify ArchDaily API status; fall back to scoped Tavily if dead
- [ ] Write tests for retrieval functions

**Role 3 — Christian**
- [ ] Claude client setup (Anthropic SDK, Sonnet 4.6)
- [ ] Per-image schema extractor: image in, structured schema attributes out (sneaker/streetwear dimensions)
- [ ] Schema output validated against `docs/schema.md` controlled vocabulary
- [ ] Write tests for schema extractor

---

## Phase 2 — Slice 1 end-to-end (June 9–15)

**Role 1 — Victor**
- [ ] Brief submission UI (sub-slice selector + free-text input)
- [ ] Agent visibility log component (streaming reasoning during load)
- [ ] Output layout: brief summary + pattern blocks stacked
- [ ] Per-pattern component: title, description, image grid (project + designer + year)
- [ ] Are.na-referenced visual style: clean, minimal, image-forward

**Role 2 — Gary**
- [ ] Retrieval agent loop (max 4 iterations): observe → decide → act → repeat
- [ ] Self-assessment logic: corpus representative? gaps? off-context noise?
- [ ] Caching layer: keyed by sub-slice + normalized brief
- [ ] Seed corpus slice 1: ~75 sneaker/streetwear images, hand-curated
- [ ] Write tests for agent loop and caching layer

**Role 3 — Christian**
- [ ] Seed corpus extraction: run extractor over all ~75 seed images, store results
- [ ] Editorial synthesizer: aggregated schema + brief → 4–6 named saturation patterns
- [ ] Synthesis prompt primed on Snarkitecture voice (dry, factual, material-specific)
- [ ] Sneaker/streetwear reference patterns wired in
- [ ] Manual end-to-end run: verify full pipeline produces valid output
- [ ] Write tests for synthesizer output structure

---

## Phase 3 — Integration + slice 2 (June 15–18)

**Role 1 — Victor**
- [ ] Connect frontend to live pipeline (brief → results)
- [ ] Loading state with agent log visible
- [ ] Polish: typography, spacing, image attribution display
- [ ] Cross-browser / responsive check
- [ ] Slice 2 UI: swap sub-slice selector label only (no layout changes)

**Role 2 — Gary**
- [ ] Seed corpus slice 2: ~75 contemporary fashion images, hand-curated
- [ ] Swap publication list for slice 2 (Dezeen, Frame, Wallpaper, Sight Unseen)
- [ ] Verify caching works across both slices

**Role 3 — Christian**
- [ ] Seed corpus extraction: run extractor over slice 2 seed images
- [ ] Swap schema to contemporary fashion dimensions
- [ ] Update synthesis prompt with slice 2 reference patterns
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
