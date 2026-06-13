"""
Image-list consolidation: dedupe + per-source cap + interleave.

Shared by live retrieval (``retrieval.agent``) and the seed corpus loader
(``corpus.seed_loader``). Pulled out of ``retrieval.agent`` so the loader can
reuse the same logic without importing the agent module, which constructs an
Anthropic client and loads ``.env`` at import time.

The per-source cap is a parameter, not a fixed constant: live retrieval uses the
strict default (``MAX_IMAGES_PER_SOURCE``) because open-web listicles can return
~100 URLs from one page, while the hand-curated seed corpus passes a higher cap
since it carries no flood risk.
"""

from __future__ import annotations

from collections import Counter, defaultdict
from itertools import zip_longest
from urllib.parse import urlsplit, urlunsplit

# URL path segments that reliably indicate product/editorial content
# rather than retail interior photography
_PRODUCT_URL_PATTERNS = (
    "/releases/",
    "/products/",
    "/release-date/",
    "/buy/",
    "/shop/",
    "/review/",
    "/best-",
    "/top-",
    "/roundup/",
    "/gift-guide/",
    "/collab/",
    "/collection/",
    "/lookbook/",
)


def _looks_like_interior(img: dict) -> bool:
    """
    Fast heuristic — returns False if the image URL or source URL
    strongly suggests product photography rather than a retail interior.
    No vision call — purely string-based.
    """
    url = (img.get("source_url") or img.get("image_url") or "").lower()
    return not any(pattern in url for pattern in _PRODUCT_URL_PATTERNS)


# Cap on images kept from any single source page. Listicle/slideshow pages can
# return ~100 image URLs each, which flood the corpus and the UI with shots from
# one article. Capping keeps the corpus diverse across pages. This is the
# live-retrieval default; callers may override via ``max_per_source``.
MAX_IMAGES_PER_SOURCE = 6


def _normalize_image_url(url: str) -> str:
    """Return a dedup key for an image URL by dropping the query string.

    Image CDNs serve one asset at many sizes via query params
    (e.g. .../foo.jpg?w=1080 vs ?w=960) — same picture, different URL.
    Stripping the query collapses those variants; the path (which carries
    the asset identity, e.g. foo-tw.jpg vs foo-000.jpg) is preserved.
    """
    try:
        parts = urlsplit(url)
        return urlunsplit((parts.scheme, parts.netloc, parts.path, "", ""))
    except ValueError:
        return url


def _consolidate_images(
    all_images: list[dict], max_per_source: int = MAX_IMAGES_PER_SOURCE
) -> list[dict]:
    """Dedupe, cap per source page, and interleave a raw image list.

    0. Pre-filter obvious product/editorial URLs before dedup.
    1. Dedupe by normalized URL.
    2. Cap images per source page.
    3. Interleave by source page (round-robin).
    """
    # Step 0 — drop obvious non-interior URLs
    candidates = [img for img in all_images if _looks_like_interior(img)]

    seen: set[str] = set()
    per_source: Counter[str] = Counter()
    kept: list[dict] = []

    for img in candidates:
        url = img.get("image_url", "")
        if not url:
            continue
        key = _normalize_image_url(url)
        if key in seen:
            continue
        source_page = img.get("source_url", "") or key
        if per_source[source_page] >= max_per_source:
            continue
        seen.add(key)
        per_source[source_page] += 1
        kept.append(img)

    groups: dict[str, list[dict]] = defaultdict(list)
    for img in kept:
        groups[img.get("source_url") or img.get("image_url", "")].append(img)

    return [
        img for row in zip_longest(*groups.values()) for img in row if img is not None
    ]
