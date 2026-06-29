"""Tests for retrieval.sources eligibility helpers."""

from __future__ import annotations

from retrieval.sources import (
    is_evidence_eligible,
    is_seed_row,
    looks_like_image_url,
    normalize_source_domain,
)


def test_normalize_source_domain_strips_www():
    assert normalize_source_domain("www.hypebeast.com") == "hypebeast.com"


def test_looks_like_image_url_rejects_article_page():
    assert not looks_like_image_url("https://hypebeast.com/2025/1/best-sneakers")
    assert looks_like_image_url("https://cdn.example.com/photo.jpg")


def test_is_seed_row_accepts_null_retrieval_method():
    assert is_seed_row({"retrieval_method": None})
    assert is_seed_row({"retrieval_method": "seed"})
    assert not is_seed_row({"retrieval_method": "tavily"})


def test_live_row_on_allowlist_with_image_url():
    row = {
        "retrieval_method": "tavily",
        "source": "www.sneakerfreaker.com",
        "title": "Kith Williamsburg — interior",
        "image_url": "https://cdn.example.com/store.jpg",
        "source_url": "https://sneakerfreaker.com/features/kith/",
    }
    assert is_evidence_eligible(row, "sneaker_streetwear")


def test_live_row_off_allowlist_rejected():
    row = {
        "retrieval_method": "tavily",
        "source": "www.pinterest.com",
        "title": "Sneaker store",
        "image_url": "https://cdn.example.com/store.jpg",
        "source_url": "https://pinterest.com/pin/1",
    }
    assert not is_evidence_eligible(row, "sneaker_streetwear")


def test_live_row_roundup_title_rejected():
    row = {
        "retrieval_method": "tavily",
        "source": "hypebeast.com",
        "title": "Best Sneaker Releases This Week",
        "image_url": "https://cdn.example.com/kick.jpg",
        "source_url": "https://hypebeast.com/2025/1/best",
    }
    assert not is_evidence_eligible(row, "sneaker_streetwear")


def test_seed_row_always_eligible_even_off_allowlist():
    row = {
        "retrieval_method": None,
        "source": "madhappy.com",
        "title": "Madhappy — interior 1",
        "image_url": "https://madhappy.com/cdn/shop/files/hero.jpg",
        "source_url": "https://madhappy.com/pages/store",
    }
    assert is_evidence_eligible(row, "sneaker_streetwear")
