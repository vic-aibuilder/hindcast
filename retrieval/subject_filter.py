"""
Vision-based subject filter for Hindcast retrieval.

Runs a fast binary Claude vision check on each candidate image
before it enters the extraction pipeline. Drops images that are
not retail interior spaces — product shots, street style,
exterior facades, logo splash screens, editorial collages, etc.

This is the real fix for issue #38. The URL pre-filter in
consolidate.py catches obvious structural patterns; this catches
everything else by actually looking at the image.
"""

from __future__ import annotations

import os
from concurrent.futures import ThreadPoolExecutor, as_completed

import anthropic
from dotenv import load_dotenv

load_dotenv()

MODEL = "claude-sonnet-4-6"
MAX_WORKERS = 5  # parallel vision checks


def _is_retail_interior(image_url: str, client: anthropic.Anthropic) -> bool:
    """
    Binary vision check — is this image a retail interior space?
    Tries URL delivery first, falls back to base64 if CDN blocks it.
    """
    # Try URL delivery first
    image_content = {"type": "image", "source": {"type": "url", "url": image_url}}

    for attempt in range(2):
        try:
            response = client.messages.create(
                model=MODEL,
                max_tokens=10,
                messages=[
                    {
                        "role": "user",
                        "content": [
                            image_content,
                            {
                                "type": "text",
                                "text": (
                                    "Does this image show the INTERIOR of a retail store or brand "
                                    "space — meaning you can see walls, floor, ceiling, and fixtures "
                                    "inside a physical shop or boutique?\n\n"
                                    "Reply YES only if the image is clearly taken from INSIDE a store "
                                    "and shows the architectural space itself.\n\n"
                                    "Reply NO for ALL of these:\n"
                                    "- People portraits or group photos\n"
                                    "- Exterior building facades\n"
                                    "- Logo-only images or brand splash screens\n"
                                    "- Product photos without a visible store interior\n"
                                    "- Street photography\n"
                                    "- Social media collages or Pinterest grids\n"
                                    "- YouTube thumbnails\n"
                                    "- Any image where a retail interior space is not the "
                                    "primary subject\n\n"
                                    "Reply YES or NO only. No other text."
                                ),
                            },
                        ],
                    }
                ],
            )
            answer = response.content[0].text.strip().upper()
            return answer == "YES"

        except anthropic.BadRequestError:
            if attempt == 0:
                # URL delivery failed — try base64 fallback
                try:
                    import base64
                    import httpx

                    r = httpx.get(
                        image_url,
                        timeout=10.0,
                        follow_redirects=True,
                        headers={"User-Agent": "Mozilla/5.0"},
                    )
                    r.raise_for_status()
                    media_type = r.headers.get("content-type", "image/jpeg").split(";")[
                        0
                    ]
                    image_content = {
                        "type": "image",
                        "source": {
                            "type": "base64",
                            "media_type": media_type,
                            "data": base64.standard_b64encode(r.content).decode(),
                        },
                    }
                    continue  # retry with base64
                except Exception:
                    return False  # can't fetch — drop it
            return False  # both attempts failed — drop it

        except Exception:
            return True  # unknown error — let it through

    return False


def filter_to_interiors(
    images: list[dict],
    client: anthropic.Anthropic | None = None,
    max_to_check: int = 60,
) -> list[dict]:
    """
    Filter a list of image dicts to retail interiors only.

    Runs vision checks in parallel using ThreadPoolExecutor.
    Only checks up to max_to_check images — images beyond this
    cap are DROPPED without inspection. This is intentional:
    extraction caps at 40 downstream anyway, so images beyond
    position 60 would never be extracted regardless. The cap
    controls cost and latency, not quality.

    Order matters: retrieval agent should rank relevant images
    first. The consolidate layer's round-robin interleave helps
    ensure varied sources appear in the first 60.

    Args:
        images:       List of image dicts with image_url field.
        client:       Anthropic client. Created from env if not provided.
        max_to_check: Max images to vision-check. Images beyond this
                      cap are dropped to keep cost bounded.

    Returns:
        Filtered list containing only confirmed retail interiors.
    """
    if client is None:
        client = anthropic.Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # Cap candidates before vision checks
    candidates = images[:max_to_check]
    results: dict[int, bool] = {}

    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {
            executor.submit(_is_retail_interior, img.get("image_url", ""), client): i
            for i, img in enumerate(candidates)
            if img.get("image_url")
        }
        for future in as_completed(futures):
            idx = futures[future]
            try:
                results[idx] = future.result()
            except Exception:
                results[idx] = False

    kept = [img for i, img in enumerate(candidates) if results.get(i, False)]
    dropped = len(candidates) - len(kept)

    print(
        f"  Subject filter: {len(kept)} kept, {dropped} dropped from {len(candidates)} checked"
    )
    return kept
