from __future__ import annotations

import bpy
from mathutils import Vector, Matrix
from geometry_utils import curve_between, add_sphere

AXIS_COLORS = {
    'x': (0.86, 0.08, 0.10, 1.0),
    'y': (0.08, 0.65, 0.20, 1.0),
    'z': (0.05, 0.32, 0.90, 1.0),
}


def create_emission_material(name, color, strength=2.0):
    mat = bpy.data.materials.new(name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get('Principled BSDF')
    bsdf.inputs['Base Color'].default_value = color
    if 'Emission Color' in bsdf.inputs:
        bsdf.inputs['Emission Color'].default_value = color
    elif 'Emission' in bsdf.inputs:
        bsdf.inputs['Emission'].default_value = color
    if 'Emission Strength' in bsdf.inputs:
        bsdf.inputs['Emission Strength'].default_value = strength
    bsdf.inputs['Roughness'].default_value = 0.4
    return mat


def add_coordinate_frame(name='Frame', origin=(0, 0, 0), scale=0.6):
    root = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(root)
    root.location = origin
    mats = {k: create_emission_material(f'{name}_{k.upper()}_Mat', c, 1.3) for k, c in AXIS_COLORS.items()}
    axes = {
        'x': curve_between(f'{name}_X', (0, 0, 0), (scale, 0, 0), radius=0.012, material=mats['x']),
        'y': curve_between(f'{name}_Y', (0, 0, 0), (0, scale, 0), radius=0.012, material=mats['y']),
        'z': curve_between(f'{name}_Z', (0, 0, 0), (0, 0, scale), radius=0.012, material=mats['z']),
    }
    for obj in axes.values():
        obj.parent = root
    return root, axes


def add_point(name, location, material=None, radius=0.06):
    p = add_sphere(name, location, radius)
    if material is not None:
        p.data.materials.append(material)
    return p


def add_trajectory(name, points, material=None, radius=0.015):
    if len(points) < 2:
        raise ValueError('Trajectory needs at least two points')
    curve_data = bpy.data.curves.new(name=name, type='CURVE')
    curve_data.dimensions = '3D'
    curve_data.bevel_depth = radius
    curve_data.bevel_resolution = 3
    spline = curve_data.splines.new('POLY')
    spline.points.add(len(points) - 1)
    for dst, p in zip(spline.points, points):
        dst.co = (*p, 1.0)
    obj = bpy.data.objects.new(name, curve_data)
    bpy.context.collection.objects.link(obj)
    if material is not None:
        obj.data.materials.append(material)
    return obj


def apply_matrix(obj, matrix_4x4):
    obj.matrix_world = Matrix(matrix_4x4)
    return obj
