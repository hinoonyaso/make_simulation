"""Experiment contract: optical coordinates, ideal sensor and controlled inverse errors."""
import math
import numpy as np

W,H=160,120
FX=FY=150.
CX,CY=(W-1)/2,(H-1)/2
FPS=30
SAMPLES=301
SIGMA_Z=.04
SEED=20260916
PHASES=['intro','lateral','depth','ideal','noise','bad_k','correct','recap']


def center(kind,j):
    s=j/(SAMPLES-1)
    if kind=='depth':return (.25,.1,2.8-1.2*s)
    return (-.42+.92*s,.1+.06*math.sin(2*math.pi*s),2.2+.10*math.sin(math.pi*s))


def reconstruct(u,v,z,fx=FX):
    return np.array([(u-CX)*z/fx,(v-CY)*z/FY,z],dtype=float)


def to_world(p):
    x,y,z=p;return (x,z,-y)


def from_world(p):
    x,z,minus_y=p;return (x,-minus_y,z)
