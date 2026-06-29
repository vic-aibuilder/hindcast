"""
Prune junk rows from schema_extractions without touching brief_cache.

Removes live-retrieval extractions that should never surface in pattern
evidence grids: off-allowlist sources, product roundups, non-image URLs.

Usage:
    python -m scripts.clean_corpus              # dry-run (default)
    python -m scripts.clean_corpus --apply      # delete rows
    python -m scripts.clean_corpus --sub-slice sneaker_streetwear --apply
"""

from __future__ import annotations

import argparse
import sys

from dotenv import load_dotenv

from pipeline.storage import get_connection, init_db
from retrieval.sources import is_evidence_eligible, is_seed_row

load_dotenv()


def _rows_to_prune(sub_slice: str | None) -> list[tuple[int, str, str, str]]:
    conn = get_connection()
    query = """
        SELECT se.image_id, se.sub_slice
        FROM schema_extractions se
    """
    params: tuple = ()
    if sub_slice:
        query += " WHERE se.sub_slice = ?"
        params = (sub_slice,)
    extraction_rows = conn.execute(query, params).fetchall()

    prune: list[tuple[int, str, str, str]] = []
    for row in extraction_rows:
        img_row = conn.execute(
            "SELECT * FROM images WHERE id = ?", (row["image_id"],)
        ).fetchone()
        if img_row is None:
            continue
        img = dict(img_row)
        if is_seed_row(img):
            continue
        if is_evidence_eligible(img, row["sub_slice"]):
            continue
        prune.append(
            (
                row["image_id"],
                row["sub_slice"],
                img.get("source") or "",
                img.get("title") or "",
            )
        )
    conn.close()
    return prune


def _delete_rows(image_ids: list[int], sub_slice: str) -> int:
    if not image_ids:
        return 0
    conn = get_connection()
    placeholders = ",".join("?" * len(image_ids))
    with conn:
        cur = conn.execute(
            f"""
            DELETE FROM schema_extractions
            WHERE sub_slice = ?
              AND image_id IN ({placeholders})
            """,  # nosec B608
            (sub_slice, *image_ids),
        )
    conn.close()
    return cur.rowcount


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--apply",
        action="store_true",
        help="Delete prunable rows (default is dry-run)",
    )
    parser.add_argument(
        "--sub-slice",
        choices=["sneaker_streetwear", "contemporary_fashion"],
        default=None,
        help="Limit to one sub-slice",
    )
    args = parser.parse_args(argv)

    init_db()
    prune = _rows_to_prune(args.sub_slice)
    if not prune:
        print("Nothing to prune.")
        return 0

    by_slice: dict[str, list[int]] = {}
    for image_id, sub_slice, source, title in prune:
        by_slice.setdefault(sub_slice, []).append(image_id)
        print(f"  [{sub_slice}] id={image_id}  {source}  {title[:70]}")

    print(f"\nTotal extractions to prune: {len(prune)}")
    if not args.apply:
        print("Dry-run only — re-run with --apply to delete.")
        return 0

    deleted = 0
    for sub_slice, ids in by_slice.items():
        deleted += _delete_rows(ids, sub_slice)
    print(f"Deleted {deleted} schema_extractions rows.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
