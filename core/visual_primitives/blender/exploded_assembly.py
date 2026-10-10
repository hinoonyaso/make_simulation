"""Procedural concentric-race/roller assembly helper reusable across mechanisms.

This builds a demonstrative assembly from dimensions supplied by the caller; it
does not imply CAD fidelity or contact/structural solver results.
"""
from __future__ import annotations


def create_ring(bpy, name: str, major_radius: float, minor_radius: float, material,
                *, location=(0, 0, 0), segments=96, ring_segments=16):
    bpy.ops.mesh.primitive_torus_add(major_segments=segments, minor_segments=ring_segments,
                                     major_radius=major_radius, minor_radius=minor_radius,
                                     location=location)
    obj = bpy.context.object
    obj.name = name
    obj.data.materials.append(material)
    for poly in obj.data.polygons:
        poly.use_smooth = True
    return obj


def create_roller_set(bpy, material, *, count=8, pitch_radius=1.18, roller_radius=.20,
                      z=0.0, segments=24, rings=12):
    import math
    from mathutils import Vector
    result = []
    for index in range(count):
        angle = math.tau * index / count
        bpy.ops.mesh.primitive_uv_sphere_add(segments=segments, ring_count=rings,
            radius=roller_radius, location=(pitch_radius*math.cos(angle), pitch_radius*math.sin(angle), z))
        ball = bpy.context.object
        ball.name = f"rolling_element_{index+1:02d}"
        ball.data.materials.append(material)
        for poly in ball.data.polygons:
            poly.use_smooth = True
        # A shallow orientation marker makes the rolling direction inspectable.
        ball.rotation_mode = "QUATERNION"
        ball["assembly_role"] = "rolling_element"
        ball["pitch_angle_rad"] = angle
        result.append(ball)
    return result


def set_keyed_visibility(obj, visible_intervals, scene):
    """Key visibility per inclusive frame intervals (render visibility only)."""
    boundaries = {1, scene.frame_end}
    for start, end in visible_intervals:
        boundaries.update((max(1, start), min(scene.frame_end, end)))
        if end < scene.frame_end:
            boundaries.add(end + 1)
    for frame in sorted(boundaries):
        visible = any(start <= frame <= end for start, end in visible_intervals)
        obj.hide_render = not visible
        obj.keyframe_insert(data_path="hide_render", frame=frame)
