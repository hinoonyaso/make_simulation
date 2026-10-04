from __future__ import annotations

import bpy
from mathutils import Vector


def create_target(name="CameraTarget", location=(0.0, 0.0, 0.8)):
    obj = bpy.data.objects.new(name, None)
    bpy.context.collection.objects.link(obj)
    obj.empty_display_type = 'PLAIN_AXES'
    obj.location = location
    return obj


def create_camera(name="Camera", location=(5.0, -5.0, 3.2), lens=50.0):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    bpy.context.collection.objects.link(cam)
    cam.location = location
    cam.data.lens = lens
    bpy.context.scene.camera = cam
    return cam


def look_at(obj, target, track_axis='-Z', up_axis='Y'):
    target_location = target.location if hasattr(target, 'location') else Vector(target)
    direction = target_location - obj.location
    obj.rotation_euler = direction.to_track_quat(track_axis, up_axis).to_euler()
    return obj


def add_track_to(obj, target, track_axis='TRACK_NEGATIVE_Z', up_axis='UP_Y'):
    c = obj.constraints.new(type='TRACK_TO')
    c.target = target
    c.track_axis = track_axis
    c.up_axis = up_axis
    return c


def setup_dof(camera, focus_object, fstop=4.0):
    camera.data.dof.use_dof = True
    camera.data.dof.focus_object = focus_object
    camera.data.dof.aperture_fstop = fstop
