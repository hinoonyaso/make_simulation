"""Frame-sampled inputs and computed FK used by both animation engines."""
import json
import math
from pathlib import Path
import numpy as np
from model import fk, chain, validate, L1, L2, H

ROOT=Path(__file__).resolve().parent

def interpolate(u, keys):
    for (t0,p0),(t1,p1) in zip(keys,keys[1:]):
        if u<=t1:
            v=np.clip((u-t0)/(t1-t0),0,1); v=v*v*(3-2*v)
            return np.array(p0)*(1-v)+np.array(p1)*v
    return np.array(keys[-1][1],dtype=float)

POSE=[35,25,-40]
MOTION={
 'B01':[(0,[0,25,-40]),(.25,[0,25,-40]),(.8,POSE),(1,POSE)],
 'B02':[(0,POSE),(.12,POSE),(.4,[35,55,-40]),(.55,[35,55,-40]),(.8,[35,55,-75]),(1,POSE)],
 'B03':[(0,[0,25,0]),(.2,[0,25,0]),(.8,[0,65,0]),(1,[0,65,0])],
 'B04':[(0,[0,65,0]),(.2,[0,65,0]),(.8,[0,30,0]),(1,[0,30,0])],
 'B05':[(0,[0,30,-40]),(.2,[0,30,-40]),(.8,[0,55,-40]),(1,[0,55,-40])],
 'B06':[(0,[0,55,-40]),(.15,[0,55,-40]),(.55,[0,55,20]),(.65,[0,55,20]),(.9,[0,25,-40]),(1,[0,25,-40])],
 'B07':[(0,[0,25,-40]),(.2,[0,25,-40]),(.8,[65,25,-40]),(1,[65,25,-40])],
 'B08':[(0,[65,25,-40]),(.12,[65,25,-40]),(.38,[65,50,-40]),(.48,[65,50,-40]),(.7,[65,50,-65]),(.82,[65,50,-65]),(1,POSE)],
}

def main():
    timeline=json.loads((ROOT/'output/timeline.json').read_text())
    frames=[]
    for b in timeline['beats']:
        for i in range(b['frames']):
            u=i/max(1,b['frames']-1)
            qdeg=interpolate(u,MOTION.get(b['id'],[(0,POSE),(1,POSE)]))
            q=np.radians(qdeg)
            joints=fk(q)
            a,c,d=chain(q)
            position=(a@c@d)[:3,3]
            assert np.linalg.norm(position-joints[-1])<1e-12
            alpha,beta=q[1:]
            planar=[[0,0],[L1*math.cos(alpha),L1*math.sin(alpha)],
                    [L1*math.cos(alpha)+L2*math.cos(alpha+beta),L1*math.sin(alpha)+L2*math.sin(alpha+beta)]]
            frames.append(dict(frame=len(frames),time=len(frames)/30,beat=b['id'],scene=b['scene'],tool=b['tool'],u=u,
                               q_deg=qdeg.tolist(),q_rad=q.tolist(),joints=joints.tolist(),ee=position.tolist(),planar=planar))
    out=dict(fps=30,L1=L1,L2=L2,h=H,evidence='computed ideal kinematics, offline trace playback',frames=frames)
    (ROOT/'output/trace.json').write_text(json.dumps(out,separators=(',',':')))
    result=validate();result['trace_frames']=len(frames)
    (ROOT/'output/model_validation.json').write_text(json.dumps(result,indent=2))
    print(f'Computed and validated {len(frames)} synchronized states')

if __name__=='__main__':main()
