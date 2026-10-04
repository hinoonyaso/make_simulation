"""Executable teaching stack: synthetic lidar -> obstacle estimate -> costs -> A* -> sampled controller -> differential-drive kinematics. Not ROS/Nav2 execution."""
import json,heapq,itertools,math
from pathlib import Path
import numpy as np
R=Path(__file__).resolve().parent
DT=.1;ROBOT_R=.25;PERSON_R=.3;GOAL=np.array([3.,0.,0.]);START=np.array([-3.,0.,0.]);RES=.15
XS=np.arange(-4.5,4.51,RES);YS=np.arange(-3,3.01,RES);XX,YY=np.meshgrid(XS,YS);POINTS=np.stack((XX,YY),-1)
BOXES=[(-1.0,1.65,-.2,2.45),(-.8,-2.45,.0,-1.65)]
ANGLES=np.linspace(-np.pi,np.pi,120,endpoint=False)
def wrap(a):return (a+np.pi)%(2*np.pi)-np.pi
def static_clear(q):
 q=np.asarray(q);best=np.minimum(4.5-np.abs(q[...,0]),3-np.abs(q[...,1]))
 for x0,y0,x1,y1 in BOXES:
  delta=np.maximum(np.maximum(np.array([x0,y0])-q,q-np.array([x1,y1])),0);dist=np.linalg.norm(delta,axis=-1)
  best=np.minimum(best,dist)
 return best

def clearance(q,det=None):
 out=static_clear(q)
 if det is not None:out=np.minimum(out,np.linalg.norm(np.asarray(q)-det,axis=-1)-PERSON_R)
 return out

def costmap(det=None):
 d=clearance(POINTS,det);cost=np.where(d<1.0,180*np.exp(-3.5*np.maximum(d-ROBOT_R,0)),0.);cost[d<=ROBOT_R+.22]=255
 return cost

def cell(p):return (int(np.clip(round((p[0]-XS[0])/RES),0,len(XS)-1)),int(np.clip(round((p[1]-YS[0])/RES),0,len(YS)-1)))
def plan(p,det):
 costs=costmap(det);start=cell(p);goal=cell(GOAL);g={start:0.};parent={};queue=[];counter=itertools.count();heapq.heappush(queue,(0.,next(counter),start));closed=set()
 while queue:
  _,_,u=heapq.heappop(queue)
  if u in closed:continue
  closed.add(u)
  if u==goal:
   path=[u]
   while path[-1]!=start:path.append(parent[path[-1]])
   return [[float(XS[x]),float(YS[y])] for x,y in path[::-1]]
  for dx,dy in [(1,0),(0,1),(-1,0),(0,-1),(1,1),(1,-1),(-1,1),(-1,-1)]:
   v=(u[0]+dx,u[1]+dy)
   if not(0<=v[0]<len(XS) and 0<=v[1]<len(YS)) or costs[v[1],v[0]]>=255:continue
   if dx and dy and (costs[u[1],v[0]]>=255 or costs[v[1],u[0]]>=255):continue
   new=g[u]+math.hypot(dx,dy)*RES*(1+.018*costs[v[1],v[0]])
   if new<g.get(v,float('inf')):
    g[v]=new;parent[v]=u;h=math.dist(v,goal)*RES;heapq.heappush(queue,(new+h,next(counter),v))
 return []

def person(t,enabled):
 if not enabled or t<2.:return None
 return np.array([0.,max(0.,.4-(t-2.)*.5)])

def lidar(p,obstacle,rng):
 # First intersections with known room edges, boxes, and a new circular obstacle.
 segments=[[[-4.5,-3],[4.5,-3]],[[4.5,-3],[4.5,3]],[[4.5,3],[-4.5,3]],[[-4.5,3],[-4.5,-3]]]
 for x0,y0,x1,y1 in BOXES:segments += [[[x0,y0],[x1,y0]],[[x1,y0],[x1,y1]],[[x1,y1],[x0,y1]],[[x0,y1],[x0,y0]]]
 dirs=np.c_[np.cos(ANGLES+p[2]),np.sin(ANGLES+p[2])];ranges=np.full(len(dirs),3.2);dynamic=np.zeros(len(dirs),bool)
 for a,b in np.array(segments):
  edge=b-a;delta=a-p[:2];den=dirs[:,0]*edge[1]-dirs[:,1]*edge[0];valid=np.abs(den)>1e-9
  den=np.where(valid,den,1);t=(delta[0]*edge[1]-delta[1]*edge[0])/den;u=(delta[0]*dirs[:,1]-delta[1]*dirs[:,0])/den
  ok=valid&(t>0)&(u>=0)&(u<=1);ranges=np.minimum(ranges,np.where(ok,t,100))
 if obstacle is not None:
  v=obstacle-p[:2];projection=dirs@v;disc=PERSON_R**2-(v@v-projection**2);near=projection-np.sqrt(np.maximum(disc,0));dynamic=(disc>=0)&(near>0)&(near<ranges);ranges=np.where(dynamic,near,ranges)
 observed=ranges+rng.normal(0,.002,len(ranges));hits=p[:2]+observed[:,None]*dirs
 # Detect novel returns by comparing to expected static-map ranges, no truth labels enter the fit.
 novel=static_clear(hits)>.12;novel &= observed<3.15
 pts=hits[novel];det=None
 if len(pts)>=4:
  mat=np.c_[2*pts[:,0],2*pts[:,1],np.ones(len(pts))];rhs=np.sum(pts**2,axis=1);fit=np.linalg.lstsq(mat,rhs,rcond=None)[0];radius=math.sqrt(max(0,fit[2]+fit[0]**2+fit[1]**2))
  if .15<radius<.5:det=fit[:2]
 return hits,observed,det

def propagate(p,v,w,dt):
 # Exact constant-twist differential-drive kinematics.
 out=np.array(p,float).copy();theta=p[2]
 if abs(w)<1e-8:out[:2]+=v*dt*np.array([np.cos(theta),np.sin(theta)])
 else:out[0]+=v/w*(np.sin(theta+w*dt)-np.sin(theta));out[1]+=v/w*(-np.cos(theta+w*dt)+np.cos(theta))
 out[2]=wrap(theta+w*dt);return out

def control(p,previous,path,det):
 dist=np.linalg.norm(p[:2]-GOAL[:2])
 if dist<.12:
  w=float(np.clip(2*wrap(GOAL[2]-p[2]),-1.,1.));return np.array([0.,w]),[],[]
 pts=np.array(path);idx=int(np.argmin(np.linalg.norm(pts-p[:2],axis=1)));j=idx;length=0
 while j<len(pts)-1 and length<.7:length+=np.linalg.norm(pts[j+1]-pts[j]);j+=1
 target=pts[j]
 vs=np.unique(np.r_[0,np.linspace(max(0,previous[0]-.08),min(.55,previous[0]+.08),5)])
 ws=np.linspace(max(-1.5,previous[1]-.35),min(1.5,previous[1]+.35),11);best=(float('inf'),np.zeros(2));candidates=[]
 for v in vs:
  for w in ws:
   predicted=np.array([propagate(p,v,w,t) for t in np.arange(.15,1.51,.15)]);clear=clearance(predicted[:,:2],det)
   if clear.min()<ROBOT_R+.11:continue
   desired=np.arctan2(target[1]-predicted[-1,1],target[0]-predicted[-1,0]);heading=abs(wrap(desired-predicted[-1,2]))
   score=3*np.linalg.norm(predicted[-1,:2]-target)+.25*heading+.045/(clear.min()-.2)-.18*v
   candidates.append([float(v),float(w),float(score)])
   if score<best[0]:best=(score,np.array([v,w]))
 return best[1],candidates,target.tolist()

def run(enabled):
 rng=np.random.default_rng(14);p=START.copy();vel=np.zeros(2);wheel=np.zeros(2);path=[];rows=[];plans=[];det=None;last_plan=-100;events=[]
 for k in range(650):
  t=round(k*DT,4);truth_person=person(t,enabled);hits,ranges,newdet=lidar(p,truth_person,rng)
  if newdet is not None:det=newdet
  reason=None
  if not path:reason='initial_plan'
  elif det is not None and clearance(np.array(path)[np.argmin(np.linalg.norm(np.array(path)-p[:2],axis=1)):],det).min()<ROBOT_R+.1:reason='path_invalid'
  elif t-last_plan>=1.-1e-6:reason='periodic_replan'
  if reason:
   path=plan(p,det);last_plan=t;plans.append(dict(time=t,reason=reason,path=path,observation=None if det is None else det.tolist()));events.append(dict(time=t,event=reason,result='SUCCESS' if path else 'FAILURE'))
  cmd,candidates,target=control(p,vel,path,det) if path else (np.zeros(2),[],[])
  if reason=='path_invalid':cmd=np.zeros(2) # controlled pause while replacing a now-invalid reference.
  nextp=propagate(p,*cmd,DT);left=(cmd[0]-.45*cmd[1]/2)/.1;right=(cmd[0]+.45*cmd[1]/2)/.1;wheel+=np.array([left,right])*DT
  minimum=min(clearance(p[:2],truth_person),clearance(nextp[:2],truth_person))-ROBOT_R
  rows.append(dict(k=k,time=t,pose=p.tolist(),next_pose=nextp.tolist(),person=None if truth_person is None else truth_person.tolist(),detected=None if det is None else det.tolist(),scan=ranges.tolist(),hits=hits.tolist(),cmd=cmd.tolist(),wheel_rates=[left,right],wheel_angles=wheel.tolist(),path_id=len(plans)-1,lookahead=target,candidates=candidates[::max(1,len(candidates)//12)],state='REPLAN' if reason=='path_invalid' else ('FOLLOW_PATH' if path else 'WAIT'),clearance_m=float(minimum)))
  p=nextp;vel=cmd
  if np.linalg.norm(p[:2]-GOAL[:2])<.12 and abs(wrap(p[2]-GOAL[2]))<.08:
   events.append(dict(time=t+DT,event='goal_reached',result='SUCCESS'));break
 metrics=dict(success=events[-1]['event']=='goal_reached',duration_s=rows[-1]['time']+DT,final_position_error_m=float(np.linalg.norm(p[:2]-GOAL[:2])),final_yaw_error_rad=float(abs(wrap(p[2]-GOAL[2]))),minimum_clearance_m=min(r['clearance_m'] for r in rows),path_invalid_replans=sum(x['reason']=='path_invalid' for x in plans),plans=len(plans))
 return dict(rows=rows,plans=plans,events=events,metrics=metrics)
if __name__=='__main__':
 baseline=run(False);dynamic=run(True);print('baseline',baseline['metrics']);print('dynamic',dynamic['metrics'])
 assert np.allclose(propagate(np.zeros(3),1,0,1),[1,0,0])
 assert np.allclose(propagate(np.zeros(3),0,1,1),[0,0,1])
 for result in [baseline,dynamic]:assert result['metrics']['success'] and result['metrics']['minimum_clearance_m']>0
 assert dynamic['metrics']['path_invalid_replans']>=1
 doc=dict(dt=DT,resolution=RES,robot_radius=ROBOT_R,person_radius=PERSON_R,wheel_radius=.1,wheel_track=.45,start=START.tolist(),goal=GOAL.tolist(),boxes=BOXES,xs=XS.tolist(),ys=YS.tolist(),static_costmap=costmap().tolist(),baseline=baseline,dynamic=dynamic)
 (R/'output/trace.json').write_text(json.dumps(doc));(R/'output/model_validation.json').write_text(json.dumps({k:doc[k]['metrics'] for k in ['baseline','dynamic']},indent=2))
