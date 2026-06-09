"""
Tavily search integration for Hindcast.
Primary retrieval workhorse — scoped to curated design publications only.
"""

from __future__ import annotations

import os
from tavily import TavilyClient
from dotenv import load_dotenv

load_dotenv()

# Publication domains per sub-slice — locked in PRD.md Source list
# Do not search the open web
DOMAINS = {
    "sneaker_streetwear": [
        "hypebeast.com",
        "highsnobiety.com",
        "dezeen.com",
        "sneakerfreaker.com",
    ],
    "contemporary_fashion": [
        "dezeen.com",
        "frame-web.com",
        "wallpaper.com",
        "sightunseen.com",
    ],
}

# Human-readable labels for agent prompt + UI
PUBLICATION_LABELS: dict[str, list[str]] = {
    "sneaker_streetwear": [
        "Hypebeast",
        "Highsnobiety",
        "Dezeen",
        "Sneaker Freaker",
    ],
    "contemporary_fashion": [
        "Dezeen",
        "Frame",
        "Wallpaper",
        "Sight Unseen",
    ],
}

_client = TavilyClient(api_key=os.getenv("TAVILY_API_KEY"))


def search(
    query: str,
    sub_slice: str,
    max_results: int = 10,
) -> list[dict]:
    """
    Search design publications for a given query, scoped to the sub-slice
    publication list.

    Args:
        query:       Search query string.
        sub_slice:   "sneaker_streetwear" or "contemporary_fashion".
        max_results: Max number of results to return (default 10).

    Returns:
        List of dicts with keys:
            url, title, content, source, images (list of image URLs)
    """
    if sub_slice not in DOMAINS:
        raise ValueError(
            f"Unknown sub_slice '{sub_slice}'. Must be one of: {list(DOMAINS.keys())}"
        )

    domains = DOMAINS[sub_slice]

    response = _client.search(
        query=query,
        include_domains=domains,
        max_results=max_results,
        include_images=True,
        search_depth="advanced",
    )

    results = []
    for r in response.get("results", []):
        results.append(
            {
                "url": r.get("url", ""),
                "title": r.get("title", ""),
                "content": r.get("content", ""),
                "source": _extract_domain(r.get("url", "")),
                "images": r.get("images", []),
            }
        )

    return results


def _extract_domain(url: str) -> str:
    """Extract the domain from a URL for source attribution."""
    try:
        return url.split("/")[2]
    except IndexError:
        return ""


if __name__ == "__main__":
    # Smoke test — run directly to verify Tavily key and domain scoping
    print("Testing sneaker/streetwear retrieval...")
    results = search(
        query="sneaker retail store interior NYC 2025",
        sub_slice="sneaker_streetwear",
        max_results=5,
    )
    for r in results:
        print(f"\n  [{r['source']}] {r['title']}")
        print(f"  URL: {r['url']}")
        print(f"  Images found: {len(r['images'])}")

    print("\nTesting contemporary fashion retrieval...")
    results = search(
        query="contemporary fashion retail interior NYC 2025",
        sub_slice="contemporary_fashion",
        max_results=5,
    )
    for r in results:
        print(f"\n  [{r['source']}] {r['title']}")
        print(f"  URL: {r['url']}")
        print(f"  Images found: {len(r['images'])}")
