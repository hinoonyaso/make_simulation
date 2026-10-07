"""R18 optical rerender of the same R06 solver samples and R10 source/camera mapping."""
import bpy,json,sys,math,shutil
from pathlib import Path
from mathutils import Quaternion,Euler,Vector
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import look
from surface_treatment import apply_surface
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
variant=args[args.index('--variant')+1] if '--variant' in args else 'combined'
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'));s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
settings=apply_surface(s,variant,baseline='avoidance')
mapping=json.loads((H.parent/'revision_10/output/blender/source_mapping.json').read_text())
ON=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text());OFF=json.loads((H.parent/'revision_06/data/baseline_planner_off.json').read_text())
root=bpy.data.objects['TurtleBot3'];wheels=[bpy.data.objects['TB3Wheel_left'],bpy.data.objects['TB3Wheel_right']];initial=Euler((math.pi/2,0,0)).to_quaternion()
for o in [root,*wheels]:o.animation_data_clear();o.rotation_mode='QUATERNION'
plan=bpy.data.objects['ReferencePlan'];actual=bpy.data.objects['ActualHistory'];goal=bpy.data.objects['GoalRange']
for o in [plan,actual,goal]:o.animation_data_clear();o.data.animation_data_clear()
for name,color in [('PlanGreen',(.03,.55,.28,1)),('ActualBlue',(.04,.45,.8,1)),('Goal',(.03,.55,.28,1))]:
 mat=bpy.data.materials[name];mat.animation_data_clear();mat.node_tree.animation_data_clear();shader=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');shader.inputs['Base Color'].default_value=color;shader.inputs['Roughness'].default_value=.5
cum=[0.]
for a,b in zip(ON['samples'],ON['samples'][1:]):cum.append(cum[-1]+math.dist(a['root_position_m'][:2],b['root_position_m'][:2]))
cam=s.camera;cam.animation_data_clear();cam.data.type='PERSP';cam.data.lens=55
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=64;s.render.use_motion_blur=False;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=30;s.render.image_settings.file_format='PNG'
out=H/'output/blender';out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
(out/f'settings_{variant}.json').write_text(json.dumps(settings,indent=2)+'\n')
frames=list(range(1,279))+list(range(317,723))
if '--probe-frame' in args:frames=[int(args[args.index('--probe-frame')+1])]
records=[];cache={}
for f in frames:
 record=mapping[f-1];source=ON if record['beat']=='B05' else OFF;idx=record['source_index'];row=source['samples'][idx];q=Quaternion(row['orientation_wxyz']);root.location=row['root_position_m'];root.rotation_quaternion=q
 for wheel,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  wheel.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted();wheel.location=q.inverted()@(Vector(pos)-Vector(row['root_position_m']))
 plan.hide_render=actual.hide_render=record['beat']=='B01';goal.hide_render=False;actual.data.bevel_factor_end=cum[idx]/cum[-1] if record['beat']=='B05' else 0
 positions={'overview':((-.4,-3,5.5),(0,.12,.10)),'contact':((-1.35,-2.4,2.4),(-.55,0,.14)),'turn_clearance':((-.25,-.8,3.6),(0,.55,.10)),'goal_hold':((.72,-1.15,1.28),(1.18,0,.10))}
 look(cam,*positions[record['view']]);bpy.context.view_layer.update()
 errors=[]
 for wheel,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  err=(wheel.matrix_world.translation-Vector(pos)).length;ang=(wheel.matrix_world.to_quaternion()@initial).rotation_difference(Quaternion(world)).angle;assert err<1e-5 and min(abs(ang),abs(2*math.pi-ang))<1e-4;errors.append(err)
 target=out/(f'candidate_{variant}_{f:04d}.png' if '--probe-frame' in args else f'frames/frame_{f:04d}.png')
 signature=(record['beat'],idx,record['view'])
 if signature in cache:shutil.copy2(cache[signature],target)
 else:s.render.filepath=str(target);bpy.ops.render.render(write_still=True);cache[signature]=target
 records.append({**record,'recorded_pose_t':row['t'],'wheel_pose_check':'PASS','max_position_error_m':max(errors),'camera_position':list(cam.location),'variant':variant})
(out/(f'candidate_{variant}_{frames[0]:04d}_mapping.json' if '--probe-frame' in args else 'mapping.json')).write_text(json.dumps({'records':records,'unique_states':len(cache),'source':'read-only R06/R10; actual recorded wheel positions and rotations'},indent=2)+'\n')
