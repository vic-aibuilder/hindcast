"""
Hindcast pipeline entry point — v2.

Wires Gary's retrieval / storage / cache layer with
Chris's hardened src/ extraction and synthesis modules.

Victor's frontend calls POST /query → api.py → run_query() here.
"""

from __future__ import annotations

import os
from anthropic import Anthropic
from dotenv import load_dotenv

from retrieval.agent import run as run_retrieval_agent
from pipeline.storage import (
    init_db,
    save_images,
    save_extraction,
    get_images_by_sub_slice,
    image_has_extraction,
    get_extractions_for_image,
    hash_brief,
)
from corpus.cache import check as cache_check, store as cache_store
from src.extractor import extract
from src.synthesizer import synthesize, SaturationPattern

load_dotenv()

CACHE_MIN_IMAGES = 30
MAX_EXTRACTION_BATCH = 40


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_all_extractions(sub_slice: str) -> list[dict]:
    """
    Reconstruct per-image extraction dicts from the database.
    Returns a list of flat schema dicts — one per image —
    for passing to src/synthesizer.synthesize().
    """
    images = get_images_by_sub_slice(sub_slice, limit=500)
    extractions = []
    for img in images:
        image_id = img.get("id")
        if image_id and image_has_extraction(image_id):
            schema = get_extractions_for_image(image_id)
            if schema:
                extractions.append(schema)
    return extractions


# ── Main pipeline ─────────────────────────────────────────────────────────────


def run_query(brief: str, sub_slice: str) -> dict:
    """
    Run the full Hindcast pipeline for a brief.

    This is the function api.py calls.

    Args:
        brief:     Free-text design brief from the user.
        sub_slice: "sneaker_streetwear" or "contemporary_fashion".

    Returns:
        {
            "brief":          str,
            "sub_slice":      str,
            "cache_hit":      bool,
            "images":         list[dict],
            "corpus_size":    int,
            "patterns":       list[SaturationPattern],
            "retrieval_log":  list[str],
        }
    """
    init_db()
    retrieval_log = []
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    # ── Step 1: Check cache ───────────────────────────────────────────────────
    retrieval_log.append(f"checking cache for '{sub_slice}' brief...")
    cached_images = cache_check(brief, sub_slice, min_images=CACHE_MIN_IMAGES)

    if cached_images:
        retrieval_log.append(
            f"cache hit — {len(cached_images)} images, skipping live retrieval."
        )
        images = cached_images
        cache_hit = True

    else:
        # ── Step 2: Live retrieval ────────────────────────────────────────────
        retrieval_log.append("cache cold — running live retrieval...")
        agent_result = run_retrieval_agent(brief=brief, sub_slice=sub_slice)
        images = agent_result["images"]
        retrieval_log.extend(agent_result["log"])
        retrieval_log.append(f"retrieval complete — {len(images)} images returned.")

        # ── Step 3: Save to database ──────────────────────────────────────────
        retrieval_log.append("saving images to database...")
        brief_hash = hash_brief(brief, sub_slice)
        saved_ids = save_images(images, sub_slice, brief_hash)

        for i, img in enumerate(images):
            if i < len(saved_ids):
                img["id"] = saved_ids[i]

        # ── Step 4: Schema extraction (Chris's hardened extractor) ────────────
        retrieval_log.append(
            f"extracting schema from up to {MAX_EXTRACTION_BATCH} images..."
        )
        images_with_ids = [img for img in images if img.get("id")][
            :MAX_EXTRACTION_BATCH
        ]

        extracted_count = 0
        for img in images_with_ids:
            image_id = img.get("id")
            image_url = img.get("image_url", "")

            if not image_id or not image_url:
                continue
            if image_has_extraction(image_id):
                continue

            try:
                schema = extract(image_url, client=client)
                if schema:
                    save_extraction(image_id, schema, sub_slice)
                    extracted_count += 1
            except Exception as e:
                retrieval_log.append(f"  skipped {image_url[:50]}... ({e})")
                continue

        retrieval_log.append(
            f"extraction complete — {extracted_count} new images extracted."
        )

        # ── Step 5: Write to cache ────────────────────────────────────────────
        all_ids = [img["id"] for img in images_with_ids if img.get("id")]
        cache_store(brief, sub_slice, all_ids)
        retrieval_log.append("results cached.")
        cache_hit = False

    # ── Step 6: Collect extractions for synthesis ─────────────────────────────
    retrieval_log.append("collecting extractions for synthesis...")
    extractions = _get_all_extractions(sub_slice)
    retrieval_log.append(
        f"{len(extractions)} extracted images available for synthesis."
    )

    # ── Step 7: Editorial synthesis (Chris's hardened synthesizer) ────────────
    retrieval_log.append("running editorial synthesis...")
    patterns: list[SaturationPattern] = synthesize(
        extractions=extractions,
        brief=brief,
        sub_slice=sub_slice,
        client=client,
    )
    retrieval_log.append(f"synthesis complete — {len(patterns)} patterns generated.")

    # ── Step 8: Assemble result ───────────────────────────────────────────────
    all_corpus_images = get_images_by_sub_slice(sub_slice, limit=500)

    return {
        "brief": brief,
        "sub_slice": sub_slice,
        "cache_hit": cache_hit,
        "images": images[:50],
        "corpus_size": len(all_corpus_images),
        "patterns": patterns,
        "retrieval_log": retrieval_log,
    }


if __name__ == "__main__":
    print("=" * 60)
    print("HINDCAST — Integration Test (src/ modules)")
    print("=" * 60)

    result = run_query(
        brief=(
            "NYC sneaker retail store interiors — "
            "concrete, steel fixtures, minimal gallery feel, 2025"
        ),
        sub_slice="sneaker_streetwear",
    )

    print("\n── Retrieval Log ──")
    for line in result["retrieval_log"]:
        print(f"  {line}")

    print("\n── Corpus ──")
    print(f"  Images this query: {len(result['images'])}")
    print(f"  Total corpus size: {result['corpus_size']}")
    print(f"  Cache hit: {result['cache_hit']}")

    print(f"\n── Patterns ({len(result['patterns'])}) ──")
    for p in result["patterns"]:
        print(f"\n  {p.get('title', '')}")
        desc = p.get("description", "")
        print(f"  {desc[:120]}{'...' if len(desc) > 120 else ''}")
        print(f"  image_count: {p.get('image_count', '—')}")

    print("\n" + "=" * 60)
    print("Integration test complete.")
    print("=" * 60)
