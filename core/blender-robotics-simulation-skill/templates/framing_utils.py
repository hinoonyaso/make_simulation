from __future__ import annotations
import math
from mathutils import Vector
from camera_utils import look_at

def world_bounds(objects):
    pts=[]
    for obj in objects:
        if obj is None or not hasattr(obj,'bound_box'): continue
        pts.extend([obj.matrix_world @ Vector(corner) for corner in obj.bound_box])
    if not pts: raise ValueError('no renderable bounds')
    lo=Vector((min(p.x for p in pts),min(p.y for p in pts),min(p.z for p in pts)))
    hi=Vector((max(p.x for p in pts),max(p.y for p in pts),max(p.z for p in pts)))
    return lo,hi

def frame_objects(camera, target, objects, margin=1.25, min_distance=.8):
    """Fit hero objects in perspective view while preserving current viewing direction."""
    lo,hi=world_bounds(objects); center=(lo+hi)*.5; extent=(hi-lo)
    radius=max(extent.length*.5, .15)
    target.location=center
    if camera.data.type=='ORTHO':
        camera.data.ortho_scale=max(extent.x, extent.y, extent.z)*margin
        look_at(camera,target); return camera
    direction=(camera.location-center)
    if direction.length < 1e-6: direction=Vector((1,-1,.65))
    direction.normalize()
    fov=min(float(camera.data.angle_x), float(camera.data.angle_y))
    dist=max(radius/max(math.sin(fov*.5),1e-3)*margin, min_distance)
    camera.location=center+direction*dist
    look_at(camera,target)
    return camera
