"""R15 framing of unchanged R14 solver articulation on the established studio asset; no pose integration."""
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
initial=Euler((math.pi/2,0,0)).to_quaternion()
cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO'
centers=[Vector(r['root_position_m']) for r in rows];center=sum(centers,Vector())/len(centers);center.z=.08
span=max((p-center).length for p in centers)
# Local camera follows actual body translation; wheel/body poses stay unmodified.
# Settled, tighter component view when the body is hidden, wide entry/exit.
cam.data.ortho_scale=.95
look(cam,center+Vector((.45,-.8,.7)),center)
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=24;s.render.use_motion_blur=False
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=50 if '--preview' in args else 100;s.render.fps=30;s.render.image_settings.file_format='PNG'
out=H/'output/cases'/kind;out.mkdir(parents=True,exist_ok=True);(out/'frames').mkdir(exist_ok=True)
frames=[1,40,76,91,145,181] if '--preview' in args else range(1,182)
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
 bpy.context.view_layer.update()
 for w,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  error=(w.matrix_world.translation-Vector(pos)).length;assert error<1e-5,error
  angle=(w.matrix_world.to_quaternion()@initial).rotation_difference(Quaternion(world)).angle;assert min(abs(angle),abs(2*math.pi-angle))<1e-4,angle
 records.append({'frame':f,'source_t_s':row['t'],'wheel_pose_check':'PASS','body_hidden':40<=f<=145,'ortho_scale_m':cam.data.ortho_scale,'camera_target_m':list(aim)})
 s.render.filepath=str(out/(f'preview_{f:04d}.png' if '--preview' in args else f'frames/frame_{f:04d}.png'));bpy.ops.render.render(write_still=True)
(out/('preview_mapping.json' if '--preview' in args else f'mapping_{min(frames):04d}.json')).write_text(json.dumps({'records':records,'source':f'data/baseline_{kind}.json','mode':'actual solver-state replay; clear floor with drum hidden'},indent=2)+'\n')
