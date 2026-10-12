"""Small renderer-neutral education animation operations for Blender objects."""
from __future__ import annotations


def keyframe_rotation(obj, axis: str, start_frame: int, end_frame: int,
                      start_angle: float = 0.0, end_angle: float = 6.283185307179586) -> None:
    axes = {"X": 0, "Y": 1, "Z": 2}
    if axis.upper() not in axes or end_frame <= start_frame:
        raise ValueError("rotation requires axis X/Y/Z and an increasing frame interval")
    i = axes[axis.upper()]
    obj.rotation_euler[i] = start_angle
    obj.keyframe_insert("rotation_euler", index=i, frame=start_frame)
    obj.rotation_euler[i] = end_angle
    obj.keyframe_insert("rotation_euler", index=i, frame=end_frame)


def keyframe_translation(obj, start_frame: int, end_frame: int, start, end) -> None:
    if end_frame <= start_frame:
        raise ValueError("translation requires an increasing frame interval")
    obj.location = start
    obj.keyframe_insert("location", frame=start_frame)
    obj.location = end
    obj.keyframe_insert("location", frame=end_frame)


def exploded_view(objects, offsets: dict[str, tuple[float, float, float]],
                  base_locations: dict[str, object], start_frame: int, end_frame: int,
                  *, explode: bool = True) -> None:
    if end_frame <= start_frame:
        raise ValueError("exploded view requires an increasing frame interval")
    for obj in objects:
        if obj.name not in offsets:
            continue
        base = base_locations[obj.name].copy()
        delta = offsets[obj.name]
        exploded = base + type(base)(delta)
        obj.delta_location = base if explode else exploded
        obj.keyframe_insert("delta_location", frame=start_frame)
        obj.delta_location = exploded if explode else base
        obj.keyframe_insert("delta_location", frame=end_frame)


def isolate_objects(objects, visible_names: set[str]) -> None:
    for obj in objects:
        visible = obj.name in visible_names
        obj.hide_viewport = not visible
        obj.hide_render = not visible


def set_transparency(objects, opacity: float) -> None:
    if not 0 <= opacity <= 1:
        raise ValueError("opacity must be in [0, 1]")
    for obj in objects:
        if obj.type != "MESH":
            continue
        for material in obj.data.materials:
            if material is None:
                continue
            material.diffuse_color = (*material.diffuse_color[:3], opacity)
            if hasattr(material, "surface_render_method"):
                material.surface_render_method = "DITHERED" if opacity < 1 else "OPAQUE"


def keyframe_highlight(obj, start_frame: int, end_frame: int, material) -> None:
    if end_frame <= start_frame:
        raise ValueError("highlight requires an increasing frame interval")
    if obj.type != "MESH":
        raise ValueError(f"highlight target is not a mesh: {obj.name}")
    obj.data.materials.append(material)
    slot = len(obj.data.materials)-1
    obj.active_material_index = slot
    obj.keyframe_insert("active_material_index", frame=start_frame)
    obj.active_material_index = 0
    obj.keyframe_insert("active_material_index", frame=end_frame)


def set_cutaway(obj, cutter, *, enabled: bool = True):
    if not enabled:
        return None
    modifier = obj.modifiers.new("Education cutaway", "BOOLEAN")
    modifier.operation = "DIFFERENCE"
    modifier.object = cutter
    modifier.show_viewport = True
    modifier.show_render = True
    return modifier
