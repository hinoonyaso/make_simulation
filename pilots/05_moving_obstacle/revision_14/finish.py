"""Run after explicit R14 TTS approval; preserves the one manifest timing contract."""
import subprocess,sys
from pathlib import Path
H=Path(__file__).resolve().parent;ROOT=H.parents[2]
def run(*args):subprocess.run([str(x) for x in args],cwd=ROOT,check=True)
manifest=H/'visual_manifest.json'
if not (H/'output/local_audio_edits.json').exists():
 run(sys.executable,ROOT/'core/narration/prepare_audio.py','tts',manifest)
run(sys.executable,ROOT/'core/narration/prepare_audio.py','captions',manifest,'--model','base')
run('manim','-qm','--fps','30','--resolution','960,540','--disable_caching','--media_dir',H/'output/preview_render',H/'reasoning_scene.py','WheelDiscovery')
run('manim','-qh','--fps','30','--resolution','1920,1080','--disable_caching','--media_dir',H/'output/patch',H/'reasoning_scene.py','FixedMeanPatch')
run(sys.executable,H/'assemble.py','--critical')
print('Measured critical excerpt ready. Inspect actual frames before final rendering.',flush=True)
