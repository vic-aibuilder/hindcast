"""
End-to-end Hindcast pipeline runner — extractor → synthesizer.
Usage: python -m scripts.run_e2e
"""

from __future__ import annotations

import json
import sys
import textwrap
import time

from src.extractor import extract
from src.synthesizer import synthesize

URLS = [
    "https://images.unsplash.com/photo-1556742049-0cfed4f6a45d?w=800",
    "https://images.unsplash.com/photo-1441986300917-64674bd600d8?w=800",
    "https://images.unsplash.com/photo-1555529669-e69e7aa0ba9a?w=800",
    "https://images.unsplash.com/photo-1560472355-536de3962603?w=800",
    "https://images.unsplash.com/photo-1567401893414-76b7b1e5a7a5?w=800",
    "https://images.unsplash.com/photo-1600585154340-be6161a56a0c?w=800",
    "https://images.unsplash.com/photo-1487754180451-c456f719a1fc?w=800",
    "https://images.unsplash.com/photo-1534528741775-53994a69daeb?w=800",
    "https://images.unsplash.com/photo-1493809842364-78817add7ffb?w=800",
    "https://images.unsplash.com/photo-1524758631624-e2822e304c36?w=800",
]

BRIEF = "sneaker and streetwear retail flagship spaces in New York City, 2025."
SUB_SLICE = "sneaker_streetwear"


def run() -> None:
    print("=" * 60)
    print("HINDCAST — END-TO-END PIPELINE TEST")
    print(f"Corpus: {len(URLS)} images  |  Sub-slice: {SUB_SLICE}")
    print("=" * 60)

    # ── Phase 1: Extract ────────────────────────────────────────
    print("\nPHASE 1 — EXTRACTION\n")
    extractions: list[dict] = []
    failed: list[str] = []

    for i, url in enumerate(URLS, 1):
        label = url.split("/")[-1].replace("_dezeen_2364_col_0.jpg", "")
        print(f"  [{i:02d}/{len(URLS)}] {label}")
        t0 = time.perf_counter()
        try:
            result = extract(url)
            elapsed = time.perf_counter() - t0
            extractions.append(result)
            print(f"         ✓  {elapsed:.1f}s")
        except Exception as exc:  # noqa: BLE001
            elapsed = time.perf_counter() - t0
            failed.append(url)
            print(f"         ✗  {elapsed:.1f}s  ERROR: {exc}", file=sys.stderr)

    print(f"\n  Extracted: {len(extractions)}/{len(URLS)}")
    if failed:
        print(f"  Failed:    {len(failed)}", file=sys.stderr)

    if not extractions:
        print("No extractions succeeded — cannot synthesize.", file=sys.stderr)
        sys.exit(1)

    # ── Print raw extractions ───────────────────────────────────
    print("\n" + "─" * 60)
    print("RAW EXTRACTIONS (JSON)")
    print("─" * 60)
    print(json.dumps(extractions, indent=2))

    # ── Phase 2: Synthesize ─────────────────────────────────────
    print("\n" + "=" * 60)
    print("PHASE 2 — SYNTHESIS")
    print(f"Brief: {BRIEF}")
    print("=" * 60 + "\n")

    t0 = time.perf_counter()
    patterns = synthesize(extractions, BRIEF, SUB_SLICE)
    elapsed = time.perf_counter() - t0
    print(f"Synthesis completed in {elapsed:.1f}s\n")

    # ── Print patterns ──────────────────────────────────────────
    print("─" * 60)
    print(f"SATURATION PATTERNS  ({len(patterns)} identified)")
    print("─" * 60)

    for n, p in enumerate(patterns, 1):
        print(f"\n[{n}]  {p['title']}")
        print(f"     Images: {p['image_count']}/{len(extractions)}")
        print()
        wrapped = textwrap.fill(
            p["description"],
            width=72,
            initial_indent="     ",
            subsequent_indent="     ",
        )
        print(wrapped)
        print()
        terms = ", ".join(p["dominant_terms"])
        term_lines = textwrap.fill(
            terms,
            width=68,
            initial_indent="     Terms: ",
            subsequent_indent="            ",
        )
        print(term_lines)

    print("\n" + "─" * 60)
    print("SYNTHESIS JSON (full)")
    print("─" * 60)
    print(json.dumps(patterns, indent=2))


if __name__ == "__main__":
    run()
