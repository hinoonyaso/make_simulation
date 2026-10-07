import subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent
exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
script='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/'cases_scene.py').replace('/','\\')
for variant in ['baseline','material','light']:
 for f in [1,91]:
  out=H/'output/cases/left';out.mkdir(parents=True,exist_ok=True)
  with (out/f'candidate_{variant}_{f}.log').open('w') as log:
   subprocess.run([exe,'-b','--python',script,'--','--case','left','--variant',variant,'--probe-frame',str(f)],stdout=log,stderr=subprocess.STDOUT,check=True)
  assert (out/f'candidate_{variant}_{f:04d}.png').exists()
  print(variant,f,'READY',flush=True)
