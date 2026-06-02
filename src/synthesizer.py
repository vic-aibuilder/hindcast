"""
Editorial synthesizer for Hindcast.

Aggregates per-image schema extractions, identifies saturation patterns
via Claude Sonnet 4.6, and returns 4–6 named patterns in the Hindcast voice.

Public API
----------
    synthesize(extractions, brief, sub_slice, *, client=None) -> list[dict]
    SaturationPattern (TypedDict)
"""

from __future__ import annotations

import os
from typing import Any, TypedDict

import anthropic
from dotenv import load_dotenv

from src.schema import VOCABULARY, _LIST_DIMS

load_dotenv()

MODEL = "claude-sonnet-4-6"

# ---------------------------------------------------------------------------
# Return type
# ---------------------------------------------------------------------------


class SaturationPattern(TypedDict):
    title: str
    description: str
    dominant_terms: list[str]
    image_count: int


# ---------------------------------------------------------------------------
# Sub-slice context — primes the synthesis prompt per vertical
# ---------------------------------------------------------------------------

_SUB_SLICE_CONTEXT: dict[str, str] = {
    "sneaker_streetwear": (
        "Sneaker and streetwear retail interiors — industrial register. "
        "Reference brands: Adidas, Nike, New Balance, On, Kith, Flight Club. "
        "Dominant material language: concrete, blackened steel, stainless steel, raw plaster. "
        "Cultural references: court, archive, warehouse, locker room, stadium. "
        "Watch for: sole-out wall displays, hero pedestals, court-painted floors, "
        "oversized brand graphics, lightbox ceilings, modular grid fixture systems."
    ),
    "contemporary_fashion": (
        "Contemporary fashion retail, elevated/designer end — warm-minimal, quiet luxury register. "
        "Reference brands: The Row, Toteme, Khaite, Acne Studios. "
        "Dominant material language: travertine, limestone, pale oak, fluted plaster, microcement. "
        "Watch for: arched openings, built-in niches, gallery-sparse merchandising, "
        "residential furniture moments, very edited product display, restrained or no branding. "
        "Not streetwear-adjacent (Aimé Leon Dore, Kith apparel) — that is slice 1."
    ),
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are the editorial synthesizer for Hindcast, an internal Snarkitecture tool that maps \
visual saturation in NYC brand and retail spaces. Your job: read aggregated schema frequency \
data from a corpus of interior images and identify the design moves that have become defaults — \
the things everyone is doing, the choices that have stopped reading as choices.

REASONING FRAMEWORK — FILTERWORLD
Apply this lens without naming it explicitly in output. Saturation happens through \
repetition and algorithmic spread. A spatial move starts as a distinction — gets photographed, \
circulated, copied, copied again — until the third or fourth iteration stops reading as a \
decision and starts reading as what this category of space "should" look like. Your question \
for each dimension: has this term crossed the line from choice to convention? Frequency in \
the corpus is the evidence. The pattern name is your verdict.

Alex Mustonen's framing: "It relies on having seen it before. If you've only ever been in \
one space, you think it's unique. But if you've been in others that look like that — that's \
probably not even the second one, it's the third, the fourth. The more people do it, the \
more normal it becomes, to the point that the thing that was once unique is no longer special."

CALIBRATION TARGET — HINDCAST VOICE
Your output must read like this register exactly:

"I looked at all the sneaker/streetwear projects, and here are the top three elements being \
overused. I'm seeing a lot of full-height dark wood paneling. I'm seeing a lot of lightbox \
overhead. I'm seeing a lot of stainless steel retail fixtures."

That is the target register. Dry. Factual. Names the specific material or fixture, not the \
category. No commentary on quality or intent. No recommendations. Reports what is; the \
designer decides what to do with it.

CALIBRATION REFERENCE — DTC LIFESTYLE RETAIL CONVERGENCE (Alex Mustonen, Snarkitecture)
The following is a saturation read prepared directly by the client. Use it as a naming convention \
and voice reference — this is what Hindcast output should sound like at its best.

Context: walk through SoHo and you see it — a cluster of lifestyle brands, all ostensibly distinct, \
all sharing the same spatial language. Bleached white walls, blonde wood fixtures, terrazzo or \
concrete floors, minimal product display, maybe a plant. This is what happens when brands \
default to "aesthetic" without making an actual spatial decision.

The client identified these six saturated moves in the DTC/athletic lifestyle retail cluster. \
Note the naming convention — a specific material or spatial element, stated plainly:

  THE BRIGHT WHITE WALL — "The default 'clean' that reads as no decision."
  THE BLONDE WOOD FIXTURE — "Natural material signaling without specificity."
  THE STOCK FIXTURE RAIL — "Chrome or matte black rails. Stock fixtures, no custom thought."
  THE TERRAZZO FLOOR — "Durable 'premium' surface, now ubiquitous."
  THE SPARSE PRODUCT DISPLAY — "Luxury signaling borrowed without the luxury."
  THE ARCHITECTURAL PLANT — "The finishing touch that signals nothing."

Brand readings in this register — note the precision and the absence of editorializing:
  Alo Yoga, Prince St: "Glossy white box, polished generic athletic-retail fixtures, \
aspirational lighting. Looks expensive but spatially unmemorable."
  Everlane, Prince St: "The interior is essentially the visual identity of the brand: \
beige, minimal, inoffensive, forgettable. Transparency as an ethos, invisibility as a space."
  Allbirds: "Natural materials, warm whites, sustainability messaging on the walls. \
Every location looks like every other location."

The underlying principle — the Seagram Building logic: contrast with context isn't \
contrarianism, it's how you make something worth remembering. When every brand in a \
category shares the same spatial language, the result is visual white noise. Hindcast \
surfaces this before the designer starts work.

VOICE RULES — NON-NEGOTIABLE
- Dry, factual, measured. Not warm, not promotional.
- Materially specific. Not "metal fixtures" — "stainless steel retail fixtures." \
Not "warm tones" — "off-white plaster and pale oak."
- Design-literate. Use real terminology: millwork, plinth, cove lighting, fluted plaster, \
travertine, terrazzo, perforated steel.
- Maps, does not prescribe. Never say "would benefit from," "consider," \
"designers should," or any equivalent.
- No performative language. No "fascinatingly," "strikingly," "notably," \
"it's worth pointing out," "interestingly."
- No exclamation points.
- No hedging. Not "appears to" or "seems to." State what the data shows.
- No padding. If a sentence does not add information, cut it.

PATTERN FORMAT — EXACT
Each pattern must follow this structure:
  title         ALL CAPS. Names the move directly and specifically. \
Examples: THE LIGHTBOX CEILING, THE STAINLESS STEEL FIXTURE DEFAULT, \
THE EXPOSED BRICK CARRY-OVER, THE ARCHED NICHE, THE SOLE-OUT WALL.
  description   Exactly 3 sentences. First: name the spatial or material move and \
where it clusters. Second: name the specific vocabulary terms driving it and how they \
co-occur. Third (ALWAYS a data observation): state precisely what is rare, absent, or \
structurally underused in this corpus — the open ground.
  dominant_terms  Controlled-vocabulary terms from the frequency data that define this pattern.
  image_count   How many images in the corpus exhibit this pattern.

Return 4–6 patterns. Most saturated first. Do not repeat the same material or move \
across multiple patterns — each pattern must name a distinct default.\
"""

# Saturation / rarity thresholds used in the frequency report
_SATURATED_PCT = 0.40
_RARE_PCT = 0.10

# Minimum fraction of dominant_terms an image must match to count for a pattern
_PATTERN_MATCH_THRESHOLD = 0.5

# ---------------------------------------------------------------------------
# Tool definition
# ---------------------------------------------------------------------------

_SYNTHESIS_TOOL: dict[str, Any] = {
    "name": "return_saturation_patterns",
    "description": (
        "Return 4–6 named saturation patterns from the corpus. "
        "Each pattern identifies a design move that has become a default in this sub-slice."
    ),
    "input_schema": {
        "type": "object",
        "required": ["patterns"],
        "additionalProperties": False,
        "properties": {
            "patterns": {
                "type": "array",
                "minItems": 4,
                "maxItems": 6,
                "description": "Saturation patterns ranked most-to-least saturated.",
                "items": {
                    "type": "object",
                    "required": [
                        "title",
                        "description",
                        "dominant_terms",
                        "image_count",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "title": {
                            "type": "string",
                            "description": (
                                "Pattern name in ALL CAPS — names the move directly. "
                                "Example: THE LIGHTBOX CEILING"
                            ),
                        },
                        "description": {
                            "type": "string",
                            "description": (
                                "Exactly 3 sentences. Dry and factual. Materially specific. "
                                "Last sentence is always a data observation about what is "
                                "rare, absent, or structurally underused in the corpus."
                            ),
                        },
                        "dominant_terms": {
                            "type": "array",
                            "items": {"type": "string"},
                            "description": (
                                "Controlled-vocabulary terms from the frequency data "
                                "that define this pattern."
                            ),
                        },
                        "image_count": {
                            "type": "integer",
                            "minimum": 1,
                            "description": "Number of corpus images exhibiting this pattern.",
                        },
                    },
                },
            }
        },
    },
}

# ---------------------------------------------------------------------------
# Aggregation
# ---------------------------------------------------------------------------


def _aggregate(extractions: list[dict]) -> dict[str, Any]:
    """
    Count term frequencies across all extractions.

    Returns::

        {
          "total": int,
          "categories": {
            "material": {"wood": {"white oak": 3, ...}, ...},
            ...
          }
        }
    """
    total = len(extractions)
    counts: dict[str, dict[str, dict[str, int]]] = {
        cat: {dim: {} for dim in dims} for cat, dims in VOCABULARY.items()
    }

    for extraction in extractions:
        for cat, dims in VOCABULARY.items():
            cat_data = extraction.get(cat)
            if not isinstance(cat_data, dict):
                continue
            for dim in dims:
                value = cat_data.get(dim)
                if (cat, dim) in _LIST_DIMS:
                    if isinstance(value, list):
                        for term in value:
                            counts[cat][dim][term] = counts[cat][dim].get(term, 0) + 1
                else:
                    if isinstance(value, str) and value:
                        counts[cat][dim][value] = counts[cat][dim].get(value, 0) + 1

    return {"total": total, "categories": counts}


def _format_aggregation(agg: dict[str, Any]) -> str:
    """
    Render aggregated counts as a human-readable frequency report for the synthesis prompt.

    Each term is annotated with count/total, percentage, and a SATURATED / RARE flag.
    Zero-occurrence terms are listed at the bottom as absence signals.
    """
    total: int = agg["total"]
    lines: list[str] = []
    absence_signals: list[str] = []

    _cat_labels = {
        "material": "MATERIAL",
        "form_geometry": "FORM / GEOMETRY",
        "color": "COLOR",
        "lighting": "LIGHTING",
        "texture": "TEXTURE",
        "opacity": "OPACITY",
        "atmosphere_warmth": "ATMOSPHERE / WARMTH",
    }

    lines.append(f"CORPUS: {total} image{'s' if total != 1 else ''} analyzed")
    lines.append("")
    lines.append("FREQUENCY REPORT  (sorted by frequency, highest first)")
    lines.append("─" * 60)

    for cat, dims in agg["categories"].items():
        lines.append(f"\n{_cat_labels.get(cat, cat.upper())}")
        for dim, term_counts in dims.items():
            if not term_counts:
                # track all terms as absent
                for term in VOCABULARY[cat][dim]:
                    absence_signals.append(f"{cat}.{dim}: '{term}'")
                continue

            dim_label = dim.replace("_", " ")
            lines.append(f"  {dim_label}")

            sorted_terms = sorted(term_counts.items(), key=lambda x: x[1], reverse=True)
            for term, count in sorted_terms:
                pct = count / total if total > 0 else 0.0
                if pct >= _SATURATED_PCT:
                    flag = "  ← SATURATED"
                elif pct <= _RARE_PCT:
                    flag = "  ← RARE"
                else:
                    flag = ""
                lines.append(f"    {term:<34} {count:>3}/{total}  ({pct:>4.0%}){flag}")

            # collect zero-occurrence terms for absence block
            for term in VOCABULARY[cat][dim]:
                if term not in term_counts:
                    absence_signals.append(f"{cat}.{dim}: '{term}'")

    lines.append("\n" + "─" * 60)

    if absence_signals:
        lines.append("\nZERO-OCCURRENCE TERMS (not seen in any image)")
        for sig in absence_signals:
            lines.append(f"  {sig}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Image-count grounding
# ---------------------------------------------------------------------------


def _count_images_for_pattern(
    extractions: list[dict],
    dominant_terms: list[str],
    threshold: float = _PATTERN_MATCH_THRESHOLD,
) -> int:
    """
    Count extractions that contain at least *threshold* fraction of *dominant_terms*.

    Uses actual per-image data rather than relying on Claude's estimate, which is
    reasoned from aggregated totals and can miscount co-occurrence.

    A term is "matched" the first time it appears in any dimension of the extraction;
    duplicates across dimensions are deduplicated via a set.
    """
    if not dominant_terms:
        return 0

    term_set = set(dominant_terms)
    min_matches = max(1, round(len(dominant_terms) * threshold))
    matched_images = 0

    for extraction in extractions:
        matched_terms: set[str] = set()
        for cat, dims in VOCABULARY.items():
            cat_data = extraction.get(cat)
            if not isinstance(cat_data, dict):
                continue
            for dim in dims:
                if len(matched_terms) >= len(term_set):
                    break
                value = cat_data.get(dim)
                if (cat, dim) in _LIST_DIMS:
                    if isinstance(value, list):
                        matched_terms.update(term_set.intersection(value))
                else:
                    if isinstance(value, str) and value in term_set:
                        matched_terms.add(value)

        if len(matched_terms) >= min_matches:
            matched_images += 1

    return matched_images


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def synthesize(
    extractions: list[dict],
    brief: str,
    sub_slice: str,
    *,
    client: anthropic.Anthropic | None = None,
) -> list[SaturationPattern]:
    """
    Aggregate schema extractions and return 4–6 named saturation patterns.

    Parameters
    ----------
    extractions:
        Schema dicts as returned by ``src.extractor.extract()``, one per image.
        Reliable saturation reading requires at least 8–10 images; fewer will
        produce patterns but with weaker frequency signal.
    brief:
        Free-text brief the user submitted — preserved verbatim in the prompt
        so the synthesizer can orient patterns to the query.
    sub_slice:
        ``"sneaker_streetwear"`` or ``"contemporary_fashion"``.
    client:
        Optional pre-built ``anthropic.Anthropic`` instance. Constructed from
        ``ANTHROPIC_API_KEY`` when ``None``.

    Returns
    -------
    list[SaturationPattern]
        4–6 dicts, each with: ``title``, ``description``, ``dominant_terms``,
        ``image_count``. Ranked most-to-least saturated. ``image_count`` is
        computed from the actual extraction data, not Claude's estimate.

    Raises
    ------
    ValueError
        If ``sub_slice`` is not recognized or ``extractions`` is empty.
    RuntimeError
        If Claude does not return a tool call.
    """
    if not extractions:
        raise ValueError("extractions is empty — nothing to synthesize")
    if sub_slice not in _SUB_SLICE_CONTEXT:
        raise ValueError(
            f"Unknown sub_slice {sub_slice!r}. "
            f"Valid values: {sorted(_SUB_SLICE_CONTEXT)}"
        )

    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or add it to .env."
            )
        client = anthropic.Anthropic(api_key=api_key)

    agg = _aggregate(extractions)
    freq_report = _format_aggregation(agg)
    sub_ctx = _SUB_SLICE_CONTEXT[sub_slice]

    user_message = "\n\n".join(
        [
            f"BRIEF\n{brief.strip()}",
            f"SUB-SLICE\n{sub_ctx}",
            freq_report,
            (
                "Identify 4–6 saturation patterns in this corpus. "
                "Use the frequency report to determine which design moves have become defaults. "
                "Apply the Filterworld lens: which terms have crossed from choice to convention? "
                "Name what is saturated. Name precisely what is absent or rare. "
                "Cite exact vocabulary terms — not categories."
            ),
        ]
    )

    response = client.messages.create(
        model=MODEL,
        max_tokens=4096,
        system=_SYSTEM_PROMPT,
        tools=[_SYNTHESIS_TOOL],
        tool_choice={"type": "tool", "name": "return_saturation_patterns"},
        messages=[{"role": "user", "content": user_message}],
    )

    tool_block = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if tool_block is None:
        raise RuntimeError(
            f"Claude did not return a tool call. "
            f"Stop reason: {response.stop_reason!r}. "
            f"Content block types: {[b.type for b in response.content]}"
        )

    raw_patterns: list[dict] = tool_block.input.get("patterns", [])

    # Ground-truth image_count from actual extraction data
    patterns: list[SaturationPattern] = []
    for p in raw_patterns:
        dominant_terms: list[str] = p.get("dominant_terms", [])
        computed_count = _count_images_for_pattern(extractions, dominant_terms)
        patterns.append(
            SaturationPattern(
                title=p.get("title", ""),
                description=p.get("description", ""),
                dominant_terms=dominant_terms,
                # prefer computed count; fall back to Claude's estimate if computation is 0
                image_count=computed_count or p.get("image_count", 0),
            )
        )

    return patterns
