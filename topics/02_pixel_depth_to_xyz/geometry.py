"""Shared optical-camera geometry and narration-driven motion (meters, pixels)."""
import json
import math
from pathlib import Path

ROOT=Path(__file__).resolve().parent
FPS=30
FX=FY=600.
CX,CY=320.,240.
U,V=440.,300.
XN,YN=(U-CX)/FX,(V-CY)/FY
BLENDER_CHAPTERS={0,1,3,6,7,9}


def point(z,u=U,v=V):
    return ((u-CX)*z/FX,(v-CY)*z/FY,z)


def project(p):
    x,y,z=p
    return (FX*x/z+CX,FY*y/z+CY)


def state(frame,records):
    t=(frame-1)/FPS
    rec=next((r for r in records if r['start']<=t+1e-8<r['end']),records[-1])
    ci,li=rec['chapter'],rec['line']
    transitions={(0,1):(1.,2.5),(0,2):(2.5,2.),(3,2):(1.,2.),(9,2):(2.,1.)}
    z=1. if ci==3 and li<2 else 2.
    if (ci,li) in transitions:
        a,b=transitions[(ci,li)]
        s=min(1.,max(0.,(t-rec['start']-.6)/3.))
        s=s*s*(3-2*s)
        z=a+(b-a)*s
    return dict(chapter=ci,line=li,z=z,range=math.sqrt(sum(q*q for q in point(z))),
                show_candidates=(ci==0 and li==1),show_range=ci==7,
                visible=ci in BLENDER_CHAPTERS)
