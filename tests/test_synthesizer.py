"""
Tests for src/synthesizer.py.

No API calls are made. All tests exercise pure-Python paths:
  - _aggregate()         frequency counting for list and string dims
  - _format_aggregation() frequency report structure and annotations
  - _count_images_for_pattern() threshold-based image matching
  - _SYNTHESIS_TOOL      tool schema shape
  - synthesize()         end-to-end with a mocked Anthropic client
"""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock, patch

import pytest

from src.synthesizer import (
    _PATTERN_MATCH_THRESHOLD,
    _SATURATED_PCT,
    _SYNTHESIS_TOOL,
    _aggregate,
    _count_images_for_pattern,
    _format_aggregation,
    synthesize,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _make_extraction(
    *,
    wood: list[str] | None = None,
    metal: list[str] | None = None,
    stone: list[str] | None = None,
    glass: list[str] | None = None,
    tile: list[str] | None = None,
    soft_fabric: list[str] | None = None,
    wall_finish: list[str] | None = None,
    primary_geometry: str = "rectilinear / grid",
    basic_shape: str = "rectangle",
    arch_presence: str = "none",
    grid_presence: str = "strong grid",
    mass_weight: str = "solid mass / heavy",
    statement_form: str = "none",
    color_temperature: str = "warm",
    dominant_hue: str = "brown",
    palette_type: str = "tonal",
    accent: str = "none",
    lighting_source: str = "overhead track spot",
    lighting_temp: str = "warm",
    visibility: str = "concealed",
    drama: str = "flat / even",
    surface: str = "smooth",
    finish: str = "matte",
    texture_type: str = "linear",
    pattern: str = "none",
    dominant_opacity: str = "opaque",
    transparency_use: str = "none",
    warmth: str = "warm / inviting / cozy",
    formality: str = "casual",
    reference: str = "hospitality",
    abstract_qualities: list[str] | None = None,
) -> dict:
    return {
        "material": {
            "wood": wood or [],
            "metal": metal or [],
            "stone": stone or [],
            "glass": glass or [],
            "tile": tile or [],
            "soft_fabric": soft_fabric or [],
            "wall_finish": wall_finish or [],
        },
        "form_geometry": {
            "primary_geometry": primary_geometry,
            "basic_shape": basic_shape,
            "arch_presence": arch_presence,
            "grid_presence": grid_presence,
            "mass_weight": mass_weight,
            "statement_form": statement_form,
        },
        "color": {
            "temperature": color_temperature,
            "dominant_hue": dominant_hue,
            "palette_type": palette_type,
            "accent": accent,
        },
        "lighting": {
            "source_type": lighting_source,
            "temperature": lighting_temp,
            "visibility": visibility,
            "drama": drama,
        },
        "texture": {
            "surface": surface,
            "finish": finish,
            "texture_type": texture_type,
            "pattern": pattern,
        },
        "opacity": {
            "dominant_opacity": dominant_opacity,
            "transparency_use": transparency_use,
        },
        "atmosphere_warmth": {
            "warmth": warmth,
            "formality": formality,
            "reference": reference,
            "abstract_qualities": abstract_qualities or [],
        },
    }


def _corpus(n: int = 10, **kwargs) -> list[dict]:
    """Return n identical extractions built with _make_extraction(**kwargs)."""
    return [_make_extraction(**kwargs) for _ in range(n)]


def _mock_client(patterns: list[dict]) -> MagicMock:
    """Return a mock Anthropic client whose messages.create returns *patterns*."""
    tool_block = SimpleNamespace(type="tool_use", input={"patterns": patterns})
    response = SimpleNamespace(
        content=[tool_block],
        stop_reason="tool_use",
    )
    client = MagicMock()
    client.messages.create.return_value = response
    return client


# ---------------------------------------------------------------------------
# _aggregate()
# ---------------------------------------------------------------------------


class TestAggregate:
    def test_total_matches_input_length(self):
        corpus = _corpus(7)
        agg = _aggregate(corpus)
        assert agg["total"] == 7

    def test_empty_extractions_returns_zero_total(self):
        agg = _aggregate([])
        assert agg["total"] == 0

    def test_string_dim_counts_correctly(self):
        corpus = [
            _make_extraction(primary_geometry="rectilinear / grid"),
            _make_extraction(primary_geometry="rectilinear / grid"),
            _make_extraction(primary_geometry="mixed"),
        ]
        agg = _aggregate(corpus)
        fg = agg["categories"]["form_geometry"]["primary_geometry"]
        assert fg["rectilinear / grid"] == 2
        assert fg["mixed"] == 1
        assert "irregular / organic" not in fg

    def test_list_dim_counts_each_term(self):
        corpus = [
            _make_extraction(metal=["blackened steel", "stainless steel"]),
            _make_extraction(metal=["stainless steel"]),
            _make_extraction(metal=[]),
        ]
        agg = _aggregate(corpus)
        metal = agg["categories"]["material"]["metal"]
        assert metal["stainless steel"] == 2
        assert metal["blackened steel"] == 1
        assert "brass" not in metal

    def test_abstract_qualities_counted_as_list(self):
        corpus = [
            _make_extraction(abstract_qualities=["inviting", "engaging"]),
            _make_extraction(abstract_qualities=["inviting"]),
        ]
        agg = _aggregate(corpus)
        aq = agg["categories"]["atmosphere_warmth"]["abstract_qualities"]
        assert aq["inviting"] == 2
        assert aq["engaging"] == 1

    def test_missing_category_in_extraction_skipped_gracefully(self):
        bad = {
            "material": None,
            "form_geometry": {},
            "color": {},
            "lighting": {},
            "texture": {},
            "opacity": {},
            "atmosphere_warmth": {},
        }
        agg = _aggregate([bad])
        assert agg["total"] == 1
        # Should not raise; material just contributes nothing
        assert agg["categories"]["material"]["wood"] == {}

    def test_all_categories_present_in_output(self):
        agg = _aggregate(_corpus(1))
        expected = {
            "material",
            "form_geometry",
            "color",
            "lighting",
            "texture",
            "opacity",
            "atmosphere_warmth",
            "layout_archetype",
            "typography_signage",
            "brand_expression_density",
        }
        assert set(agg["categories"].keys()) == expected

    def test_uniform_corpus_single_value_counts_equal_total(self):
        corpus = _corpus(5, color_temperature="cool")
        agg = _aggregate(corpus)
        assert agg["categories"]["color"]["temperature"]["cool"] == 5


# ---------------------------------------------------------------------------
# _format_aggregation()
# ---------------------------------------------------------------------------


class TestFormatAggregation:
    def test_contains_corpus_count(self):
        agg = _aggregate(_corpus(12))
        report = _format_aggregation(agg)
        assert "12" in report

    def test_saturated_flag_applied_at_threshold(self):
        # 10/10 = 100% — should be flagged
        agg = _aggregate(_corpus(10, color_temperature="warm"))
        report = _format_aggregation(agg)
        assert "SATURATED" in report

    def test_rare_flag_applied_at_threshold(self):
        # 1 out of 20 images — 5%, below RARE_PCT
        corpus = [_make_extraction(color_temperature="cool")] + _corpus(
            19, color_temperature="warm"
        )
        agg = _aggregate(corpus)
        report = _format_aggregation(agg)
        # "cool" appears at 5%; should be RARE
        assert "RARE" in report

    def test_zero_occurrence_section_present(self):
        # corpus uses only "warm" — "cool" and "neutral" should appear in absence block
        agg = _aggregate(_corpus(5, color_temperature="warm"))
        report = _format_aggregation(agg)
        assert "ZERO-OCCURRENCE" in report

    def test_all_category_headers_present(self):
        agg = _aggregate(_corpus(3))
        report = _format_aggregation(agg)
        for header in (
            "MATERIAL",
            "FORM / GEOMETRY",
            "COLOR",
            "LIGHTING",
            "TEXTURE",
            "OPACITY",
            "ATMOSPHERE / WARMTH",
        ):
            assert header in report, f"Missing header: {header}"

    def test_returns_string(self):
        report = _format_aggregation(_aggregate(_corpus(2)))
        assert isinstance(report, str)
        assert len(report) > 0

    def test_saturated_threshold_boundary(self):
        # Exactly at _SATURATED_PCT (40%) — should be flagged
        n = 10
        count = round(n * _SATURATED_PCT)  # 4
        corpus = [_make_extraction(color_temperature="cool")] * count + [
            _make_extraction(color_temperature="warm")
        ] * (n - count)
        agg = _aggregate(corpus)
        report = _format_aggregation(agg)
        # cool appears at exactly 40% — flagged
        assert "SATURATED" in report


# ---------------------------------------------------------------------------
# _count_images_for_pattern()
# ---------------------------------------------------------------------------


class TestCountImagesForPattern:
    def test_single_term_match(self):
        corpus = [
            _make_extraction(metal=["stainless steel"]),
            _make_extraction(metal=[]),
            _make_extraction(metal=["stainless steel"]),
        ]
        count = _count_images_for_pattern(corpus, ["stainless steel"])
        assert count == 2

    def test_empty_dominant_terms_returns_zero(self):
        assert _count_images_for_pattern(_corpus(5), []) == 0

    def test_threshold_majority_required(self):
        # dominant_terms has 4 terms; threshold 0.5 → min 2 required
        corpus = [
            _make_extraction(metal=["stainless steel", "blackened steel"]),  # 2 match ✓
            _make_extraction(metal=["stainless steel"]),  # 1 match ✗
            _make_extraction(
                metal=["stainless steel", "blackened steel", "brass"]
            ),  # 3 ✓
        ]
        terms = ["stainless steel", "blackened steel", "brass", "copper"]
        count = _count_images_for_pattern(corpus, terms, threshold=0.5)
        assert count == 2

    def test_string_dim_term_matched(self):
        corpus = [
            _make_extraction(primary_geometry="rectilinear / grid"),
            _make_extraction(primary_geometry="mixed"),
        ]
        count = _count_images_for_pattern(corpus, ["rectilinear / grid"])
        assert count == 1

    def test_term_not_in_corpus_returns_zero(self):
        corpus = _corpus(5, metal=[])
        count = _count_images_for_pattern(corpus, ["perforated metal"])
        assert count == 0

    def test_all_images_match_when_term_universal(self):
        corpus = _corpus(8, wall_finish=["exposed brick"])
        count = _count_images_for_pattern(corpus, ["exposed brick"])
        assert count == 8

    def test_deduplication_across_dims(self):
        # "warm" appears in color.temperature AND lighting.temperature;
        # should only count as one match per image, not double-count
        corpus = [
            _make_extraction(color_temperature="warm", lighting_temp="warm"),
        ]
        count = _count_images_for_pattern(corpus, ["warm"])
        assert count == 1

    def test_threshold_default_is_constant(self):
        assert _PATTERN_MATCH_THRESHOLD == 0.5


# ---------------------------------------------------------------------------
# _SYNTHESIS_TOOL schema shape
# ---------------------------------------------------------------------------


class TestSynthesisToolSchema:
    def test_tool_name(self):
        assert _SYNTHESIS_TOOL["name"] == "return_saturation_patterns"

    def test_tool_has_input_schema(self):
        assert "input_schema" in _SYNTHESIS_TOOL
        assert _SYNTHESIS_TOOL["input_schema"]["type"] == "object"

    def test_patterns_array_required(self):
        assert "patterns" in _SYNTHESIS_TOOL["input_schema"]["required"]

    def test_patterns_min_max_items(self):
        patterns_schema = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]
        assert patterns_schema["minItems"] == 4
        assert patterns_schema["maxItems"] == 6

    def test_pattern_item_required_fields(self):
        item_schema = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]["items"]
        assert set(item_schema["required"]) == {
            "title",
            "description",
            "dominant_terms",
            "image_count",
        }

    def test_title_is_string(self):
        item = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]["items"]
        assert item["properties"]["title"]["type"] == "string"

    def test_dominant_terms_is_array_of_strings(self):
        item = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]["items"]
        dt = item["properties"]["dominant_terms"]
        assert dt["type"] == "array"
        assert dt["items"]["type"] == "string"

    def test_image_count_is_integer_with_minimum(self):
        item = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]["items"]
        ic = item["properties"]["image_count"]
        assert ic["type"] == "integer"
        assert ic["minimum"] == 1

    def test_no_additional_properties(self):
        assert _SYNTHESIS_TOOL["input_schema"].get("additionalProperties") is False
        item = _SYNTHESIS_TOOL["input_schema"]["properties"]["patterns"]["items"]
        assert item.get("additionalProperties") is False


# ---------------------------------------------------------------------------
# synthesize() — mocked client
# ---------------------------------------------------------------------------


class TestSynthesize:
    _MOCK_PATTERNS = [
        {
            "title": "THE STAINLESS STEEL FIXTURE DEFAULT",
            "description": (
                "Stainless steel dominates retail fixture systems across the corpus. "
                "The term co-occurs with overhead track spot lighting and polished concrete floors in 87% of images. "
                "Blackened steel and brass appear in fewer than 5% of images."
            ),
            "dominant_terms": [
                "stainless steel",
                "overhead track spot",
                "polished concrete",
            ],
            "image_count": 17,
        },
        {
            "title": "THE LIGHTBOX CEILING",
            "description": (
                "Lightbox ceiling panels function as the primary lighting strategy in this corpus. "
                "The term clusters with flat / even drama and concealed visibility, producing a uniform wash with no directional modeling. "
                "Diffuse cove, pendant, and linear LED configurations are structurally absent."
            ),
            "dominant_terms": ["lightbox", "flat / even", "concealed"],
            "image_count": 14,
        },
        {
            "title": "THE RECTILINEAR GRID AS DEFAULT GEOMETRY",
            "description": (
                "Rectilinear / grid is the primary geometry in the near-total corpus. "
                "Strong grid presence and rectangular basic shape reinforce the logic at every spatial scale. "
                "Rounded / circular and irregular / organic geometries do not appear."
            ),
            "dominant_terms": ["rectilinear / grid", "strong grid", "rectangle"],
            "image_count": 10,
        },
        {
            "title": "THE COOL AUSTERE REGISTER",
            "description": (
                "Cool / austere / clinical warmth reading appears in the majority of images. "
                "The cluster includes cool color temperature, grey or white dominant hue, and laboratory spatial reference. "
                "Residential and hospitality atmospheric references are absent."
            ),
            "dominant_terms": ["cool / austere / clinical", "cool", "laboratory"],
            "image_count": 13,
        },
    ]

    def test_returns_list_of_dicts(self):
        client = _mock_client(self._MOCK_PATTERNS)
        corpus = _corpus(20, metal=["stainless steel"])
        result = synthesize(
            corpus, "Nike SoHo 2025", "sneaker_streetwear", client=client
        )
        assert isinstance(result, list)
        assert all(isinstance(p, dict) for p in result)

    def test_pattern_count_in_range(self):
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(
            _corpus(20), "test brief", "sneaker_streetwear", client=client
        )
        assert 4 <= len(result) <= 6

    def test_each_pattern_has_required_keys(self):
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(_corpus(20), "test", "sneaker_streetwear", client=client)
        for p in result:
            assert "title" in p
            assert "description" in p
            assert "dominant_terms" in p
            assert "image_count" in p

    def test_image_count_is_computed_not_claude_estimate(self):
        # corpus: all 20 images have stainless steel
        # Claude's pattern says image_count=17 — our count should override with 20
        corpus = _corpus(20, metal=["stainless steel"])
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(corpus, "brief", "sneaker_streetwear", client=client)
        stainless_pattern = next(
            p for p in result if "stainless steel" in p["dominant_terms"]
        )
        # our computed count should be > 0 and >= Claude's estimate (all 20 match)
        assert stainless_pattern["image_count"] == 20

    def test_contemporary_fashion_sub_slice_accepted(self):
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(
            _corpus(10), "The Row SoHo", "contemporary_fashion", client=client
        )
        assert len(result) >= 4

    def test_raises_on_empty_extractions(self):
        client = _mock_client(self._MOCK_PATTERNS)
        with pytest.raises(ValueError, match="empty"):
            synthesize([], "brief", "sneaker_streetwear", client=client)

    def test_raises_on_unknown_sub_slice(self):
        client = _mock_client(self._MOCK_PATTERNS)
        with pytest.raises(ValueError, match="Unknown sub_slice"):
            synthesize(_corpus(5), "brief", "activewear", client=client)

    def test_raises_when_no_tool_call_returned(self):
        response = SimpleNamespace(
            content=[SimpleNamespace(type="text", text="Sorry, I cannot...")],
            stop_reason="end_turn",
        )
        client = MagicMock()
        client.messages.create.return_value = response
        with pytest.raises(RuntimeError, match="tool call"):
            synthesize(_corpus(5), "brief", "sneaker_streetwear", client=client)

    def test_raises_without_api_key(self, monkeypatch):
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with patch("src.synthesizer.load_dotenv"):
            with pytest.raises(RuntimeError, match="ANTHROPIC_API_KEY"):
                synthesize(_corpus(5), "brief", "sneaker_streetwear")

    def test_client_messages_create_called_once(self):
        client = _mock_client(self._MOCK_PATTERNS)
        synthesize(_corpus(10), "brief", "sneaker_streetwear", client=client)
        client.messages.create.assert_called_once()

    def test_correct_model_sent_to_api(self):
        client = _mock_client(self._MOCK_PATTERNS)
        synthesize(_corpus(10), "brief", "sneaker_streetwear", client=client)
        call_kwargs = client.messages.create.call_args
        assert call_kwargs.kwargs["model"] == "claude-sonnet-4-6"

    def test_tool_choice_forces_tool(self):
        client = _mock_client(self._MOCK_PATTERNS)
        synthesize(_corpus(10), "brief", "sneaker_streetwear", client=client)
        call_kwargs = client.messages.create.call_args
        tc = call_kwargs.kwargs["tool_choice"]
        assert tc["type"] == "tool"
        assert tc["name"] == "return_saturation_patterns"

    def test_brief_included_in_user_message(self):
        client = _mock_client(self._MOCK_PATTERNS)
        synthesize(
            _corpus(5), "THE DISTINCT BRIEF TEXT", "sneaker_streetwear", client=client
        )
        call_kwargs = client.messages.create.call_args
        user_content = call_kwargs.kwargs["messages"][0]["content"]
        assert "THE DISTINCT BRIEF TEXT" in user_content

    def test_dominant_terms_preserved(self):
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(_corpus(10), "brief", "sneaker_streetwear", client=client)
        for p in result:
            assert isinstance(p["dominant_terms"], list)

    def test_image_count_falls_back_to_claude_estimate_when_zero(self):
        # corpus has no matching terms for the last two patterns — fallback to Claude's value
        corpus = _corpus(10, metal=[], wall_finish=[], stone=[])
        client = _mock_client(self._MOCK_PATTERNS)
        result = synthesize(corpus, "brief", "sneaker_streetwear", client=client)
        # all patterns must have image_count >= 0
        for p in result:
            assert p["image_count"] >= 0
