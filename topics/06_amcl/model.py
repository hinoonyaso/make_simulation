"""Educational adaptive particle localization, analytic likelihood field, not Nav2 execution."""
import json,math
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parent
WALLS=np.array([[[-4,-3],[5,-3]],[[5,-3],[5,4]],[[5,4],[-4,4]],[[-4,4],[-4,-3]],[[2,0],[2,2]],[[2,2],[3.5,2]]],float)
ANGLES=np.linspace(-np.pi,np.pi,36,endpoint=False)
def wrap(a):return (a+np.pi)%(2*np.pi)-np.pi
def endpoints(p,z):
 p=np.atleast_2d(p);a=p[:,2,None]+ANGLES
 return p[:,None,:2]+z[None,:,None]*np.stack((np.cos(a),np.sin(a)),axis=-1)
def distance(q):
 q=np.asarray(q);best=np.full(q.shape[:-1],100.)
 for a,b in WALLS:
  u=np.clip(np.sum((q-a)*(b-a),axis=-1)/np.sum((b-a)**2),0,1)
  best=np.minimum(best,np.linalg.norm(q-(a+u[...,None]*(b-a)),axis=-1))
 return best
def observe(p,rng,sigma=.025):
 vals=[]
 for a in ANGLES+p[2]:
  d=np.array([np.cos(a),np.sin(a)]);hits=[]
  for v,w in WALLS:
   mat=np.column_stack((d,v-w))
   if abs(np.linalg.det(mat))<1e-10:continue
   t,u=np.linalg.solve(mat,v-p[:2])
   if t>0 and 0<=u<=1:hits.append(t)
  vals.append(min(hits))
 return np.array(vals)+rng.normal(0,sigma,len(vals))
def score(p,z):
 d=distance(endpoints(p,z));log=np.log(.95*np.exp(-.5*(d/.45)**2)+.05/12).mean(axis=1)*6
 valid=(p[:,0]>-3.9)&(p[:,0]<4.9)&(p[:,1]>-2.9)&(p[:,1]<3.9)&(distance(p[:,:2])>.12)
 log[~valid]=-1e6;return log

def adaptive_resample(p,w,rng):
 cdf=np.cumsum(w);bins=set();parents=[];limit=900
 for n in range(900):
  idx=min(len(w)-1,int(np.searchsorted(cdf,rng.random())));parents.append(idx)
  key=tuple(np.floor((p[idx]+[4,3,np.pi])/[.35,.35,.25]).astype(int));bins.add(key);k=len(bins)
  if k>1:
   z=2.326;limit=int(math.ceil((k-1)/(.16)*(1-2/(9*(k-1))+z*math.sqrt(2/(9*(k-1))))**3))
   limit=np.clip(limit,180,900)
  if n+1>=limit:break
 return p[parents].copy(),np.array(parents),len(bins)
def simulate(seed=42,sensor=True):
 rng=np.random.default_rng(seed);obsrng=np.random.default_rng(6)
 p=np.c_[rng.uniform(-3.8,4.8,900),rng.uniform(-2.8,3.8,900),rng.uniform(-np.pi,np.pi,900)]
 while np.any(distance(p[:,:2])<.15):
  mask=distance(p[:,:2])<.15;p[mask,:2]=rng.uniform([-3.8,-2.8],[4.8,3.8],(mask.sum(),2))
 initial=p.copy();truth=np.array([-1.1,-.5,.3]);rows=[]
 for k in range(22):
  prior=p.copy();delta=np.array([.085,.01,.028])
  c,s=np.cos(truth[2]),np.sin(truth[2]);truth[:2]+=np.array([[c,-s],[s,c]])@delta[:2];truth[2]+=delta[2]
  odom=delta+np.array([.004,-.002,.002]);noisy=odom+rng.normal(0,[.065,.065,.045],(len(p),3));c=np.cos(p[:,2]);s=np.sin(p[:,2]);p[:,0]+=c*noisy[:,0]-s*noisy[:,1];p[:,1]+=s*noisy[:,0]+c*noisy[:,1];p[:,2]=wrap(p[:,2]+noisy[:,2])
  z=observe(truth,obsrng);log=score(p,z) if sensor else np.zeros(len(p));w=np.exp(log-log.max());w/=w.sum()
  estimate=np.r_[np.sum(p[:,:2]*w[:,None],axis=0),np.arctan2(np.sum(np.sin(p[:,2])*w),np.sum(np.cos(p[:,2])*w))]
  weighted=p.copy();p,parents,bins=adaptive_resample(p,w,rng)
  rows.append(dict(index=k,time_s=(k+1)*.5,truth=truth.copy().tolist(),prior=prior.tolist(),predicted=weighted.tolist(),weights=w.tolist(),resampled=p.tolist(),parents=parents.tolist(),count=len(p),bins=bins,scan=z.tolist(),estimate=estimate.tolist(),position_error_m=float(np.linalg.norm(estimate[:2]-truth[:2])),heading_error_rad=float(abs(wrap(estimate[2]-truth[2])))))
 return initial,rows
if __name__=='__main__':
 initial,rows=simulate();_,blind=simulate(sensor=False)
 metrics=dict(final_position_error_m=rows[-1]['position_error_m'],final_heading_error_deg=rows[-1]['heading_error_rad']*180/np.pi,no_sensor_final_error_m=blind[-1]['position_error_m'],initial_particles=len(initial),final_particles=rows[-1]['count'],counts=[r['count'] for r in rows])
 print(metrics)
 assert np.isclose(observe(np.zeros(3),np.random.default_rng(1),0)[18],2)
 for r in rows:
  assert np.isclose(sum(r['weights']),1)
  assert np.allclose(np.array(r['predicted'])[r['parents']],r['resampled'])
 assert metrics['final_position_error_m']<.3
 assert metrics['final_position_error_m']<metrics['no_sensor_final_error_m']
 doc=dict(seed=42,observation_seed=6,walls=WALLS.tolist(),angles=ANGLES.tolist(),initial=initial.tolist(),rows=rows,metrics=metrics,comparison=blind)
 (ROOT/'output/trace.json').write_text(json.dumps(doc));(ROOT/'output/model_validation.json').write_text(json.dumps(metrics,indent=2))
