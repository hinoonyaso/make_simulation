"""Frame-exact composition from Manim + Blender + the validated sensor trace."""
import json, subprocess, functools
from pathlib import Path
import numpy as np
from PIL import Image,ImageDraw,ImageFont
ROOT=Path(__file__).resolve().parent;OUT=ROOT/'output'
FONT='/usr/share/fonts/truetype/nanum/NanumGothic.ttf'
F=ImageFont.truetype(FONT,28);SM=ImageFont.truetype(FONT,23)
INK='#202D43';BLUE='#2676D5';RED='#D34F55';GREEN='#198F70'
@functools.lru_cache(maxsize=40)
def load(path,size):return Image.open(path).convert('RGB').resize(size,Image.Resampling.LANCZOS)
@functools.lru_cache(maxsize=10)
def depth_image(name):
 a=np.load(OUT/'data'/f'{name}.npy');q=np.clip((a-1)/3.5,0,1)*3
 stops=np.array([[56,90,175],[37,190,208],[242,210,74],[230,123,50]])
 i=np.minimum(q.astype(int),2);col=stops[i]*(1-(q-i)[...,None])+stops[i+1]*(q-i)[...,None]
 return Image.fromarray(col.astype('uint8')).resize((560,420),Image.Resampling.NEAREST)
def t(s):
 n=round(s*100);h,n=divmod(n,360000);m,n=divmod(n,6000);sec,n=divmod(n,100);return f'{h}:{m:02}:{sec:02}.{n:02}'
def main():
 trace=json.loads((OUT/'trace.json').read_text());W,H=1920,1080
 source=ROOT/'media/videos/lesson/1080p30/PixelDepthSimulation.mp4'
 decoder=subprocess.Popen(['ffmpeg','-v','error','-i',str(source),'-f','rawvideo','-pix_fmt','rgb24','-'],stdout=subprocess.PIPE)
 encoder=subprocess.Popen(['ffmpeg','-v','error','-y','-f','rawvideo','-pix_fmt','rgb24','-s','1920x1080','-r','30','-i','-','-an','-c:v','libx264','-crf','18','-preset','fast','-threads','4','-pix_fmt','yuv420p',str(OUT/'composite_silent.mp4')],stdin=subprocess.PIPE)
 for frame,sid in enumerate(trace['video_map']):
  raw=decoder.stdout.read(W*H*3);assert len(raw)==W*H*3,(frame,len(raw))
  im=Image.frombytes('RGB',(W,H),raw);st=trace['states'][sid];ci=st['phase'];d=ImageDraw.Draw(im)
  if ci<7:
   im.paste(load(str(OUT/'blender/world'/f"{st['view_id']:04}.png"),(840,540)),(80,270))
   d.rectangle((220,807,800,848),fill='#F7F9FC');d.text((235,812),'● 실제 표면',font=F,fill=GREEN);d.text((525,812),'○ 복원 위치',font=F,fill=RED)
   d.text((115,858),f"t = {st['sim_time']:.2f} s   |   sample {st['sample']:03}",font=SM,fill=INK)
   d.text((115,910),'P = ('+', '.join(f'{x:+.3f}' for x in st['estimated'])+') m',font=F,fill=RED)
   if ci in [1,2]:
    img=load(str(OUT/'blender/rgb'/f"{st['geometry_id']:04}.png"),(560,420)).copy() if ci==1 else depth_image(st['depth_id']).copy()
    mark=ImageDraw.Draw(img);u,v=st['uv'];x=(u+.5)*3.5;y=(v+.5)*3.5
    mark.ellipse((x-9,y-9,x+9,y+9),outline='white',width=3);mark.line((x-15,y,x+15,y),fill='black',width=2);mark.line((x,y-15,x,y+15),fill='black',width=2)
    im.paste(img,(1150,300));d=ImageDraw.Draw(im)
    d.text((1170,735),f"(u,v) = ({u},{v})   Z = {st['z_observed']:.3f} m",font=SM,fill=INK)
    if ci==2:
     for x in range(560):
      q=x/559*3;i=min(int(q),2);cs=np.array([[56,90,175],[37,190,208],[242,210,74],[230,123,50]]);c=tuple((cs[i]*(1-q+i)+cs[i+1]*(q-i)).astype(int));d.line((1150+x,710,1150+x,720),fill=c)
     d.text((1150,680),'1.0 m',font=SM,fill='white');d.text((1630,680),'4.5 m',font=SM,fill='black')
   if ci in [4,5]:
    x0,y0,x1,y1=1120,610,1750,815
    d.text((1120,560),'3D 위치 오차 [mm]',font=SM,fill=INK)
    for value in [0,50,100,150]:
     y=y1-value/150*(y1-y0);d.line((x0,y,x1,y),fill='#DDE5EF',width=2);d.text((x0-47,y-12),str(value),font=SM,fill=INK)
    ids=trace['phase_states'][ci][:st['sample']+1]
    pts=[(x0+trace['states'][i]['sim_time']/10*(x1-x0),y1-trace['states'][i]['error_mm']/150*(y1-y0)) for i in ids]
    if len(pts)>1:d.line(pts,fill=RED,width=3)
    d.text((1120,835),f"현재 {st['error_mm']:.2f} mm",font=F,fill=RED);d.text((1550,840),'0 → 10 s',font=SM,fill=INK)
   if ci==3:d.text((1160,740),f"(u,v)=({st['uv'][0]}, {st['uv'][1]})   Z={st['z_observed']:.3f} m",font=SM,fill=BLUE)
  d.rectangle((70,980,1850,985),fill='#DDE5EF');d.rectangle((70,980,70+1780*(frame+1)/len(trace['video_map']),985),fill=BLUE)
  encoder.stdin.write(im.tobytes())
  if frame%600==0:print('COMPOSITE',frame,flush=True)
 decoder.stdout.close();assert decoder.wait()==0;encoder.stdin.close();assert encoder.wait()==0
 cues=json.loads((OUT/'caption_timing.json').read_text())
 ass='''[Script Info]
ScriptType: v4.00+
PlayResX: 1920
PlayResY: 1080
[V4+ Styles]
Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding
Style: Main,NanumGothic,34,&H00FFFFFF,&H00FFFFFF,&H00432D20,&H00432D20,0,0,0,0,100,100,0,0,3,7,0,2,30,30,28,1
[Events]
Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
'''
 ass+=''.join(f"Dialogue: 0,{t(c['start'])},{t(c['end'])},Main,,0,0,0,,{c['caption']}\n" for c in cues);(OUT/'subtitles.ko.ass').write_text(ass)
 doc=json.loads((ROOT/'storyboard.json').read_text());timeline=json.loads((OUT/'render_timeline.json').read_text())
 meta=';FFMETADATA1\ntitle=Pixel + Depth → 3D XYZ\nlanguage=kor\n'
 for row,ch in zip(timeline,doc['chapters']):meta+=f"[CHAPTER]\nTIMEBASE=1/1000\nSTART={round(row['start']*1000)}\nEND={round(row['end']*1000)}\ntitle={ch['title']}\n"
 (OUT/'chapters.ffmeta').write_text(meta)
 subprocess.run(['ffmpeg','-v','error','-y','-i',str(OUT/'composite_silent.mp4'),'-i',str(OUT/'narration.wav'),'-i',str(OUT/'chapters.ffmeta'),'-map','0:v:0','-map','1:a:0','-map_metadata','2','-map_chapters','2','-vf',f"ass={OUT/'subtitles.ko.ass'}",'-af','loudnorm=I=-16:TP=-1.5:LRA=11','-c:v','libx264','-crf','18','-preset','fast','-threads','4','-c:a','aac','-b:a','192k','-t',str(len(trace['video_map'])/30),'-movflags','+faststart',str(OUT/'pixel_depth_simulation_ko_v3.mp4')],check=True)
if __name__=='__main__':main()
