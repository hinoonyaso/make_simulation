import subprocess
from pathlib import Path
H=Path(__file__).resolve().parent
unc='\\\\wsl.localhost\\Ubuntu-24.04'+str(H/'cases_scene.py').replace('/','\\')
with (H/'output/cases_full.log').open('w') as f:subprocess.run(['/mnt/c/Program Files/Blender Foundation/Blender 5.2/blender.exe','-b','--python',unc,'--','--case','left','--variant','boundary'],stdout=f,stderr=subprocess.STDOUT,check=True)
assert (H/'output/cases/left/frames/frame_0181.png').exists()
subprocess.run(['ffmpeg','-v','error','-y','-framerate','30','-i',str(H/'output/cases/left/frames/frame_%04d.png'),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p',str(H/'output/cases/left/raw.mp4')],check=True)
