"""Shared, Blender-independent 30 fps motion schedule for the existing narration."""
import bisect
import json
import math
from pathlib import Path

ROOT = Path(__file__).resolve().parent
FPS = 30
L1, L2 = 1.0, 0.8
RECORDS = json.loads((ROOT / 'assets/audio/manifest.json').read_text())
STARTS = [r['start'] for r in RECORDS]
FRAME_COUNT = round(RECORDS[-1]['end'] * FPS)


def fk(a,b):
    return (math.cos(a)+.8*math.cos(a+b), math.sin(a)+.8*math.sin(a+b))


def smooth(u):
    u=max(0,min(1,u))
    error=1/(1+math.exp(5))
    return (1/(1+math.exp(-10*(u-.5)))-error)/(1-2*error)


def pose(frame):
    t=(frame-1)/FPS
    ri=max(0,min(len(RECORDS)-1,bisect.bisect_right(STARTS,t+1e-9)-1))
    r=RECORDS[ri]; ci,li=r['chapter'],r['line']
    starts=[(-20,100),(30,60),(25,40),(10,25),(30,60),(30,60),
            (0,0),(-25,100),(25,55),(0,35),(30,60),(30,60)]
    motions={0:(0,(30,60)),2:(3,(65,-50)),3:(0,(30,60)),
             5:(1,(82.6590069833698,-60)),6:(1,(0,180)),
             7:(2,(65,20)),9:(0,(0,0)),11:(3,(0,90))}
    a,b=[math.radians(x) for x in starts[ci]]
    progress=0.0
    if ci in motions:
        line,end=motions[ci]
        mr=RECORDS[ci*4+line]
        u=max(0,min(1,(t-mr['start']-.6)/(mr['duration']-.6)))
        progress=3*u*u-2*u*u*u if ci==7 else smooth(u)
        ea,eb=[math.radians(x) for x in end]
        a += progress*(ea-a); b += progress*(eb-b)
    if ci==8:
        mr=RECORDS[35]
        dt=max(0,min(mr['duration']-.6,t-mr['start']-.6))
        a+=.3*dt; b+=.2*dt
    return {'chapter':ci,'line':li,'q1':a,'q2':b,'progress':progress}


def signature(state):
    return (state['chapter'],state['line'],round(state['q1'],10),round(state['q2'],10),round(state['progress'],10))


if __name__=='__main__':
    print('Timeline frames:',FRAME_COUNT)
    print('Unique render states:',len({signature(pose(f)) for f in range(1,FRAME_COUNT+1)}))
