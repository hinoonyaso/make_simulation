import json,subprocess
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output';r=next(r for r in json.loads((H/'assets/audio/manifest.json').read_text()) if r['beat']=='B08');sec=r['duration'];font='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
filter=f'[0:v]setpts=(PTS-STARTPTS)*{sec/(181/30)},fps=30,scale=960:540,drawtext=fontfile={font}:text=R17:x=35:y=35:fontsize=30:fontcolor=0x20242a[a];[1:v]setpts=(PTS-STARTPTS)*{sec/(181/30)},fps=30,scale=960:540,drawtext=fontfile={font}:text=R18:x=35:y=35:fontsize=30:fontcolor=0x20242a[b];[a][b]hstack=inputs=2[v];[2:a]loudnorm=I=-16:TP=-1.5:LRA=11[s]'
subprocess.run(['ffmpeg','-v','error','-y','-i',str(H.parent/'revision_17/output/cases/left/raw.mp4'),'-i',str(O/'cases/left/raw.mp4'),'-i',str(H/'assets/audio/B08.wav'),'-filter_complex',filter,'-map','[v]','-map','[s]','-t',str(sec),'-c:v','libx264','-threads','2','-crf','18','-pix_fmt','yuv420p','-c:a','aac','-b:a','192k','-movflags','+faststart',str(O/'material_motion_comparison.mp4')],check=True)
print('R17/R18 identical source/state/camera comparison:',sec,'seconds')
