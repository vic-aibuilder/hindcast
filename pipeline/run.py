"""
Hindcast pipeline entry point — v2.

Wires Gary's retrieval / storage / cache layer with
Chris's hardened src/ extraction and synthesis modules.

Victor's frontend calls POST /query → api.py → run_query() here.
"""

from __future__ import annotations

import os
import re
from collections import Counter
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

from anthropic import Anthropic
from dotenv import load_dotenv

from retrieval.agent import run as run_retrieval_agent, _extract_metadata
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
from retrieval.sources import is_evidence_eligible
from src.extractor import extract
from src.synthesizer import synthesize, SaturationPattern

load_dotenv()

CACHE_MIN_IMAGES = 5
MAX_EXTRACTION_BATCH = 40
MAX_EVIDENCE_IMAGES = 15

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


def _evidence_sort_key(img: dict[str, Any]) -> tuple[str, int, str]:
    """
    Sort key to group a pattern's evidence images by store, then interior order.

    Store identity: the extracted ``project`` when present, else the part of the
    title before the ' — ' separator (seed titles are 'Store — interior N').
    Interior order: 'hero' first, then 'interior 1', 'interior 2', …; anything
    without an interior marker sorts last within its store.
    """
    title = (img.get("title") or "").strip()
    project = img.get("project")
    if project:
        store, remainder = project.strip(), title
    else:
        parts = re.split(r"\s*—\s*", title, maxsplit=1)
        store = parts[0].strip()
        remainder = parts[1] if len(parts) > 1 else ""

    remainder_l = remainder.lower()
    if "hero" in remainder_l:
        order = 0
    else:
        m = re.search(r"interior\s+(\d+)", remainder_l)
        order = int(m.group(1)) if m else 999
    return (store.lower(), order, title.lower())


def _query_image_ids(images: list[dict]) -> set[int]:
    """Image IDs belonging to this query's retrieval/cache batch."""
    return {img["id"] for img in images if isinstance(img.get("id"), int)}


def _scoped_evidence_ids(
    matched_ids: list[int],
    *,
    query_ids: set[int],
    sub_slice: str,
) -> list[int]:
    """
    Keep evidence IDs that belong to this query and pass junk filters.

    Synthesis still reads the full extracted corpus for saturation signal, but
    pattern grids only show images from the current brief's batch (#74).
    """
    if not matched_ids or not query_ids:
        return []

    from pipeline.storage import get_connection

    conn = get_connection()
    placeholders = ",".join("?" * len(matched_ids))
    rows = conn.execute(
        f"SELECT * FROM images WHERE id IN ({placeholders})",  # nosec B608
        matched_ids,
    ).fetchall()
    conn.close()

    eligible: list[int] = []
    for row in rows:
        row_dict = dict(row)
        image_id = row_dict["id"]
        if image_id not in query_ids:
            continue
        if not is_evidence_eligible(row_dict, sub_slice):
            continue
        eligible.append(image_id)

    # Preserve synthesizer match order; cap at PRD target (8–15).
    order = {image_id: idx for idx, image_id in enumerate(matched_ids)}
    eligible.sort(key=lambda i: order.get(i, len(matched_ids)))
    return eligible[:MAX_EVIDENCE_IMAGES]


def _evidence_images_for_pattern_ids(image_ids: list[int]) -> list[dict[str, Any]]:
    """
    Fetch image metadata rows for pattern evidence IDs.
    """
    if not image_ids:
        return []
    from pipeline.storage import get_connection

    conn = get_connection()
    placeholders = ",".join("?" * len(image_ids))
    rows = conn.execute(
        f"SELECT * FROM images WHERE id IN ({placeholders})",  # nosec B608
        image_ids,
    ).fetchall()
    conn.close()

    by_id = {row["id"]: dict(row) for row in rows}
    ordered = [by_id[i] for i in image_ids if i in by_id]
    evidence = [
        {
            "image_url": r.get("image_url"),
            "source_url": r.get("source_url"),
            "title": r.get("title"),
            "source": r.get("source"),
            "designer": r.get("designer"),
            "year": r.get("year"),
            "project": r.get("project"),
        }
        for r in ordered
    ]
    # Group each pattern's grid by store ("all Colbo, then all Flight Club")
    # instead of the retrieval round-robin interleave (#55). Display-only.
    evidence.sort(key=_evidence_sort_key)
    return evidence


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

        # ── Step 3.5: Subject filter — drop non-interiors ────────────────────────
        retrieval_log.append("filtering to retail interiors...")
        from retrieval.subject_filter import filter_to_interiors

        images = filter_to_interiors(images, client=client, max_to_check=60)
        retrieval_log.append(
            f"subject filter complete — {len(images)} confirmed interiors."
        )

        # Scope metadata pass to ≤40 candidates that will actually be extracted + displayed
        retrieval_log.append("running metadata extraction on display candidates...")
        images[:MAX_EXTRACTION_BATCH] = _extract_metadata(
            images[:MAX_EXTRACTION_BATCH], client
        )

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
    query_ids = _query_image_ids(images)
    for pattern in patterns:
        matched_ids = pattern.get("image_ids", [])
        scoped_ids = _scoped_evidence_ids(
            matched_ids, query_ids=query_ids, sub_slice=sub_slice
        )
        evidence_images = _evidence_images_for_pattern_ids(scoped_ids)
        pattern["evidence_images"] = evidence_images
        pattern["image_count"] = len(evidence_images)
        pattern.pop("image_ids", None)
        if pattern["image_count"] != len(pattern["evidence_images"]):
            raise RuntimeError(
                "pattern image_count mismatch: image_count != len(evidence_images)"
            )

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
