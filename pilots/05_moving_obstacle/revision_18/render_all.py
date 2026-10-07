"""Sequential GPU renders, safe resume by completed mapping+frame checks."""
import subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output';exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
def render(script,args,log):
 unc='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/script).replace('/','\\')
 with (O/log).open('w') as f:subprocess.run([exe,'-b','--python',unc,'--',*args],stdout=f,stderr=subprocess.STDOUT,check=True)
def encode(frames,path,start,count):
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-start_number',str(start),'-i',str(frames/'frame_%04d.png'),'-frames:v',str(count),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(path)],check=True)
render('handoff_scene.py',[],'handoff_render.log');assert (O/'handoff/source4.png').exists();print('HANDOFF PASS',flush=True)
for kind in ['left','equal','spin','stop']:
 d=O/'cases'/kind
 complete=(d/'mapping_0001.json').exists() and all((d/f'frames/frame_{f:04d}.png').exists() for f in range(1,182))
 if not complete:render('cases_scene.py',['--case',kind,'--variant','selected'],f'cases_{kind}.log')
 assert len(json.loads((d/'mapping_0001.json').read_text())['records'])==181
 encode(d/'frames',d/'raw.mp4',1,181);print(kind,'181 frames PASS',flush=True)
d=O/'blender';frames=list(range(1,279))+list(range(317,723))
if not (d/'mapping.json').exists() or not all((d/f'frames/frame_{f:04d}.png').exists() for f in frames):render('avoidance_scene.py',['--variant','selected'],'avoidance_full.log')
assert len(json.loads((d/'mapping.json').read_text())['records'])==684
encode(d/'frames',d/'opening_raw.mp4',1,278);encode(d/'frames',d/'avoidance_raw.mp4',317,406);print('AVOIDANCE 684 mapped frames PASS',flush=True)
