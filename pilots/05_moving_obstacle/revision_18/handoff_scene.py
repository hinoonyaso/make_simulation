"""Exact recorded R06 pose119/command120, camera matched to R10 encoded continuation."""
import bpy,json,sys,math
from pathlib import Path
from mathutils import Quaternion,Euler,Vector
from bpy_extras.object_utils import world_to_camera_view
H=Path(__file__).resolve().parent;sys.path.insert(0,str(H));sys.path.insert(0,str(H.parents[2]/'core/blender-robotics-simulation-skill/templates'))
from studio_utils import look,principled_material
bpy.ops.wm.open_mainfile(filepath=str(H.parent/'revision_10/output/blender/avoidance_studio.blend'));s=bpy.context.scene;bpy.app.handlers.frame_change_post.clear();s.frame_set(317)
D=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text());row=D['samples'][119];command=D['samples'][120];q=Quaternion(row['orientation_wxyz']);root=bpy.data.objects['TurtleBot3'];root.animation_data_clear();root.location=row['root_position_m'];root.rotation_mode='QUATERNION';root.rotation_quaternion=q
initial=Euler((math.pi/2,0,0)).to_quaternion();errors=[]
for wheel,world,pos in zip([bpy.data.objects['TB3Wheel_left'],bpy.data.objects['TB3Wheel_right']],reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
 wheel.animation_data_clear();wheel.rotation_mode='QUATERNION';wheel.rotation_quaternion=q.inverted()@Quaternion(world)@initial.inverted();wheel.location=q.inverted()@(Vector(pos)-Vector(row['root_position_m']))
actual=bpy.data.objects['ActualHistory'];actual.data.animation_data_clear();rows=D['samples'];cum=[0.]
for a,b in zip(rows,rows[1:]):cum.append(cum[-1]+math.dist(a['root_position_m'][:2],b['root_position_m'][:2]))
actual.data.bevel_factor_end=cum[119]/cum[-1]
for name in ['ReferencePlan','ActualHistory','GoalRange']:bpy.data.objects[name].animation_data_clear();bpy.data.objects[name].hide_render=False
# Same optical plan/history treatment as R12 encoded response.
for name,color in [('PlanGreen',(.03,.55,.28,1)),('ActualBlue',(.04,.45,.8,1))]:
 mat=bpy.data.materials[name];bs=next(n for n in mat.node_tree.nodes if n.type=='BSDF_PRINCIPLED');bs.inputs['Base Color'].default_value=color;bs.inputs['Roughness'].default_value=.5
from surface_treatment import apply_surface
settings=apply_surface(s,'selected',baseline='avoidance')
cam=s.camera;cam.animation_data_clear();look(cam,(-.4,-3,5.5),(0,.12,.10))
s.render.engine='BLENDER_EEVEE';s.eevee.taa_render_samples=64;s.render.use_motion_blur=False;s.render.resolution_x=1920;s.render.resolution_y=1080;s.render.resolution_percentage=100;s.render.fps=30;s.render.image_settings.file_format='PNG'
bpy.context.view_layer.update();frame_width=128/9;frame_height=8
p=Vector(row['root_position_m']);forward=p+q@Vector((.25,0,0));target=Vector((*command['lookahead_m'][:2],.02))
projection={}
for name,point in [('root',p+Vector((0,0,.06))),('forward',forward+Vector((0,0,.06))),('target',target),('drum',Vector((0,0,.58)))]:
 ndc=world_to_camera_view(s,cam,point);projection[name]=[(ndc.x-.5)*frame_width,(ndc.y-.5)*frame_height,0]
for wheel,world,pos in zip([bpy.data.objects['TB3Wheel_left'],bpy.data.objects['TB3Wheel_right']],reversed(row['wheel_orientations_wxyz']),reversed(row['wheel_positions_m'])):
 err=(wheel.matrix_world.translation-Vector(pos)).length;ang=(wheel.matrix_world.to_quaternion()@initial).rotation_difference(Quaternion(world)).angle;assert err<1e-5 and min(ang,2*math.pi-ang)<1e-4;errors.append({'position_m':err,'angle_rad':ang})
out=H/'output/handoff';out.mkdir(parents=True,exist_ok=True);(out/'mapping.json').write_text(json.dumps({'source_pose_sample':119,'source_pose_t':row['t'],'command_sample':120,'command_t':command['t'],'next_encoded_frame':317,'next_encoded_source_sample':120,'projection':projection,'wheel_errors':errors,'status':'PASS'},indent=2)+'\n');s.render.filepath=str(out/'source4.png');bpy.ops.render.render(write_still=True)
