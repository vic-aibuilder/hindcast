"""
Per-image schema extractor for Hindcast.

Given an image URL, calls Claude Sonnet 4.6 (vision) via tool-use and returns
a structured dict covering all 7 shared base categories defined in Schema v2.2.
Values are constrained to, and validated against, the controlled vocabulary
before the result is returned.

Public API
----------
    extract(image_url, *, client=None, validate=True) -> dict
    SchemaValidationError

CLI
---
    python -m src.extractor <image_url>
"""

from __future__ import annotations

import base64
import json
import os
import sys
from typing import Any

import anthropic
import httpx
from dotenv import load_dotenv

from src.schema import VOCABULARY, _LIST_DIMS

load_dotenv()

MODEL = "claude-sonnet-4-6"

SYSTEM_PROMPT = (
    "You are a visual schema extractor for Hindcast, an internal Snarkitecture tool "
    "that maps visual saturation in brand and retail spaces. Analyze the image and "
    "extract structured schema attributes using only the controlled vocabulary provided "
    "via the tool schema. "
    "Be precise and literal — score only what is visibly present in the image, not what "
    "the brand might typically use in other contexts. Do not infer, speculate, or output "
    "values outside the controlled vocabulary. For list fields, include only elements "
    "clearly visible; return an empty list if none are present."
)

# ---------------------------------------------------------------------------
# Tool definition (built once at module load)
# ---------------------------------------------------------------------------


def _str_prop(vocab: list[str], description: str = "") -> dict[str, Any]:
    prop: dict[str, Any] = {"type": "string", "enum": vocab}
    if description:
        prop["description"] = description
    return prop


def _arr_prop(vocab: list[str], description: str = "") -> dict[str, Any]:
    prop: dict[str, Any] = {"type": "array", "items": {"type": "string", "enum": vocab}}
    if description:
        prop["description"] = description
    return prop


def _build_tool() -> dict[str, Any]:
    v = VOCABULARY
    return {
        "name": "extract_schema_attributes",
        "description": (
            "Extract visual schema attributes from a brand or retail interior image "
            "using Schema v2.4 controlled vocabulary. Score only what is visibly "
            "present. Return empty arrays for list fields when the element is absent."
        ),
        "input_schema": {
            "type": "object",
            "required": [
                "material",
                "form_geometry",
                "color",
                "lighting",
                "texture",
                "opacity",
                "atmosphere_warmth",
                "layout_archetype",
                "typography_signage",
                "brand_expression_density",
            ],
            "additionalProperties": False,
            "properties": {
                "material": {
                    "type": "object",
                    "description": "Primary Category 1 — Material. List each material type visibly present.",
                    "required": [
                        "wood",
                        "metal",
                        "stone",
                        "glass",
                        "tile",
                        "soft_fabric",
                        "wall_finish",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "wood": _arr_prop(
                            v["material"]["wood"], "Wood species / finish visible"
                        ),
                        "metal": _arr_prop(
                            v["material"]["metal"], "Metal types visible"
                        ),
                        "stone": _arr_prop(
                            v["material"]["stone"], "Stone types visible"
                        ),
                        "glass": _arr_prop(
                            v["material"]["glass"], "Glass types visible"
                        ),
                        "tile": _arr_prop(v["material"]["tile"], "Tile types visible"),
                        "soft_fabric": _arr_prop(
                            v["material"]["soft_fabric"],
                            "Soft / fabric materials visible",
                        ),
                        "wall_finish": _arr_prop(
                            v["material"]["wall_finish"], "Wall finishes visible"
                        ),
                    },
                },
                "form_geometry": {
                    "type": "object",
                    "description": "Primary Category 2 — Form / Geometry.",
                    "required": [
                        "primary_geometry",
                        "basic_shape",
                        "arch_presence",
                        "grid_presence",
                        "mass_weight",
                        "statement_form",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "primary_geometry": _str_prop(
                            v["form_geometry"]["primary_geometry"]
                        ),
                        "basic_shape": _str_prop(v["form_geometry"]["basic_shape"]),
                        "arch_presence": _str_prop(v["form_geometry"]["arch_presence"]),
                        "grid_presence": _str_prop(v["form_geometry"]["grid_presence"]),
                        "mass_weight": _str_prop(v["form_geometry"]["mass_weight"]),
                        "statement_form": _str_prop(
                            v["form_geometry"]["statement_form"]
                        ),
                    },
                },
                "color": {
                    "type": "object",
                    "description": "Primary Category 3 — Color.",
                    "required": [
                        "temperature",
                        "dominant_hue",
                        "palette_type",
                        "accent",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "temperature": _str_prop(v["color"]["temperature"]),
                        "dominant_hue": _str_prop(v["color"]["dominant_hue"]),
                        "palette_type": _str_prop(v["color"]["palette_type"]),
                        "accent": _str_prop(v["color"]["accent"]),
                    },
                },
                "lighting": {
                    "type": "object",
                    "description": "Secondary Category 4 — Lighting.",
                    "required": [
                        "source_type",
                        "temperature",
                        "visibility",
                        "drama",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "source_type": _str_prop(v["lighting"]["source_type"]),
                        "temperature": _str_prop(v["lighting"]["temperature"]),
                        "visibility": _str_prop(v["lighting"]["visibility"]),
                        "drama": _str_prop(v["lighting"]["drama"]),
                    },
                },
                "texture": {
                    "type": "object",
                    "description": "Secondary Category 5 — Texture.",
                    "required": ["surface", "finish", "texture_type", "pattern"],
                    "additionalProperties": False,
                    "properties": {
                        "surface": _str_prop(v["texture"]["surface"]),
                        "finish": _str_prop(v["texture"]["finish"]),
                        "texture_type": _str_prop(v["texture"]["texture_type"]),
                        "pattern": _str_prop(v["texture"]["pattern"]),
                    },
                },
                "opacity": {
                    "type": "object",
                    "description": "Secondary Category 6 — Opacity.",
                    "required": ["dominant_opacity", "transparency_use"],
                    "additionalProperties": False,
                    "properties": {
                        "dominant_opacity": _str_prop(v["opacity"]["dominant_opacity"]),
                        "transparency_use": _str_prop(v["opacity"]["transparency_use"]),
                    },
                },
                "atmosphere_warmth": {
                    "type": "object",
                    "description": "Secondary Category 7 — Atmosphere / Warmth.",
                    "required": [
                        "warmth",
                        "formality",
                        "reference",
                        "abstract_qualities",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "warmth": _str_prop(v["atmosphere_warmth"]["warmth"]),
                        "formality": _str_prop(v["atmosphere_warmth"]["formality"]),
                        "reference": _str_prop(v["atmosphere_warmth"]["reference"]),
                        "abstract_qualities": _arr_prop(
                            v["atmosphere_warmth"]["abstract_qualities"],
                            "Atmospheric qualities applicable to this space",
                        ),
                    },
                },
                "layout_archetype": {
                    "type": "object",
                    "description": "Base Category 8 — Layout Archetype.",
                    "required": ["layout", "circulation", "density"],
                    "additionalProperties": False,
                    "properties": {
                        "layout": _str_prop(
                            v["layout_archetype"]["layout"],
                            "Primary organizational logic of the floor plan",
                        ),
                        "circulation": _str_prop(
                            v["layout_archetype"]["circulation"],
                            "How visitor movement is choreographed",
                        ),
                        "density": _str_prop(
                            v["layout_archetype"]["density"],
                            "How tightly the space is occupied",
                        ),
                    },
                },
                "typography_signage": {
                    "type": "object",
                    "description": "Base Category 9 — Typography / Signage.",
                    "required": [
                        "signage_density",
                        "logo_treatment",
                        "typography_style",
                    ],
                    "additionalProperties": False,
                    "properties": {
                        "signage_density": _str_prop(
                            v["typography_signage"]["signage_density"],
                            "How much text and logotype is visible in the space",
                        ),
                        "logo_treatment": _str_prop(
                            v["typography_signage"]["logo_treatment"],
                            "How the brand logo is deployed spatially",
                        ),
                        "typography_style": _str_prop(
                            v["typography_signage"]["typography_style"],
                            "Dominant typeface register when type is present",
                        ),
                    },
                },
                "brand_expression_density": {
                    "type": "object",
                    "description": "Base Category 10 — Brand Expression Density.",
                    "required": ["density", "mode"],
                    "additionalProperties": False,
                    "properties": {
                        "density": _str_prop(
                            v["brand_expression_density"]["density"],
                            "Intensity of brand expression across the space",
                        ),
                        "mode": _str_prop(
                            v["brand_expression_density"]["mode"],
                            "Primary channel through which brand expression operates",
                        ),
                    },
                },
            },
        },
    }


_TOOL: dict[str, Any] = _build_tool()

# ---------------------------------------------------------------------------
# Public exceptions
# ---------------------------------------------------------------------------


class SchemaValidationError(ValueError):
    """Raised when extracted values fall outside the controlled vocabulary."""


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _fetch_image(url: str) -> tuple[str, str]:
    """Download *url* and return ``(base64_data, media_type)``."""
    try:
        resp = httpx.get(url, follow_redirects=True, timeout=30)
        resp.raise_for_status()
    except httpx.HTTPError as exc:
        raise RuntimeError(f"Failed to fetch image from {url!r}: {exc}") from exc

    content_type = resp.headers.get("content-type", "").split(";")[0].strip().lower()
    _mime_map = {
        "image/jpeg": "image/jpeg",
        "image/jpg": "image/jpeg",
        "image/png": "image/png",
        "image/gif": "image/gif",
        "image/webp": "image/webp",
    }
    media_type = _mime_map.get(content_type)

    if not media_type:
        lower_url = url.lower().split("?")[0]
        if lower_url.endswith((".jpg", ".jpeg")):
            media_type = "image/jpeg"
        elif lower_url.endswith(".png"):
            media_type = "image/png"
        elif lower_url.endswith(".gif"):
            media_type = "image/gif"
        elif lower_url.endswith(".webp"):
            media_type = "image/webp"
        else:
            media_type = "image/jpeg"

    return base64.standard_b64encode(resp.content).decode("utf-8"), media_type


def validate(result: dict[str, Any]) -> list[str]:
    """
    Check *result* against the controlled vocabulary.

    Returns a list of human-readable violation messages. An empty list means
    the result is clean. This function is exposed publicly so callers can
    run validation on cached or externally sourced extractions.
    """
    violations: list[str] = []

    for category, dims in VOCABULARY.items():
        cat_data = result.get(category)
        if not isinstance(cat_data, dict):
            violations.append(f"Missing or invalid category block: '{category}'")
            continue
        for dim, allowed in dims.items():
            value = cat_data.get(dim)
            if (category, dim) in _LIST_DIMS:
                if not isinstance(value, list):
                    violations.append(
                        f"{category}.{dim}: expected list, got {type(value).__name__!r}"
                    )
                    continue
                out_of_vocab = [v for v in value if v not in allowed]
                if out_of_vocab:
                    violations.append(
                        f"{category}.{dim}: out-of-vocabulary values {out_of_vocab}"
                    )
            else:
                if value is None:
                    violations.append(f"{category}.{dim}: missing")
                elif value not in allowed:
                    violations.append(
                        f"{category}.{dim}: '{value}' not in vocabulary {allowed}"
                    )

    return violations


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def extract(
    image_url: str,
    *,
    client: anthropic.Anthropic | None = None,
    validate_result: bool = True,
) -> dict[str, Any]:
    """
    Analyze an image and return a structured schema extraction (Schema v2.2).

    Uses Claude Sonnet 4.6 vision via tool-use to ensure values are constrained
    to the controlled vocabulary. The tool schema encodes all enum lists, so
    out-of-vocabulary values are rejected before they reach the application.

    Parameters
    ----------
    image_url:
        Publicly accessible URL of the image to analyze.
    client:
        Optional pre-built ``anthropic.Anthropic`` instance. When *None*, one
        is constructed from the ``ANTHROPIC_API_KEY`` environment variable.
    validate_result:
        When *True* (default), raises ``SchemaValidationError`` if the
        extracted values fall outside the controlled vocabulary. Set to *False*
        only when debugging raw Claude output.

    Returns
    -------
    dict
        Keys: ``material``, ``form_geometry``, ``color``, ``lighting``,
        ``texture``, ``opacity``, ``atmosphere_warmth``.

    Raises
    ------
    RuntimeError
        If the image cannot be fetched or Claude does not return a tool call.
    SchemaValidationError
        If *validate_result* is *True* and the extraction contains
        out-of-vocabulary values.
    """
    if client is None:
        api_key = os.environ.get("ANTHROPIC_API_KEY")
        if not api_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is not set. Export it or add it to .env."
            )
        client = anthropic.Anthropic(api_key=api_key)

    image_b64, media_type = _fetch_image(image_url)

    response = client.messages.create(
        model=MODEL,
        max_tokens=2048,
        system=SYSTEM_PROMPT,
        tools=[_TOOL],
        tool_choice={"type": "tool", "name": "extract_schema_attributes"},
        messages=[
            {
                "role": "user",
                "content": [
                    {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": image_b64,
                        },
                    },
                    {
                        "type": "text",
                        "text": (
                            "Analyze this brand or retail interior image and extract "
                            "schema attributes for all 7 categories using only the "
                            "controlled vocabulary. Score only what is visibly present."
                        ),
                    },
                ],
            }
        ],
    )

    tool_block = next(
        (block for block in response.content if block.type == "tool_use"),
        None,
    )
    if tool_block is None:
        raise RuntimeError(
            f"Claude did not return a tool call. "
            f"Stop reason: {response.stop_reason!r}. "
            f"Content blocks: {[b.type for b in response.content]}"
        )

    result: dict[str, Any] = tool_block.input

    if validate_result:
        violations = validate(result)
        if violations:
            raise SchemaValidationError(
                f"Schema validation failed for {image_url!r}:\n"
                + "\n".join(f"  • {v}" for v in violations)
            )

    return result


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python -m src.extractor <image_url>", file=sys.stderr)
        sys.exit(1)

    url = sys.argv[1]
    print(f"Extracting schema for: {url}", file=sys.stderr)
    data = extract(url)
    print(json.dumps(data, indent=2))
