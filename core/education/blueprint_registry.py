"""Small registry mapping reusable visual concepts to renderer-neutral blueprints."""
from __future__ import annotations

BLUEPRINTS = {
    "exploded_assembly": {"renderers": ["blender"], "evidence": "conceptual_illustration",
                          "operations": ["explode", "assemble", "highlight_parts", "isolate_object"]},
    "layered_structure": {"renderers": ["blender", "manim"], "evidence": "conceptual_illustration",
                           "operations": ["separate_layers", "assemble", "highlight_parts", "isolate_object"]},
    "signal_timing": {"renderers": ["manim"], "evidence": "derived_calculation"},
    "coordinate_transform": {"renderers": ["manim", "blender"], "evidence": "derived_calculation",
                              "operations": ["rotate", "translate", "coordinate_frame", "force_arrow", "torque_arrow"]},
    "process_flow": {"renderers": ["manim"], "evidence": "conceptual_illustration"},
    "before_after": {"renderers": ["manim", "blender"], "evidence": "conceptual_illustration",
                      "operations": ["highlight_parts", "transparency", "cutaway"]},
    "mechanism_motion": {"renderers": ["blender"], "evidence": "conceptual_illustration",
                          "operations": ["rotate", "translate", "highlight_parts"]},
}

ASSET_BLUEPRINTS = {
    "edu.bearing_6204.v1": {"exploded_assembly", "layered_structure", "coordinate_transform", "before_after", "mechanism_motion"},
    "edu.spur_gears_20_40.v1": {"exploded_assembly", "coordinate_transform", "before_after", "mechanism_motion"},
    "edu.bldc_motor_concept.v1": {"exploded_assembly", "layered_structure", "coordinate_transform", "before_after", "mechanism_motion"},
    "edu.pcb_layered.v1": {"exploded_assembly", "layered_structure", "process_flow", "before_after"},
    "edu.mechanical_primitives.v1": {"exploded_assembly", "layered_structure", "coordinate_transform", "before_after"},
    "edu.energy_structural_thermal.v1": {"exploded_assembly", "layered_structure", "coordinate_transform", "before_after", "mechanism_motion"},
}


def validate_asset_blueprint(asset_id: str, name: str, animation: dict | None = None) -> dict:
    blueprint = get_blueprint(name)
    if asset_id not in ASSET_BLUEPRINTS:
        raise ValueError(f"unsupported education asset id: {asset_id}")
    if name not in ASSET_BLUEPRINTS[asset_id]:
        raise ValueError(f"unsupported asset/blueprint combination: {asset_id} + {name}")
    config = animation or {}
    if not isinstance(config, dict):
        raise ValueError("animation must be an object")
    unknown = set(config) - set(blueprint["operations"])
    if unknown:
        raise ValueError(f"blueprint {name} does not support animation operations: {sorted(unknown)}")
    return {"asset_id": asset_id, "blueprint": name, "animation": dict(config),
            "renderer": "blender" if "blender" in blueprint["renderers"] else "manim",
            "evidence": blueprint["evidence"]}


def get_blueprint(name: str) -> dict:
    try:
        return dict(BLUEPRINTS[name])
    except KeyError as exc:
        raise ValueError(f"unknown educational blueprint: {name}") from exc


def available_blueprints() -> dict[str, dict]:
    return {key: dict(value) for key, value in BLUEPRINTS.items()}
