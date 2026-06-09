from __future__ import annotations

import pytest

from retrieval.consolidate import (
    MAX_IMAGES_PER_SOURCE,
    _consolidate_images,
    _normalize_image_url,
)


# ---------------------------------------------------------------------------
# _normalize_image_url — collapse CDN size variants
# ---------------------------------------------------------------------------


class TestNormalizeImageUrl:
    def test_query_string_stripped(self):
        a = "https://image-cdn.hypb.st/foo-tw.jpg?w=1080&q=90&fit=max"
        b = "https://image-cdn.hypb.st/foo-tw.jpg?w=960&q=90&fit=max"
        assert _normalize_image_url(a) == _normalize_image_url(b)

    def test_different_assets_not_collapsed(self):
        a = "https://image-cdn.hypb.st/foo-tw.jpg?w=960"
        b = "https://image-cdn.hypb.st/foo-000.jpg?w=960"
        assert _normalize_image_url(a) != _normalize_image_url(b)

    @pytest.mark.parametrize("bad", ["", "not a url", "::::"])
    def test_handles_garbage(self, bad):
        # Should not raise
        _normalize_image_url(bad)


# ---------------------------------------------------------------------------
# _consolidate_images — dedupe + per-source cap + interleave
# ---------------------------------------------------------------------------


def _img(url, source_url, title="t"):
    return {"image_url": url, "source_url": source_url, "title": title}


class TestConsolidateImages:
    def test_size_variants_deduped(self):
        imgs = [
            _img("https://cdn/x/a.jpg?w=1080", "https://site/page1"),
            _img("https://cdn/x/a.jpg?w=960", "https://site/page1"),
        ]
        assert len(_consolidate_images(imgs)) == 1

    def test_per_source_cap_enforced(self):
        imgs = [
            _img(f"https://cdn/x/{i}.jpg", "https://site/flood")
            for i in range(MAX_IMAGES_PER_SOURCE + 5)
        ]
        out = _consolidate_images(imgs)
        assert len(out) == MAX_IMAGES_PER_SOURCE

    def test_interleaved_across_sources(self):
        # Two source pages, 3 images each — output should alternate sources,
        # not show one page's run before the other's.
        imgs = [_img(f"https://cdn/a{i}.jpg", "https://site/A") for i in range(3)]
        imgs += [_img(f"https://cdn/b{i}.jpg", "https://site/B") for i in range(3)]
        out = _consolidate_images(imgs)
        first_two = {img["source_url"] for img in out[:2]}
        assert first_two == {"https://site/A", "https://site/B"}

    def test_empty_urls_skipped(self):
        imgs = [
            _img("", "https://site/p"),
            _img("https://cdn/ok.jpg", "https://site/p"),
        ]
        out = _consolidate_images(imgs)
        assert len(out) == 1
        assert out[0]["image_url"] == "https://cdn/ok.jpg"
