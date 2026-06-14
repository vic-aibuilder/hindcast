"""
scripts/backfill_metadata.py

One-time backfill: runs the LLM metadata pass over seed corpus rows
that have NULL designer/year/project, and writes results back to the DB.

Usage:
    python -m scripts.backfill_metadata

Safe to re-run — skips rows where all three fields are already populated.
"""

from __future__ import annotations

import os
from anthropic import Anthropic
from dotenv import load_dotenv

from pipeline.storage import get_connection
from retrieval.agent import _extract_metadata

load_dotenv()


def run_backfill() -> None:
    client = Anthropic(api_key=os.getenv("ANTHROPIC_API_KEY"))
    conn = get_connection()

    # Fetch rows where all three attribution fields are still NULL
    rows = conn.execute(
        """
        SELECT id, image_url, source_url, title
        FROM images
        WHERE designer IS NULL AND year IS NULL AND project IS NULL
        """
    ).fetchall()
    conn.close()

    if not rows:
        print("Nothing to backfill — all rows already have metadata.")
        return

    print(f"Backfilling {len(rows)} images...")

    # Build image dicts in the shape _extract_metadata expects
    images = [
        {
            "id": row["id"],
            "image_url": row["image_url"],
            "source_url": row["source_url"],
            "title": row["title"],
        }
        for row in rows
    ]

    # Run the same metadata pass used in the live pipeline
    enriched = _extract_metadata(images, client)

    # Write results back to the DB
    conn = get_connection()
    updated = 0
    with conn:
        for img in enriched:
            conn.execute(
                """
                UPDATE images
                SET designer = ?, year = ?, project = ?
                WHERE id = ?
                """,
                (
                    img.get("designer"),
                    img.get("year"),
                    img.get("project"),
                    img["id"],
                ),
            )
            updated += 1

    conn.close()
    print(f"Backfill complete — {updated} rows updated.")


if __name__ == "__main__":
    run_backfill()
