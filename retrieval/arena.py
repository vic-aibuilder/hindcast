"""
Are.na API integration for Hindcast.
Secondary retrieval source — adds human-curated taste signal
that algorithmic search lacks.
"""

import os
import httpx
from dotenv import load_dotenv

load_dotenv()

ARENA_BASE_URL = "https://api.are.na/v2"
ARENA_ACCESS_TOKEN = os.getenv("ARENA_ACCESS_TOKEN")

# Are.na search terms per sub-slice
# These target channels likely to contain relevant curated imagery
ARENA_QUERIES = {
    "sneaker_streetwear": [
        "sneaker store interior",
        "streetwear retail design",
        "sneaker retail architecture",
    ],
    "contemporary_fashion": [
        "fashion retail interior",
        "luxury retail design",
        "contemporary fashion store",
        "quiet luxury interior",
    ],
}

_headers = {
    "Authorization": f"Bearer {ARENA_ACCESS_TOKEN}",
    "Content-Type": "application/json",
}


def search_channels(query: str, per: int = 10) -> list[dict]:
    """
    Search Are.na channels by query string.

    Returns list of channel dicts with id, title, slug.
    """
    response = httpx.get(
        f"{ARENA_BASE_URL}/search/channels",
        params={"q": query, "per": per},
        headers=_headers,
        timeout=10.0,
    )
    response.raise_for_status()
    return response.json().get("channels", [])


def get_channel_images(channel_slug: str, per: int = 20) -> list[dict]:
    """
    Retrieve image blocks from an Are.na channel.

    Returns list of dicts with image_url, source_url, title.
    """
    response = httpx.get(
        f"{ARENA_BASE_URL}/channels/{channel_slug}/contents",
        params={"per": per, "sort": "position"},
        headers=_headers,
        timeout=10.0,
    )
    response.raise_for_status()

    blocks = response.json().get("contents", [])
    images = []

    for block in blocks:
        # Only process image blocks
        if block.get("class") != "Image":
            continue

        image = block.get("image", {})
        display = image.get("display", {})
        original = image.get("original", {})

        image_url = display.get("url") or original.get("url")

        if not image_url:
            continue

        images.append(
            {
                "image_url": image_url,
                "source_url": (block.get("source") or {}).get("url", ""),
                "title": block.get("title", ""),
                "channel": channel_slug,
                "arena_id": block.get("id"),
            }
        )

    return images


def search(sub_slice: str, max_images: int = 20) -> list[dict]:
    """
    Full Are.na search for a given sub-slice.
    Searches relevant queries, retrieves image blocks from returned channels.

    Args:
        sub_slice:   "sneaker_streetwear" or "contemporary_fashion".
        max_images:  Max total images to return across all channels.

    Returns:
        List of image dicts with image_url, source_url, title, channel.
    """
    if sub_slice not in ARENA_QUERIES:
        raise ValueError(
            f"Unknown sub_slice '{sub_slice}'. "
            f"Must be one of: {list(ARENA_QUERIES.keys())}"
        )

    queries = ARENA_QUERIES[sub_slice]
    all_images = []
    seen_urls = set()

    for query in queries:
        if len(all_images) >= max_images:
            break

        channels = search_channels(query, per=3)

        for channel in channels:
            if len(all_images) >= max_images:
                break

            slug = channel.get("slug", "")
            if not slug:
                continue

            try:
                images = get_channel_images(slug, per=10)
                for img in images:
                    if img["image_url"] not in seen_urls:
                        seen_urls.add(img["image_url"])
                        all_images.append(img)
            except httpx.HTTPError:
                # Skip channels that fail — don't let one bad channel
                # break the whole retrieval pass
                continue

    return all_images[:max_images]


if __name__ == "__main__":
    # Smoke test — run directly to verify Are.na token
    print("Testing Are.na retrieval — sneaker/streetwear...")
    images = search("sneaker_streetwear", max_images=10)
    print(f"  Returned {len(images)} images")
    for img in images[:3]:
        print(f"  [{img['channel']}] {img['title']}")
        print(f"  {img['image_url']}")

    print("\nTesting Are.na retrieval — contemporary fashion...")
    images = search("contemporary_fashion", max_images=10)
    print(f"  Returned {len(images)} images")
    for img in images[:3]:
        print(f"  [{img['channel']}] {img['title']}")
        print(f"  {img['image_url']}")
