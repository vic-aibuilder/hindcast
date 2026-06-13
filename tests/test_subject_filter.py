"""
Tests for the vision-based retail interior subject filter.

Uses a mock Anthropic client to test filter logic without
making real API calls or spending credits.
"""

from __future__ import annotations

from unittest.mock import MagicMock

from retrieval.subject_filter import filter_to_interiors, _is_retail_interior


def _mock_client(response_text: str) -> MagicMock:
    """Build a mock Anthropic client that returns a fixed text response."""
    client = MagicMock()
    message = MagicMock()
    content_block = MagicMock()
    content_block.text = response_text
    message.content = [content_block]
    client.messages.create.return_value = message
    return client


def test_keeps_yes_response():
    client = _mock_client("YES")
    result = _is_retail_interior("https://example.com/interior.jpg", client)
    assert result is True


def test_drops_no_response():
    client = _mock_client("NO")
    result = _is_retail_interior("https://example.com/product.jpg", client)
    assert result is False


def test_yes_case_insensitive():
    client = _mock_client("yes")
    result = _is_retail_interior("https://example.com/interior.jpg", client)
    assert result is True


def test_filter_keeps_interiors():
    client = _mock_client("YES")
    images = [{"image_url": f"https://example.com/img-{i}.jpg"} for i in range(5)]
    kept = filter_to_interiors(images, client=client)
    assert len(kept) == 5


def test_filter_drops_non_interiors():
    client = _mock_client("NO")
    images = [{"image_url": f"https://example.com/img-{i}.jpg"} for i in range(5)]
    kept = filter_to_interiors(images, client=client)
    assert len(kept) == 0


def test_filter_respects_max_to_check():
    client = _mock_client("YES")
    images = [{"image_url": f"https://example.com/img-{i}.jpg"} for i in range(100)]
    kept = filter_to_interiors(images, client=client, max_to_check=10)
    # Only first 10 checked and kept — rest dropped
    assert len(kept) == 10


def test_filter_skips_missing_url():
    client = _mock_client("YES")
    images = [
        {"image_url": "https://example.com/valid.jpg"},
        {"image_url": ""},
        {},
    ]
    kept = filter_to_interiors(images, client=client)
    assert len(kept) == 1


def test_bad_request_drops_image():
    import anthropic

    client = MagicMock()
    client.messages.create.side_effect = anthropic.BadRequestError(
        message="invalid image",
        response=MagicMock(status_code=400),
        body={},
    )
    result = _is_retail_interior("https://example.com/bad.jpg", client)
    assert result is False
