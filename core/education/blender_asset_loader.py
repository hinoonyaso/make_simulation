"""Registry-backed import helpers for education Blender scenes.

Importing a model is explicit and local only. AssetFactory performs path and
SHA-256 checks before Blender appends the declared collection.
"""
from __future__ import annotations

from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[2]
ASSET_FACTORY_DIR = ROOT / "core/visual-assets"
if str(ASSET_FACTORY_DIR) not in sys.path:
    sys.path.insert(0, str(ASSET_FACTORY_DIR))
from asset_factory import AssetFactory


def resolve_education_asset(asset_id: str, *, root: Path = ROOT) -> dict:
    factory = AssetFactory(root)
    entry = factory._entry(asset_id)
    if entry.get("tool") != "blender" or entry.get("kind") != "procedural":
        raise ValueError(f"{asset_id}: education loader supports registered Blender procedural assets only")
    report = factory.validate_asset(asset_id)
    path = Path(report["path"])
    if path.suffix.lower() != ".blend":
        raise ValueError(f"{asset_id}: expected a .blend source, got {path.suffix or 'no extension'}")
    return {"asset_id": asset_id, "path": path, "sha256": report["sha256"],
            "license": report.get("license"),
            "collection": entry.get("blender_collection"),
            "entry": entry}


def load_education_asset(asset_id: str, scene, *, location=(0, 0, 0), rotation=(0, 0, 0),
                         scale=(1, 1, 1), material_override=None,
                         animation_mode="PLAY", animation_frame=1,
                         root: Path = ROOT) -> dict:
    """Append a verified collection and apply a single assembly transform.

    `STATIC` evaluates animation at `animation_frame` then freezes imported
    object transforms. `PLAY` retains the source keyframes in the active scene.
    """
    import bpy
    from mathutils import Euler, Matrix, Vector

    resolved = resolve_education_asset(asset_id, root=root)
    if animation_mode not in {"PLAY", "STATIC"}:
        raise ValueError("animation_mode must be PLAY or STATIC")
    collection_name = resolved["collection"]
    if not collection_name:
        raise ValueError(f"{asset_id}: registry has no blender_collection entry")
    with bpy.data.libraries.load(str(resolved["path"]), link=False) as (data_from, data_to):
        if collection_name not in data_from.collections:
            raise ValueError(f"{asset_id}: Blender collection {collection_name!r} is missing")
        data_to.collections = [collection_name]
    imported = data_to.collections[0]
    if imported is None:
        raise RuntimeError(f"{asset_id}: Blender failed to append {collection_name!r}")
    if imported.name not in scene.collection.children:
        scene.collection.children.link(imported)
    objects = list(imported.all_objects)
    if not objects:
        raise ValueError(f"{asset_id}: imported collection contains no objects")
    wrapper = bpy.data.objects.new(f"AssetRoot::{asset_id}", None)
    scene.collection.objects.link(wrapper)
    wrapper.empty_display_type = "PLAIN_AXES"
    for obj in objects:
        if obj.parent is None:
            obj.parent = wrapper
            obj.matrix_parent_inverse = Matrix.Identity(4)
    wrapper.location = Vector(location)
    wrapper.rotation_euler = Euler(rotation)
    wrapper.scale = Vector(scale)
    if material_override is not None:
        mat = bpy.data.materials.get(material_override) if isinstance(material_override, str) else material_override
        if mat is None:
            raise ValueError(f"material override does not resolve: {material_override!r}")
        for obj in objects:
            if obj.type == "MESH":
                obj.data.materials.clear()
                obj.data.materials.append(mat)
    if animation_mode == "STATIC":
        scene.frame_set(animation_frame)
        evaluated = {obj: obj.matrix_world.copy() for obj in objects}
        for obj, matrix in evaluated.items():
            if obj.animation_data:
                obj.animation_data_clear()
            obj.matrix_world = matrix
    return {**resolved, "collection_object": imported, "root_object": wrapper,
            "objects": objects, "animation_mode": animation_mode}
