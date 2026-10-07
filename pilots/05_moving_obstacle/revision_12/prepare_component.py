"""Encode a validated read-only joint replay and its explicit viewing annotations."""
import json,subprocess
from pathlib import Path
from PIL import Image
H=Path(__file__).resolve().parent;O=H/'output/component'
def run(args):subprocess.run([str(x) for x in args],check=True)
records=[]
for p in sorted(O.glob('mapping_*.json')):records.extend(json.loads(p.read_text())['records'])
assert [r['frame'] for r in records]==list(range(1,85))
assert [r['source_sample'] for r in records]==sorted(r['source_sample'] for r in records)
assert records[0]['source_sample']==60 and records[-1]['source_sample']==84
for r in records:
 p=O/f'frames/frame_{r["frame"]:04d}.png'
 with Image.open(p) as im:assert im.size==(1920,1080);im.verify()
 assert max(e['orientation_error_rad'] for e in r['wheel_pose_errors'])<1e-4
 assert max(e['position_error_m'] for e in r['wheel_pose_errors'])<1e-5
font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
labels=[('기록된 바퀴의 실제 응답',45,38),('실험 2.00→2.80초 · 3.5배 느린 재생',95,28),('상판 숨김·위상 점은 보기 위한 주석',135,25),('오른쪽: 파랑 · 왼쪽: 흰 점',171,25)]
filters=[]
for i,(label,y,size) in enumerate(labels):
 label_file=O/f'label_{i}.txt'
 label_file.write_text(label,encoding='utf-8')
 filters.append(f"drawtext=fontfile={font}:textfile={label_file}:x=65:y={y}:fontsize={size}:fontcolor=0x20242a")
vf=','.join(filters)
run(['ffmpeg','-v','error','-y','-framerate','30','-i',O/'frames/frame_%04d.png','-vf',vf,'-frames:v','84','-c:v','libx264','-threads','2','-preset','fast','-crf','18','-pix_fmt','yuv420p',O/'response.mp4'])
(O/'validated_mapping.json').write_text(json.dumps({'status':'PASS','records':records,'frames':84,'native_size':[1920,1080],'source_interval_s':[2,2.8],'presentation_interval_s':[0,2.8],'body_visibility':'hidden frames10–74 only in render','phase_marks':'rigid pivot children, render annotations','claim':'recorded response, not command-driven wheel motion or new simulation'},indent=2)+'\n')
print('PASS: 84 native frames; source order; exact recorded wheel/root transforms; component encoding')
