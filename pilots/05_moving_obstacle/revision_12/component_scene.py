"""Faithful recorded articulation; visibility and phase dots are render annotations."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Quaternion,Euler,Vector
H=Path(__file__).resolve().parent
sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import look,principled_material
args=sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else []
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'))
s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear()
D=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text());rows=D['samples']
root=bpy.data.objects['TurtleBot3'];wheels=[bpy.data.objects['TB3Wheel_left'],bpy.data.objects['TB3Wheel_right']]
root.animation_data_clear();root.rotation_mode='QUATERNION'
for w in wheels:w.animation_data_clear();w.rotation_mode='QUATERNION'
for obj in ['ReferencePlan','ActualHistory','GoalRange']:
 o=bpy.data.objects.get(obj)
 if o:o.hide_render=True;o.animation_data_clear()
robot_meshes=[o for o in bpy.data.objects if o.type=='MESH' and any(p==root for p in [o.parent,o.parent.parent if o.parent else None])]
body=[o for o in robot_meshes if not o.name.startswith('TB3Tyre_')]
initial=Euler((math.pi/2,0,0)).to_quaternion()
phase=[]
for wheel,color in zip(wheels,[(.9,.92,.96,1),(.02,.5,.9,1)]):
 for face in [-1,1]:
  bpy.ops.mesh.primitive_uv_sphere_add(segments=16,ring_count=8,radius=.0035)
  dot=bpy.context.object;dot.name='PhaseAnnotation_'+wheel.name+str(face);dot.parent=wheel;dot.location=(.024,face*.012,.01);dot.data.materials.append(principled_material(dot.name,color,roughness=.5));phase.append(dot)
cam=s.camera;cam.animation_data_clear();cam.data.type='ORTHO';cam.data.ortho_scale=.58
# Fixed oblique camera, bounded around the swept interval, exposes both wheel faces.
centers=[Vector(r['root_position_m']) for r in rows[60:85]];center=sum(centers,Vector())/len(centers);center.z=.055
look(cam,center+Vector((.34,-.52,.32)),center)
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=24;s.render.use_motion_blur=False
s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=50 if '--preview' in args else 100;s.render.fps=30
s.render.image_settings.file_format='PNG';out=H/'output/component';out.mkdir(exist_ok=True);(out/'frames').mkdir(exist_ok=True)
records=[]
def state(frame):
 idx=60+round(24*(frame-1)/83);row=rows[idx];q=Quaternion(row['orientation_wxyz']);root.location=row['root_position_m'];root.rotation_quaternion=q
 for wheel,world,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  wheel.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted()
  wheel.location=q.inverted()@(Vector(pos)-Vector(row['root_position_m']))
 # View aid only; the trace and physical geometry remain unchanged.
 for obj in body:obj.hide_render=10<=frame<=74
 bpy.context.view_layer.update()
 errors=[]
 for wheel,expected,pos in zip(wheels,reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
  observed=wheel.matrix_world.to_quaternion()@initial
  error=abs(observed.rotation_difference(Quaternion(expected)).angle);error=min(error,abs(2*math.pi-error));assert error<1e-4,error
  position_error=(wheel.matrix_world.translation-Vector(pos)).length;assert position_error<1e-5,position_error
  errors.append({'wheel':wheel.name,'orientation_error_rad':error,'position_error_m':position_error})
 return {'frame':frame,'source_sample':idx,'source_t_s':idx/30,'body_hidden':10<=frame<=74,'wheel_pose_errors':errors}
frames=[1,12,42,74,84] if '--preview' in args else range(1,85)
if '--start-frame' in args:frames=range(int(args[args.index('--start-frame')+1]),int(args[args.index('--end-frame')+1])+1)
for f in frames:
 records.append(state(f));s.render.filepath=str(out/(f'preview_{f:04d}.png' if '--preview' in args else f'frames/frame_{f:04d}.png'));bpy.ops.render.render(write_still=True)
(out/('preview_mapping.json' if '--preview' in args else f'mapping_{min(frames):04d}.json')).write_text(json.dumps({'records':records,'source':'../revision_06/data/baseline_planner_on.json','mode':'recorded articulated response; presentation retimed','playback_duration_s':2.8,'source_duration_s':.8,'phase_dot':'render-only rigidly attached wheel annotation','status':'PASS'},indent=2)+'\n')
