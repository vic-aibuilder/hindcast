"""
Hindcast retrieval agent.

A Claude tool-use loop that reads a brief, searches across Tavily and Are.na,
self-assesses the returned corpus, refines if needed, and returns a
consolidated set of images with metadata.

Loop: observe → decide → act → repeat (hard ceiling: 4 iterations).
Agent reasoning is logged at each step for surfacing in the UI loading state.
"""

from __future__ import annotations

import json
import os
from collections import Counter, defaultdict
from itertools import zip_longest
from urllib.parse import urlsplit, urlunsplit

from anthropic import Anthropic
from dotenv import load_dotenv

from retrieval.tavily import search as tavily_search, PUBLICATION_LABELS
from retrieval.arena import search as arena_search

load_dotenv()


MODEL = "claude-sonnet-4-6"
MAX_ITERATIONS = 4

# Cap on images kept from any single source page. Listicle/slideshow pages can
# return ~100 image URLs each, which flood the corpus and the UI with shots from
# one article. Capping keeps the corpus diverse across pages.
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


def _consolidate_images(all_images: list[dict]) -> list[dict]:
    """Dedupe, cap per source page, and interleave a raw image list.

    1. Dedupe by normalized URL — CDN endpoints serve one asset at many sizes
       (e.g. .../foo.jpg?w=1080 vs ?w=960): distinct URLs, identical pictures.
    2. Cap images per source page (MAX_IMAGES_PER_SOURCE) so a single listicle
       can't flood the corpus.
    3. Interleave by source page (round-robin) so consecutive images come from
       different articles — keeps the UI's first screen and the extraction
       sample varied instead of showing runs from one page.
    """
    seen: set[str] = set()
    per_source: Counter[str] = Counter()
    kept: list[dict] = []
    for img in all_images:
        url = img.get("image_url", "")
        if not url:
            continue
        key = _normalize_image_url(url)
        if key in seen:
            continue
        source_page = img.get("source_url", "") or key
        if per_source[source_page] >= MAX_IMAGES_PER_SOURCE:
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


# ── Tool definitions exposed to the agent ────────────────────────────────────

TOOLS = [
    {
        "name": "tavily_search",
        "description": (
            "Search curated design publications (Hypebeast, Dezeen, Wallpaper, "
            "Frame, Highsnobiety, Sight Unseen, ArchDaily) for retail interior "
            "images relevant to the brief. Scoped to the sub-slice publication "
            "list — does not search the open web. Use multiple targeted queries "
            "to build a representative corpus."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": (
                        "Search query. Be specific — include material descriptors, "
                        "spatial terms, brand context, and NYC where relevant. "
                        "Example: 'Nike flagship store interior NYC concrete 2025'"
                    ),
                },
                "sub_slice": {
                    "type": "string",
                    "enum": ["sneaker_streetwear", "contemporary_fashion"],
                    "description": "Sub-slice to scope publication list.",
                },
                "max_results": {
                    "type": "integer",
                    "description": "Max results to return. Default 10.",
                    "default": 10,
                },
            },
            "required": ["query", "sub_slice"],
        },
    },
    {
        "name": "arena_search",
        "description": (
            "Search Are.na for human-curated design imagery relevant to the "
            "sub-slice. Adds taste-signal that algorithmic search lacks. "
            "Use once per query — Are.na is secondary to Tavily."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "sub_slice": {
                    "type": "string",
                    "enum": ["sneaker_streetwear", "contemporary_fashion"],
                    "description": "Sub-slice to use for Are.na channel queries.",
                },
                "max_images": {
                    "type": "integer",
                    "description": "Max images to return. Default 20.",
                    "default": 20,
                },
            },
            "required": ["sub_slice"],
        },
    },
]


# ── System prompt ─────────────────────────────────────────────────────────────


def _system_prompt(sub_slice: str) -> str:
    slice_label = (
        "sneaker and streetwear retail"
        if sub_slice == "sneaker_streetwear"
        else "contemporary fashion retail (elevated/designer end — The Row, "
        "Toteme, Khaite, Acne; warm-minimal / quiet luxury)"
    )
    pubs = ", ".join(PUBLICATION_LABELS.get(sub_slice, []))
    return f"""You are the retrieval agent for Hindcast, an internal tool for
Snarkitecture that maps visual saturation in retail design.

Your job is to build a representative corpus of images for a design brief
focused on {slice_label} in New York City (all five boroughs), 2025–present.

PUBLICATION SCOPE (hard limit — Tavily is scoped to these only):
{pubs}

You have two tools:
- tavily_search: searches the publication list above. Your primary workhorse.
- arena_search: searches Are.na for human-curated imagery. Use once as a supplement.

LOOP BEHAVIOR:
1. Read the brief. Plan your search strategy.
2. Execute searches. Start broad, then refine toward gaps.
3. Self-assess: Is the corpus representative? Are there style or context gaps?
   Is there off-topic noise?
4. Refine and search again if needed.
5. Stop when the corpus is sufficient OR you have reached the iteration limit.

SEARCH STRATEGY RULES:
- Run 2–4 Tavily queries per iteration, varying descriptors
  (material, form, brand, neighborhood, fixture type).
- Use Are.na once — it is a taste layer, not a workhorse.
- Bias toward NYC results. If results skew non-NYC, add "NYC" or
  specific borough names to your query.
- Prioritize 2025 coverage. Add "2025" or "2026" to queries when helpful.
- Stop early if you have 25+ relevant images and no significant gaps.

LOG your reasoning at each step — what you searched, what came back,
what gaps remain, what you'll do next. This log surfaces in the UI."""


# ── Tool execution ────────────────────────────────────────────────────────────


def _execute_tool(tool_name: str, tool_input: dict) -> tuple[str, list[dict]]:
    """
    Execute a tool call and return (log_message, images).
    Images is a list of dicts with url, title, source, etc.
    """
    if tool_name == "tavily_search":
        results = tavily_search(
            query=tool_input["query"],
            sub_slice=tool_input["sub_slice"],
            max_results=tool_input.get("max_results", 10),
        )
        # Flatten image URLs out of Tavily results
        images = []
        for r in results:
            for img_url in r.get("images", []):
                images.append(
                    {
                        "image_url": img_url,
                        "source_url": r["url"],
                        "title": r["title"],
                        "source": r["source"],
                        "retrieval_method": "tavily",
                    }
                )
            # Also include the page URL itself as a potential image source
            if not r.get("images"):
                images.append(
                    {
                        "image_url": r["url"],
                        "source_url": r["url"],
                        "title": r["title"],
                        "source": r["source"],
                        "retrieval_method": "tavily",
                    }
                )

        log = (
            f"tavily_search('{tool_input['query']}') → "
            f"{len(results)} results, {len(images)} images"
        )
        if results:
            domains = Counter(r["source"] for r in results)
            log += f" [sources: {', '.join(f'{d}({n})' for d, n in domains.most_common())}]"
        return log, images

    elif tool_name == "arena_search":
        images = arena_search(
            sub_slice=tool_input["sub_slice"],
            max_images=tool_input.get("max_images", 20),
        )
        # Normalize Are.na results to match Tavily format
        normalized = []
        for img in images:
            normalized.append(
                {
                    "image_url": img["image_url"],
                    "source_url": img.get("source_url", ""),
                    "title": img.get("title", ""),
                    "source": "are.na",
                    "retrieval_method": "arena",
                    "channel": img.get("channel", ""),
                }
            )
        log = f"arena_search({tool_input['sub_slice']}) → {len(normalized)} images"
        return log, normalized

    else:
        return f"Unknown tool: {tool_name}", []


# ── Main agent loop ───────────────────────────────────────────────────────────


def run(brief: str, sub_slice: str, client: Anthropic | None = None) -> dict:
    """
    Run the retrieval agent for a given brief and sub-slice.

    Args:
        brief:     Free-text design brief from the user.
        sub_slice: "sneaker_streetwear" or "contemporary_fashion".

    Returns:
        {
            "images":   list of image dicts (url, source, title, etc.),
            "log":      list of reasoning strings for UI display,
            "iterations": int,
        }
    """
    if client is None:
        client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))

    messages = [
        {
            "role": "user",
            "content": (
                f"Brief: {brief}\n\n"
                f"Sub-slice: {sub_slice}\n"
                f"City: New York City, all five boroughs\n"
                f"Time window: 2025–present\n\n"
                "Build a representative image corpus for this brief. "
                f"You have a maximum of {MAX_ITERATIONS} iterations."
            ),
        }
    ]

    all_images = []
    reasoning_log = []
    iteration = 0

    while iteration < MAX_ITERATIONS:
        iteration += 1
        reasoning_log.append(f"— iteration {iteration} of {MAX_ITERATIONS} —")

        response = client.messages.create(
            model=MODEL,
            max_tokens=4096,
            system=_system_prompt(sub_slice),
            tools=TOOLS,
            messages=messages,
        )

        # Collect any text reasoning Claude produced
        for block in response.content:
            if block.type == "text" and block.text.strip():
                reasoning_log.append(block.text.strip())

        # If Claude is done (no tool calls), exit the loop
        if response.stop_reason == "end_turn":
            reasoning_log.append("Agent: corpus sufficient — stopping.")
            break

        # Process tool calls
        tool_results = []
        made_tool_call = False

        for block in response.content:
            if block.type != "tool_use":
                continue

            made_tool_call = True
            log_msg, images = _execute_tool(block.name, block.input)
            reasoning_log.append(log_msg)
            all_images.extend(images)

            tool_results.append(
                {
                    "type": "tool_result",
                    "tool_use_id": block.id,
                    "content": json.dumps(
                        {
                            "images_retrieved": len(images),
                            "log": log_msg,
                        }
                    ),
                }
            )

        if not made_tool_call:
            break

        # Append assistant response and tool results to message history
        messages.append({"role": "assistant", "content": response.content})
        messages.append({"role": "user", "content": tool_results})

        # If max iterations reached, stop
        if iteration >= MAX_ITERATIONS:
            reasoning_log.append(
                f"Agent: reached {MAX_ITERATIONS}-iteration ceiling — stopping."
            )
            break

    unique_images = _consolidate_images(all_images)

    reasoning_log.append(
        f"Retrieval complete: {len(unique_images)} unique images "
        f"across {iteration} iteration(s)."
    )

    return {
        "images": unique_images,
        "log": reasoning_log,
        "iterations": iteration,
    }


if __name__ == "__main__":
    # Smoke test — runs a real agent loop against both sub-slices
    print("=" * 60)
    print("SMOKE TEST — Sneaker/Streetwear")
    print("=" * 60)

    result = run(
        brief="NYC sneaker retail store interiors, concrete and steel, 2025",
        sub_slice="sneaker_streetwear",
    )

    print("\nReasoning log:")
    for line in result["log"]:
        print(f"  {line}")

    print(f"\nImages retrieved: {len(result['images'])}")
    print(f"Iterations used: {result['iterations']}")
    for img in result["images"][:5]:
        print(f"  [{img['source']}] {img['title'][:60]}")
        print(f"  {img['image_url'][:80]}")
