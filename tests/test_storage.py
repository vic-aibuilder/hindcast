"""Unit tests for the schema-extraction storage round-trip and migration."""

from __future__ import annotations

import json

import pytest

from pipeline.storage import (
    get_connection,
    get_extractions_for_image,
    get_extracted_schemas_for_sub_slice,
    hash_brief,
    init_db,
    purge_legacy_extractions,
    save_extraction,
    save_images,
)


@pytest.fixture(autouse=True)
def fresh_db(tmp_path, monkeypatch):
    """Isolate each test to a temporary database."""
    monkeypatch.setenv("DB_PATH", str(tmp_path / "test.db"))
    init_db()


def _one_image() -> int:
    ids = save_images(
        [{"image_url": "https://example.com/a.jpg", "source": "dezeen.com"}],
        "sneaker_streetwear",
        hash_brief("b", "sneaker_streetwear"),
    )
    return ids[0]


def test_nested_schema_round_trips():
    """A nested {category: {dimension: value}} extraction survives write→read intact."""
    image_id = _one_image()
    schema = {
        "material": {"metal": ["stainless steel"], "wood": []},
        "color": {"temperature": "cool"},
    }
    save_extraction(image_id, schema, "sneaker_streetwear")

    read_back = get_extractions_for_image(image_id)
    assert read_back == schema
    # Specifically: categories come back as dicts (not stringified), lists intact.
    assert isinstance(read_back["material"], dict)
    assert read_back["material"]["metal"] == ["stainless steel"]


def test_purge_removes_legacy_str_rows():
    """str()-format rows (pre-fix) are detected and deleted; JSON rows are kept."""
    image_id = _one_image()
    now = "2026-06-10T00:00:00+00:00"
    with get_connection() as conn:
        # One legacy row (stringified dict, single quotes — not valid JSON)
        conn.execute(
            "INSERT INTO schema_extractions (image_id, dimension, value, sub_slice, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (image_id, "material", "{'metal': ['steel']}", "sneaker_streetwear", now),
        )
        # One valid JSON row (post-fix)
        conn.execute(
            "INSERT INTO schema_extractions (image_id, dimension, value, sub_slice, created_at) "
            "VALUES (?, ?, ?, ?, ?)",
            (
                image_id,
                "color",
                json.dumps({"temperature": "cool"}),
                "sneaker_streetwear",
                now,
            ),
        )

    removed = purge_legacy_extractions()
    assert removed == 1

    remaining = (
        get_connection().execute("SELECT dimension FROM schema_extractions").fetchall()
    )
    assert [r["dimension"] for r in remaining] == ["color"]


def test_purge_is_idempotent():
    """A second purge over clean (JSON-only) data deletes nothing."""
    image_id = _one_image()
    save_extraction(image_id, {"color": {"temperature": "cool"}}, "sneaker_streetwear")
    assert purge_legacy_extractions() == 0
    assert purge_legacy_extractions() == 0


def test_get_extracted_schemas_skips_unextracted_images():
    """Seed extractions are found even when many unextracted images exist."""
    extracted_id = _one_image()
    save_extraction(
        extracted_id,
        {"material": {"metal": ["steel"]}, "color": {"temperature": "cool"}},
        "sneaker_streetwear",
    )

    # Simulate live-retrieval junk: many images, no extractions.
    junk = [
        {"image_url": f"https://example.com/junk-{i}.jpg", "source": "hypebeast.com"}
        for i in range(600)
    ]
    save_images(junk, "sneaker_streetwear", hash_brief("live", "sneaker_streetwear"))

    schemas = get_extracted_schemas_for_sub_slice("sneaker_streetwear")
    assert len(schemas) == 1
    assert schemas[0]["material"]["metal"] == ["steel"]
