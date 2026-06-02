"""
Tests for src/extractor.py — validation logic and vocabulary structure.

No API calls are made. All tests exercise the pure-Python paths:
  - VOCABULARY completeness
  - validate() with clean, partially bad, and fully bad inputs
  - _build_tool() schema shape
  - _LIST_DIMS coverage
"""

from __future__ import annotations

import pytest

from src.extractor import (
    MODEL,
    VOCABULARY,
    _LIST_DIMS,
    _TOOL,
    validate,
)

# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

ALL_CATEGORIES = [
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
]

MATERIAL_LIST_DIMS = [
    "wood",
    "metal",
    "stone",
    "glass",
    "tile",
    "soft_fabric",
    "wall_finish",
]


def _clean_result() -> dict:
    """Return a minimal valid extraction — one value per dim, empty lists for list dims."""
    return {
        "material": {
            "wood": ["white oak"],
            "metal": ["blackened steel"],
            "stone": [],
            "glass": [],
            "tile": [],
            "soft_fabric": [],
            "wall_finish": ["exposed brick"],
        },
        "form_geometry": {
            "primary_geometry": "rectilinear / grid",
            "basic_shape": "rectangle",
            "arch_presence": "none",
            "grid_presence": "strong grid",
            "mass_weight": "solid mass / heavy",
            "statement_form": "none",
        },
        "color": {
            "temperature": "warm",
            "dominant_hue": "brown",
            "palette_type": "tonal",
            "accent": "none",
        },
        "lighting": {
            "source_type": "overhead track spot",
            "temperature": "warm",
            "visibility": "concealed",
            "drama": "flat / even",
        },
        "texture": {
            "surface": "smooth",
            "finish": "matte",
            "texture_type": "linear",
            "pattern": "none",
        },
        "opacity": {
            "dominant_opacity": "opaque",
            "transparency_use": "none",
        },
        "atmosphere_warmth": {
            "warmth": "warm / inviting / cozy",
            "formality": "casual",
            "reference": "hospitality",
            "abstract_qualities": ["inviting", "engaging"],
        },
        "layout_archetype": {
            "layout": "open plan / gallery",
            "circulation": "open",
            "density": "edited",
        },
        "typography_signage": {
            "signage_density": "minimal",
            "logo_treatment": "logo-restrained",
            "typography_style": "sans-serif",
        },
        "brand_expression_density": {
            "density": "moderate",
            "mode": "atmosphere-driven",
        },
    }


# ---------------------------------------------------------------------------
# Vocabulary structure tests
# ---------------------------------------------------------------------------


class TestVocabularyStructure:
    def test_all_categories_present(self):
        for cat in ALL_CATEGORIES:
            assert cat in VOCABULARY, f"Missing category: {cat}"

    def test_material_has_all_dimensions(self):
        expected = {
            "wood",
            "metal",
            "stone",
            "glass",
            "tile",
            "soft_fabric",
            "wall_finish",
        }
        assert set(VOCABULARY["material"].keys()) == expected

    def test_form_geometry_has_all_dimensions(self):
        expected = {
            "primary_geometry",
            "basic_shape",
            "arch_presence",
            "grid_presence",
            "mass_weight",
            "statement_form",
        }
        assert set(VOCABULARY["form_geometry"].keys()) == expected

    def test_color_has_all_dimensions(self):
        assert set(VOCABULARY["color"].keys()) == {
            "temperature",
            "dominant_hue",
            "palette_type",
            "accent",
        }

    def test_lighting_has_all_dimensions(self):
        assert set(VOCABULARY["lighting"].keys()) == {
            "source_type",
            "temperature",
            "visibility",
            "drama",
        }

    def test_texture_has_all_dimensions(self):
        assert set(VOCABULARY["texture"].keys()) == {
            "surface",
            "finish",
            "texture_type",
            "pattern",
        }

    def test_opacity_has_all_dimensions(self):
        assert set(VOCABULARY["opacity"].keys()) == {
            "dominant_opacity",
            "transparency_use",
        }

    def test_atmosphere_warmth_has_all_dimensions(self):
        assert set(VOCABULARY["atmosphere_warmth"].keys()) == {
            "warmth",
            "formality",
            "reference",
            "abstract_qualities",
        }

    def test_layout_archetype_has_all_dimensions(self):
        assert set(VOCABULARY["layout_archetype"].keys()) == {
            "layout",
            "circulation",
            "density",
        }

    def test_typography_signage_has_all_dimensions(self):
        assert set(VOCABULARY["typography_signage"].keys()) == {
            "signage_density",
            "logo_treatment",
            "typography_style",
        }

    def test_brand_expression_density_has_all_dimensions(self):
        assert set(VOCABULARY["brand_expression_density"].keys()) == {
            "density",
            "mode",
        }

    def test_all_vocab_lists_are_non_empty(self):
        for cat, dims in VOCABULARY.items():
            for dim, values in dims.items():
                assert len(values) > 0, f"{cat}.{dim} has empty vocabulary list"

    def test_no_duplicate_vocab_values(self):
        for cat, dims in VOCABULARY.items():
            for dim, values in dims.items():
                assert len(values) == len(set(values)), (
                    f"{cat}.{dim} has duplicate vocabulary values: {values}"
                )

    def test_model_is_claude_sonnet(self):
        assert MODEL == "claude-sonnet-4-6"


# ---------------------------------------------------------------------------
# _LIST_DIMS coverage tests
# ---------------------------------------------------------------------------


class TestListDims:
    def test_all_material_dims_are_list_dims(self):
        for dim in MATERIAL_LIST_DIMS:
            assert ("material", dim) in _LIST_DIMS, (
                f"('material', '{dim}') should be in _LIST_DIMS"
            )

    def test_abstract_qualities_is_list_dim(self):
        assert ("atmosphere_warmth", "abstract_qualities") in _LIST_DIMS

    def test_single_value_dims_not_in_list_dims(self):
        single_value_dims = [
            ("form_geometry", "primary_geometry"),
            ("form_geometry", "arch_presence"),
            ("color", "temperature"),
            ("lighting", "drama"),
            ("texture", "finish"),
            ("opacity", "dominant_opacity"),
            ("atmosphere_warmth", "warmth"),
        ]
        for pair in single_value_dims:
            assert pair not in _LIST_DIMS, f"{pair} should not be a list dim"


# ---------------------------------------------------------------------------
# validate() — clean input
# ---------------------------------------------------------------------------


class TestValidateClean:
    def test_clean_result_returns_no_violations(self):
        assert validate(_clean_result()) == []

    def test_all_list_dims_can_be_empty(self):
        result = _clean_result()
        for dim in MATERIAL_LIST_DIMS:
            result["material"][dim] = []
        result["atmosphere_warmth"]["abstract_qualities"] = []
        assert validate(result) == []

    def test_multiple_values_in_list_dim(self):
        result = _clean_result()
        result["material"]["metal"] = ["blackened steel", "stainless steel", "brass"]
        assert validate(result) == []

    def test_all_abstract_qualities_at_once(self):
        result = _clean_result()
        result["atmosphere_warmth"]["abstract_qualities"] = [
            "inviting",
            "accessible",
            "engaging",
            "memorable",
            "compelling",
        ]
        assert validate(result) == []


# ---------------------------------------------------------------------------
# validate() — out-of-vocabulary values
# ---------------------------------------------------------------------------


class TestValidateBad:
    def test_unknown_string_dim_value_flagged(self):
        result = _clean_result()
        result["color"]["temperature"] = "lukewarm"
        violations = validate(result)
        assert any("color.temperature" in v for v in violations)
        assert any("lukewarm" in v for v in violations)

    def test_unknown_list_dim_value_flagged(self):
        result = _clean_result()
        result["material"]["wood"] = ["bamboo"]
        violations = validate(result)
        assert any("material.wood" in v for v in violations)
        assert any("bamboo" in v for v in violations)

    def test_mixed_valid_invalid_in_list_flagged(self):
        result = _clean_result()
        result["material"]["stone"] = ["travertine", "sandstone"]
        violations = validate(result)
        assert any("material.stone" in v for v in violations)

    def test_string_where_list_expected_flagged(self):
        result = _clean_result()
        result["material"]["wood"] = "white oak"  # should be a list
        violations = validate(result)
        assert any("material.wood" in v for v in violations)

    def test_missing_category_flagged(self):
        result = _clean_result()
        del result["lighting"]
        violations = validate(result)
        assert any("lighting" in v for v in violations)

    def test_missing_dim_in_category_flagged(self):
        result = _clean_result()
        del result["color"]["accent"]
        violations = validate(result)
        assert any("color.accent" in v for v in violations)

    def test_multiple_violations_all_reported(self):
        result = _clean_result()
        result["color"]["temperature"] = "lukewarm"
        result["atmosphere_warmth"]["warmth"] = "hot"
        result["material"]["glass"] = ["stained glass"]
        violations = validate(result)
        assert len(violations) >= 3

    def test_category_is_not_dict_flagged(self):
        result = _clean_result()
        result["texture"] = "smooth"
        violations = validate(result)
        assert any("texture" in v for v in violations)


# ---------------------------------------------------------------------------
# validate() — enum boundary checks
# ---------------------------------------------------------------------------


class TestValidateEnumBoundary:
    @pytest.mark.parametrize("value", VOCABULARY["color"]["temperature"])
    def test_all_color_temperature_values_valid(self, value: str):
        result = _clean_result()
        result["color"]["temperature"] = value
        assert validate(result) == []

    @pytest.mark.parametrize("value", VOCABULARY["atmosphere_warmth"]["warmth"])
    def test_all_atmosphere_warmth_values_valid(self, value: str):
        result = _clean_result()
        result["atmosphere_warmth"]["warmth"] = value
        assert validate(result) == []

    @pytest.mark.parametrize("value", VOCABULARY["opacity"]["dominant_opacity"])
    def test_all_opacity_dominant_opacity_values_valid(self, value: str):
        result = _clean_result()
        result["opacity"]["dominant_opacity"] = value
        assert validate(result) == []

    @pytest.mark.parametrize("value", VOCABULARY["form_geometry"]["arch_presence"])
    def test_all_arch_presence_values_valid(self, value: str):
        result = _clean_result()
        result["form_geometry"]["arch_presence"] = value
        assert validate(result) == []


# ---------------------------------------------------------------------------
# Tool schema structure tests
# ---------------------------------------------------------------------------


class TestToolSchema:
    def test_tool_name(self):
        assert _TOOL["name"] == "extract_schema_attributes"

    def test_tool_has_input_schema(self):
        assert "input_schema" in _TOOL
        assert _TOOL["input_schema"]["type"] == "object"

    def test_tool_requires_all_categories(self):
        required = set(_TOOL["input_schema"]["required"])
        assert required == {
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

    def test_material_dims_are_arrays_in_tool(self):
        mat = _TOOL["input_schema"]["properties"]["material"]["properties"]
        for dim in MATERIAL_LIST_DIMS:
            assert mat[dim]["type"] == "array", (
                f"material.{dim} should be array type in tool"
            )

    def test_single_value_dims_are_strings_in_tool(self):
        color_props = _TOOL["input_schema"]["properties"]["color"]["properties"]
        for dim in ("temperature", "dominant_hue", "palette_type", "accent"):
            assert color_props[dim]["type"] == "string", (
                f"color.{dim} should be string type in tool"
            )

    def test_tool_enums_match_vocabulary(self):
        """Enum values in the tool schema must exactly match VOCABULARY."""
        color_props = _TOOL["input_schema"]["properties"]["color"]["properties"]
        assert color_props["temperature"]["enum"] == VOCABULARY["color"]["temperature"]
        assert (
            color_props["dominant_hue"]["enum"] == VOCABULARY["color"]["dominant_hue"]
        )

    def test_atmosphere_abstract_qualities_is_array_in_tool(self):
        atm_props = _TOOL["input_schema"]["properties"]["atmosphere_warmth"][
            "properties"
        ]
        assert atm_props["abstract_qualities"]["type"] == "array"
        assert (
            atm_props["abstract_qualities"]["items"]["enum"]
            == VOCABULARY["atmosphere_warmth"]["abstract_qualities"]
        )

    def test_no_additional_properties_on_all_objects(self):
        """Every object in the tool schema should have additionalProperties: False."""
        top_level = _TOOL["input_schema"]
        assert top_level.get("additionalProperties") is False

        for cat in ALL_CATEGORIES:
            cat_schema = top_level["properties"][cat]
            assert cat_schema.get("additionalProperties") is False, (
                f"{cat} object in tool schema is missing additionalProperties: false"
            )

    def test_layout_archetype_dims_are_strings_in_tool(self):
        props = _TOOL["input_schema"]["properties"]["layout_archetype"]["properties"]
        for dim in ("layout", "circulation", "density"):
            assert props[dim]["type"] == "string", (
                f"layout_archetype.{dim} should be string"
            )

    def test_typography_signage_dims_are_strings_in_tool(self):
        props = _TOOL["input_schema"]["properties"]["typography_signage"]["properties"]
        for dim in ("signage_density", "logo_treatment", "typography_style"):
            assert props[dim]["type"] == "string", (
                f"typography_signage.{dim} should be string"
            )

    def test_brand_expression_density_dims_are_strings_in_tool(self):
        props = _TOOL["input_schema"]["properties"]["brand_expression_density"][
            "properties"
        ]
        for dim in ("density", "mode"):
            assert props[dim]["type"] == "string", (
                f"brand_expression_density.{dim} should be string"
            )

    def test_new_category_enums_match_vocabulary(self):
        la = _TOOL["input_schema"]["properties"]["layout_archetype"]["properties"]
        assert la["layout"]["enum"] == VOCABULARY["layout_archetype"]["layout"]
        assert (
            la["circulation"]["enum"] == VOCABULARY["layout_archetype"]["circulation"]
        )
        ts = _TOOL["input_schema"]["properties"]["typography_signage"]["properties"]
        assert (
            ts["signage_density"]["enum"]
            == VOCABULARY["typography_signage"]["signage_density"]
        )
        bed = _TOOL["input_schema"]["properties"]["brand_expression_density"][
            "properties"
        ]
        assert (
            bed["density"]["enum"] == VOCABULARY["brand_expression_density"]["density"]
        )
        assert bed["mode"]["enum"] == VOCABULARY["brand_expression_density"]["mode"]
