"""Reproduce R16 without new TTS or changes to reference sources."""
import argparse,json,subprocess,sys,time
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2];O=H/'output';M=H/'visual_manifest.json'
def run(*args):subprocess.run([str(x) for x in args],cwd=ROOT,check=True)
def main(skip_render=False):
 doc=json.loads(M.read_text());assert 240<=sum(b['sec'] for b in doc['beats'])<=360
 if not skip_render:
  run('manim','-qh','--fps','30','--resolution','1920,1080','--disable_caching','--media_dir',O/'final_render',H/'reasoning_scene.py',*[f'Patch{bid}' for bid in ['B05','B07','B09','B11','B12','B13','B14','B15','B16','B17','B19','B22']])
 run(sys.executable,H/'validate_relations.py')
 run(sys.executable,H/'validate_render.py')
 run(sys.executable,H/'assemble.py')
 run(sys.executable,ROOT/'core/robotics-ai-visual-director-skill/templates/validate_visual_manifest.py',M,'--require-media')
 run(sys.executable,ROOT/'scripts/check_scene_style.py',H/'reasoning_scene.py',H/'cases_scene.py')
 run(sys.executable,ROOT/'core/davinci-resolve-robotics-postproduction-skill/scripts/stage_segments.py',M,O/'sequence.json')
 run(sys.executable,ROOT/'scripts/validate_delivery.py',O/'planner_control_long_ko_v16.mp4','--require-audio','--fps','30','--audio-manifest',H/'assets/audio/manifest.json','--caption-timing',O/'caption_timing.json','--full-decode')
 print('TECHNICAL GATES PASS; final frame and educational inspection remain separate.',flush=True)
if __name__=='__main__':
 p=argparse.ArgumentParser();p.add_argument('--skip-render',action='store_true');main(p.parse_args().skip_render)
