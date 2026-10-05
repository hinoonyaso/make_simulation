"""Checks measured poses; geometric proximity is not a force/contact measurement."""
import json,math,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent
report={'scope':'simplified open-loop Bullet experiment','checks':{},'limitations':['not calibrated TurtleBot3 dynamics; simplified box, ideal casters','no Nav2, sensing or planner','no solver contact-force export; stall is observed motion evidence']}
for case in ['clear','blocked']:
    runs={}
    for name in ['baseline','repeat','fine']:
        p=H/'data'/f'{name}_{case}.json'
        subprocess.run([sys.executable,str(H.parents[1]/'core/shared-data/validate_trace.py'),str(p)],check=True)
        runs[name]=json.loads(p.read_text())['samples']
    a,b,c=(runs[k] for k in ['baseline','repeat','fine'])
    repeat=max(abs(x-y) for r,t in zip(a,b) for x,y in zip(r['root_position_m'],t['root_position_m']))
    delta=math.dist(a[-1]['root_position_m'],c[-1]['root_position_m'])
    progress=a[-1]['root_position_m'][0]-a[0]['root_position_m'][0]
    last_speed=max(abs(r['velocity_m_s'][0]) for r in a[-30:])
    assert repeat<1e-6 and delta<.06
    assert progress>1.2 if case=='clear' else .65<progress<.8 and last_speed<.01
    assert all(abs(r['root_position_m'][2])<.01 for r in a)
    report['checks'][case]={'repeat_max_position_error_m':repeat,'fine_endpoint_difference_m':delta,'forward_progress_m':progress,'last_second_max_forward_speed_m_s':last_speed}
report['status']='PASS for repeatability, stable qualitative outcome and endpoint sensitivity below 0.06 m; not physical calibration'
(H/'output').mkdir(exist_ok=True)
(H/'output/physics_review.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report,indent=2))
