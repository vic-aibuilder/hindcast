# Hindcast — Contributor Steering Doc

## Project context

Hindcast is an internal Snarkitecture tool that takes a design brief and returns a
structured reading of what's visually saturated in a given context — the moves everyone
is making, the overused defaults, the open ground where contrast lives. It is the
opposite of a trend forecast: instead of predicting what's coming, it maps what's already
everywhere. The vertical is brand and retail; two confirmed sub-slices are
sneaker/streetwear and contemporary fashion (elevated/designer end). The city is New York
City, all five boroughs. The time window is 2025–present.

## Locked decisions

Do not reopen these without a team decision:

- **Sub-slices:** sneaker/streetwear (slice 1) + contemporary fashion — elevated/designer
  end (slice 2). Slice 2 is explicitly **not** the streetwear-adjacent apparel end (Aimé
  Leon Dore, Kith apparel); that belongs in slice 1.
- **No flagship qualifier.** Both slices cover their category broadly; flagships appear
  but the corpus is not restricted to them.
- **Geography:** NYC, all five boroughs (not Manhattan only).
- **Time window:** 2025–present. Settled.
- **Live search source:** Tavily. Scoped to a curated publication list, not the open web.
- **Model:** Claude Sonnet 4.6 (current Sonnet tier — update if a newer Sonnet ships
  before build).

## Source of truth

- **PRD.md** — product and engineering spec (Builder Brief v4). Read this first.
- **docs/schema.md** — definition layer (Schema v2.2). This is the extractor's input;
  do not alter the controlled vocabulary without a schema revision.

## Do-not-build list

If a PR touches any of the following, stop and raise with the team:

- Reverse image search
- Era / decade exploration
- Brand activations / pop-ups
- Are.na as a destination or integration (API for retrieval only; UI aesthetic reference only)
- User accounts, saved searches, or history
- Image generation
- Verticals beyond brand and retail
- Sub-slices beyond sneaker/streetwear + contemporary fashion
- Multi-city support
- Sources beyond the confirmed list
- Filtering or refinement after the initial query

## Conventions

- **Python 3.12** (backend) · **React** (frontend)
- **Lint / format:** ruff
- **Tests:** pytest
- **Dependencies:** pip + requirements.txt
- **Secrets:** never commit. Use `.env` (gitignored); see `.env.example` for required keys.

## Branch and PR naming

**Branches:** `type/brief-description` — all lowercase, hyphens, no spaces.
- `feat/` — new functionality
- `fix/` — bug fix
- `chore/` — config, docs, tooling

Examples: `feat/tavily-retrieval`, `fix/schema-extractor-keys`, `chore/update-roadmap`

**PR titles:** start with a capital letter, short, describes what changed.
Examples: `Add Tavily retrieval function`, `Fix schema extractor returning wrong keys`

**Never commit directly to `main`.** Always branch, open a PR, get at least one review.
