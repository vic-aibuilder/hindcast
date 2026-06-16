"""Tests for pipeline.run result assembly."""

from __future__ import annotations

import pytest

from pipeline.storage import hash_brief, init_db, save_extraction, save_images
from pipeline.run import run_query, _evidence_sort_key


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Use a temporary SQLite database for each test."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()


def _seed_images(sub_slice: str, count: int = 60) -> list[int]:
    brief_hash = hash_brief("cached brief", sub_slice)
    payload = [
        {
            "image_url": f"https://example.com/{sub_slice}/img-{i}.jpg",
            "source_url": f"https://example.com/{sub_slice}/source-{i}",
            "title": f"{sub_slice} image {i}",
            "source": "example.com",
            "retrieval_method": "seed",
        }
        for i in range(count)
    ]
    return save_images(payload, sub_slice, brief_hash)


def test_run_query_populates_evidence_images_and_matches_image_count(monkeypatch):
    """Pattern evidence rows are fetched from DB and count is exact."""
    sub_slice = "sneaker_streetwear"
    image_ids = _seed_images(sub_slice, count=60)
    target_id = image_ids[-1]

    save_extraction(
        target_id,
        {
            "material": {"metal": ["stainless steel"]},
            "color": {"temperature": "cool"},
        },
        sub_slice,
    )

    cached_images = [
        {
            "id": image_id,
            "image_url": f"https://example.com/{sub_slice}/img-{i}.jpg",
            "source_url": f"https://example.com/{sub_slice}/source-{i}",
            "title": f"{sub_slice} image {i}",
            "source": "example.com",
        }
        for i, image_id in enumerate(image_ids)
    ]

    monkeypatch.setattr(
        "pipeline.run.cache_check", lambda *args, **kwargs: cached_images
    )
    monkeypatch.setattr("pipeline.run.Anthropic", lambda api_key=None: object())
    monkeypatch.setattr(
        "pipeline.run.synthesize",
        lambda **kwargs: [
            {
                "title": "The Stainless Steel Fixture",
                "description": "d1 d2 d3",
                "dominant_terms": ["stainless steel"],
                "image_count": 999,
                "image_ids": [target_id],
            }
        ],
    )

    result = run_query("cached brief", sub_slice)
    pattern = result["patterns"][0]

    assert pattern["image_count"] == 1
    assert len(pattern["evidence_images"]) == 1
    assert "image_ids" not in pattern
    assert pattern["evidence_images"][0]["image_url"].endswith(
        f"img-{len(image_ids) - 1}.jpg"
    )


def test_evidence_image_can_be_outside_top_level_images_cap(monkeypatch):
    """
    Evidence can reference a seed image not present in top-level images[:50].
    """
    sub_slice = "sneaker_streetwear"
    image_ids = _seed_images(sub_slice, count=60)
    target_id = image_ids[-1]  # outside top-level images cap

    save_extraction(
        target_id,
        {
            "material": {"metal": ["stainless steel"]},
            "color": {"temperature": "cool"},
        },
        sub_slice,
    )

    cached_images = [
        {
            "id": image_id,
            "image_url": f"https://example.com/{sub_slice}/img-{i}.jpg",
            "source_url": f"https://example.com/{sub_slice}/source-{i}",
            "title": f"{sub_slice} image {i}",
            "source": "example.com",
        }
        for i, image_id in enumerate(image_ids)
    ]

    monkeypatch.setattr(
        "pipeline.run.cache_check", lambda *args, **kwargs: cached_images
    )
    monkeypatch.setattr("pipeline.run.Anthropic", lambda api_key=None: object())
    monkeypatch.setattr(
        "pipeline.run.synthesize",
        lambda **kwargs: [
            {
                "title": "The Outside-Cap Evidence",
                "description": "d1 d2 d3",
                "dominant_terms": ["stainless steel"],
                "image_count": 1,
                "image_ids": [target_id],
            }
        ],
    )

    result = run_query("cached brief", sub_slice)

    top_level_ids = {img.get("id") for img in result["images"]}
    evidence = result["patterns"][0]["evidence_images"]
    assert len(result["images"]) == 50
    assert target_id not in top_level_ids
    assert len(evidence) == 1
    assert evidence[0]["image_url"].endswith(f"img-{len(image_ids) - 1}.jpg")


def test_evidence_sort_key_groups_by_store_then_interior():
    """#55: a pattern grid should cluster by store with hero → interior order,
    undoing the retrieval round-robin interleave."""
    interleaved = [
        {"title": "Colbo NYC sneaker boutique — interior 2"},
        {"title": "Flight Club New York by Slade Architecture — interior 1"},
        {"title": "Kith Williamsburg Brooklyn — hero"},
        {"title": "Colbo NYC sneaker boutique — interior 1"},
        {"title": "Flight Club New York by Slade Architecture — hero"},
        {"title": "Kith Williamsburg Brooklyn — interior 1"},
    ]
    ordered = [img["title"] for img in sorted(interleaved, key=_evidence_sort_key)]
    assert ordered == [
        "Colbo NYC sneaker boutique — interior 1",
        "Colbo NYC sneaker boutique — interior 2",
        "Flight Club New York by Slade Architecture — hero",
        "Flight Club New York by Slade Architecture — interior 1",
        "Kith Williamsburg Brooklyn — hero",
        "Kith Williamsburg Brooklyn — interior 1",
    ]


def test_evidence_sort_key_prefers_extracted_project_over_title():
    """When `project` is present it defines the store, overriding the title."""
    aime = {"title": "zzz placeholder — interior 1", "project": "Aimé Leon Dore"}
    brain_dead = {"title": "aaa placeholder — hero", "project": "Brain Dead"}
    assert _evidence_sort_key(aime) < _evidence_sort_key(brain_dead)
