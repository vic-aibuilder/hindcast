# Hindcast — Builder Brief

**Project:** Hindcast
**Partner:** Snarkitecture — Alex Mustonen
**Status:** Draft v4 — post-meeting alignment (sub-slice + scope updates)
**Date:** May 30, 2026
**Companion docs:** Hindcast PRD (partner-facing); Hindcast Definition Layer — Schema v2.2

> **Naming note:** "Hindcast" stays as the working name. The "Anti-Trend Generator" subtitle is parked pending the naming workshop and is omitted here so it doesn't read as a locked name.

**Priority legend:** `[P0]` = MVP for prototype · `[P1]` = important for delightful experience · `[P2]` = nice-to-have

---

## Project overview

Hindcast is an internal Snarkitecture tool that takes a design brief and returns a structured reading of what's visually saturated in that context — the moves everyone is making, the defaults that read as overused, the open ground where contrast lives. The tool is the opposite of a trend forecast: instead of predicting what's coming, it maps what's already everywhere.

See the partner-facing PRD for full problem framing, value props, and tonal references.

---

## Scope

### In scope

- `[P0]` Interior design only — interiors, environments, installations, furniture.
- `[P0]` One vertical: **brand and retail** (treated as a single category, per Snarkitecture's own practice). Covers spatial brand/retail work — the built environments brands use to sell and to express identity.
- `[P0]` Two sub-slices within the vertical; user chooses sub-slice at query time. Confirmed:
  - **Sneaker/streetwear** (slice 1) — the sneaker and streetwear retail scene (Adidas, Nike, New Balance, On, plus multi-brand retailers like Kith and Flight Club).
  - **Contemporary fashion** (slice 2) — the **elevated/designer** apparel end (The Row, Toteme, Khaite, Acne; warm-minimal / quiet luxury). **Explicitly not** the streetwear-adjacent apparel end (Aimé Leon Dore, Kith apparel), which lives in slice 1.
- `[P0]` **No flagship qualifier** on either slice. Both slices cover retail in the category broadly — flagship *and* non-flagship. Flagship stores still appear in retrieval and output; removing the qualifier widens the corpus (a density decision), it does **not** exclude flagships.
- `[P0]` One city: **New York City — all five boroughs** (not Manhattan only).
- `[P0]` Time window: **2025–present** (settled).
- `[P0]` Single deep query path: brief in, saturation analysis out.
- `[P0]` Image-forward output. Project, designer, year visible under each image. URL display TBD — see Open questions; URL retained in underlying data regardless.

### Out of scope

- Image generation.
- Trend forecasting.
- Disciplines beyond interior design.
- Verticals beyond brand and retail.
- **Brand activations / pop-ups** — cut; partner confirmed this is not current studio work.
- Sub-slices beyond the two confirmed (no beauty retail, fashion showrooms, etc. in v1).
- Geography beyond NYC's five boroughs.
- Pre-2025 imagery or era exploration.
- Reverse image search.
- Instagram, TikTok, Facebook as sources.
- Are.na as a destination or integration. API used for retrieval only; aesthetic referenced for UI only.
- User accounts, saved searches, history.
- Client-facing deliverable.

> **Note on density:** with the time window fixed at 2025–present, corpus breadth is carried by (a) all five boroughs and (b) no flagship qualifier. These are the levers keeping the data set large enough to read saturation against — addressing the partner's concern that a too-narrow slice yields too few projects to detect oversaturation.

---

## Architecture

**Three-layer stack:**

1. **Retrieval** — Tavily (live search) + Are.na API + design-publication archives, augmenting a small pre-built seed corpus. A caching layer sits on top (see Retrieval architecture).
2. **Analysis & synthesis** — Claude. Handles both image understanding (per-image schema extraction) and editorial synthesis (saturation observations). No separate vision model required.
3. **Output** — image grid with editorial framing, rendered in a calm, Are.na-referenced UI.

**The pipeline:**

1. User submits brief (sub-slice; city locked to NYC / five boroughs; free-text brief; optional keywords).
2. Retrieval agent checks the cache and seed corpus, then constructs and runs live queries across sources to fill gaps. Loops to refine if needed (see Retrieval agent).
3. Each retrieved image is scored against the sub-slice's schema by Claude (single-shot per image). Seed-corpus images are pre-extracted at build time.
4. Aggregated schema data plus the original brief feeds the synthesis prompt; Claude returns 4–6 saturation observations.
5. Output rendered to the user. New extractions are written to the cache.

### Retrieval architecture (seed corpus + live + cache)

A deliberate hybrid — fits the timeline while giving saturation findings a stable population to measure against:

- `[P0]` **Seed corpus.** ~150 images (~75 per sub-slice), hand-curated and schema-extracted at build time. A baseline population so saturation reads against something stable from the first query, not just whatever a single live search returns. Built before Demo Day.
- `[P0]` **Live retrieval.** At query time, the agent retrieves additional contextually relevant images via Tavily to augment the seed, keeping findings current.
- `[P0]` **Caching layer.** Keyed by sub-slice + normalized brief. First run hits live sources, extracts schema, stores results; similar later queries serve partially or fully from cache. The cache accretes toward a larger corpus over time without an upfront ingestion pipeline. Engineering: ~1–2 days.

> **Note on saturation precision:** at ~75 images/slice, findings are directional, not statistically precise. Output language reflects this (see Voice — no exact-percentage claims). Precision improves as the cache grows — framed honestly to Alex as "the tool learns as it's used."

### Retrieval agent

- `[P0]` Runs as an agent loop, not a fixed query template. Pattern: observe → decide → act → repeat.

**Loop behavior**

1. Read the brief. Check seed corpus and cache. Propose initial search strategy across available sources.
2. Execute searches via tool calls (Tavily query, Are.na API, publication queries).
3. Self-assess the returned corpus: representative of the brief? Gaps (style, sub-context)? Off-context noise?
4. Refine queries and search again if needed.
5. Stop when corpus is judged sufficient or max iteration count reached.

**Constraints**

- `[P0]` Bounded by max iterations. Recommend **4 loops** as a hard ceiling.
- `[P0]` Tools exposed to the agent: Tavily search query, Are.na API query, per-publication search (where APIs exist).
- `[P0]` Agent reasoning is logged and surfaced in the UI during loading — visible but restrained (see Output presentation).

---

## The definition layer

- `[P0]` Two-layer system: a fixed schema underneath (data layer) and an adaptive editorial layer on top (synthesis).

> The full controlled vocabulary lives in the companion **Schema v2.2** doc; summarized here.

### Fixed schema (per sub-slice)

Every retrieved image is scored against a structured schema with controlled vocabulary — the data that makes saturation quantifiable and clusterable. A **shared seven-category base** applies across both slices; each slice adds slice-specific dimensions.

**Shared base (seven categories):** Material · Form/Geometry · Color · Lighting · Texture · Opacity · Atmosphere/Warmth.

**Sneaker/streetwear-specific dimensions** *(industrial register)* — working draft, to be revised against Alex's reference set when it arrives:

- Product display (single-pair plinth, sole-out wall, salon wall, vending grid, hero pedestal).
- Fixture system (modular grid, built-in millwork, freestanding plinth, wall-mounted).
- Floor strategy (polished concrete, raw concrete, painted court, sport flooring, wood, stone).
- Cultural reference (gallery, archive, locker room, court, skate, warehouse, stadium).
- Materiality register (industrial, technical, luxury-crossover).
- Statement object (none, sculpture, oversized graphic, installation, customization zone).

**Contemporary fashion-specific dimensions** *(elevated/designer — quiet-luxury register; **not** ALD/Kith)* — working draft, to be revised against Alex's reference set when it arrives:

- Merchandising (hero staging, edited wall, single-item plinth, hanging rail).
- Display density (very edited → moderate → full collection).
- Threshold / entry (open frontage, archway, vestibule, controlled funnel, door-only).
- Spatial generosity (gallery-sparse → moderate → dense retail).
- Furniture (none, minimal seating, residential moment, decorative objects).
- Softness index (none → minimal → moderate → dominant: upholstery, rugs, curtains).

> **Elevated-end pin (collision guard):** slice-2 materiality skews travertine / limestone / microcement, pale oak, fluted or raw plaster, warm neutrals, arches and niches, restrained-to-no branding. The raw-concrete / blackened-steel / vintage-sportif / archive-display moves belong to **slice 1**, not slice 2. Keeping this boundary is what stops the two schemas from converging.

### Adaptive editorial layer

- `[P0]` Claude reads the aggregated schema data plus the original brief and proposes 4–6 named saturation patterns. This is where the editorial voice lives. Patterns are named, described in 2–3 material sentences, and evidenced with an image set. The description's last sentence is a data observation about where the saturation *isn't* — what's rare or absent in the corpus. The tool maps; it does not prescribe.
- Synthesis prompts are primed with sub-slice-specific reference patterns so output reads as written by someone who knows the category.

---

## Output presentation

**Per-pattern structure**

- `[P0]` **Title** — Title Case, short, names the move.
- `[P0]` **Description** — 2–3 sentences, material and specific. Last sentence is a data observation about where the saturation isn't. No prescriptions.
- `[P0]` **Image grid** — 8–15 images supporting the pattern, with project + designer + year visible. (URL display: open question — retained in data either way.)

**Page-level structure**

- `[P0]` Brief summary at top (echoes the submitted brief).
- `[P0]` 4–6 pattern blocks stacked below.
- `[P0]` Total reading time under 2 minutes.

**Agent visibility during loading**

- `[P0]` Small log surfacing the retrieval agent's reasoning ("searching sneaker/streetwear… results skew Tokyo… refining toward NYC…"). Hidden once results render.
- `[P0]` Sells the AI-native frame without cluttering the final output.

**UI reference**

Are.na as the design reference: clean, minimal, image-forward, calm. Inspiration only. The interface should feel like a curated board, not a dashboard.

---

## Voice specification

- `[P0]` Output reads as written by a senior designer briefing a junior — not a critic performing for an audience.

**Partner direction (from the meeting):** dry, factual, measured, neutral. **Pushes back rather than flatters** — names the overused defaults plainly; no "this is brilliant," no cheerleading. Design-literate. Maps, doesn't prescribe.

**Training source (Alex's own suggestion):** prime the synthesis prompt on Snarkitecture's project descriptions (the Phaidon book). Their structure is **big-to-small** — start with the site (city, block, neighborhood, building), then move through the space sequentially. The output should carry that same structured logic.

**Voice rules**

- Title is a named move, not a category. Naming the move is the editorial work.
- Opening sentence is descriptive and material. Names things correctly (perforated steel, not "metal panel"; fluted plaster, not "textured wall"). No throat-clearing.
- Middle sentence (if used) lands the diagnostic — dry, slightly knowing, earned by the specificity above it.
- Last sentence is a data observation about where the saturation isn't. Frame absence in the corpus ("soft furnishings are rare in the set"), not as a recommendation. Favor qualitative framing (rare, uncommon, a small minority) over exact percentages at this corpus size.
- No design recommendations or prescriptions. "X reads as confident" and "the more radical move is Y" are out of bounds — designer's calls.
- No adjectives doing work the nouns aren't. "Oversized plinth," not "dramatic statement plinth."
- No exclamation points, no "fascinatingly," no "interestingly." Sounds like it's seen a lot and isn't easily impressed.

> **Pantone note:** Pantone Color of the Year is **not** a schema input and **not** a build feature. It came up only as a conceptual reference for how trends get generated and saturate — don't wire it in.

### Sample patterns (for calibration)

**Slice 1 — Sneaker/streetwear · The Raw Industrial Shell**
Exposed concrete floors and ceilings paired with blackened or perforated-steel fixtures, product displayed on freestanding plinths like gallery objects. The palette reads cold and utilitarian — a warehouse turned showroom. Warm or soft materials are rare across the set.
*[image grid — 8–15 images with attribution]*

**Slice 2 — Contemporary fashion · The Travertine-and-Oak Interior**
Travertine or limestone floors paired with white-oak millwork, often run as a continuous material across walls, fixtures, and built-in seating. The palette reads warm-minimal — somewhere between gallery and high-end residential. Painted or papered wall finishes are rare across the set.
*[image grid — 8–15 images with attribution]*

---

## Source list

**Vertical-agnostic (always available)**

- `[P0]` **Tavily — live search source (decided).** The primary retrieval workhorse. Scope it to a curated list of design publications — don't search the open web. (Resolves the prior open question; Google Custom Search JSON API was closed to new customers, so Tavily is the chosen replacement.)
- `[P0]` **Are.na API** — curated channels. Free, well-documented. Adds a human-taste signal the algorithmic sources lack.
- `[P0]` **Dezeen** — accessed via Tavily site-scoping rather than a custom scraper.
- `[P1]` **ArchDaily** — historically had an API; status worth a 30-min verify. Fall back to scoped search if not operational.

**Sneaker/streetwear publication list** *(firm up against Alex's reference set; narrow to 3–4 for NYC)*
Candidates: Hypebeast, Highsnobiety, Sneaker Freaker, Dezeen, Frame.

**Contemporary fashion publication list** *(firm up against Alex's reference set; narrow to 3–4 for NYC)*
Candidates: Dezeen, Frame, Wallpaper, Sight Unseen, ArchDaily — Wallpaper and Sight Unseen for the design-luxury / design-forward register where this work lives.

---

## Implementation notes

**Live search source — Tavily.** Scope to the curated publication list. One user query expands into multiple API calls (sub-slice + city + style descriptors), so plan for caching and query batching. Verify pricing and rate limits at build time.

**Known bias to acknowledge internally.** Any algorithmic search ranking is itself a form of homogenization — conceptually on-brand for what the tool detects, but a real bias in the data layer. The seed corpus partially mitigates this with a hand-curated baseline. Aware internally; not surfaced in user-facing output for the prototype.

**Latency expectations.** `[P0]` Agent loop + extraction + synthesis ≈ 30–60s/query. Acceptable for a prototype where quality outweighs speed. Cache hits and the seed corpus reduce this on repeats. The loading state with agent visibility makes the wait feel like part of the product.

---

## Claude usage

- `[P0]` Claude handles image understanding directly — no separate vision model.
- `[P0]` Claude is the retrieval agent (tool-use), the per-image schema extractor (vision + structured output), and the editorial synthesizer.
- `[P0]` One model end-to-end for the prototype: **Claude Sonnet 4.6** (current balanced tier — strong tool-use, capable vision, good editorial voice). Intent is "current Sonnet tier" if a newer version lands before build.

**Cost levers (documented, not built):** if usage grows post-demo — (1) model routing (run high-volume extraction on a cheaper tier, reserve a stronger model for synthesis); (2) prompt caching (the extraction prompt is identical across images in a query, ~90% off cached input); (3) batch API (extraction isn't latency-sensitive — 50% off, stacks with caching). Deferred at prototype scale.

### Cost estimate

Modest at prototype scale. Dominant cost is per-image extraction (~300 images/query). Rough per-query cost on Sonnet 4.6 ≈ $3–4 fully live (~600K input / 90K output). Seed corpus (extracted once) and cache cut this on repeats — a fully cached query approaches zero marginal cost. Tavily cost depends on plan/tier (verify at build); Are.na is free. **Prototype-phase total: negligible** — dozens of test queries, realistically well under $100.

---

## Build sequencing

Build the first sub-slice (**sneaker/streetwear**) end-to-end as a complete, demo-ready proof. Then adapt the same pipeline to the second sub-slice (**contemporary fashion**) by:

- Swapping the fixed schema (slice-specific dimensions).
- Swapping the source list (slice-specific publications).
- Updating the agent's search-strategy prompts (slice-specific reference patterns).
- Updating the synthesis prompts (slice-specific named patterns).

Architecture, retrieval-agent logic, extraction pipeline, output layout, and voice spec do **not** change between sub-slices — built once.

**Rough effort split:** if slice 1 is 100% of pipeline-building effort, slice 2 is ~25–40% — mostly schema work and source curation, not engineering.

**Risk framing:** if timeline pressure hits, **sneaker/streetwear is the committed deliverable**; contemporary fashion is stretch and can be shown as an extension of the same approach.

---

## Timeline (working backward from Demo Day)

- **Demo Day:** Wednesday, June 24, 6 PM @ Blackstone. Team: 3 builders (Christian, Gary, Victor).
- **Feature-freeze / build-complete target:** ~June 18–19 (the Thu/Fri before).
- **June 19–23:** build slide deck, write presentation speech, rehearse, harden the demo, pre-warm demo queries.

> Demo Day is the **performance** deadline, not the build deadline. The build must finish well before, to leave real time for deck + speech + rehearsal.

---

## Explicit do-not-build list

So nothing accidentally gets built:

- Reverse image search.
- Era / decade exploration.
- Brand activations / pop-ups.
- Are.na integration as a destination or plug-in.
- User accounts, saved searches, history.
- Image generation.
- Verticals beyond brand and retail.
- Sub-slices beyond the two confirmed.
- Multi-city support.
- Sources beyond the confirmed list.
- Filtering or refinement after the initial query (single deep query path).

---

## Open questions to resolve before kickoff

- **Sneaker/streetwear schema** — working draft above; revise against Alex's reference set when it arrives.
- **Contemporary fashion schema** — working draft above; revise against Alex's reference set, holding the elevated-end pin.
- **Publication lists (both slices)** — candidate lists drafted; firm up to 3–4 per slice against Alex's reference sets.
- **URL in visible output** — show source URL under each image, or attribution-only (project/designer/year) with URL retained in data? Affects output layout. Team + Alex input wanted.
- **ArchDaily API status** — 30-minute verification; fallback (scoped Tavily search) already identified.

> Resolved since v3: live search source (**Tavily**), city scope (**all five boroughs**), sub-slices (**sneaker/streetwear + contemporary fashion**), brand activations (**cut**), time window (**2025–present, settled**).
