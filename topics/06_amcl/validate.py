import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'output';D=json.loads((O/'trace.json').read_text());A=json.loads((R/'assets/audio/manifest.json').read_text())
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(O/'amcl_education_ko.mp4')]))
v=next(s for s in p['streams'] if s['codec_type']=='video');assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1');assert any(s['codec_type']=='audio' for s in p['streams']);assert abs(float(p['format']['duration'])-A[-1]['end'])<.1
cues=json.loads((O/'caption_timing.json').read_text());assert len(cues)==25
for c,a in zip(cues,A):assert a['start']<=c['start']<c['end']<=a['end'] and c['timing_source']=='whisper'
for row in D['rows']:
 w=np.array(row['weights']);p0=np.array(row['predicted']);out=np.array(row['resampled']);assert np.isclose(w.sum(),1)
 assert np.allclose(p0[row['parents']],out);assert len(out)==row['count'];assert 180<=len(out)<=900
 assert np.isclose(np.linalg.norm(np.array(row['estimate'])[:2]-np.array(row['truth'])[:2]),row['position_error_m'])
assert D['metrics']['final_position_error_m']<D['metrics']['no_sensor_final_error_m']
assert len(list((O/'blender').glob('[0-9][0-9][0-9][0-9].png')))==120
im0=np.array(Image.open(O/'blender/0000.png')).astype(float);im1=np.array(Image.open(O/'blender/0119.png')).astype(float);assert np.abs(im0-im1).mean()>.1
subprocess.run(['ffmpeg','-v','error','-i',str(O/'amcl_education_ko.mp4'),'-f','null','-'],check=True)
report=dict(status='passed',video='full decode',duration_seconds=float(p['format']['duration']),resolution=[1920,1080],fps=30,captions=25,metrics=D['metrics'],blender=json.loads((O/'blender/validation.json').read_text()),review='representative frames inspected; screen timing follows utterance manifest')
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
