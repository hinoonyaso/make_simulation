import json,subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];O=H/'output';M=H/'visual_manifest.json'
def run(*args):subprocess.run([str(a) for a in args],cwd=ROOT,check=True)
assert abs(sum(b['sec'] for b in json.loads(M.read_text())['beats'])-382.4)<.001
run(sys.executable,H/'validate_render.py')
run(sys.executable,H/'assemble.py')
run(sys.executable,ROOT/'core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py',M,'--require-media')
run(sys.executable,ROOT/'scripts/check_scene_style.py',H/'cases_scene.py',H/'avoidance_scene.py',H/'handoff_scene.py',H/'reasoning_scene.py')
run(sys.executable,ROOT/'core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py',M,O/'sequence.json')
run(sys.executable,ROOT/'scripts/validate_delivery.py',O/'planner_control_long_ko_v18.mp4','--require-audio','--fps','30','--audio-manifest',H/'assets/audio/manifest.json','--caption-timing',O/'caption_timing.json','--full-decode')
print('TECHNICAL GATES PASS; final pixel/motion/audio inspection is separate.',flush=True)
