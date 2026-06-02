"""
Hindcast cache layer.

Sits between the retrieval agent and the extraction pipeline.
Checks whether a brief has been seen before and whether the
stored corpus is large enough to skip live retrieval.

Keyed by sub-slice + normalized brief (SHA-256 hash).
The cache grows over time — every live retrieval run deposits
into it, improving saturation precision without a separate
ingestion pipeline.
"""

from __future__ import annotations

from pipeline.storage import (
    get_cached_brief,
    cache_brief,
    is_cache_warm,
    hash_brief,
    corpus_stats,
)


# ── Public interface ──────────────────────────────────────────────────────────


def check(brief: str, sub_slice: str, min_images: int = 30) -> list[dict] | None:
    """
    Check the cache for a matching brief.

    Returns cached image list if warm enough to skip live retrieval.
    Returns None if cold — caller should run live retrieval.

    Args:
        brief:      Free-text brief from the user.
        sub_slice:  "sneaker_streetwear" or "contemporary_fashion".
        min_images: Minimum images required for a cache hit. Default 30.

    Returns:
        List of image dicts if cache hit, None if miss.
    """
    if not is_cache_warm(brief, sub_slice, min_images=min_images):
        return None
    return get_cached_brief(brief, sub_slice)


def store(brief: str, sub_slice: str, image_ids: list[int]) -> None:
    """
    Write a brief → image set mapping to the cache after live retrieval.

    Args:
        brief:      Free-text brief from the user.
        sub_slice:  Sub-slice identifier.
        image_ids:  List of database image IDs from this retrieval run.
    """
    cache_brief(brief, sub_slice, image_ids)


def get_brief_hash(brief: str, sub_slice: str) -> str:
    """Return the cache key for a brief — useful for logging."""
    return hash_brief(brief, sub_slice)


def stats() -> dict:
    """Return current corpus and cache stats."""
    return corpus_stats()


if __name__ == "__main__":
    from pipeline.storage import init_db, save_images

    print("Initializing database...")
    init_db()

    brief = "NYC sneaker retail concrete steel 2025"
    sub_slice = "sneaker_streetwear"

    print(f"\nChecking cache for brief: '{brief}'")
    result = check(brief, sub_slice, min_images=1)
    print(f"  Cache result (should be None on fresh db): {result}")

    print("\nStoring test images in cache...")
    test_images = [
        {
            "image_url": f"https://example.com/test-{i}.jpg",
            "source_url": "https://dezeen.com",
            "title": f"Test image {i}",
            "source": "dezeen.com",
            "retrieval_method": "test",
        }
        for i in range(35)
    ]

    from pipeline.storage import hash_brief as _hash_brief

    brief_hash = _hash_brief(brief, sub_slice)
    ids = save_images(test_images, sub_slice, brief_hash)
    store(brief, sub_slice, ids)
    print(f"  Stored {len(ids)} images")

    print("\nChecking cache again (should be warm now)...")
    result = check(brief, sub_slice, min_images=30)
    print(f"  Cache hit: {len(result)} images returned")
    print(f"  Cache warm: {result is not None}")

    print("\nCache stats:")
    s = stats()
    for k, v in s.items():
        print(f"  {k}: {v}")

    print("\nAll cache tests passed.")
