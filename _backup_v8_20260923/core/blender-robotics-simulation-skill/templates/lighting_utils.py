from __future__ import annotations

import bpy
from camera_utils import look_at


def add_area_light(name, location, energy, size, target=(0.0, 0.0, 0.8), color=(1.0, 1.0, 1.0)):
    data = bpy.data.lights.new(name=name, type='AREA')
    data.energy = energy
    data.shape = 'DISK'
    data.size = size
    data.color = color
    obj = bpy.data.objects.new(name, data)
    bpy.context.collection.objects.link(obj)
    obj.location = location
    look_at(obj, target)
    return obj


def setup_three_point_lighting(subject=(0.0, 0.0, 0.8), scale=1.0):
    key = add_area_light('Key', (4.5, -4.0, 5.0), 1000 * scale, 4.0, subject)
    fill = add_area_light('Fill', (-3.8, -2.0, 2.8), 420 * scale, 3.0, subject)
    rim = add_area_light('Rim', (2.0, 4.0, 4.5), 700 * scale, 3.0, subject)
    return {'key': key, 'fill': fill, 'rim': rim}


def setup_world(strength=0.28, color=(0.055, 0.065, 0.085, 1.0)):
    world = bpy.context.scene.world or bpy.data.worlds.new('World')
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get('Background')
    bg.inputs['Color'].default_value = color
    bg.inputs['Strength'].default_value = strength
    return world
