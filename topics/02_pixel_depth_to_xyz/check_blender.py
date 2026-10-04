"""Open the saved .blend afresh and check animated geometry at key times."""
import json
import sys
from pathlib import Path
import bpy
from mathutils import Vector
ROOT=Path(__file__).resolve().parent;sys.path.insert(0,str(ROOT))
from geometry import state,point
bpy.ops.wm.open_mainfile(filepath=str(ROOT/'output/blender/pixel_depth_camera.blend'))
r=json.loads((ROOT/'assets/audio/manifest.json').read_text())
frames=[1]+[round((v['start']+1.7)*30)+1 for v in r]
errors=[]
for f in frames:
    bpy.context.scene.frame_set(f);s=state(f,r);x,y,z=point(s['z'])
    error=(bpy.data.objects['Reconstructed_P'].location-Vector((x,z,-y))).length
    assert error<2e-6,(f,error)
    assert abs(bpy.data.objects['Depth_plane_Z'].location.y-s['z'])<2e-6
    errors.append(error)
assert bpy.context.scene.render.fps==30
(ROOT/'output/blender/saved_project_validation.json').write_text(json.dumps({'checked_frames':frames,'max_position_error_m':max(errors),'status':'passed'},indent=2))
print('SAVED BLEND CHECK PASSED',max(errors))
