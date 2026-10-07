"""Frozen source-pose component view; no new physics execution."""
import bpy,json,sys
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import look
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'))
s=bpy.context.scene;s.frame_set(279)
# A static overhead view exposes the same faithful wheel pair. No invented internals.
root=bpy.data.objects.get('TB3Root')
print('ROOTS',[(o.name,list(o.location)) for o in bpy.data.objects if o.type=='EMPTY'])
row=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text())['samples'][60]
x,y,z=row['root_position_m'];cam=s.camera
cam.animation_data_clear();bpy.app.handlers.frame_change_post.clear()
look(cam,(x,y,1.6),(x,y,.10));cam.data.type='ORTHO';cam.data.ortho_scale=.65
s.render.engine='CYCLES';s.cycles.samples=24;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=30
s.render.filepath=str(H/'output/component_top.png');bpy.ops.render.render(write_still=True)
