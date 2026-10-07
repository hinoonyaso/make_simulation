"""Repair already-rendered first two cases after boundary-frame camera review."""
import subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent
script='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/'cases_scene.py').replace('/','\\')
exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
for kind in ['equal','left']:
 out=H/'output/cases'/kind
 with (out/'camera_repair.log').open('w') as log:
  subprocess.run([exe,'-b','--python',script,'--','--case',kind,'--repair'],stdout=log,stderr=subprocess.STDOUT,check=True)
 patch=json.loads((out/'mapping_0026.json').read_text())['records'];assert len(patch)==61
 original=json.loads((out/'mapping_0001.json').read_text());by={r['frame']:r for r in original['records']}
 by.update({r['frame']:r for r in patch});original['records']=[by[f] for f in range(1,182)]
 original['camera_repair']='Frames 26–55,130–160 updated after cut-entry/exit inspection.'
 (out/'mapping_0001.json').write_text(json.dumps(original,indent=2)+'\n')
 subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(out/'frames/frame_%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(out/'raw.mp4')],check=True)
 print(kind,'CAMERA REPAIR PASS',flush=True)
