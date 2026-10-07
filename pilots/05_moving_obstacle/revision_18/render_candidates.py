import subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
unc='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/'cases_scene.py').replace('/','\\')
for variant in ['baseline','material','light','combined']:
 for frame in [1,181,110]:
  log=H/f'output/candidate_{variant}_{frame}.log'
  with log.open('w') as f:subprocess.run([exe,'-b','--python',unc,'--','--case','left','--variant',variant,'--probe-frame',str(frame)],stdout=f,stderr=subprocess.STDOUT,check=True)
  assert (H/f'output/cases/left/candidate_{variant}_{frame:04d}.png').exists()
  print(variant,frame,'PASS',flush=True)
