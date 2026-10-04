"""Two mechanism demonstrations, NOT Nav2 DWB or ROS2 TEB plugin execution."""
import json,math
from pathlib import Path
import numpy as np
from scipy.optimize import least_squares
R=Path(__file__).resolve().parent;DT=.2;RR=.22;OR=.30;START=np.array([-3.,0.,0.]);GOAL=np.array([3.,0.,0.]);OBS=np.array([0.,-.18]);VMAX=.6;WMAX=1.4;N=12
PATH=np.c_[np.linspace(-3,3,121),np.zeros(121)]
def wrap(a):return (a+np.pi)%(2*np.pi)-np.pi
def advance(p,v,w,dt):
 p=np.array(p,float).copy();th=p[2]
 if abs(w)<1e-8:p[:2]+=v*dt*np.array([np.cos(th),np.sin(th)])
 else:p[:2]+=v/w*np.array([np.sin(th+w*dt)-np.sin(th),-np.cos(th+w*dt)+np.cos(th)])
 p[2]=wrap(th+w*dt);return p

def clearance(q,obstacle):
 q=np.asarray(q);c=np.minimum(1.25-np.abs(q[...,1]),3.8-np.abs(q[...,0]))-RR
 if obstacle:c=np.minimum(c,np.linalg.norm(q-OBS,axis=-1)-OR-RR)
 return c

def finish(p):
 if np.linalg.norm(p[:2]-GOAL[:2])<.10:return np.array([0.,np.clip(2*wrap(-p[2]),-WMAX,WMAX)])
 return None

def dwb(p,prev,obstacle):
 last=finish(p)
 if last is not None:return last,dict(candidates=[],selected=None)
 vs=np.unique(np.r_[0,np.linspace(max(0,prev[0]-.18),min(VMAX,prev[0]+.18),6)])
 ws=np.unique(np.r_[0,np.linspace(max(-WMAX,prev[1]-.5),min(WMAX,prev[1]+.5),17)])
 candidates=[];best=(float('inf'),np.zeros(2),None)
 for v in vs:
  for w in ws:
   pts=np.array([advance(p,v,w,t) for t in np.linspace(0,2.,21)]);c=clearance(pts[:,:2],obstacle);valid=c.min()>.09
   parts=[.55*np.mean(pts[:,1]**2),2*np.linalg.norm(pts[-1,:2]-GOAL[:2]),.20*np.mean(1/(np.maximum(c,0)+.09)),.28*(VMAX-v),.12*abs(w)]
   score=sum(parts) if valid else None;idx=len(candidates);candidates.append(dict(v=float(v),w=float(w),valid=bool(valid),score=score,costs=parts,trajectory=pts.tolist(),minimum_clearance=float(c.min())))
   if valid and score<best[0]:best=(score,np.array([v,w]),idx)
 return best[1],dict(candidates=candidates,selected=best[2])

def unpack(z,p,target):return np.vstack([p,z[:(N-2)*3].reshape(-1,3),target]),z[(N-2)*3:]
def segment_commands(poses,dt):
 diff=np.diff(poses[:,:2],axis=0);ang=np.diff(poses[:,2]);mid=(poses[:-1,2]+poses[1:,2])/2
 longitudinal=diff[:,0]*np.cos(mid)+diff[:,1]*np.sin(mid);v=longitudinal/(dt*np.sinc(ang/(2*np.pi)));w=ang/dt
 return v,w

def residual(z,p,target,obstacle,parts=False):
 poses,dt=unpack(z,p,target);diff=np.diff(poses[:,:2],axis=0);mid=(poses[:-1,2]+poses[1:,2])/2;v,w=segment_commands(poses,dt)
 samples=np.concatenate([poses[:,:2],(poses[1:,:2]+poses[:-1,:2])/2]);cl=clearance(samples,obstacle)
 kin=np.r_[60*(diff[:,0]*np.sin(mid)-diff[:,1]*np.cos(mid)),20*np.maximum(0,-v),20*np.maximum(0,v-VMAX),20*np.maximum(0,np.abs(w)-WMAX)]
 r=dict(time=.42*np.sqrt(dt),obstacle=24*np.maximum(0,.20-cl),kinematics=kin,via=.45*poses[1:-1,1],smooth=np.r_[.8*np.diff(v),.35*np.diff(w)])
 if parts:return {k:float(a@a) for k,a in r.items()}
 return np.concatenate(list(r.values()))

def teb(p,prev,obstacle,record=False):
 last=finish(p)
 if last is not None:return last,dict(poses=[],dt=[],iterations=[],costs={})
 target=np.array([min(3.,p[0]+2.4),0.,0.]);poses=np.linspace(p,target,N);poses[:,2]=np.arctan2(target[1]-p[1],target[0]-p[0]);poses[0]=p;poses[-1]=target
 # Same mild deterministic initial bend for both conditions, not a computed output.
 poses[1:-1,1]+=.06*np.sin(np.linspace(0,np.pi,N))[1:-1]
 dts=np.full(N-1,max(.2,np.linalg.norm(target[:2]-p[:2])/(.45*(N-1))))
 z=np.r_[poses[1:-1].ravel(),dts];lo=np.r_[np.tile([-3.7,-1.02,-2.8],N-2),np.full(N-1,.08)];hi=np.r_[np.tile([3.7,1.02,2.8],N-2),np.full(N-1,2.)];z=np.clip(z,lo+1e-6,hi-1e-6);history=[]
 def snapshot(z):
  pp,tt=unpack(z,p,target);cc=residual(z,p,target,obstacle,True);return dict(poses=pp.tolist(),dt=tt.tolist(),costs=cc,objective=sum(cc.values()))
 if record:history.append(snapshot(z))
 # Several bounded solves expose real intermediate iterates; no interpolated band deformation.
 for _ in range(24 if record else 1):
  opt=least_squares(residual,z,args=(p,target,obstacle),bounds=(lo,hi),max_nfev=3 if record else 65,ftol=1e-5,xtol=1e-5,gtol=1e-5);z=opt.x
  if record:history.append(snapshot(z))
 poses,dt=unpack(z,p,target);v,w=segment_commands(poses,dt);cmd=np.array([np.clip(v[0],0,VMAX),np.clip(w[0],-WMAX,WMAX)])
 # Shared collision guard checks the executed portion, not an oracle future.
 check=np.array([advance(p,*cmd,t)[:2] for t in np.linspace(0,DT,11)])
 if clearance(check,obstacle).min()<.045:cmd[:]=0
 costs=residual(z,p,target,obstacle,True)
 return cmd,dict(poses=poses.tolist(),dt=dt.tolist(),iterations=history,costs=costs,objective=sum(costs.values()),optimizer_success=bool(opt.success),kinematic_residual_max=float(np.max(np.abs(np.diff(poses[:,:2],axis=0)[:,0]*np.sin((poses[:-1,2]+poses[1:,2])/2)-np.diff(poses[:,:2],axis=0)[:,1]*np.cos((poses[:-1,2]+poses[1:,2])/2)))))

def run(method,obstacle):
 p=START.copy();prev=np.zeros(2);wheel=np.zeros(2);rows=[]
 for k in range(180):
  cmd,detail=globals()[method](p,prev,obstacle);nextp=advance(p,*cmd,DT);samples=np.array([advance(p,*cmd,t)[:2] for t in np.linspace(0,DT,21)]);c=float(clearance(samples,obstacle).min());rates=[(cmd[0]-.42*cmd[1]/2)/.1,(cmd[0]+.42*cmd[1]/2)/.1];wheel+=np.array(rates)*DT
  # The sensor interface is an explicitly ideal local obstacle map, shared by both methods.
  rows.append(dict(k=k,time=k*DT,pose=p.tolist(),next_pose=nextp.tolist(),cmd=cmd.tolist(),wheel_rates=rates,wheel_angles=wheel.tolist(),clearance=c,observation=dict(corridor_half_width=1.25,obstacle_center=OBS.tolist() if obstacle else None,obstacle_radius=OR if obstacle else None),detail=detail));p=nextp;prev=cmd
  if np.linalg.norm(p[:2]-GOAL[:2])<.10 and abs(p[2])<.08:break
 metrics=dict(success=bool(np.linalg.norm(p[:2]-GOAL[:2])<.10 and abs(p[2])<.08),duration_s=len(rows)*DT,position_error_m=float(np.linalg.norm(p[:2]-GOAL[:2])),yaw_error_rad=float(abs(p[2])),minimum_clearance_m=min(r['clearance'] for r in rows),path_length_m=sum(float(np.linalg.norm(np.array(r['next_pose'][:2])-r['pose'][:2])) for r in rows))
 print(method,obstacle,metrics,flush=True);return dict(rows=rows,metrics=metrics)
if __name__=='__main__':
 runs={}
 for method in ['dwb','teb']:
  for obstacle in [False,True]:runs[f'{method}_{"obstacle" if obstacle else "empty"}']=run(method,obstacle)
 hero_pose=np.array([-1.25,0.,0.]);hero={}
 for method in ['dwb','teb']:
  cmd,detail=globals()[method](hero_pose,np.array([.35,0]),True,**({'record':True} if method=='teb' else {}));hero[method]=dict(pose=hero_pose.tolist(),cmd=cmd.tolist(),detail=detail)
 doc=dict(dt=DT,robot_radius=RR,obstacle_radius=OR,obstacle=OBS.tolist(),corridor_half_width=1.25,start=START.tolist(),goal=GOAL.tolist(),global_path=PATH.tolist(),runs=runs,hero=hero)
 (R/'output/trace.json').write_text(json.dumps(doc));(R/'output/model_metrics.json').write_text(json.dumps({k:v['metrics'] for k,v in runs.items()},indent=2))
 for run in runs.values():assert run['metrics']['success'] and run['metrics']['minimum_clearance_m']>0
