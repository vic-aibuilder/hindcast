# Hindcast — Definition Layer · Schema v2.2

**Partner:** Snarkitecture — Alex Mustonen
**Built from:** full meeting transcript (May 28, 2026)
**Reconciled:** May 30, 2026 — updated to locked sub-slice + scope decisions
**v2.3 update:** Jun 1, 2026 — vocabulary additions from Alex Mustonen calibration document: `blonde wood`, `chrome rail`, `matte black rail` (Material/metal), `bleached white / bright white` (Material/wall_finish), `architectural plant` (Form/statement_form), `sparse product display` (Contemporary Fashion/display density)
**Companion doc:** Hindcast Builder Brief v4

> **What changed from v2.1 → v2.2.** Sub-slice 1 relabeled from "footwear flagship" to **sneaker/streetwear** (flagship qualifier dropped). Second sub-slice locked as **contemporary fashion** (elevated/designer end), replacing the deferred "apparel/womenswear" placeholder. Scope-decision section resolved: time window stays **2025–present**; density carried by all five boroughs + no flagship qualifier rather than by widening the window. Seven-category base unchanged.

---

## How to Read This Document

This schema is built directly from what Alex said in the meeting. Where a dimension came from his own words, his quote is in the notes. The schema is the lens Claude uses to score every retrieved image; consistent vocabulary is what makes saturation countable.

Alex's framing of the three primary categories, in his words:

> *"Material is one category. Form — the shape or geometry of something — is another. Color could be another one. Even if you just thought about these initial three, those are huge categories, and how you change them dramatically alters the character of the space."*

Lighting he flagged as slightly more subjective but worth including. Texture, opacity, and atmosphere came up later as he talked through the space.

---

## Locked Scope (resolved)

The scope questions Alex raised in the meeting have been decided by the team:

- **Time window: 2025–present.** Settled — not widened. (Alex floated going back 5 years to fight data thinness; the team is instead carrying breadth through the levers below.)
- **Geography: all five boroughs.** "Maybe we need to make sure Brooklyn's included." — confirmed.
- **No flagship qualifier.** Both slices cover their category broadly; flagship stores still appear, but the corpus isn't restricted to them. This widens the data set — the primary density lever now that the window is fixed.

> Alex's underlying instinct, kept in view: *"The more information you have, the better — you can't identify oversaturation on 10 projects."* Five boroughs + no flagship qualifier is how the build honors that without moving the window.

---

## Sub-Slice Status (locked)

- **Sneaker/streetwear** (slice 1) — confirmed. Alex: *"Footwear is a good place to start — you've got the Adidas, Nikes of the world, New Balance and Ons, Kith and Flight Clubs."* The category is the sneaker/streetwear scene, flagship and non-flagship.
- **Contemporary fashion** (slice 2) — confirmed, defined as the **elevated/designer** apparel end (The Row, Toteme, Khaite, Acne — warm-minimal / quiet luxury). **Not** the streetwear-adjacent apparel end (Aimé Leon Dore, Kith apparel), which is slice 1. *(Decision note: this is a demo-contrast call. The transcript-literal reading leaned toward broadening the corpus over adding a parallel category; the team chose two contrasting slices to prove the tool generalizes.)*
- **Brand activations / pop-ups** — OUT. Alex: *"Pop-up brand activation is not really — I'm not doing that anymore. It doesn't feel as relevant for Snarkitecture."*

> **Framing note:** Alex thinks of the work as "brand spaces" — places where a brand builds connection and recognition, not just transaction. Examples he named: New Era, Adidas, Starbucks Roastery, Louis Vuitton, Uniqlo.

---

## Primary Category 1 — Material

> Alex: *"Material is a little more straightforward — basic categories: wood, metal, stone, glass, tile."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Wood** | white oak, walnut, dark oak, light wood, **blonde wood**, reclaimed, plywood | *"Dark rich wood paneling… walnut"* · blonde wood = DTC/lifestyle light oak default |
| **Metal** | blackened steel, brushed aluminum, stainless steel, brass, copper, perforated metal, **chrome rail**, **matte black rail** | *"Stainless steel feels like machinery, like the future"* · chrome rail + matte black rail = stock DTC fixture system |
| **Stone** | travertine, limestone, marble, terrazzo, concrete, slate | *Note if cold-to-touch / hard — Alex used this as a warmth cue* |
| **Glass** | clear, frosted, translucent, mirror | *See Opacity below* |
| **Tile** | round tile, square tile, linear tile | *"Round tiles, square tiles, linear tiles"* |
| **Soft / fabric** | upholstery, soft furnishing, carpet, felt, foam, leather | *"Upholstery… soft furniture" flagged as a saturation signal* |
| **Wall finish** | raw plaster, painted plaster, fluted plaster, exposed brick, **bleached white / bright white**, drywall | *Exposed brick = Alex's example of an oversaturated default* · bleached white = DTC "clean" default |

Material also carries pattern and color sub-attributes — Alex noted these "play into material."

---

## Primary Category 2 — Form / Geometry

> Alex's framework: *"Rectilinear, grid logic — straight lines, sharp corners. Then rounded — circular, half-circle. And irregular — a natural shape, illogical, that works against the logic of a grid."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Primary geometry** | rectilinear / grid, rounded / circular, irregular / organic, mixed | *"Is it square, is it round? Rational or irrational?"* |
| **Basic shape** | circle, square, triangle, rectangle, irregular, cloud / landscape form | *"The triangle is really popular at certain moments… landscape-like, cloud-like forms"* |
| **Arch presence** | none, built-in niche, arched opening, dominant arch | *"You'll see a lot of arched openings… built-in niches. I noticed it a lot." Flagged as saturated.* |
| **Grid presence** | none, subtle, strong grid | *"A very strong grid look — universal design; tile, floor, ceiling structure"* |
| **Mass / weight** | solid mass / heavy, light / thin, mixed | *"A giant block of concrete vs a curtain — solid vs light"* |
| **Statement form** | none, plinth, sculptural object, oversized graphic, architectural void, installation, **architectural plant** | *The one anchor form that defines the space* · architectural plant = DTC finishing-touch default |

---

## Primary Category 3 — Color

> Alex: *"Color — warm tones, cool tones, black, white, and all the other colors. That's more analytical."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Temperature** | warm, cool, neutral | *Alex's primary color lens. "Color temperature is the basic version."* |
| **Dominant hue** | off-white, white, black, grey, brown, green, pink, earth tones, other | *"Off-whites and walnut tea brown" — his coffee-shop read* |
| **Palette type** | monochromatic, tonal, high contrast, material-driven, neutral / clean-slate | *"The absence of color — a clean slate" noted as its own move* |
| **Accent** | none, subtle, strong | *Note deliberate accents (e.g. "dark green banquettes" — a trend Alex flagged)* |

> **Pantone note:** Pantone Color of the Year is **not** a schema input. *"I don't think it needs to be incorporated."* It was a conceptual reference to how trends get generated and saturate — not a feature.

---

## Secondary Category 4 — Lighting

> Flagged as "a little subjective" but worth tracking.

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Source type** | overhead track spot, lightbox, diffuse cove, pendant, linear LED, daylight, mixed | *"Overhead light fixture — a lightbox element"* |
| **Temperature** | warm, neutral, cool, mixed | *Ties to color temperature / warmth* |
| **Visibility** | concealed, partially exposed, fully exposed | *"You see the ductwork, the wiring — they did it on purpose"* |
| **Drama** | flat / even, directional, theatrical, high contrast | |

---

## Secondary Category 5 — Texture

> Alex: *"A lot is material-based or textural — smooth vs rough, linear textures, irregular rough textures, shiny vs matte."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Surface** | smooth, rough, mixed | *Alex's primary texture axis* |
| **Finish** | matte, satin, shiny / gloss, mixed | *"Things that are shiny vs matte"* |
| **Texture type** | linear, irregular, geometric, organic | |
| **Pattern** | none, subtle, strong | *Repeating pattern — tile grid, wood grain, textile* |

---

## Secondary Category 6 — Opacity

> Alex defined the three terms himself: *"Materials that are opaque — you can't see through them — versus clear, versus translucent, where you can see shadow through it but can't look through it. And there are degrees of that too."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Dominant opacity** | opaque, translucent, clear / transparent, mixed | *Alex's three terms, verbatim* |
| **Transparency use** | none, functional, decorative, structural | |

---

## Secondary Category 7 — Atmosphere / Warmth

> Warmth is Alex's key atmospheric quality — material, color, and light together. *"Warmth is an inviting feature — comfortable, cozy. Warm tones, off-white light, upholstery, a reddish concrete floor. Versus a brighter white with black slanted stone that's literally cold to the touch — that reads cooler."*

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Warmth** | warm / inviting / cozy, neutral, cool / austere / clinical | *Alex's central atmospheric read* |
| **Formality** | raw, casual, semi-formal, formal | |
| **Reference** | gallery, museum, laboratory, residential, industrial, hospitality, archive, stadium, nature | *"It feels like a museum"; Adidas "like walking into a stadium"* |
| **Abstract qualities** | inviting, accessible, engaging, memorable, compelling | *Alex's words for the spaces Snarkitecture wants to make* |

---

## Sneaker/Streetwear — Sub-Slice Dimensions

> Industrial register. Brands Alex named: Adidas, Nike, New Balance, On, Kith, Flight Club. Working draft — revise against Alex's reference set.

| Dimension | Controlled vocabulary | Notes / Alex's words |
|---|---|---|
| **Product display** | single-pair plinth, sole-out wall, salon wall, vending grid, hero pedestal | *"Show me all the projects with stainless steel displays" — Alex's filter idea* |
| **Fixture system** | modular grid, built-in millwork, freestanding plinth, wall-mounted | *"Millwork is built-in cabinets — not loose furniture"* |
| **Floor strategy** | polished concrete, raw concrete, painted court, sport flooring, wood, stone | *Note court / sport references* |
| **Cultural reference** | gallery, archive, locker room, court, skate, warehouse, stadium | *Adidas "puts you in the mindset of sport"* |
| **Materiality register** | industrial, technical, luxury-crossover | |
| **Statement object** | none, sculpture, oversized graphic, installation, customization zone | *New Era's in-store customization / sewing area = brand-storytelling moment* |

---

## Contemporary Fashion — Sub-Slice Dimensions

> Elevated/designer register (The Row, Toteme, Khaite, Acne). Working draft — revise against Alex's reference set, holding the elevated-end pin below.

| Dimension | Controlled vocabulary | Notes |
|---|---|---|
| **Merchandising** | hero staging, edited wall, single-item plinth, hanging rail | *How garments are displayed* |
| **Display density** | very edited, **sparse product display**, moderate, full collection | *How much product is visible at once* · sparse product display = luxury signal borrowed without luxury |
| **Entry / threshold** | open frontage, archway, vestibule, controlled funnel, door-only | |
| **Spatial generosity** | gallery-sparse, moderate, dense retail | *Negative space vs product density* |
| **Furniture** | none, minimal seating, residential moment, decorative objects | *"Soft furniture" / residential cues* |
| **Softness index** | none, minimal, moderate, dominant | *Upholstery, rugs, curtains — Alex flagged soft surfaces as a saturation signal* |

> **Elevated-end pin (collision guard).** Slice-2 materiality skews **travertine / limestone / microcement, pale oak, fluted or raw plaster, warm neutrals, arches and niches, restrained-to-no branding** — the quiet-luxury cluster. The **raw-concrete / blackened-steel / vintage-sportif / archive-display** register belongs to **slice 1 (sneaker/streetwear)**, not here. Retrieval should reach broad (the best-documented examples skew mixed-gender luxury fashion that carries womenswear), but the schema should read the elevated patterns where they cluster. This boundary is what keeps the two slices' schemas from converging.

---

## How Saturation Is Detected

Alex described the logic himself — frequency across a large set, plus the recognition that a move has stopped reading as a choice:

> *"It relies on having seen it before. If you've only ever been in one space, you think it's unique. But if you've been in others that look like that — that's probably not even the second one, it's the third, the fourth. The more people do it, the more normal it becomes, to the point that the thing that was once unique is no longer special."*

His calibration example of an oversaturated default:

> *"Exposed brick walls. In the early 2000s a broker would say 'it's got exposed brick, it's really fancy.' It got so overdone that now anytime I see a new space with a big brick wall, I immediately go — it's so obvious."*

The algorithm connection — the Filterworld thesis (he called the author "Kyle Jacob"; he means **Kyle Chayka**):

> *"How does the algorithm — Instagram, TikTok, Pinterest — push design toward similarity? Blue Bottle was so influential. They're not all identical inside, but they're all light-colored, light woods, same palettes, same geometry. The Japanese and Scandinavian aesthetic caught momentum and became what a coffee shop 'should' feel like."*

---

## Output Voice

> *"I like something pretty dry and pretty factual. I didn't like the early GPT versions trying to make you feel good — 'this is brilliant.' I don't need that. I want someone to push back. Measured and neutral would be my instinct — but it would help to have some design reference in there, design terminology."*

**Voice rules**

- **Dry, factual, measured, neutral** — no performative praise, no "fascinatingly," no exclamation points.
- **Pushes back** — names the overused defaults plainly; challenges rather than flatters.
- **Materially specific** — walnut paneling, perforated steel, fluted plaster.
- **Design-literate** — real design terminology.
- **Maps, doesn't prescribe** — reports what's saturated and what's rare; the designer decides.

**Voice training source (Alex's suggestion):** train the synthesis prompt on Snarkitecture's project descriptions (the Phaidon book). Structure follows their logic — **big to small**: site, city, block, building, then a sequential walk-through.

> Writers Alex named, all unresolved (revisit later): John McPhee (specificity, storytelling through detail — unsure it translates); Blackbird Spyplane (distinctive, but "too much its own voice to copy"); Jasper Morrison (theory of "undesigned design," the unnoticed — admits he hasn't read much of it). The register is confirmed; no single writer is locked.

**Calibration target — Alex's own description of ideal output:**

> *"I looked at all the [sneaker/streetwear] projects, and here are the top three elements being overused. I'm seeing a lot of full-height dark wood paneling. I'm seeing a lot of lightbox overhead. I'm seeing a lot of stainless steel retail fixtures."*

---

*Hindcast Definition Layer — Schema v2.2 · internal build doc · reconciled May 30, 2026*
