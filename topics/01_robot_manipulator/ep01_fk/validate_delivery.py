"""Validate the computed model, shared timeline and encoded deliverable."""
import json
import subprocess
from pathlib import Path
import numpy as np
from model import validate

ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'

def main():
    timeline=json.loads((OUT/'timeline.json').read_text())
    trace=json.loads((OUT/'trace.json').read_text())['frames']
    assert len(trace)==timeline['frames']
    joints=np.array([f['joints'] for f in trace])
    length_error=float(np.max(np.abs(np.linalg.norm(np.diff(joints,axis=1),axis=2)-[2,1.5])))
    assert length_error<1e-12
    for beat in timeline['beats']:
        assert all(f['beat']==beat['id'] for f in trace[beat['start_frame']:beat['end_frame']])
    video=OUT/'EP01_3DOF_Forward_Kinematics_KO.mp4'
    probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(video)]))
    v=next(s for s in probe['streams'] if s['codec_type']=='video')
    a=next(s for s in probe['streams'] if s['codec_type']=='audio')
    assert (v['width'],v['height'])==(1920,1080)
    assert v['r_frame_rate']=='30/1'
    assert int(v['nb_frames'])==timeline['frames'],(v['nb_frames'],timeline['frames'])
    assert abs(float(v['duration'])-timeline['duration'])<.04
    assert abs(float(a['duration'])-timeline['duration'])<.1
    decode=subprocess.run(['ffmpeg','-v','error','-i',str(video),'-f','null','-'],capture_output=True,text=True)
    assert decode.returncode==0 and not decode.stderr.strip(),decode.stderr
    report=dict(model=validate(),max_link_length_error_m=length_error,trace_frames=len(trace),
                resolution=[v['width'],v['height']],fps=v['r_frame_rate'],video_codec=v['codec_name'],audio_codec=a['codec_name'],
                video_duration=float(v['duration']),audio_duration=float(a['duration']),full_decode='pass',
                visual_review='See review_report.md; pixel review is distinct from numerical checks.')
    (OUT/'final_validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2))
    print(json.dumps(report,ensure_ascii=False,indent=2))

if __name__=='__main__': main()
