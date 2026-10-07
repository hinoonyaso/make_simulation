"""Acceptance of the simplified feedback run, separate from schema validation."""
import json,math,subprocess,sys
from pathlib import Path
OUT=Path(__file__).resolve().parent/'output';H=Path(__file__).resolve().parent.parent/'revision_06';report={'scope':'educational A* / tracker / Bullet, not Nav2 or hardware','thresholds':{'goal_error_m':.15,'last_second_speed_m_s':.01,'repeat_position_error_m':1e-6,'fine_endpoint_difference_m':.10,'planner_on_conservative_clearance_m':.10,'planner_off_last_second_displacement_m':.005},'runs':{}}
for case in ['planner_off','planner_on']:
 runs={}
 for name in ['baseline','repeat','fine']:
  p=H/'data'/f'{name}_{case}.json';subprocess.run([sys.executable,str(H.parents[2]/'core/shared-data/validate_trace.py'),str(p)],check=True);runs[name]=json.loads(p.read_text())
 a,b,c=(runs[n] for n in ['baseline','repeat','fine'])
 error=max(abs(x-y) for r,s in zip(a['samples'],b['samples']) for x,y in zip(r['root_position_m'],s['root_position_m']))
 delta=math.dist(a['metrics']['final_root_position_m'],c['metrics']['final_root_position_m'])
 assert error<1e-6 and delta<.10
 for d in runs.values():
  assert all(abs(r['root_position_m'][2])<.015 for r in d['samples'])
  if case=='planner_on':
   assert max(math.hypot(*r['velocity_m_s'][:2]) for r in d['samples'][-30:])<.01
   assert d['metrics']['goal_reached'] and d['metrics']['goal_error_m']<.15
   assert d['metrics']['minimum_proxy_clearance_m']>.10
   assert d['metrics']['minimum_body_drum_clearance_m']>.05
   assert d['events'][0]['event']=='map_update_replan'
  else:
   assert not d['metrics']['goal_reached'] and d['metrics']['goal_error_m']>1.
   assert math.dist(d['samples'][-30]['root_position_m'],d['samples'][-1]['root_position_m'])<.005
 report['runs'][case]={'metrics':a['metrics'],'repeat_max_position_error_m':error,'fine_endpoint_difference_m':delta,'fine_metrics':c['metrics']}
report['status']='PASS within stated probe criteria; not time-step convergence or hardware validation'
(OUT/'run_review.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))

# Compare the displayed input and hypothetical command with the actual tracker.
import importlib.util
spec=importlib.util.spec_from_file_location('tracker',H/'planner.py');tracker=importlib.util.module_from_spec(spec);spec.loader.exec_module(tracker)
d=json.loads((H/'data/baseline_planner_on.json').read_text());prev=d['samples'][59];rec=d['samples'][60];pos=prev['root_position_m'];path=d['plans'][1]['path']
v,w,target,status=tracker.command((*pos[:2],prev['yaw_rad']),path)
assert abs(w-rec['command_w_rad_s'])<1e-9 and math.dist(target,rec['lookahead_m'])<1e-9
aligned_yaw=math.atan2(target[1]-pos[1],target[0]-pos[0]);av,aw,at,ast=tracker.command((*pos[:2],aligned_yaw),path)
assert abs(aw)<1e-12 and status==ast=='tracking'
(OUT/'controller_evidence.json').write_text(json.dumps({'source_pose_index':59,'command_index':60,'recorded_command_w_rad_s':w,'target':target,'aligned_heading_illustration':{'command_w_rad_s':aw,'physical_run':False},'rule':'clip(2.2*wrapped_heading_error,-1,1); stop/no_path preserved'},indent=2)+'\n')
print('PASS: recorded controller and aligned-direction illustration')
