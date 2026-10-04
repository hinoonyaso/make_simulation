from __future__ import annotations
import bpy
from mathutils import Vector, Euler, Quaternion

class StateObject:
    """Small wrapper for repeatable transform/visibility state keyframes."""
    def __init__(self, obj): self.obj=obj
    def state(self, frame, location=None, rotation=None, scale=None, visible=None):
        o=self.obj
        if location is not None:
            o.location=location; o.keyframe_insert(data_path="location", frame=frame)
        if rotation is not None:
            if len(rotation)==4:
                o.rotation_mode='QUATERNION'; o.rotation_quaternion=Quaternion(rotation); o.keyframe_insert(data_path="rotation_quaternion", frame=frame)
            else:
                o.rotation_mode='XYZ'; o.rotation_euler=Euler(rotation); o.keyframe_insert(data_path="rotation_euler", frame=frame)
        if scale is not None:
            o.scale=scale; o.keyframe_insert(data_path="scale", frame=frame)
        if visible is not None:
            o.hide_viewport=not visible; o.hide_render=not visible
            o.keyframe_insert(data_path="hide_viewport", frame=frame); o.keyframe_insert(data_path="hide_render", frame=frame)
        return self


def keyframe_trace(obj, samples, fps=30, time_key='t', position_key='position'):
    """Replay supplied timestamped positions faithfully."""
    if not samples: return obj
    for s in samples:
        t=float(s[time_key]); pos=s[position_key]
        frame=round(t*fps)+1
        obj.location=pos
        obj.keyframe_insert(data_path='location', frame=frame)
    return obj


def fcurves(idb):
    """F-curves of an animated ID. Blender 5 layered actions removed Action.fcurves."""
    ad=getattr(idb,'animation_data',None)
    if not ad or not ad.action: return []
    if hasattr(ad.action,'fcurves'): return list(ad.action.fcurves)
    from bpy_extras import anim_utils
    bag=anim_utils.action_get_channelbag_for_slot(ad.action, ad.action_slot)
    return list(bag.fcurves) if bag else []


def set_interpolation(idb, mode='LINEAR', paths=None):
    for fc in fcurves(idb):
        if paths is None or fc.data_path in paths:
            for kp in fc.keyframe_points: kp.interpolation=mode
    return idb


def set_linear_interpolation(obj):
    return set_interpolation(obj,'LINEAR')
