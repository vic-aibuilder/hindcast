"""
Hindcast saturation scoring layer.

Reads aggregated schema extractions from the database and computes
frequency counts per dimension and value across the corpus.

This is the data that makes saturation quantifiable — "dark wood paneling
appears in 18 of 30 images" is a saturation signal. These counts feed
directly into Chris's synthesis prompt as structured context.

At ~75 seed images per slice, findings are directional, not statistically
precise. Output language reflects this — qualitative framing only,
no exact percentage claims.
"""

from __future__ import annotations

from collections import Counter, defaultdict

from pipeline.storage import (
    get_all_extractions_for_sub_slice,
    get_images_by_sub_slice,
)


# ── Core scoring ──────────────────────────────────────────────────────────────


def compute_frequencies(sub_slice: str) -> dict:
    """
    Compute how often each schema value appears across the corpus
    for a given sub-slice.

    Returns a dict structured as:
    {
        "dimension_name": {
            "value_a": count,
            "value_b": count,
            ...
        },
        ...
    }

    Example:
    {
        "material": {"concrete": 22, "white oak": 14, "steel": 18},
        "form":     {"rectilinear": 28, "arched": 9, "organic": 3},
        ...
    }
    """
    extractions = get_all_extractions_for_sub_slice(sub_slice)

    if not extractions:
        return {}

    # Group values by dimension
    by_dimension: dict[str, list[str]] = defaultdict(list)
    for row in extractions:
        dimension = row["dimension"]
        value = row["value"]
        if dimension and value:
            by_dimension[dimension].append(value.lower().strip())

    # Count frequency per dimension
    frequencies = {}
    for dimension, values in by_dimension.items():
        frequencies[dimension] = dict(Counter(values).most_common())

    return frequencies


def compute_saturation_signals(
    sub_slice: str,
    top_n: int = 5,
    min_count: int = 2,
) -> dict:
    """
    Identify the most saturated values per dimension.

    Returns a dict of the top_n most frequent values per dimension,
    filtered to only include values appearing at least min_count times.

    This is the structured input that feeds the synthesis prompt —
    Chris reads this to generate named saturation patterns.

    Args:
        sub_slice:  "sneaker_streetwear" or "contemporary_fashion".
        top_n:      How many top values to return per dimension.
        min_count:  Minimum appearances to be considered a signal.

    Returns:
        {
            "corpus_size": int,
            "sub_slice":   str,
            "signals": {
                "dimension_name": [
                    {"value": str, "count": int, "frequency": str},
                    ...
                ],
                ...
            }
        }
    """
    frequencies = compute_frequencies(sub_slice)
    total_images = len(get_images_by_sub_slice(sub_slice, limit=10000))

    signals = {}
    for dimension, counts in frequencies.items():
        top_values = []
        for value, count in list(counts.items())[:top_n]:
            if count < min_count:
                continue
            # Qualitative frequency label — no exact percentages
            # at this corpus size (per voice spec)
            frequency_label = _qualitative_label(count, total_images)
            top_values.append(
                {
                    "value": value,
                    "count": count,
                    "frequency": frequency_label,
                }
            )
        if top_values:
            signals[dimension] = top_values

    return {
        "corpus_size": total_images,
        "sub_slice": sub_slice,
        "signals": signals,
    }


def format_for_synthesis(sub_slice: str) -> str:
    """
    Format saturation signals as a readable string for the synthesis prompt.

    This is what gets passed to Chris's editorial synthesizer —
    Claude reads this structured summary and generates named
    saturation patterns from it.

    Returns a plain-text block like:

        CORPUS: 78 images · sneaker_streetwear

        MATERIAL (top signals):
          - concrete: dominant across the set
          - steel: common across the set
          - white oak: present in a minority

        FORM (top signals):
          - rectilinear: dominant across the set
          - arched: rare in the set
        ...
    """
    result = compute_saturation_signals(sub_slice)

    if not result["signals"]:
        return f"No extractions found for sub-slice: {sub_slice}"

    lines = [
        f"CORPUS: {result['corpus_size']} images · {sub_slice}",
        "",
    ]

    for dimension, values in result["signals"].items():
        lines.append(f"{dimension.upper().replace('_', ' ')} (top signals):")
        for v in values:
            lines.append(f"  - {v['value']}: {v['frequency']}")
        lines.append("")

    return "\n".join(lines)


# ── Qualitative labeling ──────────────────────────────────────────────────────


def _qualitative_label(count: int, total: int) -> str:
    """
    Convert a raw count into a qualitative frequency label.

    Uses qualitative framing per the voice spec —
    no exact percentage claims at prototype corpus size.
    """
    if total == 0:
        return "present"

    ratio = count / total

    if ratio >= 0.6:
        return "dominant across the set"
    elif ratio >= 0.35:
        return "common across the set"
    elif ratio >= 0.15:
        return "present in a notable portion"
    elif ratio >= 0.05:
        return "present in a minority"
    else:
        return "rare in the set"


if __name__ == "__main__":
    from pipeline.storage import (
        init_db,
        save_images,
        save_extraction,
        hash_brief,
    )

    print("Initializing database...")
    init_db()

    # Seed some test images with realistic schema extractions
    print("Seeding test corpus with schema extractions...")
    sub_slice = "sneaker_streetwear"
    brief = "scoring smoke test brief"
    brief_hash = hash_brief(brief, sub_slice)

    test_images = [
        {
            "image_url": f"https://example.com/score-test-{i}.jpg",
            "source_url": "https://dezeen.com",
            "title": f"Sneaker store {i}",
            "source": "dezeen.com",
            "retrieval_method": "test",
        }
        for i in range(20)
    ]

    ids = save_images(test_images, sub_slice, brief_hash)

    # Simulate realistic schema distribution for sneaker/streetwear
    schemas = [
        {
            "material": "concrete",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "rough",
            "atmosphere": "industrial warehouse",
        },
        {
            "material": "concrete",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "polished",
            "atmosphere": "minimal gallery",
        },
        {
            "material": "steel",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "smooth",
            "atmosphere": "industrial warehouse",
        },
        {
            "material": "concrete",
            "form": "rectilinear",
            "color_temperature": "neutral",
            "lighting": "diffuse ambient",
            "texture": "rough",
            "atmosphere": "minimal gallery",
        },
        {
            "material": "white oak",
            "form": "rectilinear",
            "color_temperature": "warm",
            "lighting": "warm ambient",
            "texture": "smooth",
            "atmosphere": "warm residential",
        },
        {
            "material": "concrete",
            "form": "arched",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "rough",
            "atmosphere": "minimal gallery",
        },
        {
            "material": "steel",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "smooth",
            "atmosphere": "industrial warehouse",
        },
        {
            "material": "concrete",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "rough",
            "atmosphere": "industrial warehouse",
        },
    ]

    for i, image_id in enumerate(ids):
        schema = schemas[i % len(schemas)]
        save_extraction(image_id, schema, sub_slice)

    print(f"  Seeded {len(ids)} images with schema extractions")

    # Test frequency computation
    print("\nComputing frequencies...")
    freqs = compute_frequencies(sub_slice)
    for dimension, counts in freqs.items():
        print(f"  {dimension}: {dict(list(counts.items())[:3])}")

    # Test saturation signals
    print("\nComputing saturation signals...")
    signals = compute_saturation_signals(sub_slice, top_n=3, min_count=2)
    print(f"  Corpus size: {signals['corpus_size']}")
    print(f"  Dimensions with signals: {list(signals['signals'].keys())}")

    # Test synthesis format — this is what feeds Chris's prompt
    print("\nFormatted for synthesis prompt:")
    print("-" * 40)
    print(format_for_synthesis(sub_slice))
    print("-" * 40)

    print("All scoring tests passed.")
