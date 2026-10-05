"""Actual Blender/Bullet articulated drive experiment; robot poses are never keyframed."""
import argparse,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent

CONFIG={'fps':30,'duration_s':8.,'settle_s':.5,'wheel_radius_m':.033,'wheel_track_m':.288,'desired_forward_speed_m_s':.2,'motor_axis_sign':-1,'motor_target_rad_s':-6.060606,'motor_max_impulse':.002,'gravity_m_s2':-9.81,'body_mass_kg':1.6,'wheel_mass_kg':.10,'caster_mass_kg':.02,'floor_friction':.8,'wheel_friction':1.,'caster_friction':0.,'collision_margin_m':.001,'drum_radius_m':.3,'initial_root_x_m':-1.1,'body_dimensions_m':[.26,.22,.06],'body_center_from_root_m':[-.064,0,.068]}

def rigid(obj,kind='ACTIVE',mass=1.,friction=.8,shape='BOX'):
    bpy.context.view_layer.objects.active=obj;obj.select_set(True);bpy.ops.rigidbody.object_add();obj.select_set(False)
    rb=obj.rigid_body;rb.type=kind;rb.mass=mass;rb.friction=friction;rb.restitution=0.;rb.collision_shape=shape
    rb.use_margin=True;rb.collision_margin=CONFIG['collision_margin_m'];rb.use_deactivation=False
    rb.linear_damping=.04;rb.angular_damping=.04
    return obj

def box(name,xyz,dims,kind='ACTIVE',mass=1.,friction=.8):
    bpy.ops.mesh.primitive_cube_add(size=1,location=xyz);obj=bpy.context.object;obj.name=name;obj.dimensions=dims
    bpy.ops.object.transform_apply(location=False,rotation=False,scale=True)
    return rigid(obj,kind,mass,friction)

def joint(name,kind,a,b,loc,rot=(0,0,0)):
    bpy.ops.object.empty_add(type='PLAIN_AXES',location=loc,rotation=rot);obj=bpy.context.object;obj.name=name
    bpy.ops.rigidbody.constraint_add();c=obj.rigid_body_constraint;c.type=kind;c.object1=a;c.object2=b;c.disable_collisions=True;c.enabled=True
    return obj

def build(blocked,substeps):
    bpy.ops.wm.read_factory_settings(use_empty=True);scene=bpy.context.scene
    scene.render.fps=30;scene.frame_start=1;scene.frame_end=round(CONFIG['duration_s']*30)+1;scene.gravity=(0,0,CONFIG['gravity_m_s2'])
    box('Ground',(0,0,-.05),(6,3,.1),'PASSIVE')
    root=CONFIG['initial_root_x_m'];body=box('DynamicChassis',(root-.064,0,.068),CONFIG['body_dimensions_m'],mass=CONFIG['body_mass_kg'])
    wheels=[]
    for side in [-1,1]:
        loc=(root,side*.144,.033)
        bpy.ops.mesh.primitive_cylinder_add(vertices=32,radius=.033,depth=.018,location=loc,rotation=(math.pi/2,0,0))
        wheel=bpy.context.object;wheel.name=f'DynamicWheel{side}';rigid(wheel,mass=.10,friction=1.,shape='CYLINDER');wheels.append(wheel)
        joint(f'AxleHinge{side}','HINGE',body,wheel,loc,(math.pi/2,0,0))
        motor=joint(f'WheelMotor{side}','MOTOR',body,wheel,loc,(0,0,math.pi/2)).rigid_body_constraint
        motor.use_motor_ang=True;motor.motor_ang_max_impulse=CONFIG['motor_max_impulse']
        for frame,velocity in [(1,0),(15,0),(16,CONFIG['motor_target_rad_s']),(scene.frame_end,CONFIG['motor_target_rad_s'])]:
            motor.motor_ang_target_velocity=velocity;motor.keyframe_insert('motor_ang_target_velocity',frame=frame)
    for side in [-1,1]:
        loc=(root-.177,side*.064,.006)
        bpy.ops.mesh.primitive_uv_sphere_add(segments=12,ring_count=8,radius=.006,location=loc)
        caster=bpy.context.object;caster.name=f'IdealCaster{side}';rigid(caster,mass=.02,friction=0.,shape='SPHERE')
        joint(f'CasterMount{side}','FIXED',body,caster,loc)
    if blocked:
        bpy.ops.mesh.primitive_cylinder_add(vertices=64,radius=.3,depth=.58,location=(0,0,.29))
        obj=bpy.context.object;obj.name='StaticDrum';rigid(obj,'PASSIVE',shape='CYLINDER')
    world=scene.rigidbody_world;world.substeps_per_frame=substeps;world.solver_iterations=50;world.point_cache.frame_start=1;world.point_cache.frame_end=scene.frame_end
    return scene,body,wheels

def execute(blocked,substeps):
    scene,body,wheels=build(blocked,substeps);samples=[];previous=None
    for frame in range(1,scene.frame_end+1):
        scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
        matrix=body.evaluated_get(dg).matrix_world.copy();pos=matrix.translation;quat=matrix.to_quaternion()
        root=matrix@Vector((.064,0,-.068));velocity=[0.,0.,0.] if previous is None else [(pos[i]-previous[i])*30 for i in range(3)]
        row={'t':(frame-1)/30,'position_m':list(pos),'root_position_m':list(root),'orientation_wxyz':list(quat),'velocity_m_s':velocity,'yaw_rad':quat.to_euler().z,
             'motor_target_rad_s':CONFIG['motor_target_rad_s'] if frame>=16 else 0.,
             'wheel_positions_m':[list(w.evaluated_get(dg).matrix_world.translation) for w in wheels],
             'wheel_orientations_wxyz':[list(w.evaluated_get(dg).matrix_world.to_quaternion()) for w in wheels]}
        samples.append(row);previous=pos.copy()
    return {'schema':'robotics-visual-trace/v9','units':{'time':'s','position_m':'m','root_position_m':'m','orientation_wxyz':'1','velocity_m_s':'m/s','yaw_rad':'rad','motor_target_rad_s':'rad/s','wheel_positions_m':'m','wheel_orientations_wxyz':'1'},
            'engine':{'name':'Blender rigid body / Bullet','blender_version':bpy.app.version_string,'substeps_per_frame':substeps,'solver_iterations':50},
            'control_mode':'open-loop angular motors on dynamic wheels; dynamic chassis and floor contacts; static drum; ideal low-friction fixed caster spheres',
            'config':CONFIG,'scenario':'blocked' if blocked else 'clear','samples':samples}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--name',default='baseline');ap.add_argument('--substeps',type=int,default=8)
    args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    out=HERE/'data';out.mkdir(exist_ok=True)
    for blocked in [False,True]:
        d=execute(blocked,args.substeps);file=out/f'{args.name}_{d["scenario"]}.json';file.write_text(json.dumps(d,indent=2)+'\n')
        print('RESULT',file.name,'start',d['samples'][0]['root_position_m'],'end',d['samples'][-1]['root_position_m'],flush=True)
