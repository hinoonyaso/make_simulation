"""Validate the saved Blender project's keyframes, not just pre-render transforms."""
import json
import math
import sys
from pathlib import Path
import bpy
from bpy_extras.object_utils import world_to_camera_view

ROOT=Path(__file__).resolve().parent
sys.path.insert(0,str(ROOT))
from blender_motion import FRAME_COUNT,RECORDS,pose,fk

scene=bpy.context.scene
tip=bpy.data.objects['TCP_analytic_position']
frames={1,FRAME_COUNT}
for row in RECORDS:
    if row['chapter']!=10:
        frames.update([round(row['start']*30)+1,round((row['end']-.1)*30)+1])
frames.update(range(1,FRAME_COUNT,113))
errors=[]
for frame in sorted(frames):
    state=pose(frame)
    if state['chapter']==10:continue
    scene.frame_set(frame)
    bpy.context.view_layer.update()
    position=tip.matrix_world.translation
    expected=fk(state['q1'],state['q2'])
    err=math.hypot(position.x-expected[0],position.y-expected[1])
    assert err<3e-6,(frame,err)
    errors.append(err)
    projected=world_to_camera_view(scene,scene.camera,position)
    assert 0<projected.x<1 and 0<projected.y<1,(frame,tuple(projected))
assert scene.render.fps==30 and scene.frame_end==10407
report={'sampled_saved_frames':len(errors),'max_saved_tcp_xy_error_m':max(errors),
        'tcp_stays_in_camera':True,'timeline_frames':scene.frame_end,'fps':scene.render.fps}
(ROOT/'output/blender/saved_project_validation.json').write_text(json.dumps(report,indent=2))
print('SAVED_PROJECT_VALIDATION',json.dumps(report),flush=True)
scene.frame_set(1)
for screen in bpy.data.screens:
    for area in screen.areas:
        if area.type=='VIEW_3D':
            area.spaces.active.region_3d.view_perspective='CAMERA'
            area.spaces.active.shading.color_type='MATERIAL'
            area.spaces.active.overlay.show_overlays=False
bpy.context.preferences.filepaths.save_version=0
bpy.ops.wm.save_as_mainfile(filepath=str(ROOT/'output/blender/robot_manipulator_3d.blend'))
