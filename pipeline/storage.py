"""
Hindcast storage layer.

SQLite database for the image corpus, schema extractions, and brief cache.
Three tables:
  - images:            every retrieved image with metadata
  - schema_extractions: per-image schema attributes (one row per dimension)
  - brief_cache:       normalized brief → image set mapping for cache lookups

SQLite is appropriate for prototype scale. Swap for PostgreSQL post-demo
if query volume grows.
"""

from __future__ import annotations
import hashlib
import json
import os
import sqlite3
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

# Database lives at the project root
DB_PATH = Path(os.getenv("DB_PATH", "hindcast.db"))


# ── Connection ────────────────────────────────────────────────────────────────

def get_connection() -> sqlite3.Connection:
    """Return a database connection with row factory set."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")  # better concurrent read performance
    return conn


# ── Schema bootstrap ──────────────────────────────────────────────────────────

def init_db() -> None:
    """
    Create all tables if they don't already exist.
    Safe to call on every startup — uses CREATE TABLE IF NOT EXISTS.
    """
    conn = get_connection()
    with conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS images (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                image_url       TEXT    NOT NULL UNIQUE,
                source_url      TEXT,
                title           TEXT,
                source          TEXT,
                sub_slice       TEXT    NOT NULL,
                retrieval_method TEXT,
                channel         TEXT,
                brief_hash      TEXT,
                created_at      TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS schema_extractions (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                image_id    INTEGER NOT NULL REFERENCES images(id),
                dimension   TEXT    NOT NULL,
                value       TEXT    NOT NULL,
                sub_slice   TEXT    NOT NULL,
                created_at  TEXT    NOT NULL
            );

            CREATE TABLE IF NOT EXISTS brief_cache (
                id              INTEGER PRIMARY KEY AUTOINCREMENT,
                brief_hash      TEXT    NOT NULL UNIQUE,
                normalized_brief TEXT   NOT NULL,
                sub_slice       TEXT    NOT NULL,
                image_ids       TEXT    NOT NULL,
                created_at      TEXT    NOT NULL,
                last_accessed   TEXT    NOT NULL
            );

            CREATE INDEX IF NOT EXISTS idx_images_sub_slice
                ON images(sub_slice);

            CREATE INDEX IF NOT EXISTS idx_images_brief_hash
                ON images(brief_hash);

            CREATE INDEX IF NOT EXISTS idx_extractions_image_id
                ON schema_extractions(image_id);

            CREATE INDEX IF NOT EXISTS idx_extractions_dimension_value
                ON schema_extractions(dimension, value);

            CREATE INDEX IF NOT EXISTS idx_cache_brief_hash
                ON brief_cache(brief_hash);
        """)
    conn.close()


# ── Brief hashing ─────────────────────────────────────────────────────────────

def normalize_brief(brief: str, sub_slice: str) -> str:
    """
    Normalize a brief for consistent cache key generation.
    Lowercase, strip punctuation, sort words, prepend sub_slice.
    """
    import re
    cleaned = re.sub(r"[^\w\s]", "", brief.lower())
    words = sorted(cleaned.split())
    return f"{sub_slice}::{' '.join(words)}"


def hash_brief(brief: str, sub_slice: str) -> str:
    """Return a SHA-256 hash of the normalized brief + sub_slice."""
    normalized = normalize_brief(brief, sub_slice)
    return hashlib.sha256(normalized.encode()).hexdigest()


# ── Image storage ─────────────────────────────────────────────────────────────

def save_images(images: list[dict], sub_slice: str, brief_hash: str) -> list[int]:
    """
    Insert images into the images table.
    Skips duplicates (image_url is UNIQUE).

    Returns list of inserted row IDs (excludes skipped duplicates).
    """
    conn = get_connection()
    now = datetime.utcnow().isoformat()
    inserted_ids = []

    with conn:
        for img in images:
            try:
                cursor = conn.execute(
                    """
                    INSERT INTO images
                        (image_url, source_url, title, source,
                         sub_slice, retrieval_method, channel,
                         brief_hash, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        img.get("image_url", ""),
                        img.get("source_url", ""),
                        img.get("title", ""),
                        img.get("source", ""),
                        sub_slice,
                        img.get("retrieval_method", ""),
                        img.get("channel", ""),
                        brief_hash,
                        now,
                    ),
                )
                inserted_ids.append(cursor.lastrowid)
            except sqlite3.IntegrityError:
                # Duplicate image_url — skip silently
                pass

    conn.close()
    return inserted_ids


def get_images_for_brief(brief_hash: str) -> list[dict]:
    """
    Retrieve all images associated with a brief hash.
    Used by the cache layer to serve repeat queries.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM images WHERE brief_hash = ?",
        (brief_hash,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def get_images_by_sub_slice(sub_slice: str, limit: int = 500) -> list[dict]:
    """
    Retrieve images for a sub-slice regardless of brief.
    Used for saturation scoring across the full corpus.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT * FROM images WHERE sub_slice = ? LIMIT ?",
        (sub_slice, limit),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


# ── Schema extraction storage ─────────────────────────────────────────────────

def save_extraction(image_id: int, schema: dict, sub_slice: str) -> None:
    """
    Save Claude's schema extraction for a single image.

    schema is a flat dict of {dimension: value} pairs,
    e.g. {"material": "concrete", "form": "rectilinear", ...}
    """
    conn = get_connection()
    now = datetime.utcnow().isoformat()

    with conn:
        for dimension, value in schema.items():
            # value may be a list (multiple tags) or a string
            if isinstance(value, list):
                value = json.dumps(value)
            conn.execute(
                """
                INSERT INTO schema_extractions
                    (image_id, dimension, value, sub_slice, created_at)
                VALUES (?, ?, ?, ?, ?)
                """,
                (image_id, dimension, str(value), sub_slice, now),
            )
    conn.close()


def get_extractions_for_image(image_id: int) -> dict:
    """
    Retrieve all schema dimensions for a single image.
    Returns a flat dict of {dimension: value}.
    """
    conn = get_connection()
    rows = conn.execute(
        "SELECT dimension, value FROM schema_extractions WHERE image_id = ?",
        (image_id,),
    ).fetchall()
    conn.close()
    return {row["dimension"]: row["value"] for row in rows}


def get_all_extractions_for_sub_slice(sub_slice: str) -> list[dict]:
    """
    Retrieve all schema extractions for a sub-slice.
    Returns list of {image_id, dimension, value} dicts.
    Used by the scoring layer to compute saturation frequencies.
    """
    conn = get_connection()
    rows = conn.execute(
        """
        SELECT e.image_id, e.dimension, e.value
        FROM schema_extractions e
        JOIN images i ON i.id = e.image_id
        WHERE i.sub_slice = ?
        """,
        (sub_slice,),
    ).fetchall()
    conn.close()
    return [dict(row) for row in rows]


def image_has_extraction(image_id: int) -> bool:
    """Check whether an image has already been extracted."""
    conn = get_connection()
    row = conn.execute(
        "SELECT 1 FROM schema_extractions WHERE image_id = ? LIMIT 1",
        (image_id,),
    ).fetchone()
    conn.close()
    return row is not None


# ── Brief cache ───────────────────────────────────────────────────────────────

def cache_brief(
    brief: str,
    sub_slice: str,
    image_ids: list[int],
) -> None:
    """
    Write a brief → image set mapping to the cache.
    Called after a live retrieval run completes.
    """
    brief_hash = hash_brief(brief, sub_slice)
    normalized = normalize_brief(brief, sub_slice)
    now = datetime.utcnow().isoformat()

    conn = get_connection()
    with conn:
        conn.execute(
            """
            INSERT INTO brief_cache
                (brief_hash, normalized_brief, sub_slice,
                 image_ids, created_at, last_accessed)
            VALUES (?, ?, ?, ?, ?, ?)
            ON CONFLICT(brief_hash) DO UPDATE SET
                image_ids     = excluded.image_ids,
                last_accessed = excluded.last_accessed
            """,
            (
                brief_hash,
                normalized,
                sub_slice,
                json.dumps(image_ids),
                now,
                now,
            ),
        )
    conn.close()


def get_cached_brief(brief: str, sub_slice: str) -> list[dict] | None:
    """
    Check the cache for a matching brief.

    Returns list of image dicts if cache hit, None if miss.
    Also updates last_accessed timestamp on hit.
    """
    brief_hash = hash_brief(brief, sub_slice)
    conn = get_connection()

    row = conn.execute(
        "SELECT * FROM brief_cache WHERE brief_hash = ?",
        (brief_hash,),
    ).fetchone()

    if not row:
        conn.close()
        return None

    # Update last accessed
    with conn:
        conn.execute(
            "UPDATE brief_cache SET last_accessed = ? WHERE brief_hash = ?",
            (datetime.utcnow().isoformat(), brief_hash),
        )

    image_ids = json.loads(row["image_ids"])
    conn.close()

    # Fetch the actual image rows
    if not image_ids:
        return None

    conn = get_connection()
    placeholders = ",".join("?" * len(image_ids))
    rows = conn.execute(
        f"SELECT * FROM images WHERE id IN ({placeholders})",
        image_ids,
    ).fetchall()
    conn.close()

    return [dict(r) for r in rows] if rows else None


def is_cache_warm(brief: str, sub_slice: str, min_images: int = 30) -> bool:
    """
    Return True if the cache has enough images for this brief
    to skip live retrieval entirely.
    """
    cached = get_cached_brief(brief, sub_slice)
    return cached is not None and len(cached) >= min_images


# ── Stats (useful for debugging and demo prep) ────────────────────────────────

def corpus_stats() -> dict:
    """
    Return a summary of the current corpus state.
    Useful for checking pre-warm progress before Demo Day.
    """
    conn = get_connection()

    total_images = conn.execute(
        "SELECT COUNT(*) FROM images"
    ).fetchone()[0]

    by_slice = conn.execute(
        "SELECT sub_slice, COUNT(*) as count FROM images GROUP BY sub_slice"
    ).fetchall()

    total_extractions = conn.execute(
        "SELECT COUNT(*) FROM schema_extractions"
    ).fetchone()[0]

    cached_briefs = conn.execute(
        "SELECT COUNT(*) FROM brief_cache"
    ).fetchone()[0]

    conn.close()

    return {
        "total_images": total_images,
        "by_slice": {row["sub_slice"]: row["count"] for row in by_slice},
        "total_extractions": total_extractions,
        "cached_briefs": cached_briefs,
        "db_path": str(DB_PATH),
    }


if __name__ == "__main__":
    # Smoke test — initializes the database and runs basic read/write checks
    print("Initializing database...")
    init_db()

    print("Testing image save...")
    test_images = [
        {
            "image_url": "https://example.com/test-image-1.jpg",
            "source_url": "https://dezeen.com/test-article",
            "title": "Test sneaker store NYC",
            "source": "dezeen.com",
            "retrieval_method": "tavily",
        },
        {
            "image_url": "https://example.com/test-image-2.jpg",
            "source_url": "https://hypebeast.com/test-article",
            "title": "Test streetwear interior",
            "source": "hypebeast.com",
            "retrieval_method": "tavily",
        },
    ]

    test_hash = hash_brief("NYC sneaker retail 2025", "sneaker_streetwear")
    ids = save_images(test_images, "sneaker_streetwear", test_hash)
    print(f"  Saved {len(ids)} images with IDs: {ids}")

    print("Testing schema extraction save...")
    if ids:
        save_extraction(ids[0], {
            "material": "concrete",
            "form": "rectilinear",
            "color_temperature": "cool",
            "lighting": "overhead track",
            "texture": "rough",
        }, "sneaker_streetwear")
        print(f"  Extraction saved for image {ids[0]}")

        extracted = get_extractions_for_image(ids[0])
        print(f"  Retrieved extraction: {extracted}")

    print("Testing brief cache...")
    cache_brief("NYC sneaker retail 2025", "sneaker_streetwear", ids)
    cached = get_cached_brief("NYC sneaker retail 2025", "sneaker_streetwear")
    print(f"  Cache hit: {len(cached)} images returned")

    warm = is_cache_warm("NYC sneaker retail 2025", "sneaker_streetwear", min_images=1)
    print(f"  Cache warm: {warm}")

    print("\nCorpus stats:")
    stats = corpus_stats()
    for k, v in stats.items():
        print(f"  {k}: {v}")

    print("\nAll storage tests passed.")