"""Sample the actual final: all beats plus defined craft/cut/term boundaries."""
import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;O=H/'output';out=O/'final_review';out.mkdir(exist_ok=True)
media=O/'planner_control_long_ko_v17.mp4'
beats=json.loads((H/'visual_manifest.json').read_text())['beats'];audio=json.loads((H/'assets/audio/manifest.json').read_text());by={r['beat']:r for r in audio}
sets={'overview':[(b['id'],b['sec']*.55) for b in beats], 'physical':[], 'reasoning':[]}
for bid in ['B06','B08','B10','B18']:
 for f in [1,39,55,91,99,100,110,125,126,145,146,181]:sets['physical'].append((bid,min(by[bid]['duration']-.06,(f-1)/181*by[bid]['duration'])))
for bid,times in {'B14':[4,7,10,11.8,12.5,13.5,17.4,18.5,20.5,22,24,26,30,31,35,38], 'B19':[2,5.8,6.5,8.9,10,11.5,12.7,14,19.8,20.5,21.1,21.8,22.5,24.6], 'B20':[0,.5,1.4,1.5,1.6,2,5,12,19]}.items():
 sets['reasoning'].extend((bid,t) for t in times)
index=[]
for group,items in sets.items():
 d=out/group;d.mkdir(exist_ok=True)
 for i,(bid,relative) in enumerate(items):
  t=by[bid]['start']+relative;p=d/f'{i:02d}_{bid}_{t:07.2f}s.jpg'
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t),'-i',str(media),'-frames:v','1','-q:v','2',str(p)],check=True)
  index.append({'group':group,'beat':bid,'time_s':t,'file':str(p.relative_to(H))})
 for batch in range((len(items)+11)//12):
  files=sorted(d.glob('*.jpg'))[batch*12:(batch+1)*12]
  canvas=Image.new('RGB',(960,((len(files)+1)//2)*295),'#222222');draw=ImageDraw.Draw(canvas)
  for n,p in enumerate(files):
   im=Image.open(p);im.thumbnail((480,270));x=n%2*480;y=n//2*295;canvas.paste(im,(x,y));draw.text((x+4,y+271),p.name,fill='white')
  canvas.save(out/f'{group}_{batch}.png')
(out/'index.json').write_text(json.dumps(index,indent=2)+'\n')
print(f'{len(index)} final frames extracted',flush=True)
