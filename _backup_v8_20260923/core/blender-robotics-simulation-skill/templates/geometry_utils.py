from __future__ import annotations

import bpy
from mathutils import Vector


def apply_bevel(obj, width=0.02, segments=3):
    mod = obj.modifiers.new(name='Bevel', type='BEVEL')
    mod.width = width
    mod.segments = segments
    mod.limit_method = 'ANGLE'
    return mod


def add_cube(name, location=(0, 0, 0), scale=(1, 1, 1), bevel=0.03):
    bpy.ops.mesh.primitive_cube_add(location=location)
    obj = bpy.context.object
    obj.name = name
    obj.scale = scale
    bpy.ops.object.transform_apply(location=False, rotation=False, scale=True)
    if bevel > 0:
        apply_bevel(obj, bevel)
    return obj


def add_cylinder(name, location=(0, 0, 0), radius=0.25, depth=1.0, bevel=0.02):
    bpy.ops.mesh.primitive_cylinder_add(vertices=48, radius=radius, depth=depth, location=location)
    obj = bpy.context.object
    obj.name = name
    if bevel > 0:
        apply_bevel(obj, bevel)
    return obj


def add_sphere(name, location=(0, 0, 0), radius=0.15):
    bpy.ops.mesh.primitive_uv_sphere_add(segments=48, ring_count=24, radius=radius, location=location)
    obj = bpy.context.object
    obj.name = name
    return obj


def curve_between(name, start, end, radius=0.012, material=None):
    start = Vector(start)
    end = Vector(end)
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new('POLY')
    spline.points.add(1)
    spline.points[0].co = (*start, 1.0)
    spline.points[1].co = (*end, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    if material is not None:
        obj.data.materials.append(material)
    return obj


def add_floor(size=12.0, z=0.0):
    bpy.ops.mesh.primitive_plane_add(size=size, location=(0, 0, z))
    floor = bpy.context.object
    floor.name = 'Floor'
    return floor
