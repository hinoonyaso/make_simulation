"""Local physical checks; limits are educational, not hardware qualification."""
import json,math,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
report={}
for kind in ['equal','left','spin','stop']:
 runs={}
 for mode in ['baseline','repeat','fine']:
  p=H/'data'/f'{mode}_{kind}.json'
  subprocess.run([sys.executable,str(H.parents[2]/'core/shared-data/validate_trace.py'),str(p)],check=True)
  d=json.loads(p.read_text());rows=d['samples'];assert len(rows)==181
  assert d['engine']['name']=='Blender rigid body / Bullet'
  assert all(all(math.isfinite(x) for x in r['root_position_m']+r['velocity_m_s']) for r in rows)
  assert max(abs(r['root_position_m'][2]) for r in rows)<.01
  assert all(abs(r['forward_target_m_s']-(r['left_target_m_s']+r['right_target_m_s'])/2)<1e-9 for r in rows)
  assert all(abs(r['turn_target_rad_s']-(r['right_target_m_s']-r['left_target_m_s'])/.288)<1e-9 for r in rows)
  runs[mode]=rows
 a,b,c=runs['baseline'],runs['repeat'],runs['fine']
 repeat=max(math.dist(x['root_position_m'],y['root_position_m']) for x,y in zip(a,b))
 fine=math.dist(a[-1]['root_position_m'],c[-1]['root_position_m'])
 assert repeat<1e-6;assert fine<.1
 unwrapped=sum((v['yaw_rad']-u['yaw_rad']+math.pi)%(2*math.pi)-math.pi for u,v in zip(a,a[1:]))
 move=math.dist(a[0]['root_position_m'][:2],a[-1]['root_position_m'][:2])
 if kind=='equal':assert move>.5 and abs(unwrapped)<.1
 if kind=='left':assert unwrapped>1 and a[-1]['root_position_m'][1]>.1
 if kind=='spin':assert unwrapped>2 and move<.1
 if kind=='stop':
  assert all(r['left_target_m_s']==r['right_target_m_s']==0 for r in a[90:])
  before=sum(math.hypot(*r['velocity_m_s'][:2]) for r in a[75:90])/15
  after=sum(math.hypot(*r['velocity_m_s'][:2]) for r in a[-15:])/15
  assert after<before*.5
 report[kind]={'repeat_max_position_m':repeat,'fine_endpoint_delta_m':fine,'net_position_m':move,'unwrapped_turn_rad':unwrapped,'endpoint_speed_m_s':math.hypot(*a[-1]['velocity_m_s'][:2])}
(H/'output/physics_validation.json').write_text(json.dumps({'status':'PASS','limits':{'repeat_m':1e-6,'fine_endpoint_m':.1},'cases':report,'boundary':'Stop target leaves residual motion. No exact no-slip prediction or hardware claim.'},indent=2)+'\n')
print(json.dumps(report,indent=2));print('PHYSICS PASS')
