"""R18 scoped invariants: optical changes, same audio/data/time, mapped physical states."""
import json,hashlib,subprocess,wave
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output';P=H.parent/'revision_17'
def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def probe(path):return json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames,duration','-of','json',str(path)],text=True))['streams'][0]
assert json.loads((O/'geometry_audit.json').read_text())['status']=='PASS'
checks=[]
for folder,pattern in [('data','*.json'),('assets/audio','B*.wav')]:
 for p in (H/folder).glob(pattern):assert sha(p)==sha(P/folder/p.name);checks.append(str(p.relative_to(H)))
for f in ['assets/audio/manifest.json','output/caption_timing.json','output/narration.wav']:assert sha(H/f)==sha(P/f)
doc=json.loads((H/'visual_manifest.json').read_text());old=json.loads((P/'visual_manifest.json').read_text())
for a,b in zip(doc['beats'],old['beats']):
 assert a['id']==b['id']
 for key in ['narration','caption','sec','audio']:assert a.get(key)==b.get(key),(a['id'],key)
for case in ['equal','left','spin','stop']:
 d=O/'cases'/case;records=json.loads((d/'mapping_0001.json').read_text())['records'];assert len(records)==181 and [r['frame'] for r in records]==list(range(1,182));assert all(r['variant']=='selected' and r['wheel_pose_check']=='PASS' for r in records)
 stream=probe(d/'raw.mp4');assert (stream['width'],stream['height'],stream['r_frame_rate'],stream['nb_frames'])==(1920,1080,'30/1','181')
 settings=json.loads((d/'settings_selected.json').read_text());assert settings['lights']['Key']['energy']==850 and abs(settings['lights']['Key']['size']-2.2)<1e-6 and settings['world_strength']>.25 and settings['variant']=='selected'
recorded=json.loads((O/'blender/mapping.json').read_text())['records'];original=json.loads((H.parent/'revision_10/output/blender/source_mapping.json').read_text());expected=original[:278]+original[316:722];assert len(recorded)==684
for r,e in zip(recorded,expected):
 assert r['wheel_pose_check']=='PASS' and r['variant']=='selected'
 for key in ['frame','source_index','source_t','view','beat']:assert r[key]==e[key],(r,e)
for name,count in [('opening_raw.mp4',278),('avoidance_raw.mp4',406)]:
 stream=probe(O/'blender'/name);assert (stream['width'],stream['height'],stream['r_frame_rate'],stream['nb_frames'])==(1920,1080,'30/1',str(count))
hand=json.loads((O/'handoff/mapping.json').read_text());assert hand['status']=='PASS' and hand['source_pose_sample']==119 and hand['next_encoded_source_sample']==120
stream=probe(O/'final_render/videos/reasoning_scene/1080p30/PatchB19.mp4');assert (stream['width'],stream['height'],stream['r_frame_rate'])==(1920,1080,'30/1')
assert abs(float(stream['duration'])-next(b['sec'] for b in doc['beats'] if b['id']=='B19'))<.25
report={'status':'PASS','identical_to_R17':checks,'audio_caption_timing':'22 WAVs / manifest / concatenated PCM /70 cues byte-identical','case_wheel_pose_checks':724,'avoidance_wheel_pose_checks':684,'source_mapping':'identical R10 pose/view/sample order in displayed ranges','handoff':hand,'new_simulation_run':False}
(O/'render_validation.json').write_text(json.dumps(report,indent=2)+'\n');print('R18 OPTICAL RENDER / SAME AUDIO / SAME SOURCE PASS')
