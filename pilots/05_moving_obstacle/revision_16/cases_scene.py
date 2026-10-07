"""R16 connected mechanism of unchanged R14 solver articulation on the established studio asset; no pose integration."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Quaternion,Euler,Vector
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import look,principled_material
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
kind=args[args.index('--case')+1] if '--case' in args else 'equal'
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'))
s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
rows=json.loads((H/'data'/f'baseline_{kind}.json').read_text())['samples']
root=bpy.data.objects['TurtleBot3'];wheels=[bpy.data.objects['TB3Wheel_left'],bpy.data.objects['TB3Wheel_right']]
root.animation_data_clear();root.rotation_mode='QUATERNION'
for w in wheels:w.animation_data_clear();w.rotation_mode='QUATERNION'
for o in bpy.data.objects:
 if any(x in o.name for x in ['Drum','Torus','ReferencePlan','ActualHistory','GoalRange']):o.hide_render=True;o.animation_data_clear()
body=[o for o in bpy.data.objects if o.type=='MESH' and not o.name.startswith('TB3Tyre_') and any(p==root for p in [o.parent,o.parent.parent if o.parent else None])]
for wheel in wheels:
 for face in [-1,1]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.004)
  dot=bpy.context.object;dot.name='WheelPhaseAnnotation';dot.parent=wheel;dot.location=(.024,face*.012,.01);dot.data.materials.append(principled_material('WheelPhase',(.02,.5,.9,1),roughness=.5))
# Local render-only guides; their coordinates follow recorded poses, not commands.
variant=args[args.index('--variant')+1] if '--variant' in args else 'material'
def guide(name,color,radius=.0015):
 data=bpy.data.curves.new(name,'CURVE');data.dimensions='3D';data.bevel_depth=radius;data.bevel_resolution=3
 obj=bpy.data.objects.new(name,data);s.collection.objects.link(obj);obj.data.materials.append(principled_material(name+'Mat',color,roughness=.55));return obj
def points(obj,pts):
 obj.data.splines.clear();sp=obj.data.splines.new('POLY');sp.points.add(len(pts)-1)
 for dst,src in zip(sp.points,pts):dst.co=(*src,1)
axle=guide('AnnotatedAxleReference',(.08,.12,.16,1))
heading=guide('AnnotatedBodyHeading',(.025,.46,.25,1),.002)
tracks=[guide('LeftMeasuredGroundHistory',(.12,.16,.2,1)),guide('RightMeasuredGroundHistory',(.02,.38,.65,1))]
startline=guide('SameStartGroundReference',(.34,.38,.4,1),.001)
start=[Vector(x) for x in rows[0]['wheel_positions_m']];start[0].z=start[1].z=.0015
points(startline,start)
bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.004)
center_mark=bpy.context.object;center_mark.name='AnnotatedBodyCenter';center_mark.data.materials.append(principled_material('CenterAnnotation',(.025,.46,.25,1),roughness=.5))
if variant!='baseline':
 for o in body:
  if not o.data.materials:continue
  # Faithful STL geometry and dimensions remain unchanged; only optical response changes.
  metal=any(t in o.name.lower() for t in ['plate','deck','base','frame'])
  old=o.data.materials[0]
  if metal:mat=principled_material('R16DeckMetal',(.13,.16,.20,1),metallic=.15,roughness=.46)
  else:
   mat=old.copy();mat.name='R16_'+old.name
   if mat.use_nodes:
    bs=next((n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED'),None)
    if bs:bs.inputs['Roughness'].default_value=.52
  o.data.materials[0]=mat
 if variant=='light':
  light_data=bpy.data.lights.new('R16BroadKey','AREA');light_data.energy=8;light_data.shape='DISK';light_data.size=.65
  key=bpy.data.objects.new('R16BroadKey',light_data);s.collection.objects.link(key)
  aim=Vector(rows[len(rows)//2]['root_position_m'])+Vector((0,0,.09));look(key,aim+Vector((.22,-.42,.65)),aim)
initial=Euler((math.pi/2,0,0)).to_quaternion()
cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO'
centers=[Vector(r['root_position_m']) for r in rows];center=sum(centers,Vector())/len(centers);center.z=.08
span=max((p-center).length for p in centers)
# Local camera follows actual body translation; wheel/body poses stay unmodified.
# Settled, tighter component view when the body is hidden, wide entry/exit.
cam.data.ortho_scale=.95
look(cam,center+Vector((.45,-.8,.7)),center)
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=64;s.render.use_motion_blur=False
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=50 if '--preview' in args else 100;s.render.fps=30;s.render.image_settings.file_format='PNG'
out=H/'output/cases'/kind;out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
frames=[1,40,76,91,145,181] if '--preview' in args else range(1,182)
if '--probe-frame' in args:frames=[int(args[args.index('--probe-frame')+1])]
if '--repair' in args:frames=list(range(26,56))+list(range(130,161))
if '--start-frame' in args:frames=range(int(args[args.index('--start-frame')+1]),int(args[args.index('--end-frame')+1])+1)
records=[]
for f in frames:
 row=rows[f-1];q=Quaternion(row['orientation_wxyz']);root.location=row['root_position_m'];root.rotation_quaternion=q
 # Symmetric easing around visibility changes, constant scale through the key mechanism.
 def ease(x):
  x=max(0.,min(1.,x));return x*x*(3-2*x)
 tight=min(ease((f-40)/15),ease((145-f)/15))
 cam.data.ortho_scale=.95-.33*tight
 aim=Vector(row['root_position_m'])+Vector((0,0,.065-.04*tight))
 look(cam,aim+Vector((.45,-.8,.7)),aim)
 for w,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  w.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted();w.location=q.inverted()@(Vector(pos)-Vector(row['root_position_m']))
 for o in body:o.hide_render=40<=f<=145
 measured=[Vector(x) for x in reversed(row['wheel_positions_m'])]
 points(axle,[v+Vector((0,0,.007)) for v in measured])
 ctr=sum(measured,Vector())/2;forward=q@Vector((1,0,0))
 points(heading,[ctr,ctr+forward*.09]);center_mark.location=ctr
 for obj in [axle,heading,center_mark]:obj.hide_render=not (40<=f<=145)
 for side,obj in enumerate(tracks):
  pts=[Vector(r['wheel_positions_m'][1-side]) for r in rows[:f]]
  for v in pts:v.z=.0018
  if len(pts)<2:pts=pts+pts
  points(obj,pts)
 bpy.context.view_layer.update()
 for w,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  error=(w.matrix_world.translation-Vector(pos)).length;assert error<1e-5,error
  angle=(w.matrix_world.to_quaternion()@initial).rotation_difference(Quaternion(world)).angle;assert min(abs(angle),abs(2*math.pi-angle))<1e-4,angle
 records.append({'frame':f,'source_t_s':row['t'],'wheel_pose_check':'PASS','body_hidden':40<=f<=145,'ortho_scale_m':cam.data.ortho_scale,'camera_target_m':list(aim),'annotations':'recorded wheel-center connection/body heading/ground history; not hardware/force','variant':variant})
 s.render.filepath=str(out/(f'candidate_{variant}_{f:04d}.png' if '--probe-frame' in args else f'preview_{f:04d}.png' if '--preview' in args else f'frames/frame_{f:04d}.png'));bpy.ops.render.render(write_still=True)
(out/(f'candidate_{variant}_mapping.json' if '--probe-frame' in args else 'preview_mapping.json' if '--preview' in args else f'mapping_{min(frames):04d}.json')).write_text(json.dumps({'records':records,'source':f'data/baseline_{kind}.json','mode':'actual solver-state replay; clear floor with drum hidden'},indent=2)+'\n')
