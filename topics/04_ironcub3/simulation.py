"""Original planar educational model, NOT an iRonCub controller reproduction."""
import json
from pathlib import Path
import numpy as np
from scipy.linalg import expm
from scipy.optimize import minimize

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'
M,G,I,ARM=50.,9.81,8.,.32
DT,CONTROL_DT,TAU,N=.01,.1,.35,30

def reference(t):
    # Smooth commands remain identical for both plant conditions.
    s=np.clip((np.asarray(t)-1)/3,0,1);s=s*s*(3-2*s)
    return np.stack([.5*s,1.4+.4*s],axis=-1)

def controller():
    # State x,z,vx,vz,pitch,angular rate,left/right thrust deviations / mass.
    a=np.zeros((8,8));b=np.zeros((8,2))
    a[0,2]=a[1,3]=1;a[2,4]=G;a[3,6:8]=1;a[4,5]=1
    a[5,6]=ARM*M/I;a[5,7]=-ARM*M/I
    a[6,6]=a[7,7]=-1/TAU;b[6,0]=b[7,1]=1/TAU
    aug=np.zeros((10,10));aug[:8,:8]=a;aug[:8,8:]=b
    disc=expm(aug*CONTROL_DT);ad,bd=disc[:8,:8],disc[:8,8:]
    P=np.vstack([np.linalg.matrix_power(ad,j+1) for j in range(N)])
    B=np.zeros((N*8,N*2))
    for j in range(N):
        for k in range(j+1):B[j*8:(j+1)*8,k*2:(k+1)*2]=np.linalg.matrix_power(ad,j-k)@bd
    weights=np.tile([30,40,6,6,20,2,.02,.02],N)
    h=B.T@(weights[:,None]*B)+np.eye(N*2)*.08
    return P,B,weights,h

def run(tau):
    P,B,w,h=controller();state=np.array([0,1.4,0,0,0,0,0,0.],float)
    warm=np.zeros(2*N);command=np.zeros(2);rows=[];residuals=[]
    for k in range(1201):
        t=k*DT
        if k%10==0:
            target=np.zeros((N,8));target[:,:2]=reference(t+np.arange(1,N+1)*CONTROL_DT)
            grad=B.T@(w*(P@state-target.ravel()))
            optimum=np.linalg.solve(h,-grad)
            if np.any(optimum < -G/2) or np.any(optimum > 10-G/2):
                scale=np.max(np.diag(h))
                result=minimize(lambda u:((.5*u@h@u+grad@u)/scale,(h@u+grad)/scale),warm,jac=True,
                    method='SLSQP',bounds=[(-G/2,10-G/2)]*(2*N),
                    options={'maxiter':1000,'ftol':1e-12})
                if not result.success:raise RuntimeError(result.message)
                optimum=result.x
            command=optimum[:2];warm=np.r_[optimum[2:],optimum[-2:]]
            residuals.append(float(np.max(np.abs(h@optimum+grad))))
        f=(state[6:8]+G/2)*M
        rows.append(dict(t=round(t,4),x=float(state[0]),z=float(state[1]),
            pitch=float(state[4]),vx=float(state[2]),vz=float(state[3]),
            jets=[float(f[0]/2),float(f[1]/2),float(f[0]/2),float(f[1]/2)],
            commanded_jets=[float((command[0]+G/2)*M/2),float((command[1]+G/2)*M/2)]*2,
            target=reference(t).tolist(),error=float(np.linalg.norm(state[:2]-reference(t)))))
        if k==1200:break
        def dynamics(s):
            total=(s[6]+s[7]+G)*M
            return np.array([s[2],s[3],total*np.sin(s[4])/M,
                total*np.cos(s[4])/M-G,s[5],ARM*M*(s[6]-s[7])/I,
                (command[0]-s[6])/tau,(command[1]-s[7])/tau])
        a=dynamics(state);b=dynamics(state+DT*a/2);c=dynamics(state+DT*b/2);d=dynamics(state+DT*c)
        state+=DT*(a+2*b+2*c+d)/6
    errors=np.array([r['error'] for r in rows])
    return dict(tau=tau,frames=rows,metrics=dict(position_rmse_m=float(np.sqrt(np.mean(errors**2))),
        max_error_m=float(errors.max()),final_error_m=float(errors[-1]),
        max_pitch_deg=float(max(abs(r['pitch']) for r in rows)*180/np.pi)))

def main():
    OUT.mkdir(exist_ok=True)
    data=dict(config=dict(mass_kg=M,gravity=G,inertia_kg_m2=I,lever_arm_m=ARM,
        integration_dt=DT,controller_dt=CONTROL_DT,prediction_horizon_s=N*CONTROL_DT,
        controller_tau_s=TAU,jet_max_N=250,seed=None),
        scope='Original 2D airborne rigid-body MPC; ideal state feedback; first-order thrust; no contact, UKF, whole-body joints or paper benchmark reproduction.',
        nominal=run(.35),mismatch=run(.77))
    # Independently predictable hover: four equal jets balance gravity and torque.
    hover=np.full(4,M*G/4)
    assert abs(hover.sum()-M*G)<1e-10
    assert abs(ARM*(hover[0]+hover[2]-hover[1]-hover[3]))<1e-10
    for mode in ('nominal','mismatch'):
        r=data[mode]
        assert len(r['frames'])==1201
        assert all(0<=j<=250+1e-8 for f in r['frames'] for j in f['jets'])
        assert all(f['z']>1.0 for f in r['frames']), 'Airborne model crossed display floor'
        assert all(np.isfinite(f['error']) for f in r['frames'])
    (OUT/'simulation.json').write_text(json.dumps(data,ensure_ascii=False))
    metrics={m:data[m]['metrics'] for m in ('nominal','mismatch')}
    (OUT/'model_validation.json').write_text(json.dumps(dict(passed=True,metrics=metrics),indent=2))
    print(json.dumps(metrics,indent=2))

if __name__=='__main__':main()
