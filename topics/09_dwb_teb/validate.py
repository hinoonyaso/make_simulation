import json,subprocess
from pathlib import Path
import numpy as np
from model import advance,clearance,DT
R=Path(__file__).resolve().parent;O=R/'output';D=json.loads((O/'trace.json').read_text());report={}
assert np.allclose(advance([0,0,0],1,0,1),[1,0,0]);assert np.allclose(advance([0,0,0],0,1,1),[0,0,1])
for name,run in D['runs'].items():
 minimum=100.;kin=[]
 for row in run['rows']:
  p=np.array(row['pose']);v,w=row['cmd'];assert np.allclose(advance(p,v,w,DT),row['next_pose'],atol=1e-10);assert 0<=v<=.6+1e-8 and abs(w)<=1.4+1e-8
  l,r=row['wheel_rates'];assert abs((l+r)*.1/2-v)<1e-10 and abs((r-l)*.1/.42-w)<1e-10
  q=np.array([advance(p,v,w,t)[:2] for t in np.linspace(0,DT,21)]);minimum=min(minimum,float(clearance(q,name.endswith('obstacle')).min()));detail=row['detail']
  if name.startswith('dwb') and detail['selected'] is not None:
   best=detail['candidates'][detail['selected']];assert best['valid'];assert best['score']==min(c['score'] for c in detail['candidates'] if c['valid']);assert np.allclose([best['v'],best['w']],row['cmd'])
   for c in detail['candidates']:
    if c['valid']:assert abs(c['score']-sum(c['costs']))<1e-9
  elif name.startswith('teb') and detail['dt']:
   assert min(detail['dt'])>0;assert len(detail['poses'])==len(detail['dt'])+1;assert np.allclose(detail['poses'][0],p);assert abs(detail['objective']-sum(detail['costs'].values()))<1e-9;kin.append(detail['kinematic_residual_max'])
 assert minimum>0 and run['metrics']['success'];report[name]=dict(**run['metrics'],clearance_100hz_m=minimum,max_band_lateral_residual_m=max(kin,default=0))
for method in ['dwb','teb']:
 a=D['runs'][method+'_empty']['rows'];b=D['runs'][method+'_obstacle']['rows'];assert any(not np.allclose(x['cmd'],y['cmd']) for x,y in zip(a,b))
hist=D['hero']['teb']['detail']['iterations'];assert hist[-1]['objective']<hist[0]['objective'];assert all(b['objective']<=a['objective']+1e-6 for a,b in zip(hist,hist[1:]));assert not np.allclose(hist[0]['dt'],hist[-1]['dt']);assert not np.allclose(hist[0]['poses'],hist[-1]['poses']);report['band']=dict(initial_cost=hist[0]['objective'],final_cost=hist[-1]['objective'],snapshots=len(hist))
A=json.loads((R/'assets/audio/manifest.json').read_text());p=O/'caption_timing.json'
if p.exists():
 C=json.loads(p.read_text());assert len(A)==len(C)
 for a,c in zip(A,C):assert a['start']<=c['start']<c['end']<=a['end']
for method in ['dwb','teb']:
 p=O/f'blender/{method}_validation.json'
 if p.exists():report[method+'_blender']=json.loads(p.read_text())
v=O/'dwb_teb_education_ko.mp4'
if v.exists():
 d=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(v)]));s=next(s for s in d['streams'] if s['codec_type']=='video');assert(s['width'],s['height'],s['r_frame_rate'])==(1920,1080,'30/1');assert abs(float(d['format']['duration'])-A[-1]['end'])<.12;subprocess.run(['ffmpeg','-v','error','-i',str(v),'-f','null','-'],check=True);report['media']=dict(duration=float(d['format']['duration']),resolution='1920x1080',fps=30,full_decode='passed',caption_cues=len(A))
(O/'validation.json').write_text(json.dumps(report,indent=2));print(json.dumps(report,indent=2))
