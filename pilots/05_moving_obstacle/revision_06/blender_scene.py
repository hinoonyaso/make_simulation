"""Studio rendering of the validated planner-controlled solver trajectory."""
import json,sys,math
from pathlib import Path
import bpy
from mathutils import Quaternion,Euler
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import setup_studio,add_studio_floor,studio_lights,add_corridor,add_drum,load_turtlebot3,make_camera,look,add_trajectory,principled_material
DOC=json.loads((H/'visual_manifest.json').read_text());BEATS={b['id']:b for b in DOC['beats']}
OFF=json.loads((H/BEATS['B01']['comparison_trace']).read_text());ON=json.loads((H/BEATS['B05']['trace']).read_text())
N_OFF=round(BEATS['B01']['sec']*30);N_ON=round(BEATS['B05']['sec']*30)
s=setup_studio('FINAL',N_OFF+N_ON);s.eevee.taa_render_samples=48;s.render.use_motion_blur=False
add_studio_floor();studio_lights();add_corridor(1.45,2.5);add_drum((0,0),.3)
for o in bpy.data.objects:
 if o.type=='MESH' and ('Drum' in o.name or o.name.startswith('Torus')):
  for face in o.data.polygons:face.use_smooth=abs(face.normal.z)<.99
root,wheels,_=load_turtlebot3();root.rotation_mode='QUATERNION';initial=Euler((math.pi/2,0,0)).to_quaternion()
path=ON['plans'][1]['path']
plan=add_trajectory('ReferencePlan',[(x,y,.008) for x,y in path],principled_material('PlanGreen',(.03,.55,.28,1),roughness=.5),radius=.010)
# A target ring is an annotation, not a simulated obstacle.
bpy.ops.mesh.primitive_torus_add(major_radius=.15,minor_radius=.008,location=(1.3,0,.009));goal=bpy.context.object;goal.name='GoalRange';goal.data.materials.append(principled_material('Goal',(.03,.55,.28,1),roughness=.5))
rows=ON['samples'];actual=add_trajectory('ActualHistory',[(r['root_position_m'][0],r['root_position_m'][1],.014) for r in rows],principled_material('ActualBlue',(.04,.45,.8,1),roughness=.5),radius=.009)
# Spline reveal uses cumulative measured arclength so its tip matches the current pose.
cum=[0.]
for a,b in zip(rows,rows[1:]):cum.append(cum[-1]+math.dist(a['root_position_m'][:2],b['root_position_m'][:2]))
actual.data.bevel_factor_mapping_end='SPLINE'

def set_pose(row,frame=None):
 q=Quaternion(row['orientation_wxyz']);root.location=row['root_position_m'];root.rotation_quaternion=q
 if frame:root.keyframe_insert('location',frame=frame);root.keyframe_insert('rotation_quaternion',frame=frame)
 for wheel,world in zip(wheels,reversed(row['wheel_orientations_wxyz'])):
  wheel.rotation_mode='QUATERNION';wheel.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted()
  if frame:wheel.keyframe_insert('rotation_quaternion',frame=frame)

def on_time(t):
 # Align approach/goal hold to measured B05 phrases, leaving the source run unchanged.
 if t<9.1:return 2+(18.3-2)*t/9.1
 if t<12:return 18.3+(22-18.3)*(t-9.1)/2.9
 return 22+8*(t-12)/max(BEATS['B05']['sec']-12-1/30,.01)

mapping=[]
for i in range(N_OFF):
 t=i/30;source=0 if t<4.1 else min(8,8*(t-4.1)/(BEATS['B01']['sec']-4.1-1/30));idx=round(source*30);f=i+1
 set_pose(OFF['samples'][idx],f);mapping.append({'frame':f,'beat':'B01','source_t':source,'source_index':idx})
for obj in [plan,actual]:
 obj.hide_render=True;obj.keyframe_insert('hide_render',frame=1);obj.hide_render=False;obj.keyframe_insert('hide_render',frame=N_OFF+1)
for i in range(N_ON):
 source=min(30,on_time(i/30));idx=round(source*30);f=N_OFF+i+1;set_pose(ON['samples'][idx],f)
 actual.data.bevel_factor_end=cum[idx]/cum[-1];actual.data.keyframe_insert('bevel_factor_end',frame=f);mapping.append({'frame':f,'beat':'B05','source_t':source,'source_index':idx})
cam=make_camera();look(cam,(-.4,-3.0,5.5),(0,.12,.10));cam.data.lens=55
out=H/'output/blender';out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True);s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'frames/frame_')
(out/'source_mapping.json').write_text(json.dumps(mapping,indent=2)+'\n',newline='\n')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'avoidance_studio.blend'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--preview' in args:
 for f in [1,N_OFF,N_OFF+round(N_ON*.4),N_OFF+round(N_ON*.7),N_OFF+N_ON]:
  s.frame_set(f);s.render.filepath=str(out/f'preview_{f:04}.png');bpy.ops.render.render(write_still=True)
elif '--final-only' not in args:bpy.ops.render.render(animation=True)
# Final comparison uses exact source t=30 states, independent of presentation freeze.
for obj in [root,*wheels]:obj.animation_data_clear()
for case,data in [('off',OFF),('on',ON)]:
 for obj in [plan,actual]:
  obj.animation_data_clear();obj.data.animation_data_clear();obj.hide_render=(case=='off')
 actual.data.bevel_factor_end=1.;set_pose(data['samples'][-1]);bpy.context.view_layer.update();s.render.filepath=str(out/f'final_{case}.png');bpy.ops.render.render(write_still=True)
