"""Final encode and technical gates after reviewing the measured critical excerpt."""
import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];O=H/'output';M=H/'visual_manifest.json'
def run(*args):subprocess.run([str(x) for x in args],cwd=ROOT,check=True)
d=json.loads(M.read_text());duration=sum(b['sec'] for b in d['beats'])
assert 240<=duration<=360,f'Measured duration outside requested 4–6 min: {duration}'
assert all((O/f'cases/{k}/raw.mp4').exists() for k in ['equal','left','spin','stop'])
run('manim','-qh','--fps','30','--resolution','1920,1080','--disable_caching','--media_dir',O/'final_render',H/'reasoning_scene.py','WheelDiscovery')
run('manim','-qh','--fps','30','--resolution','1920,1080','--disable_caching','--media_dir',H/'output/patch',H/'reasoning_scene.py','FixedMeanPatch')
run(sys.executable,H/'assemble.py')
run(sys.executable,ROOT/'core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py',M,'--require-media')
run(sys.executable,ROOT/'scripts/check_scene_style.py',H/'reasoning_scene.py',H/'cases_scene.py')
run(sys.executable,ROOT/'core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py',M,O/'sequence.json')
run(sys.executable,ROOT/'scripts/validate_delivery.py',O/'planner_control_long_ko_v14.mp4','--require-audio','--fps','30','--audio-manifest',H/'assets/audio/manifest.json','--caption-timing',O/'caption_timing.json','--full-decode')
print('Technical gates passed. Inspect final actual frames and record remaining educational limits.',flush=True)
