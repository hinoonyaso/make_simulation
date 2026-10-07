"""Finish only after encoded physical media is closed and all mappings exist."""
import time,subprocess,json,sys
from pathlib import Path
H=Path(__file__).resolve().parent;O=H/'output'
paths=[(O/'blender/opening_raw.mp4',278),(O/'blender/avoidance_raw.mp4',406)]+[(O/f'cases/{k}/raw.mp4',181) for k in ['left','equal','spin','stop']]
def ready():
 for p,count in paths:
  if not p.exists():return False
  result=subprocess.run(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=nb_frames','-of','json',str(p)],capture_output=True,text=True)
  if result.returncode:return False
  if json.loads(result.stdout)['streams'][0].get('nb_frames')!=str(count):return False
 return (O/'blender/mapping.json').exists()
while not ready():time.sleep(2)
print('ALL ENCODED PHYSICAL MEDIA READY',flush=True)
with (O/'delivery.log').open('w') as log:subprocess.run([sys.executable,str(H/'deliver.py')],stdout=log,stderr=subprocess.STDOUT,check=True)
subprocess.run([sys.executable,str(H/'review_samples.py')],check=True)
print('DELIVERY GATES AND ACTUAL FINAL FRAME EXTRACTION COMPLETE',flush=True)
