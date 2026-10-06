"""Planner feedback drives Bullet wheel motors; robot poses are never prescribed."""
import argparse,importlib.util,json,math,sys
from pathlib import Path
import bpy
from mathutils import Vector
HERE=Path(__file__).resolve().parent
sys.path.insert(0,str(HERE))
import planner
spec=importlib.util.spec_from_file_location('probe',HERE/'../../06_physics_probe/physics_run.py');probe=importlib.util.module_from_spec(spec);spec.loader.exec_module(probe)

def execute(enabled,substeps,duration):
    probe.CONFIG.update(initial_root_x_m=-1.4,duration_s=duration)
    scene,body,wheels=probe.build(True,substeps)
    # Actual passive corridor walls match the planner's inner wall surfaces.
    for side in [-1,1]:probe.box(f'CorridorWall{side}',(0,side*1.5,.16),(5,.1,.32),'PASSIVE')
    motors=[bpy.data.objects[f'WheelMotor{side}'] for side in [-1,1]]
    for motor in motors:motor.animation_data_clear();motor.rigid_body_constraint.motor_ang_target_velocity=0.
    samples=[];plans=[];events=[];path=[];previous=None;pose=(-1.4,0,0);known=False;v=w=0.;target=None;state='settle';reached=False
    for frame in range(1,scene.frame_end+1):
        t=(frame-1)/30
        if enabled:
            if not path:
                path=planner.plan(pose[:2],False);plans.append({'t':t,'reason':'initial_plan','path':path,'obstacle_known':False})
            if t>=2. and not known:
                known=True;path=planner.plan(pose[:2],True);plans.append({'t':t,'reason':'map_update','path':path,'obstacle_known':True});events.append({'t':t,'event':'map_update_replan'})
            if t>=.5:
                if reached:v,w,target,state=0.,0.,list(planner.GOAL),'goal_hold'
                else:v,w,target,state=planner.command(pose,path)
            if state=='goal_reached' and not reached:events.append({'t':t,'event':'goal_reached'});reached=True
        elif t>=.5:v,w=.2,0.;state='constant_command'
        if t<.5:v=w=0.
        # right wheel (y negative) must run faster for positive yaw.
        rates=[-(v+w*.144)/.033,-(v-w*.144)/.033]
        for motor,rate in zip(motors,rates):motor.rigid_body_constraint.motor_ang_target_velocity=rate
        bpy.context.view_layer.update();scene.frame_set(frame);bpy.context.view_layer.update();dg=bpy.context.evaluated_depsgraph_get();dg.update()
        matrix=body.evaluated_get(dg).matrix_world.copy();pos=matrix.translation;quat=matrix.to_quaternion();root=matrix@Vector((.064,0,-.068))
        velocity=[0.,0.,0.] if previous is None else [(pos[i]-previous[i])*30 for i in range(3)]
        pose=(*list(root)[:2],quat.to_euler().z)
        # Conservative body+wheel/caster enclosing circle; clearance is a geometry proxy, not contact force.
        physical_proxy_clearance=min(math.hypot(root.x,root.y)-.3-.23,1.45-abs(root.y)-.23)
        c,sn=math.cos(pose[2]),math.sin(pose[2]);dx,dy=-pos.x,-pos.y
        local_x,local_y=c*dx+sn*dy,-sn*dx+c*dy
        body_clearance=math.hypot(max(abs(local_x)-.13,0),max(abs(local_y)-.11,0))-.3
        samples.append({'t':t,'position_m':list(pos),'root_position_m':list(root),'orientation_wxyz':list(quat),'velocity_m_s':velocity,'yaw_rad':pose[2],'wheel_positions_m':[list(a.evaluated_get(dg).matrix_world.translation) for a in wheels],'wheel_orientations_wxyz':[list(a.evaluated_get(dg).matrix_world.to_quaternion()) for a in wheels],'command_v_m_s':v,'command_w_rad_s':w,'wheel_targets_rad_s':rates,'path_id':len(plans)-1 if enabled else -1,'obstacle_known':known,'state':state,'lookahead_m':target,'proxy_clearance_m':physical_proxy_clearance,'body_drum_clearance_m':body_clearance})
        previous=pos.copy()
    metrics={'goal_reached':reached,'goal_error_m':math.dist(pose[:2],planner.GOAL),'minimum_proxy_clearance_m':min(r['proxy_clearance_m'] for r in samples),'minimum_body_drum_clearance_m':min(r['body_drum_clearance_m'] for r in samples),'final_root_position_m':list(root)}
    return {'schema':'robotics-visual-trace/v9','units':{'time':'s','position_m':'m','root_position_m':'m','orientation_wxyz':'1','velocity_m_s':'m/s','yaw_rad':'rad','path_id':'1','wheel_positions_m':'m','wheel_orientations_wxyz':'1','command_v_m_s':'m/s','command_w_rad_s':'rad/s','wheel_targets_rad_s':'rad/s','lookahead_m':'m','proxy_clearance_m':'m','body_drum_clearance_m':'m'},'engine':{'name':'Blender rigid body / Bullet','blender_version':bpy.app.version_string,'substeps_per_frame':substeps,'solver_iterations':50},'config':dict(probe.CONFIG),'planner_config':{'algorithm':'educational A* + feedback heading/lookahead tracking; not DWB/Nav2','grid_m':planner.GRID,'robot_radius_m':planner.ROBOT_RADIUS,'margin_m':planner.MARGIN,'wall_inner_y_m':planner.WALL_Y,'goal_m':planner.GOAL,'observation':'static drum exists throughout; idealized map information added at t=2s, no simulated sensor'},'scenario':'planner_on' if enabled else 'planner_off','samples':samples,'plans':plans,'events':events,'metrics':metrics}

if __name__=='__main__':
    ap=argparse.ArgumentParser();ap.add_argument('--name',default='baseline');ap.add_argument('--substeps',type=int,default=8);ap.add_argument('--duration',type=float,default=30);args=ap.parse_args(sys.argv[sys.argv.index('--')+1:] if '--' in sys.argv else [])
    for enabled in [False,True]:
        data=execute(enabled,args.substeps,args.duration);p=HERE/'data'/f'{args.name}_{data["scenario"]}.json';p.write_text(json.dumps(data,indent=2)+'\n',newline='\n');print('RESULT',p.name,data['metrics'],flush=True)
