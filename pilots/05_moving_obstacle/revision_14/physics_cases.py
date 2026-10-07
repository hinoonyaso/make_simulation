"""New open-loop Bullet cases; recorded poses are outputs, never prescribed."""
import bpy,sys,json,math,importlib.util
from pathlib import Path
from mathutils import Vector
H=Path(__file__).resolve().parent
spec=importlib.util.spec_from_file_location('probe',H/'../../06_physics_probe/physics_run.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)
CASES={'equal':(.2,.2),'left':(.05,.25),'spin':(-.15,.15),'stop':(.2,.2)}
def execute(name,substeps):
 probe.CONFIG.update(initial_root_x_m=-.8,duration_s=6.)
 scene,body,wheels=probe.build(False,substeps);motors=[bpy.data.objects[f'WheelMotor{s}'] for s in [-1,1]]
 for m in motors:m.animation_data_clear()
 rows=[];previous=None
 for frame in range(1,182):
  t=(frame-1)/30;left,right=CASES[name]
  if t<.5 or name=='stop' and t>=3.:left=right=0.
  for motor,speed in zip(motors,[right,left]):motor.rigid_body_constraint.motor_ang_target_velocity=-speed/.033
  bpy.context.view_layer.update();scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
  matrix=body.evaluated_get(dg).matrix_world;pos=matrix.translation.copy();q=matrix.to_quaternion();root=matrix@Vector((.064,0,-.068))
  vel=[0.,0.,0.] if previous is None else [(pos[i]-previous[i])*30 for i in range(3)];previous=pos
  rows.append({'t':t,'root_position_m':list(root),'orientation_wxyz':list(q),'yaw_rad':q.to_euler().z,'velocity_m_s':vel,'wheel_positions_m':[list(w.evaluated_get(dg).matrix_world.translation) for w in wheels],'wheel_orientations_wxyz':[list(w.evaluated_get(dg).matrix_world.to_quaternion()) for w in wheels],'left_target_m_s':left,'right_target_m_s':right,'forward_target_m_s':(left+right)/2,'turn_target_rad_s':(right-left)/.288})
 units={'time':'s','root_position_m':'m','orientation_wxyz':'1','yaw_rad':'rad','velocity_m_s':'m/s','wheel_positions_m':'m','wheel_orientations_wxyz':'1','left_target_m_s':'m/s','right_target_m_s':'m/s','forward_target_m_s':'m/s','turn_target_rad_s':'rad/s'}
 return {'schema':'robotics-visual-trace/v9','units':units,'engine':{'name':'Blender rigid body / Bullet','version':bpy.app.version_string,'substeps_per_frame':substeps,'solver_iterations':50},'config':dict(probe.CONFIG),'scenario':name,'control_mode':'open-loop motor-driven dynamic chassis; clear floor; no planner or prescribed robot poses','samples':rows}
for substeps,label in [(8,'baseline'),(8,'repeat'),(16,'fine')]:
 for name in CASES:
  d=execute(name,substeps);p=H/'data'/f'{label}_{name}.json';p.write_text(json.dumps(d,indent=2)+'\n');print('RESULT',p.name,flush=True)
