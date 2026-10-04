from __future__ import annotations
import bpy
from pathlib import Path
from camera_utils import create_camera, create_target, look_at, setup_dof
from geometry_utils import add_floor, add_cube, add_cylinder, add_sphere, curve_between, apply_bevel
from lighting_utils import setup_three_point_lighting, setup_world
from material_utils import assign_material, principled_material
from robotics_visual_utils import add_coordinate_frame, add_point, add_trajectory, apply_matrix, add_stylized_robot_arm, add_planar_arm_rig, keyframe_joint_angles
from animation_utils import StateObject, keyframe_trace, set_linear_interpolation
from framing_utils import frame_objects, world_bounds
from trace_utils import load_trace, positions
from asset_utils import append_collection

FPS=30
RESOLUTIONS={"preview":(960,540),"1080p":(1920,1080),"1440p":(2560,1440)}
OUT=Path(bpy.path.abspath("//renders"))

COLORS={
    "bg":(0.011,0.017,0.033,1), "neutral":(0.18,0.22,0.30,1),
    "sensor":(0.039,0.55,0.89,1), "active":(0.96,0.58,0.02,1),
    "result":(0.04,0.68,0.44,1), "error":(0.94,0.20,0.20,1),
    "learned":(0.49,0.23,0.93,1), "x":(0.86,0.08,0.12,1),
    "y":(0.05,0.65,0.24,1), "z":(0.05,0.31,0.98,1),
}

PROFILES={
    "PREVIEW":("BLENDER_EEVEE","preview",32,"AgX"),
    "FINAL":("BLENDER_EEVEE","1080p",128,"AgX"),
    "DELIVERY":("BLENDER_EEVEE","1440p",160,"AgX"),
    "TECHNICAL":("BLENDER_EEVEE","1080p",96,"Khronos PBR Neutral"),
    "HERO":("CYCLES","1440p",256,"AgX"),
}


def clear():
    bpy.ops.object.select_all(action='SELECT')
    bpy.ops.object.delete(use_global=False)


def _engine(scene,name):
    try: scene.render.engine=name
    except TypeError:
        if name=='BLENDER_EEVEE': scene.render.engine='BLENDER_EEVEE_NEXT'
        else: raise


def render_setup(profile='FINAL', video='output.mp4', transparent=False):
    p=profile.upper(); eng,res_key,samples,view=PROFILES[p]
    width,height=RESOLUTIONS[res_key]
    s=bpy.context.scene; OUT.mkdir(parents=True,exist_ok=True)
    _engine(s,eng); s.render.fps=FPS
    s.render.resolution_x,s.render.resolution_y=width,height; s.render.resolution_percentage=100
    try: s.view_settings.view_transform=view
    except (TypeError,ValueError): s.view_settings.view_transform='AgX'
    s.view_settings.exposure=0; s.render.film_transparent=bool(transparent)
    if s.render.engine=='CYCLES':
        s.cycles.samples=samples; s.cycles.use_denoising=True; s.cycles.use_adaptive_sampling=True
    elif hasattr(s,'eevee') and hasattr(s.eevee,'taa_render_samples'):
        s.eevee.taa_render_samples=samples
    s.render.image_settings.file_format='FFMPEG'; s.render.ffmpeg.format='MPEG4'; s.render.ffmpeg.codec='H264'
    s.render.ffmpeg.constant_rate_factor='HIGH'; s.render.ffmpeg.ffmpeg_preset='GOOD'; s.render.filepath=str(OUT/video)
    return s


def material_library():
    return {
        'neutral': principled_material('Neutral', (0.26,0.31,0.40,1), roughness=.34, metallic=.18),
        'robot_link': principled_material('RobotLink', (0.32,0.26,0.62,1), roughness=.30, metallic=.12),
        'robot_joint': principled_material('RobotJoint', (0.10,0.12,0.17,1), roughness=.27, metallic=.35),
        'sensor': principled_material('Sensor', COLORS['sensor'], roughness=.35, metallic=.08),
        'active': principled_material('Active', COLORS['active'], roughness=.32, metallic=.05),
        'result': principled_material('Result', COLORS['result'], roughness=.38, metallic=.04),
        'error': principled_material('Error', COLORS['error'], roughness=.38, metallic=.02),
        'learned': principled_material('Learned', COLORS['learned'], roughness=.38, metallic=.05),
        'floor': principled_material('Floor', (0.035,0.045,0.065,1), roughness=.72, metallic=0),
    }


def camera_shot(kind='wide', subject=(0,0,.8)):
    specs={
        'wide':((5.2,-5.2,3.4),50,None,6),
        'medium':((4.0,-4.0,2.6),60,None,6),
        'detail':((2.5,-2.5,1.8),85,None,4),
        'hero':((3.25,-3.25,2.25),70,None,4.5),
        'top':((0,0,8),60,'ORTHO',6),
    }
    loc,lens,typ,ortho=specs[kind]
    t=create_target(location=subject); c=create_camera(location=loc,lens=lens)
    if typ: c.data.type=typ; c.data.ortho_scale=ortho
    look_at(c,t); return c,t


def bootstrap(profile='FINAL', subject=(0,0,.8), camera='wide', style='minimal', floor=True, transparent=False):
    clear(); mats=material_library(); render_setup(profile, transparent=transparent)
    setup_world(.12, COLORS['bg'])
    fl=None
    if floor:
        fl=add_floor(14,0); assign_material(fl,mats['floor'])
    setup_three_point_lighting(subject, .85)
    cam,target=camera_shot(camera,subject)
    return {'scene':bpy.context.scene,'materials':mats,'floor':fl,'camera':cam,'target':target,'colors':COLORS}



def frame_hero(ctx, objects, margin=1.22):
    """Fit selected hero meshes into the current camera before manual art-direction tweaks."""
    return frame_objects(ctx['camera'], ctx['target'], objects, margin=margin)

def transparent_sequence(directory='frames'):
    d=OUT/directory; d.mkdir(parents=True,exist_ok=True)
    s=bpy.context.scene; s.render.film_transparent=True
    s.render.image_settings.file_format='PNG'; s.render.image_settings.color_mode='RGBA'
    s.render.filepath=str(d/'frame_'); return d


def image_sequence(directory='frames'):
    d=OUT/directory; d.mkdir(parents=True,exist_ok=True)
    s=bpy.context.scene; s.render.image_settings.file_format='PNG'; s.render.filepath=str(d/'frame_'); return d


def review(frames=(1,), directory='review'):
    s=bpy.context.scene; d=OUT/directory; d.mkdir(parents=True,exist_ok=True)
    fmt,path,cur=s.render.image_settings.file_format,s.render.filepath,s.frame_current
    s.render.image_settings.file_format='PNG'
    try:
        for f in frames:
            s.frame_set(int(f)); s.render.filepath=str(d/f'review_{int(f):04d}.png'); bpy.ops.render.render(write_still=True)
    finally:
        s.frame_set(cur); s.render.image_settings.file_format=fmt; s.render.filepath=path
    return d

__all__=['bpy','COLORS','bootstrap','render_setup','camera_shot','look_at','image_sequence','transparent_sequence','review',
         'add_cube','add_cylinder','add_sphere','curve_between','apply_bevel','assign_material','principled_material',
         'add_coordinate_frame','add_point','add_trajectory','apply_matrix','add_stylized_robot_arm','setup_dof',
         'StateObject','keyframe_trace','set_linear_interpolation','frame_objects','frame_hero','world_bounds','load_trace','positions','append_collection',
         'add_planar_arm_rig','keyframe_joint_angles']
