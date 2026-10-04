"""Render and package the QLoRA lesson."""
import json, subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent
OUT=ROOT/'output'; OUT.mkdir(exist_ok=True)
def run(*args): subprocess.run(args,check=True,cwd=ROOT)
run('uv','run','--offline','manim','-qh','--fps','30','--media_dir',str(ROOT/'media'),'qlora_video.py','QLoRALesson')
src=ROOT/'media/videos/qlora_video/1080p30/QLoRALesson.mp4'
run('ffmpeg','-v','error','-y','-i',str(src),'-f','lavfi','-i','anullsrc=r=48000:cl=stereo','-shortest','-c:v','copy','-c:a','aac','-b:a','128k','-movflags','+faststart',str(OUT/'qlora_education_ko.mp4'))
info=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(OUT/'qlora_education_ko.mp4')]))
(OUT/'validation.json').write_text(json.dumps(info,indent=2))
print(OUT/'qlora_education_ko.mp4')
