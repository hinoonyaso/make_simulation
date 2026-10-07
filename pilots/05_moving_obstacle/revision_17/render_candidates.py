import subprocess,json
from pathlib import Path
H=Path(__file__).resolve().parent;exe='/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe'
def execute(script,args,log):
 unc='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/script).replace('/','\\')
 with log.open('w') as f:subprocess.run([exe,'-b','--python',unc,'--',*args],stdout=f,stderr=subprocess.STDOUT,check=True)
# Handoff already rendered; candidate retry fixes face material slot selection.
assert (H/'output/handoff/source4.png').exists();print('HANDOFF PASS',flush=True)
for variant in ['boundary']:
 for frame in [1]:
  execute('cases_scene.py',['--case','left','--variant',variant,'--probe-frame',str(frame)],H/f'output/candidate_{variant}_{frame}.log')
  assert (H/f'output/cases/left/candidate_{variant}_{frame:04d}.png').exists();print(variant,frame,'PASS',flush=True)
