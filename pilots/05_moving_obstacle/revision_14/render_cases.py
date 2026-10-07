"""Bounded Blender jobs with artifact checks (Windows can exit 0 after Python errors)."""
import subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent
exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
script='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/'cases_scene.py').replace('/','\\')
for case in ['equal','left','spin','stop']:
 for start,end in [(1,60),(61,120),(121,181)]:
  out=H/'output/cases'/case;out.mkdir(parents=True,exist_ok=True)
  with (out/f'render_{start:04d}.log').open('w') as log:
   subprocess.run([exe,'-b','--python',script,'--','--case',case,'--start-frame',str(start),'--end-frame',str(end)],stdout=log,stderr=subprocess.STDOUT,check=True)
  mapping=json.loads((out/f'mapping_{start:04d}.json').read_text());assert len(mapping['records'])==end-start+1
  assert all((out/f'frames/frame_{f:04d}.png').exists() for f in range(start,end+1))
  print(case,start,end,'PASS',flush=True)
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(out/'frames/frame_%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(out/'raw.mp4')],check=True)
print('ALL CASE RENDERS PASS',flush=True)
