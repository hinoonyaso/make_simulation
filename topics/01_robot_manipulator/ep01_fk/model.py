"""Ideal yaw/pitch/pitch FK. Metres, radians, right handed world Z up."""
import math
import numpy as np

L1, L2, H = 2.0, 1.5, 0.6

def fk(q):
    yaw, shoulder, elbow = q
    c, s = math.cos(yaw), math.sin(yaw)
    r1 = L1 * math.cos(shoulder)
    r2 = r1 + L2 * math.cos(shoulder + elbow)
    return np.array([[0, 0, H],
                     [r1*c, r1*s, H+L1*math.sin(shoulder)],
                     [r2*c, r2*s, H+L1*math.sin(shoulder)+L2*math.sin(shoulder+elbow)]])

def rz(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,-s,0,0],[s,c,0,0],[0,0,1,0],[0,0,0,1.]])

def pitch(a):
    c, s = math.cos(a), math.sin(a)
    return np.array([[c,0,-s,0],[0,1,0,0],[s,0,c,0],[0,0,0,1.]])

def tr(x=0,y=0,z=0):
    m=np.eye(4); m[:3,3]=[x,y,z]; return m

def chain(q):
    a,b,c=q
    return tr(z=H)@rz(a), pitch(b)@tr(x=L1), pitch(c)@tr(x=L2)

def validate():
    rng=np.random.default_rng(1)
    errors=[]
    for q in rng.uniform(-math.pi,math.pi,(1000,3)):
        a,b,c=chain(q)
        errors.append(float(np.linalg.norm((a@b@c)[:3,3]-fk(q)[-1])))
    np.testing.assert_allclose(fk([0,0,0])[-1],[3.5,0,.6],atol=1e-12)
    np.testing.assert_allclose(fk([math.pi/2,0,0])[-1],[0,3.5,.6],atol=1e-12)
    np.testing.assert_allclose(fk([0,math.pi/2,0])[-1],[0,0,4.1],atol=1e-12)
    assert max(errors)<1e-12
    return {'random_cases':1000,'max_matrix_vs_analytic_error_m':max(errors),'analytic_cases':3,'evidence':'ideal kinematic simulation; no dynamics or hardware measurement'}

if __name__=='__main__':
    import json
    from pathlib import Path
    result=validate()
    Path(__file__).with_name('output').mkdir(exist_ok=True)
    Path(__file__).with_name('output').joinpath('model_validation.json').write_text(json.dumps(result,indent=2))
    print(result)
