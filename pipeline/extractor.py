"""
Hindcast per-image schema extractor.

Takes an image URL and returns structured schema attributes
against the sub-slice's controlled vocabulary.

Gary owns the mechanism (this file).
Chris owns the prompt (loaded from prompts/extraction_prompt.py).
One Claude call per image — single-shot, no back-and-forth.
Seed-corpus images are extracted at build time.
Live-retrieved images are extracted at query time and written to cache.
"""

from __future__ import annotations

import base64
import json
import os
import re
import httpx

from anthropic import Anthropic
from dotenv import load_dotenv

from pipeline.storage import (
    save_extraction,
    image_has_extraction,
    get_extractions_for_image,
)

load_dotenv()

client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
MODEL = "claude-sonnet-4-6"


# ── Prompt loader ─────────────────────────────────────────────────────────────

def _load_extraction_prompt(sub_slice: str) -> str:
    """
    Load the extraction prompt for the given sub-slice.
    Chris writes these — they live in prompts/extraction_prompt.py.
    Falls back to a placeholder if Chris's prompts aren't ready yet,
    so Gary can test the mechanism independently.
    """
    try:
        if sub_slice == "sneaker_streetwear":
            from prompts.extraction_prompt import SNEAKER_STREETWEAR_PROMPT
            return SNEAKER_STREETWEAR_PROMPT
        elif sub_slice == "contemporary_fashion":
            from prompts.extraction_prompt import CONTEMPORARY_FASHION_PROMPT
            return CONTEMPORARY_FASHION_PROMPT
    except ImportError:
        pass

    # Placeholder prompt — lets Gary test the pipeline
    # before Chris's prompts are ready
    return """You are a schema extractor for Hindcast, an internal design tool
for Snarkitecture.

Analyze this retail interior image and extract the following dimensions.
Return ONLY valid JSON — no preamble, no markdown, no explanation.

Extract these shared base dimensions:
- material: primary material (e.g. "concrete", "white oak", "steel", "stone")
- form: dominant geometry (e.g. "rectilinear", "arched", "organic", "irregular")
- color_temperature: "warm", "cool", or "neutral"
- color_palette: brief descriptor (e.g. "monochrome white", "dark industrial", "warm neutrals")
- lighting: lighting type (e.g. "overhead track", "diffuse natural", "warm ambient")
- texture: surface quality (e.g. "smooth", "rough", "polished", "matte")
- opacity: "opaque", "translucent", or "mixed"
- atmosphere: overall feel (e.g. "minimal gallery", "industrial warehouse", "warm residential")

Return exactly this JSON structure:
{
  "material": "",
  "form": "",
  "color_temperature": "",
  "color_palette": "",
  "lighting": "",
  "texture": "",
  "opacity": "",
  "atmosphere": ""
}"""


# ── Image fetching ────────────────────────────────────────────────────────────

def _fetch_image_as_base64(url: str) -> tuple[str, str] | None:
    """
    Fetch an image from a URL and return (base64_data, media_type).
    Returns None if the fetch fails or the URL is not an image.
    """
    try:
        response = httpx.get(
            url,
            timeout=15.0,
            follow_redirects=True,
            headers={"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"},
        )
        response.raise_for_status()

        content_type = response.headers.get("content-type", "")

        # Only process actual images
        if not any(t in content_type for t in
                   ["image/jpeg", "image/png", "image/webp", "image/gif"]):
            return None

        media_type = content_type.split(";")[0].strip()
        image_data = base64.standard_b64encode(response.content).decode("utf-8")
        return image_data, media_type

    except (httpx.HTTPError, httpx.TimeoutException):
        return None


# ── Core extraction ───────────────────────────────────────────────────────────

def extract_schema(image_url: str, sub_slice: str) -> dict | None:
    """
    Run Claude vision on a single image and return structured schema attributes.

    Args:
        image_url: URL of the image to analyze.
        sub_slice: "sneaker_streetwear" or "contemporary_fashion".

    Returns:
        Dict of {dimension: value} schema attributes,
        or None if extraction failed.
    """
    prompt = _load_extraction_prompt(sub_slice)

    # Try URL-based delivery first (faster, no bandwidth cost)
    image_content = _build_image_content_url(image_url)

    try:
        response = client.messages.create(
            model=MODEL,
            max_tokens=512,
            messages=[
                {
                    "role": "user",
                    "content": [
                        image_content,
                        {
                            "type": "text",
                            "text": prompt,
                        },
                    ],
                }
            ],
        )
    except Exception as e:
        print(f"  URL delivery failed for {image_url[:60]}: {e}")
        print("  Falling back to base64...")
        # Fall back to base64 if URL delivery fails
        image_content = _build_image_content_base64(image_url)
        if image_content is None:
            print("  Base64 fetch failed as well.")
            return None
            
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=512,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            image_content,
                            {
                                "type": "text",
                                "text": prompt,
                            },
                        ],
                    }
                ],
            )
        except Exception as e2:
            print(f"  Extraction failed for {image_url[:60]}: {e2}")
            return None

    raw = response.content[0].text.strip()
    return _parse_json_response(raw)


def _build_image_content_url(image_url: str) -> dict | None:
    """Build a URL-based image content block for Claude."""
    # Claude accepts direct URLs for images
    # This is faster than base64 when the URL is accessible
    return {
        "type": "image",
        "source": {
            "type": "url",
            "url": image_url,
        },
    }


def _build_image_content_base64(image_url: str) -> dict | None:
    """Fetch image and build a base64 content block for Claude."""
    result = _fetch_image_as_base64(image_url)
    if result is None:
        return None
    image_data, media_type = result
    return {
        "type": "image",
        "source": {
            "type": "base64",
            "media_type": media_type,
            "data": image_data,
        },
    }


def _parse_json_response(raw: str) -> dict | None:
    """
    Parse Claude's JSON response safely.
    Strips markdown fences if present.
    """
    # Strip markdown code fences if Claude included them
    cleaned = re.sub(r"```(?:json)?\s*|\s*```", "", raw).strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        print(f"  Failed to parse extraction response: {raw[:100]}")
        return None


# ── Batch extraction ──────────────────────────────────────────────────────────

def extract_and_store(
    image_id: int,
    image_url: str,
    sub_slice: str,
    skip_existing: bool = True,
) -> dict | None:
    """
    Extract schema for a single image and write to the database.

    Args:
        image_id:      Database ID of the image row.
        image_url:     URL to analyze.
        sub_slice:     Sub-slice for prompt and vocabulary selection.
        skip_existing: If True, skip images already extracted. Default True.

    Returns:
        Extracted schema dict, or None if skipped or failed.
    """
    if skip_existing and image_has_extraction(image_id):
        return get_extractions_for_image(image_id)

    schema = extract_schema(image_url, sub_slice)
    if schema:
        save_extraction(image_id, schema, sub_slice)

    return schema


def batch_extract(
    images: list[dict],
    sub_slice: str,
    max_images: int = 50,
    skip_existing: bool = True,
) -> list[dict]:
    """
    Run schema extraction over a batch of image dicts.
    Each dict must have 'id' and 'image_url' keys.

    Args:
        images:        List of image dicts from storage.
        sub_slice:     Sub-slice for prompt selection.
        max_images:    Max images to process in this batch.
        skip_existing: Skip already-extracted images.

    Returns:
        List of {image_id, schema} dicts for successfully extracted images.
    """
    results = []
    processed = 0

    for img in images[:max_images]:
        image_id = img.get("id")
        image_url = img.get("image_url", "")

        if not image_id or not image_url:
            continue

        print(f"  Extracting [{processed + 1}/{min(len(images), max_images)}] "
              f"{image_url[:60]}...")

        schema = extract_and_store(
            image_id=image_id,
            image_url=image_url,
            sub_slice=sub_slice,
            skip_existing=skip_existing,
        )

        if schema:
            results.append({"image_id": image_id, "schema": schema})
            processed += 1
        else:
            print(f"    Skipped or failed.")

    print(f"  Extracted {len(results)} images successfully.")
    return results


if __name__ == "__main__":
    # Smoke test — extracts schema from 3 real images
    # Uses placeholder prompt until Chris's prompts are ready
    from pipeline.storage import init_db, save_images, hash_brief

    print("Initializing database...")
    init_db()

    # A reliable image from MDN that won't 403 or 404
    test_images = [
        {
            "image_url": "https://raw.githubusercontent.com/mdn/learning-area/master/html/multimedia-and-embedding/images-in-html/dinosaur.jpg",
            "source_url": "https://developer.mozilla.org",
            "title": "MDN Dinosaur Test",
            "source": "mdn",
            "retrieval_method": "test",
        },
    ]

    brief = "test sneaker retail NYC 2025"
    sub_slice = "sneaker_streetwear"
    brief_hash = hash_brief(brief, sub_slice)

    print("Saving test images to database...")
    ids = save_images(test_images, sub_slice, brief_hash)
    print(f"  Saved image IDs: {ids}")

    print("\nRunning schema extraction on first image...")
    if ids:
        # Attach IDs back to image dicts for batch_extract
        for i, img in enumerate(test_images):
            if i < len(ids):
                img["id"] = ids[i]

        results = batch_extract(
            [test_images[0]],
            sub_slice=sub_slice,
            max_images=1,
        )

        if results:
            print("\nExtracted schema:")
            for k, v in results[0]["schema"].items():
                print(f"  {k}: {v}")
        else:
            print("  Extraction returned no results — check image URL accessibility.")

    print("\nExtractor smoke test complete.")
