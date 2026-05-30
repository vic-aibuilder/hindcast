# Roadmap

> Feature-freeze / build-complete target: **June 18–19**
> Demo Day: **Wednesday, June 24, 6 PM @ Blackstone**

The build is sequenced slice-first: sneaker/streetwear end-to-end, then contemporary
fashion adapted from the same pipeline.

## Slice 1 — Sneaker/streetwear (committed deliverable)

Build the full pipeline end-to-end:

- Seed corpus (~75 images, hand-curated and schema-extracted at build time)
- Retrieval agent (Tavily + Are.na + publication search, max 4 iterations)
- Per-image schema extractor (sneaker/streetwear dimensions)
- Editorial synthesizer (sneaker/streetwear reference patterns)
- Caching layer
- React UI (Are.na-referenced, image-forward)

## Slice 2 — Contemporary fashion (stretch goal)

Adapt the slice-1 pipeline with:

- Swapped fixed schema (contemporary fashion dimensions)
- Swapped source list (contemporary fashion publications)
- Updated agent search-strategy prompts
- Updated synthesis prompts and reference patterns
- Seed corpus (~75 images)

Architecture, retrieval logic, extraction pipeline, output layout, and voice spec do not
change between slices — built once. Estimated effort: ~25–40% of slice 1.

**Risk framing:** if timeline pressure hits, sneaker/streetwear is the committed
deliverable. Contemporary fashion can be shown as an extension of the same approach.

## June 19–24 — Demo prep

- Build slide deck
- Write presentation speech
- Rehearse
- Harden demo path
- Pre-warm demo queries

> Demo Day is the performance deadline. The build must finish well before June 19 to
> leave real time for deck, speech, and rehearsal.
