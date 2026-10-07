"""Sample the actual final: all beats plus defined craft/cut/term boundaries."""
import json,subprocess
from pathlib import Path
from PIL import Image,ImageDraw
H=Path(__file__).resolve().parent;O=H/'output';out=O/'final_review';out.mkdir(exist_ok=True)
media=O/'planner_control_long_ko_v16.mp4'
beats=json.loads((H/'visual_manifest.json').read_text())['beats'];audio=json.loads((H/'assets/audio/manifest.json').read_text());by={r['beat']:r for r in audio}
sets={'overview':[(b['id'],b['sec']*.55) for b in beats], 'physical':[], 'reasoning':[]}
for bid in ['B06','B08','B10','B18']:
 for f in [1,39,55,91,145,146,181]:sets['physical'].append((bid,min(by[bid]['duration']-.06,(f-1)/181*by[bid]['duration'])))
for bid,times in {'B05':[7,9,11],'B07':[7,9,11],'B09':[6,8,10],'B12':[2.9,3.6,4.1,4.8,5.7,7.5,8.1,8.4,13.9,14.45,14.9],'B13':[6.5,7.2,7.8,8.2],'B14':[3,5,7,8,10,12,14,16,18,20,22,24],'B15':[.1,.4,.7,1.2,8,10.5,11.5,12.5,13.5,15,16.5],'B11':[3,6,10],'B16':[3,6,12],'B17':[3,6,9,12],'B19':[3,5,6,7,8,9,10,12,14]}.items():
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
comparison=O/'comparison';comparison.mkdir(exist_ok=True)
examples=[('connected_component',121.6),('surface',130.3),('derived_geometry',217.8),('wide_track',241.0),('feedback',302.0),('comparison',169.0)]
canvas=Image.new('RGB',(1920,len(examples)*565),'#222222');draw=ImageDraw.Draw(canvas)
for row,(name,t) in enumerate(examples):
 for col,rev in enumerate(['R15','R16']):
  source=H.parent/'revision_15/output/planner_control_long_ko_v15.mp4' if rev=='R15' else media
  p=comparison/f'{name}_{rev}.jpg'
  subprocess.run(['ffmpeg','-v','error','-y','-ss',str(t+(8 if rev=='R16' and t>=225.233333 else 0)),'-i',str(source),'-frames:v','1','-q:v','2',str(p)],check=True)
  im=Image.open(p);im.thumbnail((960,540));canvas.paste(im,(col*960,row*565));draw.text((col*960+8,row*565+542),f'{rev}: {name} at {t+(8 if rev=="R16" and t>=225.233333 else 0):.2f}s',fill='white')
canvas.save(comparison/'R15_R16.png')
