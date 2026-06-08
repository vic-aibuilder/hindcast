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

from prompts.synthesis_prompt import SYSTEM_PROMPT
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

# Saturation / rarity thresholds used in the frequency report
_SATURATED_PCT = 0.40
_RARE_PCT = 0.10

# Minimum fraction of dominant_terms an image must match to count for a pattern
_PATTERN_MATCH_THRESHOLD = 0.5

# Title Case minor words — per PRD / Alex direction (not ALL CAPS)
_TITLE_MINOR_WORDS: frozenset[str] = frozenset(
    {"a", "an", "the", "and", "or", "with", "in", "on", "of", "as", "for", "to"}
)

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
                                "Pattern name in Title Case — names the move directly. "
                                "Lowercase minor words (the, and, with) unless first word. "
                                "Example: The Lightbox Ceiling"
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


def _normalize_pattern_title(title: str) -> str:
    """Ensure Title Case output per PRD — corrects ALL CAPS if the model drifts."""
    title = title.strip()
    if not title:
        return title
    words = title.split()
    normalized: list[str] = []
    for i, word in enumerate(words):
        core = word.lower()
        if i > 0 and core in _TITLE_MINOR_WORDS:
            normalized.append(core)
        elif word.isupper():
            normalized.append(word.capitalize())
        else:
            normalized.append(word)
    return " ".join(normalized)


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
        system=SYSTEM_PROMPT,
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
                title=_normalize_pattern_title(p.get("title", "")),
                description=p.get("description", ""),
                dominant_terms=dominant_terms,
                # prefer computed count; fall back to Claude's estimate if computation is 0
                image_count=computed_count or p.get("image_count", 0),
            )
        )

    return patterns
