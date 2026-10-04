import subprocess,json
from pathlib import Path
from PIL import Image,ImageDraw
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'
rows=json.loads((OUT/'render_timeline.json').read_text());board=Image.new('RGB',(1920,2160),'white')
for i,r in enumerate(rows):
 p=OUT/f'review_{i:02}.png'
 subprocess.run(['ffmpeg','-v','error','-y','-ss',str(r['start']+6),'-i',str(OUT/'pixel_depth_simulation_ko_v3.mp4'),'-frames:v','1',str(p)],check=True)
 board.paste(Image.open(p).resize((960,540)),((i%2)*960,(i//2)*540))
board.save(OUT/'review.png')
