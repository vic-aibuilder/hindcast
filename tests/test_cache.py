"""Unit tests for the cache layer."""

from __future__ import annotations

import pytest
from pipeline.storage import init_db, save_images, hash_brief
from corpus.cache import check, store


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Use a temporary database for each test."""
    db_file = tmp_path / "test.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    init_db()


def test_cache_miss_on_empty_db():
    result = check("NYC sneaker retail 2025", "sneaker_streetwear", min_images=1)
    assert result is None


def test_cache_hit_after_store(tmp_path, monkeypatch):
    db_file = tmp_path / "test2.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    init_db()

    brief = "NYC sneaker retail 2025"
    sub_slice = "sneaker_streetwear"
    brief_hash = hash_brief(brief, sub_slice)

    images = [
        {
            "image_url": f"https://example.com/img-{i}.jpg",
            "source_url": "https://dezeen.com",
            "title": f"Test {i}",
            "source": "dezeen.com",
            "retrieval_method": "test",
        }
        for i in range(35)
    ]

    ids = save_images(images, sub_slice, brief_hash)
    store(brief, sub_slice, ids)

    result = check(brief, sub_slice, min_images=30)
    assert result is not None
    assert len(result) == 35


def test_cache_miss_below_min_images(tmp_path, monkeypatch):
    db_file = tmp_path / "test3.db"
    monkeypatch.setenv("DB_PATH", str(db_file))
    init_db()

    brief = "NYC sneaker retail 2025"
    sub_slice = "sneaker_streetwear"
    brief_hash = hash_brief(brief, sub_slice)

    images = [
        {
            "image_url": f"https://example.com/small-{i}.jpg",
            "source_url": "https://dezeen.com",
            "title": f"Test {i}",
            "source": "dezeen.com",
            "retrieval_method": "test",
        }
        for i in range(5)
    ]

    ids = save_images(images, sub_slice, brief_hash)
    store(brief, sub_slice, ids)

    # min_images=30 but only 5 stored — should still miss
    result = check(brief, sub_slice, min_images=30)
    assert result is None
