import subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
def render(script,args):
 unc='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/script).replace('/','\\')
 with (H/('output/second_'+script+'_'+'_'.join(args)+'.log')).open('w') as f:subprocess.run(['/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe','-b','--python',unc,'--',*args],stdout=f,stderr=subprocess.STDOUT,check=True)
for frame in [1,181,110]:
 render('cases_scene.py',['--case','left','--variant','selected','--probe-frame',str(frame)])
 assert (H/f'output/cases/left/candidate_selected_{frame:04d}.png').exists();print('case',frame,'PASS',flush=True)
for frame in [317,650]:
 render('avoidance_scene.py',['--variant','selected','--probe-frame',str(frame)])
 assert (H/f'output/blender/candidate_selected_{frame:04d}.png').exists();print('avoidance',frame,'PASS',flush=True)
