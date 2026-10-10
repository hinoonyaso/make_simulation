"""Small registry mapping reusable visual concepts to renderer-neutral blueprints."""
from __future__ import annotations

BLUEPRINTS = {
    "exploded_assembly": {"renderers": ["blender"], "evidence": "conceptual_illustration"},
    "layered_structure": {"renderers": ["blender", "manim"], "evidence": "conceptual_illustration"},
    "signal_timing": {"renderers": ["manim"], "evidence": "derived_calculation"},
    "coordinate_transform": {"renderers": ["manim", "blender"], "evidence": "derived_calculation"},
    "process_flow": {"renderers": ["manim"], "evidence": "conceptual_illustration"},
    "before_after": {"renderers": ["manim", "blender"], "evidence": "conceptual_illustration"},
}


def get_blueprint(name: str) -> dict:
    try:
        return dict(BLUEPRINTS[name])
    except KeyError as exc:
        raise ValueError(f"unknown educational blueprint: {name}") from exc


def available_blueprints() -> dict[str, dict]:
    return {key: dict(value) for key, value in BLUEPRINTS.items()}
