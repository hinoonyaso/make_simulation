import json,subprocess
from pathlib import Path
import numpy as np
from PIL import Image
R=Path(__file__).resolve().parent;O=R/'output'
p=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-show_streams','-of','json',str(O/'slam_education_ko.mp4')]))
v=next(s for s in p['streams'] if s['codec_type']=='video');a=next(s for s in p['streams'] if s['codec_type']=='audio')
assert (v['width'],v['height'],v['r_frame_rate'])==(1920,1080,'30/1')
manifest=json.loads((R/'assets/audio/manifest.json').read_text());duration=float(p['format']['duration']);assert abs(duration-manifest[-1]['end'])<.1
cues=json.loads((O/'caption_timing.json').read_text());assert len(cues)==len(manifest)==25
for i,c in enumerate(cues):
 assert manifest[i]['start']<=c['start']<c['end']<=manifest[i]['end']
 if i:assert cues[i-1]['end']<=c['start']
assert all(c['timing_source']=='whisper' for c in cues)
D=json.loads((O/'trace.json').read_text());truth=np.array(D['truth']);est=np.array(D['estimates']);odom=np.array(D['odometry']);m=D['metrics']
assert np.isclose(np.sqrt(np.mean(np.sum((est[:,:2]-truth[:,:2])**2,axis=1))),m['position_rmse_corrected_m'])
assert m['position_rmse_corrected_m']<m['position_rmse_odometry_m']
# Ensure the animation frames actually differ after timeline evaluation.
for mode in ['scan','motion']:
 files=list((O/f'blender/{mode}').glob('*.png'));assert len(files)==96
 first=np.array(Image.open(O/f'blender/{mode}/0000.png')).astype(float);last=np.array(Image.open(O/f'blender/{mode}/0095.png')).astype(float)
 assert np.mean(np.abs(first-last))>.1
subprocess.run(['ffmpeg','-v','error','-i',str(O/'slam_education_ko.mp4'),'-f','null','-'],check=True)
report={'video':'passed full decode','resolution':[1920,1080],'fps':30,'duration_seconds':duration,'caption_cues':len(cues),'caption_alignment':'Whisper forced alignment of known Korean TTS','metrics':m,'blender_reopen':json.loads((O/'blender/reopen_validation.json').read_text()),'limitations':'synthetic static 2D environment; no loop closure; single seed estimator run; visual timing adapted to narration'}
(O/'validation.json').write_text(json.dumps(report,ensure_ascii=False,indent=2));print(json.dumps(report,ensure_ascii=False,indent=2))
