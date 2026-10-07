"""Validate sourced ideal relations and recorded feedback indices before rendering."""
import json,math
from pathlib import Path
H=Path(__file__).resolve().parent
D=json.loads((H.parent/'revision_06/data/baseline_planner_on.json').read_text());b=D['config']['wheel_track_m']
case=json.loads((H/'data/baseline_left.json').read_text())
l,r=case['samples'][30]['left_target_m_s'],case['samples'][30]['right_target_m_s']
theta=(r-l)/b;rl=l/theta;rr=r/theta
assert math.isclose(rr-rl,b) and math.isclose(rr*theta-rl*theta,b*theta)
assert math.isclose((rl+rr)/2*theta,(l+r)/2)
assert math.isclose((r-l)/(2*b),theta/2)
report={'ideal_geometry':{'status':'PASS','b_m':b,'vL_m_s':l,'vR_m_s':r,'theta_rad_in_1s':theta,'radius_difference_m':rr-rl,'center_travel_m_in_1s':(rl+rr)/2*theta,'wide_theta_rad_in_1s':theta/2}}
cycle=[]
for idx in [60,90,120]:
 row=D['samples'][idx];prev=D['samples'][idx-1]
 err=(math.atan2(row['lookahead_m'][1]-prev['root_position_m'][1],row['lookahead_m'][0]-prev['root_position_m'][0])-prev['yaw_rad']+math.pi)%(2*math.pi)-math.pi
 assert math.isclose(max(-1,min(1,err*2.2)),row['command_w_rad_s'],abs_tol=1e-8)
 v,w=row['command_v_m_s'],row['command_w_rad_s']
 cycle.append({'sample':idx,'input_pose_sample':idx-1,'input_pose_t_s':prev['t'],'command_t_s':row['t'],'error_rad':err,'w_rad_s':w,'v_m_s':v,'left_target_m_s':v-w*b/2,'right_target_m_s':v+w*b/2})
assert cycle[0]['error_rad']>0 and cycle[-1]['error_rad']<0
report['same_run_feedback']={'status':'PASS','source':'read-only R06 baseline_planner_on.json','rule':'clip(2.2*heading_error,-1,+1)','states':cycle,'presentation':'recorded samples rounded to source sample, no integration; command from preceding pose'}
(H/'output/relation_validation.json').write_text(json.dumps(report,indent=2)+'\n')
print('GEOMETRY / SAME-RUN FEEDBACK PASS')
