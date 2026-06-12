"""
Hindcast pipeline entry point — v2.

Wires Gary's retrieval / storage / cache layer with
Chris's hardened src/ extraction and synthesis modules.

Victor's frontend calls POST /query → api.py → run_query() here.
"""

from __future__ import annotations

import os
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed

from anthropic import Anthropic
from dotenv import load_dotenv

from retrieval.agent import run as run_retrieval_agent
from pipeline.storage import (
    init_db,
    save_images,
    save_extraction,
    get_extracted_schemas_for_sub_slice,
    count_extracted_images_for_sub_slice,
    image_has_extraction,
    hash_brief,
)
from corpus.cache import check as cache_check, store as cache_store
from src.extractor import extract
from src.synthesizer import synthesize, SaturationPattern

load_dotenv()

CACHE_MIN_IMAGES = 30
MAX_EXTRACTION_BATCH = 40

# Concurrency for the schema-extraction step. Each unit is one Claude vision
# call; we fan these out because they dominate query latency. Kept modest to
# stay under API rate limits — override with HINDCAST_EXTRACTION_WORKERS.
# NOTE: only the vision calls run in parallel; SQLite writes (save_extraction)
# stay on the main thread because WAL still allows only one writer at a time.
EXTRACTION_WORKERS = int(os.environ.get("HINDCAST_EXTRACTION_WORKERS", "8"))


# ── Helpers ───────────────────────────────────────────────────────────────────


def _get_all_extractions(sub_slice: str) -> list[dict]:
    """
    Reconstruct per-image extraction dicts from the database.
    Returns nested schema dicts for passing to src/synthesizer.synthesize().
    """
    return get_extracted_schemas_for_sub_slice(sub_slice)


def _source_breakdown(images: list[dict]) -> dict[str, int]:
    """Count retrieved images by publication domain for UI/debug."""
    counts: Counter[str] = Counter()
    for img in images:
        src = img.get("source") or "unknown"
        counts[src] += 1
    return dict(counts.most_common())


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
        agent_result = run_retrieval_agent(
            brief=brief, sub_slice=sub_slice, client=client
        )
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
        images_with_ids = [img for img in images if img.get("id")][
            :MAX_EXTRACTION_BATCH
        ]

        # Candidates = have an id + url and aren't already extracted. The
        # image_has_extraction() reads are cheap and stay sequential here.
        candidates = [
            (img["id"], img.get("image_url", ""))
            for img in images_with_ids
            if img.get("id")
            and img.get("image_url")
            and not image_has_extraction(img["id"])
        ]
        retrieval_log.append(
            f"extracting schema from {len(candidates)} images "
            f"({EXTRACTION_WORKERS}-way parallel)..."
        )

        # Fan out the slow Claude vision calls; collect results as they finish
        # and write to SQLite on this (main) thread only — WAL is single-writer,
        # so concurrent save_extraction() calls would hit "database is locked".
        extracted_count = 0
        with ThreadPoolExecutor(max_workers=EXTRACTION_WORKERS) as pool:
            future_to_img = {
                pool.submit(extract, url, client=client): (image_id, url)
                for image_id, url in candidates
            }
            for future in as_completed(future_to_img):
                image_id, image_url = future_to_img[future]
                try:
                    schema = future.result()
                except Exception as e:
                    retrieval_log.append(f"  skipped {image_url[:50]}... ({e})")
                    continue
                if schema:
                    save_extraction(image_id, schema, sub_slice)
                    extracted_count += 1

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

    source_breakdown = _source_breakdown(images)

    # ── Step 8: Assemble result ───────────────────────────────────────────────
    extracted_corpus_size = count_extracted_images_for_sub_slice(sub_slice)

    if source_breakdown:
        breakdown = ", ".join(f"{k}: {v}" for k, v in source_breakdown.items())
        retrieval_log.append(f"publication mix this query — {breakdown}")

    return {
        "brief": brief,
        "sub_slice": sub_slice,
        "cache_hit": cache_hit,
        "images": images[:50],
        "corpus_size": extracted_corpus_size,
        "patterns": patterns,
        "retrieval_log": retrieval_log,
        "source_breakdown": source_breakdown,
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
