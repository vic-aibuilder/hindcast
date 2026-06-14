"""
Hindcast controlled vocabulary — Schema v2.6.

Single source of truth for the per-image schema dimensions and allowed values.
Importable by the extractor, synthesizer, retrieval pipeline, and tests.

v2.3: blonde wood, chrome rail, matte black rail, bleached white / bright white,
       architectural plant — from Alex Mustonen calibration doc
v2.4: layout_archetype, typography_signage, brand_expression_density — base cats 8–10
v2.5: Phaidon monograph voice-training terms — Kith, Stampd, Veilance, Valextra
v2.6: added quiet luxury material vocab: terrazzo, raw silk panel to material.other;
      lime wash, tadelakt, venetian plaster to material.wall_finish;
      bouclé, mohair, linen, cashmere to material.soft_fabric
"""

from __future__ import annotations

VOCABULARY: dict[str, dict[str, list[str]]] = {
    "material": {
        "wood": [
            "white oak",
            "walnut",
            "dark oak",
            "light wood",
            "blonde wood",
            "bleached white oak",
            "reclaimed",
            "plywood",
        ],
        "metal": [
            "blackened steel",
            "brushed aluminum",
            "stainless steel",
            "quilted stainless steel",
            "brass",
            "copper",
            "perforated metal",
            "chrome rail",
            "matte black rail",
        ],
        "stone": [
            "travertine",
            "raw / honed / unfilled travertine",
            "limestone",
            "marble",
            "Carrara marble",
            "terrazzo",
            "concrete",
            "slate",
            "Ceppo di Gré stone",
        ],
        "other": [
            "white Corian",
            "terrazzo",
            "raw silk panel",
        ],
        "glass": ["clear", "frosted", "translucent", "mirror"],
        "tile": ["round tile", "square tile", "linear tile"],
        "soft_fabric": [
            "upholstery",
            "soft furnishing",
            "carpet",
            "felt",
            "foam",
            "leather",
            "bouclé",
            "mohair",
            "linen",
            "cashmere",
        ],
        "wall_finish": [
            "raw plaster",
            "painted plaster",
            "fluted plaster",
            "lime wash",
            "tadelakt",
            "venetian plaster",
            "exposed brick",
            "whitewashed brick",
            "bleached white / bright white",
            "drywall",
        ],
    },
    "form_geometry": {
        "primary_geometry": [
            "rectilinear / grid",
            "rounded / circular",
            "irregular / organic",
            "mixed",
        ],
        "basic_shape": [
            "circle",
            "square",
            "triangle",
            "rectangle",
            "irregular",
            "cloud / landscape form",
        ],
        "arch_presence": [
            "none",
            "built-in niche",
            "arched opening",
            "dominant arch",
        ],
        "grid_presence": ["none", "subtle", "strong grid"],
        "mass_weight": ["solid mass / heavy", "light / thin", "mixed"],
        "statement_form": [
            "none",
            "plinth",
            "sculptural object",
            "oversized graphic",
            "architectural void",
            "installation",
            "architectural plant",
            "triangular fin system",
            "gradient wall",
        ],
    },
    "color": {
        "temperature": ["warm", "cool", "neutral"],
        "dominant_hue": [
            "off-white",
            "white",
            "black",
            "grey",
            "brown",
            "green",
            "pink",
            "earth tones",
            "other",
        ],
        "palette_type": [
            "monochromatic",
            "tonal",
            "high contrast",
            "material-driven",
            "neutral / clean-slate",
        ],
        "accent": ["none", "subtle", "strong"],
    },
    "lighting": {
        "source_type": [
            "overhead track spot",
            "lightbox",
            "diffuse cove",
            "pendant",
            "linear LED",
            "daylight",
            "mixed",
        ],
        "temperature": ["warm", "neutral", "cool", "mixed"],
        "visibility": ["concealed", "partially exposed", "fully exposed"],
        "drama": ["flat / even", "directional", "theatrical", "high contrast"],
    },
    "texture": {
        "surface": ["smooth", "rough", "mixed"],
        "finish": ["matte", "satin", "shiny / gloss", "mixed"],
        "texture_type": ["linear", "irregular", "geometric", "organic"],
        "pattern": ["none", "subtle", "strong"],
    },
    "opacity": {
        "dominant_opacity": ["opaque", "translucent", "clear / transparent", "mixed"],
        "transparency_use": ["none", "functional", "decorative", "structural"],
    },
    "atmosphere_warmth": {
        "warmth": [
            "warm / inviting / cozy",
            "neutral",
            "cool / austere / clinical",
        ],
        "formality": ["raw", "casual", "semi-formal", "formal"],
        "reference": [
            "gallery",
            "museum",
            "laboratory",
            "residential",
            "industrial",
            "hospitality",
            "archive",
            "archive room",
            "stadium",
            "nature",
        ],
        "abstract_qualities": [
            "inviting",
            "accessible",
            "engaging",
            "memorable",
            "compelling",
        ],
    },
    "layout_archetype": {
        "layout": [
            "open plan / gallery",
            "linear path",
            "grid",
            "found-space",
            "labyrinthine",
            "single room",
            "antechamber / entry sequence",
            "forced perspective corridor",
        ],
        "circulation": ["open", "directed", "theatrical", "free"],
        "density": ["sparse / gallery", "edited", "dense retail"],
    },
    "typography_signage": {
        "signage_density": ["none", "minimal", "moderate", "heavy"],
        "logo_treatment": [
            "logo-as-architecture",
            "logo-as-graphic",
            "logo-restrained",
            "logo-absent",
        ],
        "typography_style": [
            "serif",
            "sans-serif",
            "monospace",
            "hand-lettered",
            "none visible",
        ],
    },
    "brand_expression_density": {
        "density": ["very high", "high", "moderate", "low", "minimal"],
        "mode": [
            "material-embedded",
            "graphic",
            "logo-dominant",
            "atmosphere-driven",
            "product-driven",
        ],
    },
}

# Dimensions that accept multiple values (all others take exactly one value)
_LIST_DIMS: frozenset[tuple[str, str]] = frozenset(
    {
        ("material", "wood"),
        ("material", "metal"),
        ("material", "stone"),
        ("material", "glass"),
        ("material", "tile"),
        ("material", "soft_fabric"),
        ("material", "wall_finish"),
        ("material", "other"),
        ("atmosphere_warmth", "abstract_qualities"),
    }
)
