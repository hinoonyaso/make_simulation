"""Allow-listed topic to renderer and educational asset contracts."""
from __future__ import annotations

import ast
from dataclasses import dataclass
import hashlib
import json
from pathlib import Path
from typing import Any
from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[2]
CATALOG = ROOT / "assets/education/catalog.json"
TOOL_RENDERER = {"M": "manim", "B": "blender"}


@dataclass(frozen=True)
class EducationRenderer:
    topic: str
    aliases: tuple[str, ...]
    blender_script: str | None
    manim_script: str
    manim_scene_class: str
    asset_id: str
    supported_modes: tuple[str, ...]
    blueprint_support: tuple[tuple[str, tuple[str, ...]], ...]
    context_builder: Callable[[dict[str, Any]], dict[str, Any]] | None = None

    def blueprints_for(self, renderer: str) -> tuple[str, ...]:
        return dict(self.blueprint_support).get(renderer, ())


def _spur_gear_context(asset: dict[str, Any]) -> dict[str, Any]:
    """Derive ideal external spur-gear kinematics from the validated asset sidecar."""
    metadata = asset["metadata"]
    try:
        z1 = int(metadata["pinion_teeth"])
        z2 = int(metadata["gear_teeth"])
        module_m = float(metadata["module_m"])
        catalog_dimensions = asset["catalog_dimensions"]
        catalog_module_m = float(catalog_dimensions["module_mm"]) / 1000
        catalog_center_m = float(catalog_dimensions["center_distance_mm"]) / 1000
    except (KeyError, TypeError, ValueError) as exc:
        raise RendererResolutionError(f"BLOCKED: gear asset metadata lacks valid tooth/module dimensions: {exc}") from exc
    if z1 <= 0 or z2 <= 0 or module_m <= 0:
        raise RendererResolutionError("BLOCKED: gear tooth counts and module must be positive")
    center_distance_m = module_m * (z1 + z2) / 2
    ratio = z1 / z2
    if abs(module_m - catalog_module_m) > 1e-9 or abs(center_distance_m - catalog_center_m) > 1e-9:
        raise RendererResolutionError("BLOCKED: gear sidecar dimensions disagree with the asset catalog")
    if abs(float(metadata.get("ratio", ratio)) - z2 / z1) > 1e-9:
        raise RendererResolutionError("BLOCKED: gear sidecar ratio disagrees with its tooth counts")
    if abs(float(metadata.get("center_distance_m", center_distance_m)) - center_distance_m) > 1e-9:
        raise RendererResolutionError("BLOCKED: gear sidecar center distance disagrees with module and tooth counts")
    return {
        "calculation_kind": "derived_ideal_kinematics",
        "formula": "omega_2 / omega_1 = -Z_1 / Z_2",
        "pinion_teeth": z1,
        "gear_teeth": z2,
        "module_m": module_m,
        "center_distance_m": center_distance_m,
        "omega_2_over_omega_1": -ratio,
        "source_asset_id": asset["id"],
        "assumption": "ideal external spur-gear kinematics; losses, backlash and tooth contact are not solved",
    }


REGISTRY: dict[str, EducationRenderer] = {
    "ball_bearing": EducationRenderer(
        topic="ball_bearing", aliases=("ball_bearing_concept_smoke",),
        blender_script="pilots/v13_education/blender/bearing_scene.py",
        manim_script="pilots/v13_education/manim/bearing_scene.py",
        manim_scene_class="BearingLessonScene", asset_id="edu.bearing_6204.v1",
        supported_modes=("blender", "manim"),
        blueprint_support=(
            ("blender", ("before_after", "exploded_assembly", "layered_structure", "coordinate_transform")),
            ("manim", ("before_after", "layered_structure", "coordinate_transform")),
        ),
    ),
    "spur_gears": EducationRenderer(
        topic="spur_gears", aliases=(), blender_script=None,
        manim_script="pilots/v14_education/manim/spur_gears_scene.py",
        manim_scene_class="SpurGearsLessonScene", asset_id="edu.spur_gears_20_40.v1",
        supported_modes=("manim",),
        blueprint_support=(("manim", ("before_after",)),),
        context_builder=_spur_gear_context,
    ),
}


class RendererResolutionError(ValueError):
    """A topic, renderer, Blueprint, or asset cannot be safely resolved."""


def resolve_renderer(topic: str) -> EducationRenderer:
    matches = [item for item in REGISTRY.values()
               if topic == item.topic or topic in item.aliases]
    if len(matches) != 1:
        if not matches:
            raise RendererResolutionError(f"BLOCKED: no education renderer registered for topic {topic!r}")
        raise RendererResolutionError(f"BLOCKED: ambiguous education renderer topic {topic!r}")
    return matches[0]


def _inside_root(root: Path, relative_path: str, label: str) -> Path:
    candidate = (root / relative_path).resolve()
    try:
        candidate.relative_to(root.resolve())
    except ValueError as exc:
        raise RendererResolutionError(f"BLOCKED: {label} must stay inside the repository") from exc
    return candidate


def _scene_has_class(path: Path, class_name: str) -> bool:
    try:
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    except (OSError, SyntaxError) as exc:
        raise RendererResolutionError(f"BLOCKED: cannot inspect Manim scene {path}: {exc}") from exc
    return any(isinstance(node, ast.ClassDef) and node.name == class_name for node in tree.body)


def validate_renderer_registration(renderer: EducationRenderer, *, root: Path = ROOT) -> None:
    modes = set(renderer.supported_modes)
    if "manim" not in modes:
        raise RendererResolutionError(f"BLOCKED: {renderer.topic} must register its Manim timeline renderer")
    if bool(renderer.blender_script) != ("blender" in modes):
        raise RendererResolutionError(f"BLOCKED: Blender mode and scene path disagree for {renderer.topic}")
    manim_path = _inside_root(root, renderer.manim_script, "Manim scene path")
    if not manim_path.is_file():
        raise RendererResolutionError(f"BLOCKED: registered Manim scene is missing: {renderer.manim_script}")
    if not _scene_has_class(manim_path, renderer.manim_scene_class):
        raise RendererResolutionError(
            f"BLOCKED: registered Manim class {renderer.manim_scene_class!r} is not defined in {renderer.manim_script}")
    if renderer.blender_script:
        blender_path = _inside_root(root, renderer.blender_script, "Blender scene path")
        if not blender_path.is_file():
            raise RendererResolutionError(f"BLOCKED: registered Blender scene is missing: {renderer.blender_script}")


def resolve_asset(asset_id: str, *, root: Path = ROOT) -> dict[str, Any]:
    catalog_path = _inside_root(root, "assets/education/catalog.json", "asset catalog path")
    try:
        catalog = json.loads(catalog_path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise RendererResolutionError(f"BLOCKED: cannot read education asset catalog: {exc}") from exc
    matches = [row for row in catalog.get("models", []) if row.get("id") == asset_id]
    if len(matches) != 1:
        raise RendererResolutionError(f"BLOCKED: asset id {asset_id!r} is missing or duplicated in catalog.json")
    record = matches[0]
    if record.get("status") != "GENERATED":
        raise RendererResolutionError(f"BLOCKED: education asset {asset_id!r} is not a generated, reproducible asset")
    asset_path = _inside_root(root, record.get("path", ""), "asset path")
    if not asset_path.is_file():
        raise RendererResolutionError(f"BLOCKED: registered asset file is missing: {record.get('path')}")
    metadata_path = asset_path.with_suffix(".json")
    if not metadata_path.is_file():
        raise RendererResolutionError(f"BLOCKED: asset metadata sidecar is missing: {metadata_path.relative_to(root.resolve())}")
    try:
        metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise RendererResolutionError(f"BLOCKED: invalid asset metadata {metadata_path}: {exc}") from exc
    digest = hashlib.sha256(asset_path.read_bytes()).hexdigest()
    if metadata.get("source_sha256") != digest:
        raise RendererResolutionError(f"BLOCKED: asset metadata hash does not match {record.get('path')}")
    return {
        "id": asset_id,
        "status": "PASS",
        "path": asset_path.relative_to(root.resolve()).as_posix(),
        "sha256": digest,
        "metadata_path": metadata_path.relative_to(root.resolve()).as_posix(),
        "metadata_sha256": hashlib.sha256(metadata_path.read_bytes()).hexdigest(),
        "catalog_dimensions": record.get("dimensions", {}),
        "metadata": metadata,
        "asset_loaded_by_renderer": False,
        "validation": "catalog entry, local file and source_sha256 sidecar match",
    }


def resolve_lesson_contract(spec: dict[str, Any], *, root: Path = ROOT) -> dict[str, Any]:
    renderer = resolve_renderer(spec.get("topic", ""))
    validate_renderer_registration(renderer, root=root)
    supplied_asset_id = spec.get("asset_id")
    if supplied_asset_id and supplied_asset_id != renderer.asset_id:
        raise RendererResolutionError(
            f"BLOCKED: topic {renderer.topic!r} maps to {renderer.asset_id!r}, not {supplied_asset_id!r}")
    asset = resolve_asset(renderer.asset_id, root=root)
    calculated_results = renderer.context_builder(asset) if renderer.context_builder else None
    from core.education.blueprint_registry import get_blueprint, supports_renderer

    selected = set()
    for beat in spec.get("beats", []):
        tool = beat.get("tool")
        backend = TOOL_RENDERER.get(tool)
        if backend is None:
            raise RendererResolutionError(f"BLOCKED: beat {beat.get('id', '?')} selects unsupported renderer {tool!r}")
        if backend not in renderer.supported_modes:
            raise RendererResolutionError(
                f"BLOCKED: topic {renderer.topic!r} does not implement {backend} for beat {beat.get('id', '?')}")
        selected.add(backend)
        blueprint = beat.get("blueprint")
        if blueprint:
            try:
                get_blueprint(blueprint)
            except ValueError as exc:
                raise RendererResolutionError(f"BLOCKED: beat {beat.get('id', '?')}: {exc}") from exc
            if not supports_renderer(blueprint, backend):
                raise RendererResolutionError(
                    f"BLOCKED: Blueprint {blueprint!r} has no {backend} implementation")
            if blueprint not in renderer.blueprints_for(backend):
                raise RendererResolutionError(
                    f"BLOCKED: Blueprint {blueprint!r} is registered for {backend} but not implemented by topic {renderer.topic!r}")
    return {
        "registry_id": renderer.topic,
        "requested_topic": spec["topic"],
        "asset_id": renderer.asset_id,
        "asset_validation": asset,
        "calculated_results": calculated_results,
        "supported_modes": list(renderer.supported_modes),
        "selected_modes": sorted(selected),
        "scene": {"blender_script": renderer.blender_script,
                  "manim_script": renderer.manim_script,
                  "manim_scene_class": renderer.manim_scene_class},
    }
