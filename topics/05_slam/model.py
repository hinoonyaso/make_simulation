"""Deterministic 2D raycast + odometry initialized scan-to-scan ICP; meters/radians."""
import json
from pathlib import Path
import numpy as np
from scipy.spatial import cKDTree
ROOT=Path(__file__).resolve().parent
WALLS=np.array([[[-4,-3],[5,-3]],[[5,-3],[5,4]],[[5,4],[-4,4]],[[-4,4],[-4,-3]],[[2,0],[2,2]],[[2,2],[3.5,2]]],float)
def rot(a): return np.array([[np.cos(a),-np.sin(a)],[np.sin(a),np.cos(a)]])
def transform(p,pose): return np.asarray(p)@rot(pose[2]).T+pose[:2]
def scan(pose,rng,noise=.012):
    angles=np.linspace(-np.pi,np.pi,240,endpoint=False); dirs=np.c_[np.cos(angles+pose[2]),np.sin(angles+pose[2])]
    ranges=[]
    for d in dirs:
        hits=[]
        for a,b in WALLS:
            mat=np.column_stack((d,-(b-a)))
            if abs(np.linalg.det(mat))<1e-9:continue
            t,u=np.linalg.solve(mat,a-pose[:2])
            if t>0 and 0<=u<=1:hits.append(t)
        ranges.append(min(hits))
    r=np.array(ranges)+rng.normal(0,noise,len(angles))
    return np.c_[r*np.cos(angles),r*np.sin(angles)]
def match(points,target,initial):
    pose=initial.copy(); history=[pose.copy()]; tree=cKDTree(target)
    for _ in range(35):
        q=transform(points,pose);dist,idx=tree.query(q); valid=dist<.65
        a=q[valid];b=target[idx[valid]];ac=a.mean(0);bc=b.mean(0)
        u,_,vt=np.linalg.svd((a-ac).T@(b-bc));rr=vt.T@u.T
        if np.linalg.det(rr)<0:vt[-1]*=-1;rr=vt.T@u.T
        tt=bc-rr@ac;pose[:2]=rr@pose[:2]+tt;pose[2]+=np.arctan2(rr[1,0],rr[0,0]);history.append(pose.copy())
    return pose,history

def run():
    rng=np.random.default_rng(21);truth=np.c_[np.linspace(0,1.4,16),np.linspace(0,.9,16),np.linspace(0,.35,16)]
    scans=[scan(p,rng) for p in truth]; estimates=[truth[0].copy()];predictions=[truth[0].copy()];histories=[[]]; odom=[truth[0].copy()]
    for k in range(1,len(truth)):
        delta=truth[k]-truth[k-1];delta[:2]+=np.array([.065,-.045]);delta[2]+=.026
        # Relative odometry increment expressed in previous robot frame.
        local=rot(-truth[k-1,2])@delta[:2]
        def advance(p):return np.r_[p[:2]+rot(p[2])@local,p[2]+delta[2]]
        pred=advance(estimates[-1]);predictions.append(pred.copy());odom.append(advance(odom[-1]))
        estimate,history=match(scans[k],transform(scans[k-1],estimates[-1]),pred)
        estimates.append(estimate);histories.append(np.array(history).tolist())
    estimates=np.array(estimates);predictions=np.array(predictions);odom=np.array(odom)
    grids=[]; log=np.zeros((64,80));resolution=.125;origin=np.array([-4.5,-3.5])
    for pose,points in zip(estimates,scans):
        for end in transform(points,pose):
            pts=pose[:2]+np.linspace(0,1,int(np.linalg.norm(end-pose[:2])/resolution*2)+1)[:,None]*(end-pose[:2])
            ids=np.unique(np.floor((pts-origin)/resolution).astype(int),axis=0)
            for x,y in ids:
                if 0<=x<80 and 0<=y<64:log[y,x]-=.32
            x,y=np.floor((end-origin)/resolution).astype(int)
            if 0<=x<80 and 0<=y<64:log[y,x]+=1.4
        log=np.clip(log,-5,5);grids.append(log.copy().tolist())
    err=lambda p:np.linalg.norm(p[:,:2]-truth[:,:2],axis=1)
    metrics={"position_rmse_odometry_m":float(np.sqrt(np.mean(err(odom)**2))),"position_rmse_corrected_m":float(np.sqrt(np.mean(err(estimates)**2))),"sample1_predicted_error_m":float(err(predictions)[1]),"sample1_corrected_error_m":float(err(estimates)[1])}
    assert np.isclose(np.linalg.norm(scan(np.zeros(3),rng,0)[120]),2)
    assert metrics['position_rmse_corrected_m']<metrics['position_rmse_odometry_m']
    assert np.allclose(transform([[1,0]],[0,0,np.pi/2]),[[0,1]])
    visual_truth=np.array([truth[0]+(truth[-1]-truth[0])*a for a in np.linspace(0,1,96)])
    visual_rng=np.random.default_rng(22)
    visual_scans=[scan(p,visual_rng).tolist() for p in visual_truth]
    out=dict(visual_truth=visual_truth.tolist(),visual_scans=visual_scans,seed=21,units='meters/radians',walls=WALLS.tolist(),truth=truth.tolist(),scans=[p.tolist() for p in scans],estimates=estimates.tolist(),predictions=predictions.tolist(),odometry=odom.tolist(),histories=histories,grids=grids,metrics=metrics)
    (ROOT/'output/trace.json').write_text(json.dumps(out));(ROOT/'output/model_validation.json').write_text(json.dumps(metrics,indent=2));print(metrics)
if __name__=='__main__':run()
