"""Studio rendering of the validated planner-controlled solver trajectory."""
import json,sys,math
from pathlib import Path
import bpy
from mathutils import Quaternion,Euler,Vector
H=Path(__file__).resolve().parent
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
BASELINE=False
R08_PATHS='--r08-paths' in args
CAMERA_ONLY='--camera-only' in args
sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import setup_studio,add_studio_floor,studio_lights,add_corridor,add_drum,load_turtlebot3,make_camera,look,add_trajectory,principled_material
DOC=json.loads((H/'visual_manifest.json').read_text());BEATS={b['id']:b for b in DOC['beats']}
OFF=json.loads((H/BEATS['B01']['trace']).read_text());ON=json.loads((H/BEATS['B05']['trace']).read_text())
N_OFF=round(BEATS['B01']['sec']*30);N_ON=round(BEATS['B05']['sec']*30)
AUDIO=json.loads((H/'assets/audio/manifest.json').read_text());CUES=json.loads((H/'output/caption_timing.json').read_text())
b05_start=next(r['start'] for r in AUDIO if r['beat']=='B05')
b05_cues=[r for r in CUES if b05_start<=r['start']<b05_start+BEATS['B05']['sec']]
GOAL_START=b05_cues[2]['start']-b05_start
HOLD_START=GOAL_START+2.9
s=setup_studio('FINAL',N_OFF+N_ON);s.eevee.taa_render_samples=48;s.render.use_motion_blur=False
def add_faithful_drum(center,radius,height=.58):
 def cylinder(name,z,r,depth,bevel,material):
  bpy.ops.mesh.primitive_cylinder_add(vertices=192,radius=r,depth=depth,location=(center[0],center[1],z));o=bpy.context.object;o.name=name;o.data.materials.append(material)
  mod=o.modifiers.new('RenderBevel','BEVEL');mod.width=bevel;mod.segments=6;mod.limit_method='ANGLE'
  for face in o.data.polygons:face.use_smooth=True if o.name.startswith('Torus') else abs(face.normal.z)<.99
  return o
 mat=principled_material('Drum',(.62,.09,.025,1),metallic=.15,roughness=.48)
 cylinder('Drum',height/2,radius,height,.02,mat)
 for z in [.31*height,.69*height]:
  bpy.ops.mesh.primitive_torus_add(major_segments=192,minor_segments=24,major_radius=radius,minor_radius=.012,location=(center[0],center[1],z));o=bpy.context.object;o.data.materials.append(mat)
  for face in o.data.polygons:face.use_smooth=True
 cylinder('DrumLid',height+.005,radius*.82,.012,.004,principled_material('DrumLid',(.48,.07,.02,1),metallic=.12,roughness=.5))
add_studio_floor();studio_lights();add_corridor(1.45,2.5);add_faithful_drum((0,0),.3)
for o in bpy.data.objects:
 if o.type=='MESH' and ('Drum' in o.name or o.name.startswith('Torus')):
  for face in o.data.polygons:face.use_smooth=True if o.name.startswith('Torus') else abs(face.normal.z)<.99
root,wheels,_=load_turtlebot3();root.rotation_mode='QUATERNION';initial=Euler((math.pi/2,0,0)).to_quaternion()
# Local polish only: no collision/body/trace changes.
if not BASELINE and not CAMERA_ONLY:
 for name,color,metal,rough in [('TB3Chassis',(.025,.029,.035,1),.15,.5),('TB3Sensor',(.006,.007,.009,1),.05,.38),('TB3Tyre',(.018,.018,.02,1),0,.9),('Drum',(.62,.09,.025,1),.15,.48),('DrumLid',(.48,.07,.02,1),.12,.5)]:
  mat=bpy.data.materials.get(name)
  if mat:
   shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED')
   shader.inputs['Base Color'].default_value=color;shader.inputs['Metallic'].default_value=metal;shader.inputs['Roughness'].default_value=rough
 key=bpy.data.objects['Key'];key.location=(-1.5,2.5,5.5);key.rotation_euler=(Vector((0,0,.15))-key.location).to_track_quat('-Z','Y').to_euler();key.data.energy=1450;key.data.size=3.5
 bpy.data.objects['Fill'].data.energy=280
 bpy.data.objects['Rim'].data.energy=400
 s.world.node_tree.nodes['Background'].inputs['Strength'].default_value=.30
path=ON['plans'][1]['path']
plan=add_trajectory('ReferencePlan',[(x,y,.008) for x,y in path],principled_material('PlanGreen',((.03,.55,.28,1) if R08_PATHS else (.008,.22,.07,1)),roughness=(.5 if R08_PATHS else .85)),radius=.010)
# A target ring is an annotation, not a simulated obstacle.
bpy.ops.mesh.primitive_torus_add(major_segments=192,minor_segments=24,major_radius=.15,minor_radius=.008,location=(1.3,0,.009));goal=bpy.context.object;goal.name='GoalRange'
for face in goal.data.polygons:face.use_smooth=True
goal.data.materials.append(principled_material('Goal',((.03,.55,.28,1) if R08_PATHS else (.008,.22,.07,1)),roughness=.85))
# Preserve the existing opening annotation; strengthen the goal cue at the replay.
# The goal is visible in B01; R10 rerenders both beats after tessellation changes.
goal_shader=next(n for n in goal.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED')
for f in [1,N_OFF]:
 goal_shader.inputs['Base Color'].default_value=(.03,.55,.28,1);goal_shader.inputs['Base Color'].keyframe_insert('default_value',frame=f)
 goal_shader.inputs['Roughness'].default_value=.5;goal_shader.inputs['Roughness'].keyframe_insert('default_value',frame=f)
goal_shader.inputs['Base Color'].default_value=(.03,.55,.28,1) if R08_PATHS else (.008,.22,.07,1);goal_shader.inputs['Base Color'].keyframe_insert('default_value',frame=N_OFF+1)
goal_shader.inputs['Roughness'].default_value=.5 if R08_PATHS else .85;goal_shader.inputs['Roughness'].keyframe_insert('default_value',frame=N_OFF+1)
rows=ON['samples'];actual=add_trajectory('ActualHistory',[(r['root_position_m'][0],r['root_position_m'][1],.014) for r in rows],principled_material('ActualBlue',((.04,.45,.8,1) if R08_PATHS else (.008,.15,.48,1)),roughness=(.5 if R08_PATHS else .85)),radius=.009)
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
 if t<GOAL_START:return 2+(18.3-2)*t/GOAL_START
 if t<HOLD_START:return 18.3+(22-18.3)*(t-GOAL_START)/2.9
 return 22+8*(t-HOLD_START)/max(BEATS['B05']['sec']-HOLD_START-1/30,.01)

mapping=[]
for i in range(N_OFF):
 t=i/30;source=0 if t<4.1 else min(8,8*(t-4.1)/(BEATS['B01']['sec']-4.1-1/30));idx=round(source*30);f=i+1
 set_pose(OFF['samples'][idx],f);mapping.append({'frame':f,'beat':'B01','source_t':source,'source_index':idx})
for obj in [plan,actual]:
 obj.hide_render=True;obj.keyframe_insert('hide_render',frame=1);obj.hide_render=False;obj.keyframe_insert('hide_render',frame=N_OFF+1)
for i in range(N_ON):
 source=min(30,on_time(i/30));idx=round(source*30);f=N_OFF+i+1;set_pose(ON['samples'][idx],f)
 actual.data.bevel_factor_end=cum[idx]/cum[-1];actual.data.keyframe_insert('bevel_factor_end',frame=f);mapping.append({'frame':f,'beat':'B05','source_t':source,'source_index':idx})
cam=make_camera();cam.data.lens=55
# Settled views switch at meaningful events; all poses remain solver samples.
def camera_for_frame(frame):
 if frame<=N_OFF:
  if frame/30<6.1:look(cam,(-.4,-3.,5.5),(0,.12,.10));return 'overview'
  look(cam,(-.9,-1.65,1.65),(-.3,0,.14)) if BASELINE else look(cam,(-1.35,-2.4,2.4),(-.55,0,.14));return 'contact'
 t=(frame-N_OFF-1)/30
 if t<3.:look(cam,(-.4,-3.,5.5),(0,.12,.10));return 'overview'
 if t<GOAL_START:look(cam,(-.25,-1.35,3.35) if (BASELINE or '--materials-only' in args) else (-.25,-.8,3.6),(0,.55,.10));return 'turn_clearance'
 look(cam,(1.,-1.25,1.6) if (BASELINE or '--materials-only' in args) else (.72,-1.15,1.28),(1.18,0,.10));return 'goal_hold'
for record in mapping:record['view']=camera_for_frame(record['frame'])
def apply_camera(scene):camera_for_frame(scene.frame_current)
bpy.app.handlers.frame_change_post.append(apply_camera)
camera_for_frame(1)
out=H/'output/blender';out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True);s.render.image_settings.file_format='PNG';s.render.filepath=str(out/'frames/frame_')
(out/'source_mapping.json').write_text(json.dumps(mapping,indent=2)+'\n',newline='\n')
bpy.ops.wm.save_as_mainfile(filepath=str(out/'avoidance_studio.blend'))
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
if '--single-frame' in args:
 f=int(args[args.index('--single-frame')+1]);s.frame_set(f);s.render.filepath=str(out/f'patch_{"r08" if R08_PATHS else "r10"}_{f:04}.png');bpy.ops.render.render(write_still=True);raise SystemExit(0)
elif '--craft' in args:
 s.eevee.taa_render_samples=24
 for f in [N_OFF,N_OFF+150,N_OFF+187,N_OFF+350]:
  s.frame_set(f)
  if '--materials-only' in args:
   if f==N_OFF+150:look(cam,(-.25,-1.35,3.35),(0,.55,.10))
   if f==N_OFF+350:look(cam,(1.,-1.25,1.6),(1.22,0,.10))
  variant='baseline' if BASELINE else ('camera' if CAMERA_ONLY else ('materials' if '--materials-only' in args else 'selected'))
  s.render.filepath=str(out/f'craft_{variant}_{f:04}.png');bpy.ops.render.render(write_still=True)
 raise SystemExit(0)
elif '--preview' in args:
 s.eevee.taa_render_samples=24
 for f in [1,N_OFF,N_OFF+round(N_ON*.22),N_OFF+round(N_ON*.4),N_OFF+round(N_ON*.7),N_OFF+N_ON]:
  s.frame_set(f);s.render.filepath=str(out/f'preview_{f:04}.png');bpy.ops.render.render(write_still=True)
elif '--final-only' not in args:
 if '--critical' in args:s.frame_start=N_OFF+1;s.eevee.taa_render_samples=16;s.render.resolution_percentage=50
 if '--start-frame' in args:s.frame_start=int(args[args.index('--start-frame')+1])
 if '--end-frame' in args:s.frame_end=int(args[args.index('--end-frame')+1])
 bpy.ops.render.render(animation=True)
if '--batch' in args and s.frame_end<N_OFF+N_ON:raise SystemExit(0)
# Final comparison uses exact source t=30 states, independent of presentation freeze.
bpy.app.handlers.frame_change_post.remove(apply_camera)
look(cam,(-.4,-3.,5.5),(0,.12,.10))
for obj in [root,*wheels]:obj.animation_data_clear()
for case,data in [('off',OFF),('on',ON)]:
 for obj in [plan,actual]:
  obj.animation_data_clear();obj.data.animation_data_clear();obj.hide_render=(case=='off')
 actual.data.bevel_factor_end=1.;set_pose(data['samples'][-1]);bpy.context.view_layer.update();s.render.filepath=str(out/f'final_{case}.png');bpy.ops.render.render(write_still=True)
