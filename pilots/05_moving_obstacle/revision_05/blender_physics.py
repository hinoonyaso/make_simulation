"""Faithful studio playback of recorded solver state; no new physical claims."""
import json,sys,math
from pathlib import Path
import bpy
from mathutils import Quaternion,Euler
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import setup_studio,add_studio_floor,studio_lights,add_corridor,add_drum,load_turtlebot3,make_camera,look
DOC=json.loads((HERE/'visual_manifest.json').read_text());beat=next(b for b in DOC['beats'] if b['id']=='P02')
s=setup_studio('FINAL',482);s.eevee.taa_render_samples=64;s.render.use_motion_blur=False
add_studio_floor();studio_lights();add_corridor(1.25,2.5)
root,wheels,_=load_turtlebot3();root.rotation_mode='QUATERNION'
before=set(bpy.data.objects);add_drum((0,0),.3);drums=set(bpy.data.objects)-before
for obj in drums:
    if obj.type=='MESH':
        for face in obj.data.polygons:face.use_smooth=abs(face.normal.z)<.99
initial=Euler((math.pi/2,0,0)).to_quaternion()
for case,key,offset in [('clear','comparison_trace',0),('blocked','trace',241)]:
    rows=json.loads((HERE/beat[key]).read_text())['samples']
    for i,row in enumerate(rows):
        frame=offset+i+1;q=Quaternion(row['orientation_wxyz'])
        root.location=row['root_position_m'];root.rotation_quaternion=q
        root.keyframe_insert('location',frame=frame);root.keyframe_insert('rotation_quaternion',frame=frame)
        for wheel,world in zip(wheels,reversed(row['wheel_orientations_wxyz'])):
            wheel.rotation_mode='QUATERNION';wheel.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted()
            wheel.keyframe_insert('rotation_quaternion',frame=frame)
    for obj in drums:obj.hide_render=(case=='clear');obj.keyframe_insert('hide_render',frame=offset+1)
cam=make_camera();look(cam,(-1.65,-2.8,1.65),(-.48,0,.18));cam.data.lens=58
# Fixed camera covers the swept start/end robot and drum bounds used in the probe;
# retain +X screen-right orientation for the matching Manim projection.
s.render.image_settings.file_format='PNG';out=HERE/'output/blender';out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
s.render.filepath=str(out/'frames/frame_');bpy.ops.wm.save_as_mainfile(filepath=str(out/'physics_studio.blend'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--preview' in args:
    for f in [1,241,242,460]:
        s.frame_set(f);s.render.filepath=str(out/f'preview_{f:03}.png');bpy.ops.render.render(write_still=True)
else:bpy.ops.render.render(animation=True)
