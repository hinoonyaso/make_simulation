"""Numerical checks independent of animation code; fail before rendering."""
import json
from pathlib import Path
import numpy as np
from experiment import *
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'


def main():
    d=json.loads((OUT/'trace.json').read_text());by_phase={p:[s for s in d['states'] if s['mode']==p] for p in PHASES}
    baseline=by_phase['ideal'];noise=by_phase['noise'];bad=by_phase['bad_k'];correct=by_phase['correct']
    assert len(baseline)==len(noise)==len(bad)==len(correct)==SAMPLES
    assert max(s['error_mm'] for s in baseline)<.01
    assert max(s['error_mm'] for s in correct)<.01
    depth=np.load(OUT/'data/observation_0000.npz')['depth']
    assert abs(float(depth[40,10])-4.38)<1e-4,'Known background plane depth'
    for a,n,b,c in zip(baseline,noise,bad,correct):
        assert a['geometry_id']==n['geometry_id']==b['geometry_id']==c['geometry_id']
        assert a['uv']==n['uv']==b['uv']==c['uv']
        u,v=a['uv'];direction=np.array([(u-CX)/FX,(v-CY)/FY,1.])
        dz=n['z_observed']-a['z_observed']
        assert np.linalg.norm(np.array(n['estimated'])-np.array(a['estimated'])-dz*direction)<1e-10
        delta=np.array(b['estimated'])-np.array(a['estimated'])
        assert abs(delta[0]-.25*a['estimated'][0])<1e-10 and abs(delta[1])+abs(delta[2])<1e-10
        assert a['estimated']==c['estimated']
        zmap=np.load(OUT/'data'/f"{n['depth_id']}.npy")
        assert float(zmap[v,u])==n['z_observed']
    assert d['metrics']['noise']['rmse_mm']>20
    assert d['metrics']['bad_k']['rmse_mm']>30
    assert max(o['projection_error_px'] for o in d['observations'])<2e-4
    assert len(d['video_map'])==d['frame_count']
    report=dict(status='passed',background_depth_m=float(depth[40,10]),
        max_actual_camera_projection_error_px=max(o['projection_error_px'] for o in d['observations']),
        depth_noise_response='delta_P = delta_Z * ray_direction',
        wrong_fx_response='X_est = 1.25 X_ideal; Y and Z unchanged',
        metrics=d['metrics'],sensor=d['sensor'],noise_sigma_m=SIGMA_Z,seed=SEED)
    (OUT/'model_validation.json').write_text(json.dumps(report,indent=2))
    print(json.dumps(report,indent=2))


if __name__=='__main__':main()
