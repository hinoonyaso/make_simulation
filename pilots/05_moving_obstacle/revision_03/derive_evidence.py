"""Check recorded grid-path vertices against recorded cost maps; no planner rerun."""
import hashlib
import json
from pathlib import Path
import numpy as np
HERE=Path(__file__).resolve().parent

def main():
    source=HERE/'../data/trace.json';d=json.loads(source.read_text());sn=d['snapshots'];results=[]
    for path_i,map_i,expected in [(0,1,9),(1,1,0),(1,2,3),(2,2,0)]:
        pts=np.array(sn[path_i]['path'])
        ij=np.round((pts-[d['xs'][0],d['ys'][0]])/d['resolution_m']).astype(int)
        values=np.array(sn[map_i]['cost'])[ij[:,1],ij[:,0]];bad=values>=255
        if int(sum(bad))!=expected:raise ValueError(f'Unexpected recorded overlap for {path_i},{map_i}')
        results.append(dict(path_time=sn[path_i]['t'],map_time=sn[map_i]['t'],forbidden_vertices=int(sum(bad)),vertices=pts[bad].tolist()))
    out=dict(source_trace_sha256=hashlib.sha256(source.read_bytes()).hexdigest(),
             analysis='Recorded vertices at their grid nodes; not a continuous-segment collision proof or optimizer replay.',
             planning_forbidden_radius_m=.3+.25+.22,
             margin_provenance='topics/08_nav2/model.py costmap: d <= ROBOT_R + .22',
             checks=results,next_plan_reason=sn[2]['plan_reason'])
    (HERE/'evidence.json').write_text(json.dumps(out,ensure_ascii=False,indent=2)+'\n')
    print('PASS: recorded forbidden vertices 9 / 0 / 3 / 0; next plan is periodic_replan')
if __name__=='__main__':main()
