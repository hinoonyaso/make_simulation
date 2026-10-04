"""Independent invariant, sensor, clearance, timing and final media checks."""
import json,subprocess
from pathlib import Path
import numpy as np
from model import propagate,clearance,person,ROBOT_R,lidar
R=Path(__file__).resolve().parent;O=R/'output';D=json.loads((O/'trace.json').read_text());report={}
for mode in ['baseline','dynamic']:
 run=D[mode];minimum=100.;errors=[]
 for row in run['rows']:
  p=np.array(row['pose']);v,w=row['cmd'];assert np.allclose(propagate(p,v,w,.1),row['next_pose'],atol=1e-10)
  left,right=row['wheel_rates'];assert abs((left+right)*.1/2-v)<1e-10;assert abs((right-left)*.1/.45-w)<1e-10
  assert 0<=v<=.55+1e-8 and abs(w)<=1.5+1e-8
  for dt in np.linspace(0,.1,11):
   q=propagate(p,v,w,dt);minimum=min(minimum,float(clearance(q[:2],person(row['time']+dt,mode=='dynamic'))-ROBOT_R))
  if row['person'] is not None and row['detected'] is not None:errors.append(float(np.linalg.norm(np.array(row['person'])-row['detected'])))
  if row['state']=='REPLAN':assert row['cmd']==[0.,0.]
 assert minimum>0 and run['metrics']['success'];assert run['metrics']['final_position_error_m']<.12 and run['metrics']['final_yaw_error_rad']<.08
 report[mode]=dict(**run['metrics'],clearance_sampled_at_100hz_m=minimum,max_obstacle_center_error_m=max(errors,default=0.))
assert D['dynamic']['metrics']['path_invalid_replans']>=1
# Empty sensor scene must not identify an unknown object; deterministic forward model probes.
hits,ranges,det=lidar(np.array([-3.,0.,0.]),None,np.random.default_rng(14));assert det is None
A=json.loads((R/'assets/audio/manifest.json').read_text());C=json.loads((O/'caption_timing.json').read_text());assert len(A)==len(C)==32
for a,c in zip(A,C):assert a['start']<=c['start']<c['end']<=a['end']
video=O/'nav2_education_ko.mp4'
if video.exists():
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(video)]));v=next(s for s in probe['streams'] if s['codec_type']=='video');assert(v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1');assert abs(float(probe['format']['duration'])-A[-1]['end'])<.12
 subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],check=True)
 report['media']=dict(duration_s=probe['format']['duration'],resolution='1920x1080',fps=30,full_decode='passed',captions=len(C))
for mode in ['baseline','dynamic']:
 p=O/f'blender/{mode}_validation.json'
 if p.exists():report[mode]['blender']=json.loads(p.read_text())
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
