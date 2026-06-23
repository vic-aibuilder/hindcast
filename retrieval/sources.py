"""
Publication allowlist and junk-image heuristics.

Shared by the corpus cleaner, evidence assembly, and retrieval consolidation.
"""

from __future__ import annotations

import re
from urllib.parse import urlsplit

from retrieval.consolidate import _looks_like_interior
from retrieval.tavily import DOMAINS

_IMAGE_EXTENSIONS = (".jpg", ".jpeg", ".png", ".webp", ".gif", ".avif")

# Title patterns that indicate product roundups, not store interiors.
_ROUNDUP_TITLE_RE = re.compile(
    r"(?i)"
    r"(\bbest\b.{0,40}\b(releases?|sneakers?|kicks)\b"
    r"|\btop\s+\d+\b"
    r"|\broundup\b"
    r"|\bgift\s+guide\b"
    r"|\brelease\s+dates?\b)"
)

# Hosts that never belong in an interior evidence grid.
_BLOCKED_HOSTS = frozenset(
    {
        "pinterest.com",
        "www.pinterest.com",
        "instagram.com",
        "www.instagram.com",
        "youtube.com",
        "www.youtube.com",
        "youtu.be",
    }
)


def normalize_source_domain(source: str) -> str:
    """Strip www. prefix so allowlist checks match Tavily attribution."""
    domain = (source or "").strip().lower()
    if domain.startswith("www."):
        return domain[4:]
    return domain


def allowed_domains(sub_slice: str) -> frozenset[str]:
    """Normalized publication domains for a sub-slice."""
    if sub_slice not in DOMAINS:
        raise ValueError(f"Unknown sub_slice: {sub_slice!r}")
    return frozenset(normalize_source_domain(d) for d in DOMAINS[sub_slice])


def is_seed_row(row: dict) -> bool:
    """Seed-corpus rows are kept; loader rows often have null retrieval_method."""
    method = row.get("retrieval_method")
    return method in (None, "", "seed")


def looks_like_image_url(url: str) -> bool:
    """
    Return True when *url* plausibly points at image bytes.

    Rejects article/page URLs that Tavily sometimes passes as image_url when
    include_images returns nothing.
    """
    if not url:
        return False
    try:
        parts = urlsplit(url)
    except ValueError:
        return False
    host = parts.netloc.lower()
    if host in _BLOCKED_HOSTS or host.endswith(".pinterest.com"):
        return False
    path = parts.path.lower()
    if path.endswith(_IMAGE_EXTENSIONS):
        return True
    # Common publication CDNs without file extensions in the path tail.
    return "/wp-content/uploads/" in path or "/cdn/shop/files/" in path


def is_roundup_title(title: str | None) -> bool:
    return bool(title and _ROUNDUP_TITLE_RE.search(title))


def is_evidence_eligible(row: dict, sub_slice: str) -> bool:
    """
    Return True if an images-table row is eligible for pattern evidence grids.

    Seed rows always pass. Live rows must be on the publication allowlist,
    look like real image URLs, and not be obvious product roundups.
    """
    if is_seed_row(row):
        return True

    source = normalize_source_domain(row.get("source") or "")
    if source not in allowed_domains(sub_slice):
        return False
    if is_roundup_title(row.get("title")):
        return False
    if not _looks_like_interior(row):
        return False
    image_url = row.get("image_url") or ""
    if not looks_like_image_url(image_url):
        return False
    return True
